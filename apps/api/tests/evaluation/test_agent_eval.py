"""Evaluation suite — deterministic MOCK agent against seeded cases."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.agents.graph import start_investigation
from app.db import SessionLocal
from app.main import app
from app.models.entities import Decision, PurchasingCase, ToolCall
from scripts.seed import seed

REQUIRED_TOOLS = {
    "get_inventory",
    "get_demand_forecast",
    "get_open_purchase_orders",
    "get_supplier_constraints",
    "get_budget",
    "get_storage_capacity",
    "calculate_replenishment",
}


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case_number,expected",
    [
        ("PC-1000", "ACCEPT"),
        ("PC-1001", "MODIFY"),
        ("PC-1003", "REJECT"),
        ("PC-1004", "INVESTIGATE"),
        ("PC-1005", "MODIFY"),
    ],
)
async def test_case_decisions(case_number: str, expected: str):
    await seed()
    async with SessionLocal() as session:
        case = (
            await session.execute(select(PurchasingCase).where(PurchasingCase.case_number == case_number))
        ).scalar_one_or_none()
        if case is None:
            pytest.skip("Database not seeded")
        run = await start_investigation(session, case.id)
        dec = (await session.execute(select(Decision).where(Decision.run_id == run.id))).scalars().first()
        assert dec is not None
        assert dec.decision == expected
        tools = (await session.execute(select(ToolCall).where(ToolCall.run_id == run.id))).scalars().all()
        names = {t.tool_name for t in tools}
        assert REQUIRED_TOOLS.issubset(names)
        if expected == "MODIFY" and case_number == "PC-1001":
            assert dec.recommended_quantity == 400
            assert "STORAGE_CONSTRAINT" in dec.reason_codes or "DEMAND_COVERAGE" in dec.reason_codes
