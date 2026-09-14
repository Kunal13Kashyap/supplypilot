from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.agents.graph import resume_execution, start_investigation
from app.core.deps import DbSession, get_current_user, require_approver
from app.core.errors import ApiError
from app.domain.enums import ApprovalStatus, CaseStatus
from app.models.entities import (
    AgentRun,
    Approval,
    AuditLog,
    Decision,
    FulfillmentNode,
    Product,
    PurchaseOrder,
    PurchasingCase,
    Supplier,
    ToolCall,
    User,
    ValidationEvent,
)
from app.schemas.api import (
    AgentRunOut,
    ApprovalRequest,
    AuditItem,
    CaseDetail,
    CaseListItem,
    DecisionOut,
    EvidenceSnapshot,
    ToolCallOut,
    ValidationOut,
)
from app.services.audit import record_audit

router = APIRouter(tags=["cases"])


def _decision_out(d: Decision) -> DecisionOut:
    return DecisionOut(
        id=d.id,
        decision=d.decision,
        recommended_quantity=d.recommended_quantity,
        confidence=d.confidence,
        risk_level=d.risk_level,
        requires_approval=d.requires_approval,
        reason_codes=d.reason_codes or [],
        explanation=d.explanation,
        action=d.action,
        policy_citations=d.policy_citations or [],
        financial_impact=d.financial_impact,
        created_at=d.created_at,
    )


async def _run_out(db, run: AgentRun) -> AgentRunOut:
    tools = (
        (await db.execute(select(ToolCall).where(ToolCall.run_id == run.id).order_by(ToolCall.created_at)))
        .scalars()
        .all()
    )
    dec = (
        (await db.execute(select(Decision).where(Decision.run_id == run.id).order_by(Decision.created_at.desc())))
        .scalars()
        .first()
    )
    vals = (
        (
            await db.execute(
                select(ValidationEvent).where(ValidationEvent.run_id == run.id).order_by(ValidationEvent.created_at)
            )
        )
        .scalars()
        .all()
    )
    return AgentRunOut(
        id=run.id,
        case_id=run.case_id,
        status=run.status,
        stage=run.stage,
        duration_ms=run.duration_ms,
        error=run.error,
        tool_calls=[
            ToolCallOut(
                id=t.id,
                tool_name=t.tool_name,
                status=t.status,
                duration_ms=t.duration_ms,
                input_json=t.input_json or {},
                output_json=t.output_json or {},
                summary=t.summary,
                created_at=t.created_at,
            )
            for t in tools
        ],
        decision=_decision_out(dec) if dec else None,
        validations=[
            ValidationOut(
                id=v.id,
                passed=v.passed,
                expected_json=v.expected_json,
                actual_json=v.actual_json,
                violations=v.violations or [],
                recovery_required=v.recovery_required,
                created_at=v.created_at,
            )
            for v in vals
        ],
    )


@router.get("/cases", response_model=list[CaseListItem], summary="List purchasing cases")
async def list_cases(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[CaseListItem]:
    rows = (
        await db.execute(
            select(PurchasingCase, Product, FulfillmentNode)
            .join(Product, Product.id == PurchasingCase.product_id)
            .join(FulfillmentNode, FulfillmentNode.id == PurchasingCase.node_id)
            .order_by(PurchasingCase.case_number)
        )
    ).all()
    return [
        CaseListItem(
            id=c.id,
            case_number=c.case_number,
            title=c.title,
            status=c.status,
            risk_level=c.risk_level,
            original_recommended_qty=c.original_recommended_qty,
            scenario_key=c.scenario_key,
            product_sku=p.sku,
            product_name=p.name,
            node_code=n.code,
            created_at=c.created_at,
        )
        for c, p, n in rows
    ]


@router.get("/cases/{case_id}", response_model=CaseDetail)
async def get_case(case_id: uuid.UUID, db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> CaseDetail:
    row = (
        await db.execute(
            select(PurchasingCase, Product, FulfillmentNode, Supplier)
            .join(Product, Product.id == PurchasingCase.product_id)
            .join(FulfillmentNode, FulfillmentNode.id == PurchasingCase.node_id)
            .join(Supplier, Supplier.id == PurchasingCase.supplier_id)
            .where(PurchasingCase.id == case_id)
        )
    ).first()
    if not row:
        raise ApiError(404, "case_not_found", "Purchasing case not found")
    case, product, node, supplier = row
    po_number = None
    if case.current_po_id:
        po = await db.get(PurchaseOrder, case.current_po_id)
        po_number = po.po_number if po else None
    run = (
        (await db.execute(select(AgentRun).where(AgentRun.case_id == case.id).order_by(AgentRun.created_at.desc())))
        .scalars()
        .first()
    )
    latest = await _run_out(db, run) if run else None
    evidence = None
    if latest and latest.decision:
        ev = (await db.execute(select(Decision).where(Decision.id == latest.decision.id))).scalar_one()
        raw = ev.evidence or {}
        evidence = EvidenceSnapshot(
            inventory=raw.get("inventory"),
            forecast=raw.get("forecast"),
            open_pos=raw.get("open_pos"),
            supplier=raw.get("supplier"),
            budget=raw.get("budget"),
            storage=raw.get("storage"),
            replenishment=raw.get("rules"),
        )
    return CaseDetail(
        id=case.id,
        case_number=case.case_number,
        title=case.title,
        status=case.status,
        risk_level=case.risk_level,
        original_recommended_qty=case.original_recommended_qty,
        scenario_key=case.scenario_key,
        product_sku=product.sku,
        product_name=product.name,
        node_code=node.code,
        node_name=node.name,
        supplier_code=supplier.code,
        supplier_name=supplier.name,
        current_po_number=po_number,
        latest_run=latest,
        evidence=evidence,
    )


@router.post("/cases/{case_id}/agent/run", response_model=AgentRunOut, summary="Run AI investigation")
async def run_agent(case_id: uuid.UUID, db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> AgentRunOut:
    run = await start_investigation(db, case_id)
    return await _run_out(db, run)


@router.get("/cases/{case_id}/agent-runs/{run_id}", response_model=AgentRunOut)
async def get_run(
    case_id: uuid.UUID,
    run_id: uuid.UUID,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> AgentRunOut:
    run = await db.get(AgentRun, run_id)
    if not run or run.case_id != case_id:
        raise ApiError(404, "run_not_found", "Agent run not found")
    return await _run_out(db, run)


@router.post("/decisions/{decision_id}/approve", response_model=AgentRunOut)
async def approve_decision(
    decision_id: uuid.UUID,
    body: ApprovalRequest,
    db: DbSession,
    user: Annotated[User, Depends(require_approver)],
) -> AgentRunOut:
    dec = await db.get(Decision, decision_id)
    if not dec:
        raise ApiError(404, "decision_not_found", "Decision not found")
    db.add(
        Approval(
            decision_id=dec.id,
            actor_email=user.email,
            status=ApprovalStatus.APPROVED,
            comment=body.comment,
        )
    )
    run = await db.get(AgentRun, dec.run_id)
    assert run
    await record_audit(
        db,
        event_type="approval",
        actor=user.email,
        case_id=dec.case_id,
        run_id=run.id,
        payload={"status": "approved", "comment": body.comment},
    )
    await db.flush()
    run = await resume_execution(db, run)
    return await _run_out(db, run)


@router.post("/decisions/{decision_id}/reject", response_model=DecisionOut)
async def reject_decision(
    decision_id: uuid.UUID,
    body: ApprovalRequest,
    db: DbSession,
    user: Annotated[User, Depends(require_approver)],
) -> DecisionOut:
    dec = await db.get(Decision, decision_id)
    if not dec:
        raise ApiError(404, "decision_not_found", "Decision not found")
    db.add(Approval(decision_id=dec.id, actor_email=user.email, status=ApprovalStatus.REJECTED, comment=body.comment))
    case = await db.get(PurchasingCase, dec.case_id)
    if case:
        case.status = CaseStatus.REJECTED
    run = await db.get(AgentRun, dec.run_id)
    if run:
        run.status = "completed"
        run.stage = "REJECTED_BY_HUMAN"
    await record_audit(
        db,
        event_type="approval",
        actor=user.email,
        case_id=dec.case_id,
        run_id=dec.run_id,
        payload={"status": "rejected"},
    )
    await db.commit()
    return _decision_out(dec)


@router.post("/decisions/{decision_id}/reanalyze", response_model=AgentRunOut)
async def reanalyze(
    decision_id: uuid.UUID,
    body: ApprovalRequest,
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
) -> AgentRunOut:
    dec = await db.get(Decision, decision_id)
    if not dec:
        raise ApiError(404, "decision_not_found", "Decision not found")
    db.add(
        Approval(
            decision_id=dec.id,
            actor_email=user.email,
            status=ApprovalStatus.REANALYZE,
            comment=body.comment,
        )
    )
    await record_audit(
        db,
        event_type="reanalyze",
        actor=user.email,
        case_id=dec.case_id,
        run_id=dec.run_id,
        payload={},
    )
    await db.flush()
    run = await start_investigation(db, dec.case_id)
    return await _run_out(db, run)


@router.get("/audit/{case_id}", response_model=list[AuditItem])
async def audit_for_case(
    case_id: uuid.UUID, db: DbSession, user: Annotated[User, Depends(get_current_user)]
) -> list[AuditItem]:
    rows = (
        (await db.execute(select(AuditLog).where(AuditLog.case_id == case_id).order_by(AuditLog.created_at)))
        .scalars()
        .all()
    )
    return [
        AuditItem(
            id=r.id,
            case_id=r.case_id,
            run_id=r.run_id,
            event_type=r.event_type,
            actor=r.actor,
            payload=r.payload or {},
            created_at=r.created_at,
        )
        for r in rows
    ]
