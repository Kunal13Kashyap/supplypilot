from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ApiError
from app.models.entities import (
    Budget,
    DemandForecast,
    FulfillmentNode,
    Inventory,
    Product,
    PurchaseOrder,
    PurchasingCase,
    StorageCapacity,
    Supplier,
    SupplierProduct,
)
from app.schemas.agent import (
    ToolBudgetOut,
    ToolForecastOut,
    ToolInventoryOut,
    ToolOpenPOLine,
    ToolOpenPOOut,
    ToolStorageOut,
    ToolSupplierOut,
)


async def load_case(session: AsyncSession, case_id: uuid.UUID) -> PurchasingCase:
    result = await session.execute(select(PurchasingCase).where(PurchasingCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise ApiError(404, "case_not_found", "Purchasing case not found")
    return case


async def get_inventory(session: AsyncSession, product_id: uuid.UUID, node_id: uuid.UUID) -> ToolInventoryOut:
    inv = (
        await session.execute(select(Inventory).where(Inventory.product_id == product_id, Inventory.node_id == node_id))
    ).scalar_one_or_none()
    product = await session.get(Product, product_id)
    node = await session.get(FulfillmentNode, node_id)
    if not inv or not product or not node:
        raise ApiError(404, "inventory_not_found", "Inventory record missing")
    return ToolInventoryOut(on_hand=inv.on_hand, reserved=inv.reserved, node_code=node.code, sku=product.sku)


async def get_forecast(session: AsyncSession, product_id: uuid.UUID, node_id: uuid.UUID) -> ToolForecastOut:
    row = (
        await session.execute(
            select(DemandForecast).where(DemandForecast.product_id == product_id, DemandForecast.node_id == node_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise ApiError(404, "forecast_not_found", "Demand forecast missing")
    return ToolForecastOut(quantity=row.quantity, horizon_days=row.horizon_days, source=row.source)


async def get_open_pos(
    session: AsyncSession, product_id: uuid.UUID, node_id: uuid.UUID, exclude_po_id: uuid.UUID | None = None
) -> ToolOpenPOOut:
    stmt = (
        select(PurchaseOrder)
        .options(selectinload(PurchaseOrder.lines))
        .where(PurchaseOrder.node_id == node_id, PurchaseOrder.status.in_(["open", "partial", "draft"]))
    )
    orders = (await session.execute(stmt)).scalars().unique().all()
    lines_out: list[ToolOpenPOLine] = []
    total = 0
    for po in orders:
        if exclude_po_id and po.id == exclude_po_id:
            continue
        for line in po.lines:
            if line.product_id == product_id:
                total += line.quantity
                lines_out.append(ToolOpenPOLine(po_number=po.po_number, quantity=line.quantity, status=po.status))
    return ToolOpenPOOut(total_inbound=total, orders=lines_out)


async def get_supplier_constraints(
    session: AsyncSession, supplier_id: uuid.UUID, product_id: uuid.UUID
) -> ToolSupplierOut:
    supplier = await session.get(Supplier, supplier_id)
    sp = (
        await session.execute(
            select(SupplierProduct).where(
                SupplierProduct.supplier_id == supplier_id, SupplierProduct.product_id == product_id
            )
        )
    ).scalar_one_or_none()
    if not supplier or not sp:
        raise ApiError(404, "supplier_not_found", "Supplier constraints missing")
    return ToolSupplierOut(
        code=supplier.code,
        name=supplier.name,
        reliability_score=supplier.reliability_score,
        status=supplier.status,
        moq=sp.moq,
        lead_time_days=sp.lead_time_days,
        unit_price=sp.unit_price,
        max_available=sp.max_available,
        is_primary=sp.is_primary,
    )


async def get_alternate_suppliers(
    session: AsyncSession, product_id: uuid.UUID, exclude_supplier_id: uuid.UUID
) -> list[ToolSupplierOut]:
    rows = (
        await session.execute(
            select(SupplierProduct, Supplier)
            .join(Supplier, Supplier.id == SupplierProduct.supplier_id)
            .where(
                SupplierProduct.product_id == product_id,
                SupplierProduct.supplier_id != exclude_supplier_id,
            )
        )
    ).all()
    out: list[ToolSupplierOut] = []
    for sp, supplier in rows:
        out.append(
            ToolSupplierOut(
                code=supplier.code,
                name=supplier.name,
                reliability_score=supplier.reliability_score,
                status=supplier.status,
                moq=sp.moq,
                lead_time_days=sp.lead_time_days,
                unit_price=sp.unit_price,
                max_available=sp.max_available,
                is_primary=sp.is_primary,
            )
        )
    return out


async def get_budget(session: AsyncSession, node_id: uuid.UUID) -> ToolBudgetOut:
    row = (await session.execute(select(Budget).where(Budget.node_id == node_id))).scalar_one_or_none()
    if not row:
        raise ApiError(404, "budget_not_found", "Budget missing")
    return ToolBudgetOut(amount=row.amount, spent=row.spent, remaining=row.amount - row.spent, currency=row.currency)


async def get_storage(session: AsyncSession, node_id: uuid.UUID) -> ToolStorageOut:
    row = (
        await session.execute(select(StorageCapacity).where(StorageCapacity.node_id == node_id))
    ).scalar_one_or_none()
    if not row:
        raise ApiError(404, "storage_not_found", "Storage capacity missing")
    return ToolStorageOut(additional_units_available=row.additional_units_available, used_units=row.used_units)


async def get_business_rules_map(session: AsyncSession) -> dict[str, str]:
    from app.models.entities import BusinessRule

    rows = (await session.execute(select(BusinessRule))).scalars().all()
    return {r.key: r.value for r in rows}


async def next_po_number(session: AsyncSession) -> str:
    count = (await session.execute(select(PurchaseOrder))).scalars().all()
    return f"PO-{1000 + len(count) + 1}"
