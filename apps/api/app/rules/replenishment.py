from __future__ import annotations

import math

from pydantic import BaseModel, Field


class ReplenishmentInput(BaseModel):
    on_hand: int
    inbound_open_po: int
    lead_time_demand: int
    target_stock: int
    moq: int | None = None
    unit_price: float
    budget_remaining: float
    storage_additional: int
    supplier_max_available: int | None = None
    original_recommended_qty: int


class ReplenishmentResult(BaseModel):
    inventory_position: int
    unconstrained_required: int
    recommended_quantity: int
    reason_codes: list[str] = Field(default_factory=list)
    decision: str
    feasible: bool
    notes: list[str] = Field(default_factory=list)
    financial_impact: float
    constraints: dict


def _ceil_to_moq(qty: int, moq: int) -> int:
    if moq <= 0 or qty <= 0:
        return max(qty, 0)
    return int(math.ceil(qty / moq) * moq)


def calculate_replenishment(data: ReplenishmentInput) -> ReplenishmentResult:
    """Deterministic replenishment. Never invoked as an LLM guess.

    inventory_position = on_hand + inbound_open_po - lead_time_demand
    unconstrained_required = max(0, target_stock - inventory_position)
    Then cap by storage, budget, supplier max; round up to MOQ.
    """
    from app.domain.reason_codes import ReasonCode

    reasons: list[str] = []
    notes: list[str] = []

    inventory_position = data.on_hand + data.inbound_open_po - data.lead_time_demand
    unconstrained = max(0, data.target_stock - inventory_position)

    if data.on_hand + data.inbound_open_po < data.lead_time_demand:
        reasons.append(ReasonCode.INSUFFICIENT_INVENTORY)
        reasons.append(ReasonCode.DEMAND_COVERAGE)
        reasons.append(ReasonCode.HIGH_DEMAND)
    elif unconstrained == 0:
        reasons.append(ReasonCode.EXCESS_INVENTORY)

    if data.inbound_open_po > 0:
        reasons.append(ReasonCode.OPEN_PO_EXISTS)

    reasons.append(ReasonCode.TARGET_STOCK_POLICY)

    qty = unconstrained
    if data.moq is None:
        return ReplenishmentResult(
            inventory_position=inventory_position,
            unconstrained_required=unconstrained,
            recommended_quantity=0,
            reason_codes=list(dict.fromkeys([*reasons, ReasonCode.SUPPLIER_DATA_INCOMPLETE])),
            decision="INVESTIGATE",
            feasible=False,
            notes=["Supplier MOQ is missing; cannot commit a purchase quantity."],
            financial_impact=0,
            constraints={"missing": "moq"},
        )

    if data.moq > 0:
        qty = _ceil_to_moq(qty, data.moq)
        if qty != unconstrained and unconstrained > 0:
            reasons.append(ReasonCode.SUPPLIER_MOQ)

    caps: dict[str, int] = {}
    if data.storage_additional >= 0:
        caps["storage"] = data.storage_additional
        if qty > data.storage_additional:
            reasons.append(ReasonCode.STORAGE_CONSTRAINT)
            notes.append(f"Required {qty} exceeds storage additional capacity {data.storage_additional}.")
            qty = min(qty, data.storage_additional)

    affordable = int(data.budget_remaining // data.unit_price) if data.unit_price > 0 else 0
    caps["budget_units"] = affordable
    if qty > affordable:
        reasons.append(ReasonCode.BUDGET_CONSTRAINT)
        notes.append(f"Budget allows {affordable} units at ${data.unit_price:.2f}.")
        qty = min(qty, affordable)

    if data.supplier_max_available is not None:
        caps["supplier_max"] = data.supplier_max_available
        if qty > data.supplier_max_available:
            reasons.append(ReasonCode.SUPPLIER_CAPACITY_SHORTFALL)
            qty = min(qty, data.supplier_max_available)

    if data.moq > 0 and 0 < qty < data.moq:
        reasons.append(ReasonCode.MOQ_INFEASIBLE)
        notes.append("Capped quantity is below supplier MOQ; purchase is infeasible.")
        return ReplenishmentResult(
            inventory_position=inventory_position,
            unconstrained_required=unconstrained,
            recommended_quantity=0,
            reason_codes=list(dict.fromkeys(reasons)),
            decision="REJECT",
            feasible=False,
            notes=notes,
            financial_impact=0,
            constraints=caps,
        )

    if qty == 0 and unconstrained == 0:
        decision = "REJECT" if data.original_recommended_qty > 0 else "ACCEPT"
        if data.original_recommended_qty > 0:
            reasons.append(ReasonCode.EXCESS_INVENTORY)
            decision = "REJECT"
        return ReplenishmentResult(
            inventory_position=inventory_position,
            unconstrained_required=unconstrained,
            recommended_quantity=0,
            reason_codes=list(dict.fromkeys(reasons)),
            decision=decision,
            feasible=True,
            notes=notes or ["No additional purchase is required."],
            financial_impact=0,
            constraints=caps,
        )

    if qty == 0:
        return ReplenishmentResult(
            inventory_position=inventory_position,
            unconstrained_required=unconstrained,
            recommended_quantity=0,
            reason_codes=list(dict.fromkeys(reasons)),
            decision="REJECT",
            feasible=False,
            notes=notes or ["Constraints prevent any purchase."],
            financial_impact=0,
            constraints=caps,
        )

    original = data.original_recommended_qty
    if original <= 0:
        decision = "MODIFY"
    elif original == qty:
        decision = "ACCEPT"
    else:
        decision = "MODIFY"
        if original > data.storage_additional:
            reasons.append(ReasonCode.STORAGE_CONSTRAINT)
        if original * data.unit_price > data.budget_remaining:
            reasons.append(ReasonCode.BUDGET_CONSTRAINT)

    financial = round(qty * data.unit_price, 2)
    return ReplenishmentResult(
        inventory_position=inventory_position,
        unconstrained_required=unconstrained,
        recommended_quantity=qty,
        reason_codes=list(dict.fromkeys(reasons)),
        decision=decision,
        feasible=True,
        notes=notes,
        financial_impact=financial,
        constraints=caps,
    )
