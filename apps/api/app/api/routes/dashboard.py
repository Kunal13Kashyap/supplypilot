from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select

from app.core.deps import DbSession, get_current_user
from app.models.entities import (
    AgentRun,
    Budget,
    Decision,
    Inventory,
    PurchaseOrder,
    PurchasingCase,
    Supplier,
    User,
    ValidationEvent,
)
from app.schemas.api import DashboardStats

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> DashboardStats:
    pending_ai = (
        await db.execute(select(func.count()).select_from(PurchasingCase).where(PurchasingCase.status == "open"))
    ).scalar_one()
    awaiting = (
        await db.execute(
            select(func.count()).select_from(PurchasingCase).where(PurchasingCase.status == "awaiting_approval")
        )
    ).scalar_one()
    open_pos = (
        await db.execute(select(func.count()).select_from(PurchaseOrder).where(PurchaseOrder.status == "open"))
    ).scalar_one()
    failed_val = (
        await db.execute(select(func.count()).select_from(ValidationEvent).where(ValidationEvent.passed.is_(False)))
    ).scalar_one()
    investigating = (
        await db.execute(
            select(func.count()).select_from(PurchasingCase).where(PurchasingCase.status == "investigating")
        )
    ).scalar_one()
    budgets = (await db.execute(select(Budget))).scalars().all()
    amount = sum(b.amount for b in budgets)
    spent = sum(b.spent for b in budgets)
    inv_risk = (
        await db.execute(select(func.count()).select_from(Inventory).where(Inventory.on_hand < 100))
    ).scalar_one()
    supplier_risk = (
        await db.execute(select(func.count()).select_from(Supplier).where(Supplier.reliability_score < 0.85))
    ).scalar_one()
    rec_rows = (await db.execute(select(Decision.decision, func.count()).group_by(Decision.decision))).all()
    rec_map = {str(k): int(v) for k, v in rec_rows}
    runs = (await db.execute(select(AgentRun).order_by(AgentRun.created_at.desc()).limit(8))).scalars().all()
    recent = [
        {
            "id": str(r.id),
            "status": r.status,
            "stage": r.stage,
            "duration_ms": r.duration_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]
    cases = (
        await db.execute(
            select(PurchasingCase, Inventory).join(Inventory, Inventory.product_id == PurchasingCase.product_id)
        )
    ).all()
    coverage: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case, inv in cases:
        key = str(case.product_id)
        if key in seen:
            continue
        seen.add(key)
        coverage.append(
            {
                "case": case.case_number,
                "on_hand": inv.on_hand,
                "recommended": case.original_recommended_qty,
            }
        )
    suppliers = (await db.execute(select(Supplier))).scalars().all()
    fulfillment = [{"supplier": s.name, "reliability": round(s.reliability_score * 100, 1)} for s in suppliers]
    return DashboardStats(
        pending_ai_decisions=int(pending_ai or 0),
        awaiting_approval=int(awaiting or 0),
        open_purchase_orders=int(open_pos or 0),
        failed_validations=int(failed_val or 0),
        active_investigations=int(investigating or 0),
        budget_amount=amount,
        budget_spent=spent,
        inventory_risk_skus=int(inv_risk or 0),
        supplier_risk_count=int(supplier_risk or 0),
        recommendations_by_status=rec_map,
        recent_runs=recent,
        inventory_coverage=coverage[:8],
        supplier_fulfillment=fulfillment,
    )
