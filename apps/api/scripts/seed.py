"""Idempotent demo seed for ProcureAI."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import hash_password
from app.db import SessionLocal
from app.infrastructure.embeddings import mock_embedding
from app.models.entities import (
    Budget,
    BusinessRule,
    DemandForecast,
    FulfillmentNode,
    Inventory,
    KnowledgeDocument,
    Product,
    PurchaseOrder,
    PurchaseOrderLine,
    PurchasingCase,
    StorageCapacity,
    Supplier,
    SupplierProduct,
    User,
)


async def get_or_create(session: AsyncSession, model, unique_field: str, unique_value, **kwargs):
    existing = (
        await session.execute(select(model).where(getattr(model, unique_field) == unique_value))
    ).scalar_one_or_none()
    if existing:
        return existing
    obj = model(**{unique_field: unique_value, **kwargs})
    session.add(obj)
    await session.flush()
    return obj


DOCS = [
    (
        "Purchasing SOP",
        "sop.md",
        "Buyers must not assume ERP purchase recommendations are correct. "
        "Investigate inventory, forecast, open POs, supplier constraints, budget, and storage "
        "before creating a purchase order. Record evidence on the purchasing case.",
    ),
    (
        "Approval Policy",
        "approval.md",
        "Purchases under $1,000 and low risk may auto-execute. Purchases of $1,000 or more "
        "require human approval. Purchases of $5,000 or more are high risk and must never "
        "auto-approve. Quantity modifications vs the original recommendation require approval.",
    ),
    (
        "Replenishment Policy",
        "replenishment.md",
        "inventory_position = on_hand + incoming_open_po - forecast_demand_during_lead_time. "
        "required_quantity = max(0, target_stock - inventory_position). Then apply MOQ, "
        "budget, storage additional capacity, and supplier availability. Default target_stock is 200 units.",
    ),
    (
        "Supplier Policy",
        "supplier.md",
        "Do not place orders with inactive suppliers. Respect MOQ and published available-to-promise. "
        "If supplier master data is incomplete (missing MOQ or lead time), the case must be "
        "investigated rather than executed. Reliability below 0.85 is elevated supplier risk.",
    ),
    (
        "Storage Policy",
        "storage.md",
        "Never exceed additional storage capacity at the fulfillment node. If unconstrained "
        "replenishment would overflow storage, modify the quantity downward.",
    ),
]


async def seed() -> None:
    async with SessionLocal() as session:
        await get_or_create(
            session,
            User,
            "email",
            "buyer@procure.ai",
            full_name="Avery Buyer",
            role="buyer",
            password_hash=hash_password("demo12345"),
        )
        await get_or_create(
            session,
            User,
            "email",
            "approver@procure.ai",
            full_name="Morgan Approver",
            role="approver",
            password_hash=hash_password("demo12345"),
        )

        rules = {
            "target_stock": "200",
            "approval_amount_medium": "1000",
            "approval_amount_high": "5000",
        }
        for k, v in rules.items():
            await get_or_create(session, BusinessRule, "key", k, value=v, description=k)

        seed_pos = {"PO-2001", "PO-REC-800", "PO-2002", "PO-REC-801", "PO-2500"}
        cases = (await session.execute(select(PurchasingCase))).scalars().all()
        for c in cases:
            if c.case_number == "PC-1000":
                c.current_po_id = None
        await session.flush()
        extras = (
            await session.execute(select(PurchaseOrder).where(PurchaseOrder.po_number.not_in(seed_pos)))
        ).scalars().all()
        for po in extras:
            lines = (
                await session.execute(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == po.id))
            ).scalars().all()
            for line in lines:
                await session.delete(line)
            await session.delete(po)
        await session.flush()

        for title, source, body in DOCS:
            existing = (
                await session.execute(select(KnowledgeDocument).where(KnowledgeDocument.title == title))
            ).scalar_one_or_none()
            if not existing:
                session.add(
                    KnowledgeDocument(
                        title=title,
                        source=source,
                        body=body,
                        embedding=mock_embedding(body),
                    )
                )

        northstar = await get_or_create(
            session, Supplier, "code", "NORTHSTAR", name="Northstar Components", reliability_score=0.96, status="active"
        )
        river = await get_or_create(
            session, Supplier, "code", "RIVER", name="Riverbend Supply", reliability_score=0.78, status="active"
        )
        incomplete = await get_or_create(
            session, Supplier, "code", "PIONEER", name="Pioneer Parts Co", reliability_score=0.88, status="active"
        )

        sku_ok = await get_or_create(
            session, Product, "sku", "FAST-100", name="Fastener Kit 100", category="hardware", unit_cost=5.0
        )
        sku_mod = await get_or_create(
            session, Product, "sku", "PUMP-800", name="Hydraulic Pump Cartridge", category="mro", unit_cost=8.0
        )
        sku_fail = await get_or_create(
            session,
            Product,
            "sku",
            "PUMP-800F",
            name="Hydraulic Pump Cartridge (failure demo)",
            category="mro",
            unit_cost=8.0,
        )
        sku_rej = await get_or_create(
            session, Product, "sku", "SEAL-50", name="Industrial Seal Pack", category="mro", unit_cost=50.0
        )
        sku_inv = await get_or_create(
            session, Product, "sku", "SENSOR-X", name="Line Sensor X", category="electronics", unit_cost=12.0
        )
        sku_short = await get_or_create(
            session, Product, "sku", "MOTOR-500", name="Drive Motor 500", category="mro", unit_cost=20.0
        )

        dc_ok = await get_or_create(session, FulfillmentNode, "code", "DC-OK", name="Dallas Accept Node", region="SC")
        dc_gold = await get_or_create(
            session, FulfillmentNode, "code", "DC-GOLD", name="Memphis Golden Node", region="SC"
        )
        dc_fail = await get_or_create(
            session, FulfillmentNode, "code", "DC-FAIL", name="Atlanta Failure Node", region="SE"
        )
        dc_rej = await get_or_create(
            session, FulfillmentNode, "code", "DC-BUDGET", name="Chicago Budget Node", region="MW"
        )
        dc_inv = await get_or_create(session, FulfillmentNode, "code", "DC-DATA", name="Denver Data Node", region="MT")
        dc_short = await get_or_create(
            session, FulfillmentNode, "code", "DC-SHORT", name="Columbus Shortfall Node", region="MW"
        )

        async def inv(product, node, qty):
            existing = (
                await session.execute(
                    select(Inventory).where(Inventory.product_id == product.id, Inventory.node_id == node.id)
                )
            ).scalar_one_or_none()
            if existing:
                existing.on_hand = qty
                existing.reserved = 0
                return existing
            row = Inventory(product_id=product.id, node_id=node.id, on_hand=qty, reserved=0)
            session.add(row)
            await session.flush()
            return row

        async def fc(product, node, qty):
            existing = (
                await session.execute(
                    select(DemandForecast).where(
                        DemandForecast.product_id == product.id, DemandForecast.node_id == node.id
                    )
                )
            ).scalar_one_or_none()
            if existing:
                existing.quantity = qty
                return existing
            row = DemandForecast(
                product_id=product.id, node_id=node.id, horizon_days=21, quantity=qty, source="statistical"
            )
            session.add(row)
            await session.flush()
            return row

        async def bud(node, amount, spent=0.0):
            existing = (await session.execute(select(Budget).where(Budget.node_id == node.id))).scalar_one_or_none()
            if existing:
                existing.amount = amount
                existing.spent = spent
                return existing
            row = Budget(node_id=node.id, amount=amount, spent=spent, currency="USD")
            session.add(row)
            await session.flush()
            return row

        async def stor(node, additional):
            existing = (
                await session.execute(select(StorageCapacity).where(StorageCapacity.node_id == node.id))
            ).scalar_one_or_none()
            if existing:
                existing.additional_units_available = additional
                existing.used_units = 0
                return existing
            row = StorageCapacity(node_id=node.id, additional_units_available=additional, used_units=0)
            session.add(row)
            await session.flush()
            return row

        async def sp(supplier, product, moq, lead, price, max_av, primary=True):
            existing = (
                await session.execute(
                    select(SupplierProduct).where(
                        SupplierProduct.supplier_id == supplier.id, SupplierProduct.product_id == product.id
                    )
                )
            ).scalar_one_or_none()
            if existing:
                return existing
            row = SupplierProduct(
                supplier_id=supplier.id,
                product_id=product.id,
                moq=moq,
                lead_time_days=lead,
                unit_price=price,
                max_available=max_av,
                is_primary=primary,
            )
            session.add(row)
            await session.flush()
            return row

        # ACCEPT: required = 200 - (20+0-80) wait target 200: position=20-80=-60, required=260, not 100
        # Use target_stock 200 globally. For ACCEPT we need original == calculated.
        # position = 50 + 0 - 150 = -100; required = 200 - (-100) = 300. Set original 300.
        await inv(sku_ok, dc_ok, 50)
        await fc(sku_ok, dc_ok, 150)
        await bud(dc_ok, 20000)
        await stor(dc_ok, 2000)
        await sp(northstar, sku_ok, 10, 14, 3.0, 5000)

        # GOLDEN MODIFY 400: 300+200-700=-200; required=400. original 800. storage 600. budget 4000. price 8.
        await inv(sku_mod, dc_gold, 300)
        await fc(sku_mod, dc_gold, 700)
        await bud(dc_gold, 4000)
        await stor(dc_gold, 600)
        await sp(northstar, sku_mod, 100, 21, 8.0, 5000)

        # FAILURE same math
        await inv(sku_fail, dc_fail, 300)
        await fc(sku_fail, dc_fail, 700)
        await bud(dc_fail, 4000)
        await stor(dc_fail, 600)
        await sp(northstar, sku_fail, 100, 21, 8.0, 5000)

        # REJECT budget: position=100+0-500=-400; required=600; price 50; budget 1000 → 20 units < MOQ 100
        await inv(sku_rej, dc_rej, 100)
        await fc(sku_rej, dc_rej, 500)
        await bud(dc_rej, 1000)
        await stor(dc_rej, 5000)
        await sp(northstar, sku_rej, 100, 14, 50.0, 5000)

        # INVESTIGATE incomplete supplier
        await inv(sku_inv, dc_inv, 80)
        await fc(sku_inv, dc_inv, 200)
        await bud(dc_inv, 10000)
        await stor(dc_inv, 1000)
        await sp(incomplete, sku_inv, None, None, 12.0, None)

        # SHORTFALL
        await inv(sku_short, dc_short, 40)
        await fc(sku_short, dc_short, 400)
        await bud(dc_short, 50000)
        await stor(dc_short, 5000)
        await sp(northstar, sku_short, 50, 14, 20.0, 250)
        await sp(river, sku_short, 50, 10, 22.0, 2000, primary=False)

        async def open_po(number, supplier, node, product, qty):
            existing = (
                await session.execute(
                    select(PurchaseOrder)
                    .where(PurchaseOrder.po_number == number)
                    .options(selectinload(PurchaseOrder.lines))
                )
            ).scalar_one_or_none()
            if existing:
                existing.status = "open"
                for line in existing.lines:
                    if line.product_id == product.id:
                        line.quantity = qty
                return existing
            po = PurchaseOrder(po_number=number, supplier_id=supplier.id, node_id=node.id, status="open")
            session.add(po)
            await session.flush()
            session.add(
                PurchaseOrderLine(
                    purchase_order_id=po.id,
                    product_id=product.id,
                    quantity=qty,
                    unit_price=8.0 if product.sku.startswith("PUMP") else 20.0,
                )
            )
            await session.flush()
            return po

        await open_po("PO-2001", northstar, dc_gold, sku_mod, 200)
        rec_gold = await open_po("PO-REC-800", northstar, dc_gold, sku_mod, 800)
        await open_po("PO-2002", northstar, dc_fail, sku_fail, 200)
        rec_fail = await open_po("PO-REC-801", northstar, dc_fail, sku_fail, 800)
        po_short = await open_po("PO-2500", northstar, dc_short, sku_short, 500)

        async def case(number, title, product, node, supplier, qty, scenario, po=None, mismatch=False):
            existing = (
                await session.execute(select(PurchasingCase).where(PurchasingCase.case_number == number))
            ).scalar_one_or_none()
            if existing:
                existing.status = "open"
                existing.original_recommended_qty = qty
                existing.force_validation_mismatch = mismatch
                existing.current_po_id = po.id if po else None
                return existing
            row = PurchasingCase(
                case_number=number,
                title=title,
                product_id=product.id,
                node_id=node.id,
                supplier_id=supplier.id,
                original_recommended_qty=qty,
                status="open",
                risk_level="MEDIUM",
                scenario_key=scenario,
                current_po_id=po.id if po else None,
                force_validation_mismatch=mismatch,
            )
            session.add(row)
            await session.flush()
            return row

        await case("PC-1000", "PO Recommendation #PC-1000", sku_ok, dc_ok, northstar, 300, "accept")
        await case(
            "PC-1001",
            "PO Recommendation #PC-1001",
            sku_mod,
            dc_gold,
            northstar,
            800,
            "modify_storage",
            rec_gold,
        )
        await case(
            "PC-1002",
            "PO Recommendation #PC-1002 (validation failure)",
            sku_fail,
            dc_fail,
            northstar,
            800,
            "validation_failure",
            rec_fail,
            mismatch=True,
        )
        await case("PC-1003", "PO Recommendation #PC-1003", sku_rej, dc_rej, northstar, 600, "reject_budget")
        await case("PC-1004", "PO Recommendation #PC-1004", sku_inv, dc_inv, incomplete, 200, "investigate")
        await case(
            "PC-1005",
            "PO Recommendation #PC-1005",
            sku_short,
            dc_short,
            northstar,
            500,
            "supplier_shortfall",
            po_short,
        )

        await session.commit()
        print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
