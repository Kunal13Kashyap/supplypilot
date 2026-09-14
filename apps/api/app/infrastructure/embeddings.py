from __future__ import annotations

import hashlib
import math
import random

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import KnowledgeDocument
from app.schemas.agent import KnowledgeHit


def mock_embedding(text: str, dims: int = 1536) -> list[float]:
    seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    vec = [rng.gauss(0, 1) for _ in range(dims)]
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


async def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.use_mock_llm:
        return mock_embedding(text, settings.embedding_dimensions)
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.llm_timeout_seconds)
    resp = await client.embeddings.create(model=settings.openai_embedding_model, input=text)
    return resp.data[0].embedding


async def search_knowledge(session: AsyncSession, query: str, k: int = 3) -> list[KnowledgeHit]:
    vector = await embed_text(query)
    vec_literal = "[" + ",".join(str(x) for x in vector) + "]"
    hits: list[KnowledgeHit] = []
    try:
        rows = (
            await session.execute(
                text(
                    """
                    SELECT title, source, body,
                           1 - (embedding <=> CAST(:v AS vector)) AS score
                    FROM knowledge_documents
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> CAST(:v AS vector)
                    LIMIT :k
                    """
                ),
                {"v": vec_literal, "k": k},
            )
        ).all()
        for title, source, body, score in rows:
            hits.append(
                KnowledgeHit(
                    title=title,
                    source=source,
                    excerpt=body[:400],
                    score=float(score or 0),
                )
            )
    except Exception:
        docs = (await session.execute(select(KnowledgeDocument))).scalars().all()
        q = query.lower()
        ranked = sorted(
            docs,
            key=lambda d: sum(1 for tok in q.split() if tok in d.body.lower()),
            reverse=True,
        )
        for d in ranked[:k]:
            hits.append(KnowledgeHit(title=d.title, source=d.source, excerpt=d.body[:400], score=0.5))
    if not hits:
        docs = (await session.execute(select(KnowledgeDocument))).scalars().all()
        for d in docs[:k]:
            hits.append(KnowledgeHit(title=d.title, source=d.source, excerpt=d.body[:400], score=0.1))
    return hits
