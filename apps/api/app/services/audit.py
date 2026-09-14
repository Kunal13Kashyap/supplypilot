from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog, ToolCall


async def record_audit(
    session: AsyncSession,
    *,
    event_type: str,
    actor: str = "system",
    case_id: uuid.UUID | None = None,
    run_id: uuid.UUID | None = None,
    payload: dict | None = None,
) -> None:
    session.add(
        AuditLog(
            case_id=case_id,
            run_id=run_id,
            event_type=event_type,
            actor=actor,
            payload=payload or {},
        )
    )


async def run_logged_tool(
    session: AsyncSession,
    *,
    run_id: uuid.UUID,
    case_id: uuid.UUID,
    tool_name: str,
    inputs: dict,
    summary: str,
    fn: Callable[[], Awaitable[Any]],
) -> Any:
    row = ToolCall(
        run_id=run_id,
        tool_name=tool_name,
        status="running",
        input_json=inputs,
        summary=summary,
    )
    session.add(row)
    await session.flush()
    started = time.perf_counter()
    try:
        result = await fn()
        if isinstance(result, dict):
            payload = result
        elif isinstance(result, list):
            payload = {
                "items": [x.model_dump() if hasattr(x, "model_dump") else x for x in result]
            }
        elif hasattr(result, "model_dump"):
            payload = result.model_dump()
        else:
            payload = {"value": result}
        row.status = "succeeded"
        row.output_json = payload
        row.duration_ms = int((time.perf_counter() - started) * 1000)
        await record_audit(
            session,
            event_type="tool_call",
            case_id=case_id,
            run_id=run_id,
            payload={"tool": tool_name, "status": "succeeded"},
        )
        await session.flush()
        return result
    except Exception as exc:
        row.status = "failed"
        row.error = str(exc)
        row.duration_ms = int((time.perf_counter() - started) * 1000)
        await record_audit(
            session,
            event_type="tool_error",
            case_id=case_id,
            run_id=run_id,
            payload={"tool": tool_name, "error": str(exc)},
        )
        await session.flush()
        raise
