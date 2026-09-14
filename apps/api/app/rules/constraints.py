from pydantic import BaseModel, Field

from app.domain.enums import RiskLevel
from app.domain.reason_codes import ReasonCode
from app.rules.replenishment import ReplenishmentResult


class ConstraintViolation(BaseModel):
    code: str
    message: str


class ConstraintReport(BaseModel):
    passed: bool
    violations: list[ConstraintViolation] = Field(default_factory=list)


def assess_risk(
    *,
    financial_impact: float,
    decision: str,
    medium_threshold: float,
    high_threshold: float,
    qty_delta_ratio: float,
) -> tuple[RiskLevel, bool]:
    """Returns (risk, requires_approval). HIGH never auto-executes."""
    if decision == "INVESTIGATE":
        return RiskLevel.HIGH, True
    if decision == "REJECT":
        return RiskLevel.MEDIUM, True
    if financial_impact >= high_threshold or qty_delta_ratio >= 0.5 and decision == "MODIFY":
        if financial_impact >= high_threshold:
            return RiskLevel.HIGH, True
    if financial_impact >= medium_threshold or decision == "MODIFY":
        return RiskLevel.MEDIUM, True
    return RiskLevel.LOW, False


def validate_quantity(
    *,
    qty: int,
    moq: int | None,
    storage_additional: int,
    budget_remaining: float,
    unit_price: float,
    supplier_max: int | None,
    supplier_valid: bool,
) -> ConstraintReport:
    violations: list[ConstraintViolation] = []
    if qty < 0:
        violations.append(ConstraintViolation(code="NEGATIVE_QUANTITY", message="Quantity cannot be negative"))
    if not supplier_valid:
        violations.append(ConstraintViolation(code="INVALID_SUPPLIER", message="Supplier is not active"))
    if moq is not None and qty > 0 and qty % moq != 0 and qty < moq:
        violations.append(ConstraintViolation(code=ReasonCode.SUPPLIER_MOQ, message=f"Quantity {qty} below MOQ {moq}"))
    if moq is not None and qty > 0 and qty < moq:
        violations.append(ConstraintViolation(code=ReasonCode.MOQ_INFEASIBLE, message="Quantity below MOQ"))
    if qty > storage_additional:
        violations.append(
            ConstraintViolation(
                code=ReasonCode.STORAGE_CONSTRAINT,
                message=f"Quantity {qty} exceeds storage {storage_additional}",
            )
        )
    cost = qty * unit_price
    if cost > budget_remaining + 1e-6:
        violations.append(
            ConstraintViolation(
                code=ReasonCode.BUDGET_CONSTRAINT,
                message=f"Cost {cost} exceeds budget {budget_remaining}",
            )
        )
    if supplier_max is not None and qty > supplier_max:
        violations.append(
            ConstraintViolation(
                code=ReasonCode.SUPPLIER_CAPACITY_SHORTFALL,
                message=f"Quantity {qty} exceeds supplier availability {supplier_max}",
            )
        )
    return ConstraintReport(passed=len(violations) == 0, violations=violations)


def decision_from_replenishment(result: ReplenishmentResult) -> str:
    return result.decision
