from __future__ import annotations

from typing import Protocol

from app.core.config import get_settings
from app.domain.enums import ActionType, DecisionType, RiskLevel
from app.schemas.agent import DecisionOutput


class LLMProvider(Protocol):
    async def explain_decision(
        self,
        *,
        evidence: dict,
        engine_decision: str,
        quantity: int,
        reason_codes: list[str],
        policy_excerpts: list[str],
    ) -> str: ...


class MockLLMProvider:
    async def explain_decision(
        self,
        *,
        evidence: dict,
        engine_decision: str,
        quantity: int,
        reason_codes: list[str],
        policy_excerpts: list[str],
    ) -> str:
        inv = evidence.get("inventory", {})
        fc = evidence.get("forecast", {})
        pos = evidence.get("open_pos", {})
        storage = evidence.get("storage", {})
        on_hand = inv.get("on_hand", 0)
        inbound = pos.get("total_inbound", 0)
        demand = fc.get("quantity", 0)
        covered = on_hand + inbound
        storage_cap = storage.get("additional_units_available")
        original = evidence.get("original_recommended_qty")
        policy = policy_excerpts[0] if policy_excerpts else "Internal replenishment policy"
        return (
            f"Existing inventory ({on_hand}) plus incoming PO quantity ({inbound}) covers {covered} "
            f"of the expected {demand} units of demand. The original recommendation of {original} units "
            f"was challenged against storage capacity ({storage_cap} additional units), budget, MOQ, and "
            f"target-stock policy. Deterministic replenishment yields {quantity} units with decision "
            f"{engine_decision}. Reason codes: {', '.join(reason_codes)}. Policy considered: {policy}."
        )


class OpenAIProvider:
    async def explain_decision(
        self,
        *,
        evidence: dict,
        engine_decision: str,
        quantity: int,
        reason_codes: list[str],
        policy_excerpts: list[str],
    ) -> str:
        settings = get_settings()
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.llm_timeout_seconds)
        prompt = (
            "You are a procurement operations analyst. Write 3-5 sentences of business evidence "
            "for a purchasing decision. Do not show chain of thought. Do not change the quantity "
            f"or decision. Decision={engine_decision}, quantity={quantity}, reasons={reason_codes}. "
            f"Evidence JSON: {evidence}. Policies: {policy_excerpts}"
        )
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content or MockLLMProvider().explain_decision(
            evidence=evidence,
            engine_decision=engine_decision,
            quantity=quantity,
            reason_codes=reason_codes,
            policy_excerpts=policy_excerpts,
        )


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    if settings.use_mock_llm:
        return MockLLMProvider()
    return OpenAIProvider()


def structured_decision_from_engine(
    *,
    decision: str,
    qty: int,
    confidence: float,
    risk: str,
    requires_approval: bool,
    reasons: list[str],
    evidence: dict,
    explanation: str,
    action: str,
    citations: list[str],
    financial_impact: float,
) -> DecisionOutput:
    return DecisionOutput(
        decision=DecisionType(decision),
        recommended_quantity=qty,
        confidence=confidence,
        risk_level=RiskLevel(risk),
        requires_approval=requires_approval,
        reason_codes=reasons,
        evidence=evidence,
        explanation=explanation,
        action=ActionType(action),
        policy_citations=citations,
        financial_impact=financial_impact,
    )
