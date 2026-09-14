from __future__ import annotations

import asyncio
import uuid
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ApiError
from app.db import SessionLocal
from app.domain.enums import ActionType, AgentRunStatus, CaseStatus, utcnow
from app.infrastructure.embeddings import search_knowledge
from app.infrastructure.llm import get_llm_provider, structured_decision_from_engine
from app.models.entities import AgentAction, AgentRun, Decision, PurchasingCase, ValidationEvent
from app.rules.constraints import assess_risk, validate_quantity
from app.rules.replenishment import ReplenishmentInput, calculate_replenishment
from app.services.audit import record_audit, run_logged_tool
from app.services.execution import create_or_modify_po, read_po_quantity
from app.services.procurement import (
    get_alternate_suppliers,
    get_budget,
    get_business_rules_map,
    get_forecast,
    get_inventory,
    get_open_pos,
    get_storage,
    get_supplier_constraints,
)


class AgentGraphState(TypedDict, total=False):
    case_id: str
    run_id: str
    approved: bool
    recovery_attempts: int
    stage: str
    evidence: dict[str, Any]
    replenishment: dict[str, Any]
    decision: dict[str, Any]
    needs_approval: bool
    validation: dict[str, Any]
    execution: dict[str, Any]


class PurchasingAgent:
    """LangGraph purchasing agent. LLM never writes to the database."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()
        self.investigate_graph = self._build_investigate_graph()
        self.execute_graph = self._build_execute_graph()

    def _uid(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)

    async def _run(self, state: AgentGraphState) -> AgentRun:
        run = await self.session.get(AgentRun, self._uid(state["run_id"]))
        if not run:
            raise ApiError(404, "run_not_found", "Agent run not found")
        return run

    async def _case(self, state: AgentGraphState) -> PurchasingCase:
        case = await self.session.get(PurchasingCase, self._uid(state["case_id"]))
        if not case:
            raise ApiError(404, "case_not_found", "Purchasing case not found")
        return case

    def _build_investigate_graph(self):
        g = StateGraph(AgentGraphState)
        g.add_node("load_case", self.load_case)
        g.add_node("investigate", self.investigate)
        g.add_node("rag", self.rag)
        g.add_node("apply_rules", self.apply_rules)
        g.add_node("generate_decision", self.generate_decision)
        g.add_node("await_approval", self.await_approval)
        g.add_node("complete_no_action", self.complete_no_action)
        g.add_node("execute", self.execute)
        g.add_node("validate", self.validate)
        g.add_node("recovery", self.recovery)
        g.add_node("success", self.success)
        g.add_node("escalate", self.escalate)
        g.add_edge(START, "load_case")
        g.add_edge("load_case", "investigate")
        g.add_edge("investigate", "rag")
        g.add_edge("rag", "apply_rules")
        g.add_edge("apply_rules", "generate_decision")
        g.add_conditional_edges(
            "generate_decision",
            self.route_after_decision,
            {
                "await_approval": "await_approval",
                "execute": "execute",
                "complete_no_action": "complete_no_action",
            },
        )
        g.add_edge("await_approval", END)
        g.add_edge("complete_no_action", END)
        g.add_edge("execute", "validate")
        g.add_conditional_edges(
            "validate",
            self.route_validation,
            {"success": "success", "recovery": "recovery", "escalate": "escalate"},
        )
        g.add_edge("recovery", "execute")
        g.add_edge("success", END)
        g.add_edge("escalate", END)
        return g.compile()

    def _build_execute_graph(self):
        g = StateGraph(AgentGraphState)
        g.add_node("execute", self.execute)
        g.add_node("validate", self.validate)
        g.add_node("recovery", self.recovery)
        g.add_node("success", self.success)
        g.add_node("escalate", self.escalate)
        g.add_edge(START, "execute")
        g.add_edge("execute", "validate")
        g.add_conditional_edges(
            "validate",
            self.route_validation,
            {"success": "success", "recovery": "recovery", "escalate": "escalate"},
        )
        g.add_edge("recovery", "execute")
        g.add_edge("success", END)
        g.add_edge("escalate", END)
        return g.compile()

    async def load_case(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.status = AgentRunStatus.RUNNING
        run.stage = "LOAD_CASE"
        run.started_at = run.started_at or utcnow()
        case.status = CaseStatus.INVESTIGATING
        await record_audit(
            self.session,
            event_type="run_started",
            case_id=case.id,
            run_id=run.id,
            payload={"stage": "LOAD_CASE"},
        )
        await self.session.flush()
        return {**state, "stage": "LOAD_CASE"}

    async def investigate(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.stage = "INVESTIGATE"
        product_id, node_id, supplier_id = case.product_id, case.node_id, case.supplier_id

        async def parallel_read(reader):
            async with SessionLocal() as extra:
                return await reader(extra)

        inventory, forecast, open_pos, supplier, budget, storage, rules_map = await asyncio.gather(
            parallel_read(lambda s: get_inventory(s, product_id, node_id)),
            parallel_read(lambda s: get_forecast(s, product_id, node_id)),
            parallel_read(lambda s: get_open_pos(s, product_id, node_id, exclude_po_id=case.current_po_id)),
            parallel_read(lambda s: get_supplier_constraints(s, supplier_id, product_id)),
            parallel_read(lambda s: get_budget(s, node_id)),
            parallel_read(lambda s: get_storage(s, node_id)),
            parallel_read(get_business_rules_map),
        )
        logged = [
            ("get_inventory", {"sku": str(product_id)}, "Retrieved current inventory", inventory),
            ("get_demand_forecast", {"sku": str(product_id)}, "Retrieved demand forecast", forecast),
            (
                "get_open_purchase_orders",
                {"sku": str(product_id)},
                "Retrieved open purchase orders",
                open_pos,
            ),
            (
                "get_supplier_constraints",
                {"supplier_id": str(supplier_id)},
                "Retrieved supplier constraints",
                supplier,
            ),
            ("get_budget", {"node_id": str(node_id)}, "Checked purchasing budget", budget),
            (
                "get_storage_capacity",
                {"node_id": str(node_id)},
                "Checked storage capacity",
                storage,
            ),
            ("get_business_rules", {}, "Applied replenishment policy", rules_map),
        ]
        for name, inputs, summary, value in logged:

            async def _ret(v=value):
                return v

            await run_logged_tool(
                self.session,
                run_id=run.id,
                case_id=case.id,
                tool_name=name,
                inputs=inputs,
                summary=summary,
                fn=_ret,
            )
        evidence: dict[str, Any] = {
            "inventory": inventory.model_dump(),
            "forecast": forecast.model_dump(),
            "open_pos": open_pos.model_dump(),
            "supplier": supplier.model_dump(),
            "budget": budget.model_dump(),
            "storage": storage.model_dump(),
            "rules": rules_map,
            "original_recommended_qty": case.original_recommended_qty,
            "scenario_key": case.scenario_key,
        }
        if case.scenario_key == "supplier_shortfall":
            alts = await run_logged_tool(
                self.session,
                run_id=run.id,
                case_id=case.id,
                tool_name="get_alternate_suppliers",
                inputs={"product_id": str(case.product_id)},
                summary="Retrieved alternative suppliers",
                fn=lambda: get_alternate_suppliers(self.session, case.product_id, case.supplier_id),
            )
            evidence["alternate_suppliers"] = [a.model_dump() for a in alts]
        await self.session.flush()
        return {**state, "stage": "INVESTIGATE", "evidence": evidence}

    async def rag(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.stage = "RAG"
        hits = await run_logged_tool(
            self.session,
            run_id=run.id,
            case_id=case.id,
            tool_name="search_knowledge_base",
            inputs={"query": "approval threshold replenishment storage MOQ"},
            summary="Searched procurement policies",
            fn=lambda: search_knowledge(
                self.session,
                "Can purchases above $1,000 be auto-approved? Replenishment and storage policy.",
            ),
        )
        evidence = {**state.get("evidence", {}), "knowledge": [h.model_dump() for h in hits]}
        await self.session.flush()
        return {**state, "evidence": evidence, "stage": "RAG"}

    async def apply_rules(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.stage = "CHECK_CONSTRAINTS"
        ev = state["evidence"]
        rules = ev.get("rules") or {}
        target = int(float(rules.get("target_stock", self.settings.target_stock_default)))
        supplier = ev["supplier"]

        async def calc() -> dict[str, Any]:
            inp = ReplenishmentInput(
                on_hand=ev["inventory"]["on_hand"],
                inbound_open_po=ev["open_pos"]["total_inbound"],
                lead_time_demand=ev["forecast"]["quantity"],
                target_stock=target,
                moq=supplier.get("moq"),
                unit_price=supplier["unit_price"],
                budget_remaining=ev["budget"]["remaining"],
                storage_additional=ev["storage"]["additional_units_available"],
                supplier_max_available=supplier.get("max_available"),
                original_recommended_qty=case.original_recommended_qty,
            )
            return calculate_replenishment(inp).model_dump()

        result = await run_logged_tool(
            self.session,
            run_id=run.id,
            case_id=case.id,
            tool_name="calculate_replenishment",
            inputs={"target_stock": target},
            summary="Calculated net inventory position",
            fn=calc,
        )
        if supplier.get("lead_time_days") is None or supplier.get("moq") is None:
            result["decision"] = "INVESTIGATE"
            result["feasible"] = False
            codes = list(result.get("reason_codes") or [])
            if "SUPPLIER_DATA_INCOMPLETE" not in codes:
                codes.append("SUPPLIER_DATA_INCOMPLETE")
            result["reason_codes"] = codes

        if case.scenario_key == "supplier_shortfall":
            max_av = supplier.get("max_available")
            if max_av is not None and case.original_recommended_qty > max_av:
                result["decision"] = "MODIFY"
                result["recommended_quantity"] = int(max_av)
                codes = list(result.get("reason_codes") or [])
                codes.append("SUPPLIER_CAPACITY_SHORTFALL")
                result["reason_codes"] = list(dict.fromkeys(codes))

        async def val() -> dict[str, Any]:
            report = validate_quantity(
                qty=int(result["recommended_quantity"]),
                moq=supplier.get("moq"),
                storage_additional=ev["storage"]["additional_units_available"],
                budget_remaining=ev["budget"]["remaining"],
                unit_price=supplier["unit_price"],
                supplier_max=supplier.get("max_available"),
                supplier_valid=supplier["status"] == "active",
            )
            return report.model_dump()

        await run_logged_tool(
            self.session,
            run_id=run.id,
            case_id=case.id,
            tool_name="validate_purchase_quantity",
            inputs={"qty": result["recommended_quantity"]},
            summary="Validated proposed quantity",
            fn=val,
        )
        await self.session.flush()
        return {**state, "replenishment": result, "stage": "CHECK_CONSTRAINTS"}

    async def generate_decision(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.stage = "GENERATE_DECISION"
        rep = state["replenishment"]
        ev = state["evidence"]
        qty = int(rep["recommended_quantity"])
        decision = str(rep["decision"])
        original = case.original_recommended_qty
        delta_ratio = abs(qty - original) / original if original else 1.0
        financial = float(rep.get("financial_impact") or 0)
        risk, needs_approval = assess_risk(
            financial_impact=financial,
            decision=decision,
            medium_threshold=self.settings.approval_amount_medium,
            high_threshold=self.settings.approval_amount_high,
            qty_delta_ratio=delta_ratio,
        )
        if decision == "INVESTIGATE":
            action = ActionType.NONE
            needs_approval = True
        elif decision == "REJECT" or qty == 0:
            action = ActionType.NONE
        elif case.scenario_key == "supplier_shortfall":
            action = ActionType.CREATE_ALTERNATE_PO
        elif case.current_po_id and decision == "MODIFY":
            action = ActionType.MODIFY_PO
        elif decision in ("ACCEPT", "MODIFY"):
            action = ActionType.CREATE_PO
        else:
            action = ActionType.NONE

        knowledge = ev.get("knowledge") or []
        citations = [h["title"] for h in knowledge[:3]]
        excerpts = [h.get("excerpt", "") for h in knowledge[:2]]
        llm = get_llm_provider()
        explanation = await llm.explain_decision(
            evidence=ev,
            engine_decision=decision,
            quantity=qty,
            reason_codes=rep.get("reason_codes") or [],
            policy_excerpts=excerpts or citations,
        )
        output = structured_decision_from_engine(
            decision=decision,
            qty=qty,
            confidence=0.92 if decision != "INVESTIGATE" else 0.55,
            risk=risk.value,
            requires_approval=needs_approval,
            reasons=rep.get("reason_codes") or [],
            evidence={k: ev[k] for k in ev if k != "knowledge"},
            explanation=explanation,
            action=action.value,
            citations=citations,
            financial_impact=financial,
        )
        self.session.add(
            Decision(
                run_id=run.id,
                case_id=case.id,
                decision=output.decision.value,
                recommended_quantity=output.recommended_quantity,
                confidence=output.confidence,
                risk_level=output.risk_level.value,
                requires_approval=output.requires_approval,
                reason_codes=output.reason_codes,
                evidence=output.evidence,
                explanation=output.explanation,
                action=output.action.value,
                policy_citations=output.policy_citations,
                financial_impact=output.financial_impact,
            )
        )
        case.risk_level = output.risk_level.value
        await record_audit(
            self.session,
            event_type="decision",
            case_id=case.id,
            run_id=run.id,
            payload={"decision": output.decision.value, "qty": qty},
        )
        await self.session.flush()
        return {
            **state,
            "decision": output.model_dump(mode="json"),
            "needs_approval": needs_approval,
            "stage": "GENERATE_DECISION",
        }

    def route_after_decision(self, state: AgentGraphState) -> str:
        decision = (state.get("decision") or {}).get("decision")
        action = (state.get("decision") or {}).get("action")
        if decision in ("INVESTIGATE", "REJECT") or action == "NONE":
            return "complete_no_action"
        if state.get("approved"):
            return "execute"
        if state.get("needs_approval"):
            return "await_approval"
        return "execute"

    async def await_approval(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.status = AgentRunStatus.AWAITING_APPROVAL
        run.stage = "WAIT_FOR_APPROVAL"
        case.status = CaseStatus.AWAITING_APPROVAL
        await record_audit(self.session, event_type="approval_requested", case_id=case.id, run_id=run.id, payload={})
        await self.session.flush()
        return {**state, "stage": "WAIT_FOR_APPROVAL"}

    async def complete_no_action(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        decision = (state.get("decision") or {}).get("decision")
        if decision == "INVESTIGATE":
            case.status = CaseStatus.ESCALATED
            run.status = AgentRunStatus.ESCALATED
        else:
            case.status = CaseStatus.CLOSED
            run.status = AgentRunStatus.COMPLETED
        run.stage = "SUCCESS"
        run.finished_at = utcnow()
        if run.started_at:
            run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
        await self.session.flush()
        return {**state, "stage": "SUCCESS"}

    async def execute(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.status = AgentRunStatus.EXECUTING
        run.stage = "EXECUTE_ACTION"
        case.status = CaseStatus.EXECUTING
        decision_data = state["decision"]
        qty = int(decision_data["recommended_quantity"])
        supplier = state["evidence"]["supplier"]
        dec_row = (
            (
                await self.session.execute(
                    select(Decision).where(Decision.run_id == run.id).order_by(Decision.created_at.desc())
                )
            )
            .scalars()
            .first()
        )
        if not dec_row:
            raise ApiError(400, "no_decision", "Cannot execute without a decision")
        recovery = int(state.get("recovery_attempts") or 0) > 0
        idem = f"{case.case_number}-{run.id}-r{state.get('recovery_attempts') or 0}"
        existing = (
            await self.session.execute(select(AgentAction).where(AgentAction.idempotency_key == idem))
        ).scalar_one_or_none()
        if existing and existing.status == "executed":
            return {**state, "stage": "EXECUTE_ACTION", "execution": existing.result_json}

        action_row = AgentAction(
            decision_id=dec_row.id,
            case_id=case.id,
            action_type=decision_data["action"],
            idempotency_key=idem,
            payload={"quantity": qty},
            status="pending",
        )
        self.session.add(action_row)
        await self.session.flush()

        async def do_exec() -> dict[str, Any]:
            return await create_or_modify_po(
                self.session,
                case=case,
                supplier_id=case.supplier_id,
                product_id=case.product_id,
                quantity=qty,
                unit_price=supplier["unit_price"],
                idempotency_key=idem,
                modify_existing=decision_data["action"] in ("MODIFY_PO", "CREATE_ALTERNATE_PO")
                or bool(case.current_po_id),
                force_mismatch=case.force_validation_mismatch,
                recovery=recovery,
            )

        tool_name = (
            "modify_purchase_order" if decision_data["action"] == "MODIFY_PO" or recovery else "create_purchase_order"
        )
        result = await run_logged_tool(
            self.session,
            run_id=run.id,
            case_id=case.id,
            tool_name=tool_name,
            inputs={"quantity": qty, "idempotency_key": idem},
            summary="Created or modified purchase order",
            fn=do_exec,
        )
        action_row.status = "executed"
        action_row.result_json = result
        await record_audit(self.session, event_type="action_executed", case_id=case.id, run_id=run.id, payload=result)
        await self.session.flush()
        return {**state, "stage": "EXECUTE_ACTION", "execution": result}

    async def validate(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.status = AgentRunStatus.VALIDATING
        run.stage = "VALIDATE_ACTION"
        qty = int(state["decision"]["recommended_quantity"])
        ev = state["evidence"]
        po_id = case.current_po_id
        if not po_id:
            raise ApiError(400, "po_missing", "No purchase order to validate")

        actual = await run_logged_tool(
            self.session,
            run_id=run.id,
            case_id=case.id,
            tool_name="validate_purchase_order",
            inputs={"expected_quantity": qty},
            summary="Validated resulting purchase order",
            fn=lambda: read_po_quantity(self.session, po_id, case.product_id),
        )
        violations: list[dict[str, Any]] = []
        if actual["quantity"] != qty:
            violations.append({"code": "QUANTITY_MISMATCH", "message": f"Expected {qty}, actual {actual['quantity']}"})
        report = validate_quantity(
            qty=actual["quantity"],
            moq=ev["supplier"].get("moq"),
            storage_additional=ev["storage"]["additional_units_available"],
            budget_remaining=ev["budget"]["remaining"] + qty * ev["supplier"]["unit_price"],
            unit_price=ev["supplier"]["unit_price"],
            supplier_max=ev["supplier"].get("max_available"),
            supplier_valid=ev["supplier"]["status"] == "active",
        )
        for v in report.violations:
            violations.append(v.model_dump())
        passed = len(violations) == 0
        action_row = (
            (
                await self.session.execute(
                    select(AgentAction).where(AgentAction.case_id == case.id).order_by(AgentAction.created_at.desc())
                )
            )
            .scalars()
            .first()
        )
        self.session.add(
            ValidationEvent(
                action_id=action_row.id if action_row else None,
                run_id=run.id,
                expected_json={"quantity": qty},
                actual_json=actual,
                passed=passed,
                violations=violations,
                recovery_required=not passed,
            )
        )
        await record_audit(
            self.session,
            event_type="validation",
            case_id=case.id,
            run_id=run.id,
            payload={"passed": passed, "violations": violations},
        )
        await self.session.flush()
        return {**state, "stage": "VALIDATE_ACTION", "validation": {"passed": passed, "violations": violations}}

    def route_validation(self, state: AgentGraphState) -> str:
        if (state.get("validation") or {}).get("passed"):
            return "success"
        if int(state.get("recovery_attempts") or 0) >= 1:
            return "escalate"
        return "recovery"

    async def recovery(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.status = AgentRunStatus.RECOVERY
        run.stage = "RECOVERY"
        case.status = CaseStatus.RECOVERY
        await record_audit(
            self.session, event_type="recovery", case_id=case.id, run_id=run.id, payload={"action": "MODIFY_PO"}
        )
        await self.session.flush()
        return {
            **state,
            "recovery_attempts": int(state.get("recovery_attempts") or 0) + 1,
            "approved": True,
            "stage": "RECOVERY",
        }

    async def success(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.status = AgentRunStatus.COMPLETED
        run.stage = "SUCCESS"
        case.status = CaseStatus.VALIDATED
        run.finished_at = utcnow()
        if run.started_at:
            run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
        await record_audit(self.session, event_type="run_completed", case_id=case.id, run_id=run.id, payload={})
        await self.session.flush()
        return {**state, "stage": "SUCCESS"}

    async def escalate(self, state: AgentGraphState) -> AgentGraphState:
        run = await self._run(state)
        case = await self._case(state)
        run.status = AgentRunStatus.ESCALATED
        run.stage = "ESCALATE"
        case.status = CaseStatus.ESCALATED
        run.finished_at = utcnow()
        if run.started_at:
            run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
        await record_audit(self.session, event_type="escalated", case_id=case.id, run_id=run.id, payload={})
        await self.session.flush()
        return {**state, "stage": "ESCALATE"}


async def start_investigation(session: AsyncSession, case_id: uuid.UUID) -> AgentRun:
    case = await session.get(PurchasingCase, case_id)
    if not case:
        raise ApiError(404, "case_not_found", "Purchasing case not found")
    run = AgentRun(case_id=case_id, status=AgentRunStatus.QUEUED, stage="START", state_json={})
    session.add(run)
    await session.flush()
    agent = PurchasingAgent(session)
    await agent.investigate_graph.ainvoke(
        {
            "case_id": str(case_id),
            "run_id": str(run.id),
            "approved": False,
            "recovery_attempts": 0,
        }
    )
    await session.commit()
    await session.refresh(run)
    return run


async def resume_execution(session: AsyncSession, run: AgentRun) -> AgentRun:
    dec = (
        (await session.execute(select(Decision).where(Decision.run_id == run.id).order_by(Decision.created_at.desc())))
        .scalars()
        .first()
    )
    if not dec:
        raise ApiError(400, "no_decision", "No decision to execute")
    agent = PurchasingAgent(session)
    await agent.execute_graph.ainvoke(
        {
            "case_id": str(run.case_id),
            "run_id": str(run.id),
            "approved": True,
            "recovery_attempts": 0,
            "evidence": dec.evidence,
            "decision": {
                "decision": dec.decision,
                "recommended_quantity": dec.recommended_quantity,
                "action": dec.action,
                "reason_codes": dec.reason_codes,
                "financial_impact": dec.financial_impact,
            },
            "needs_approval": False,
            "replenishment": {
                "recommended_quantity": dec.recommended_quantity,
                "decision": dec.decision,
                "reason_codes": dec.reason_codes,
                "financial_impact": dec.financial_impact,
            },
        }
    )
    await session.commit()
    await session.refresh(run)
    return run
