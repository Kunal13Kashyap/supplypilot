from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.core.deps import DbSession, get_current_user
from app.infrastructure.embeddings import search_knowledge
from app.models.entities import (
    AuditLog,
    FulfillmentNode,
    Inventory,
    KnowledgeDocument,
    Product,
    Supplier,
    User,
)
from app.schemas.api import AuditItem

router = APIRouter(tags=["ops"])


@router.get("/suppliers")
async def suppliers(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    rows = (await db.execute(select(Supplier).order_by(Supplier.name))).scalars().all()
    return [
        {
            "id": str(s.id),
            "code": s.code,
            "name": s.name,
            "reliability_score": s.reliability_score,
            "status": s.status,
        }
        for s in rows
    ]


@router.get("/inventory")
async def inventory(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    rows = (
        await db.execute(
            select(Inventory, Product, FulfillmentNode)
            .join(Product, Product.id == Inventory.product_id)
            .join(FulfillmentNode, FulfillmentNode.id == Inventory.node_id)
        )
    ).all()
    return [
        {
            "sku": p.sku,
            "product": p.name,
            "node": n.code,
            "on_hand": inv.on_hand,
            "reserved": inv.reserved,
        }
        for inv, p, n in rows
    ]


@router.get("/agent-runs")
async def agent_runs(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    from app.models.entities import AgentRun, PurchasingCase

    rows = (
        await db.execute(
            select(AgentRun, PurchasingCase)
            .join(PurchasingCase, PurchasingCase.id == AgentRun.case_id)
            .order_by(AgentRun.created_at.desc())
            .limit(50)
        )
    ).all()
    return [
        {
            "id": str(r.id),
            "case_id": str(r.case_id),
            "case_number": c.case_number,
            "status": r.status,
            "stage": r.stage,
            "duration_ms": r.duration_ms,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r, c in rows
    ]


@router.get("/audit")
async def audit_all(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[AuditItem]:
    rows = (await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200))).scalars().all()
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


@router.get("/knowledge")
async def knowledge(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    rows = (await db.execute(select(KnowledgeDocument).order_by(KnowledgeDocument.title))).scalars().all()
    return [{"id": str(d.id), "title": d.title, "source": d.source, "body": d.body} for d in rows]


@router.get("/purchase-orders")
async def list_pos(db: DbSession, user: Annotated[User, Depends(get_current_user)]) -> list[dict]:
    from sqlalchemy.orm import selectinload

    from app.models.entities import PurchaseOrder

    rows = (
        (
            await db.execute(
                select(PurchaseOrder)
                .options(selectinload(PurchaseOrder.lines))
                .order_by(PurchaseOrder.created_at.desc())
            )
        )
        .scalars()
        .unique()
        .all()
    )
    out = []
    for po in rows:
        supplier = await db.get(Supplier, po.supplier_id)
        qty = sum(line.quantity for line in po.lines)
        out.append(
            {
                "id": str(po.id),
                "po_number": po.po_number,
                "status": po.status,
                "supplier": supplier.name if supplier else "",
                "quantity": qty,
                "created_at": po.created_at.isoformat() if po.created_at else None,
            }
        )
    return out


@router.get("/knowledge/search")
async def knowledge_search(
    db: DbSession,
    user: Annotated[User, Depends(get_current_user)],
    q: str = Query(..., min_length=2),
) -> list[dict]:
    hits = await search_knowledge(db, q)
    return [h.model_dump() for h in hits]
