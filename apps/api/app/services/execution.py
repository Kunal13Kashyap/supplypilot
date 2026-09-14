from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.models.entities import (
    AgentAction,
    Budget,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchasingCase,
)
from app.services.procurement import next_po_number


async def create_or_modify_po(
    session: AsyncSession,
    *,
    case: PurchasingCase,
    supplier_id: uuid.UUID,
    product_id: uuid.UUID,
    quantity: int,
    unit_price: float,
    idempotency_key: str,
    modify_existing: bool,
    force_mismatch: bool,
    recovery: bool,
) -> dict:
    existing_action = (
        await session.execute(select(AgentAction).where(AgentAction.idempotency_key == idempotency_key))
    ).scalar_one_or_none()
    if existing_action and existing_action.status == "executed" and existing_action.result_json:
        return existing_action.result_json

    write_qty = quantity
    if force_mismatch and not recovery:
        write_qty = quantity + 100

    po: PurchaseOrder | None = None
    if modify_existing and case.current_po_id:
        po = (
            await session.execute(
                select(PurchaseOrder)
                .options(selectinload(PurchaseOrder.lines))
                .where(PurchaseOrder.id == case.current_po_id)
            )
        ).scalar_one_or_none()

    budget = (await session.execute(select(Budget).where(Budget.node_id == case.node_id))).scalar_one()
    previous_cost = 0.0
    if po:
        for line in po.lines:
            if line.product_id == product_id:
                previous_cost = line.quantity * line.unit_price
                line.quantity = write_qty
                line.unit_price = unit_price
        po.status = "open"
    else:
        po = PurchaseOrder(
            po_number=await next_po_number(session),
            supplier_id=supplier_id,
            node_id=case.node_id,
            status="open",
            idempotency_key=f"po-{idempotency_key}",
            force_qty_mismatch=force_mismatch and not recovery,
        )
        session.add(po)
        await session.flush()
        session.add(
            PurchaseOrderLine(
                purchase_order_id=po.id,
                product_id=product_id,
                quantity=write_qty,
                unit_price=unit_price,
            )
        )
        case.current_po_id = po.id

    new_cost = write_qty * unit_price
    if previous_cost > 0 and budget.spent >= previous_cost:
        budget.spent = budget.spent - previous_cost + new_cost
    else:
        budget.spent += new_cost
    await session.flush()
    return {
        "po_id": str(po.id),
        "po_number": po.po_number,
        "quantity": write_qty,
        "unit_price": unit_price,
        "requested_quantity": quantity,
    }


async def read_po_quantity(session: AsyncSession, po_id: uuid.UUID, product_id: uuid.UUID) -> dict:
    po = (
        await session.execute(
            select(PurchaseOrder).options(selectinload(PurchaseOrder.lines)).where(PurchaseOrder.id == po_id)
        )
    ).scalar_one_or_none()
    if not po:
        raise ApiError(404, "po_not_found", "Purchase order not found")
    qty = 0
    price = 0.0
    for line in po.lines:
        if line.product_id == product_id:
            qty = line.quantity
            price = line.unit_price
    return {"po_number": po.po_number, "quantity": qty, "unit_price": price, "status": po.status}
