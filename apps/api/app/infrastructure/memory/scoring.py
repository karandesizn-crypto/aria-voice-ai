from __future__ import annotations

import math
from datetime import UTC, datetime


def recency_boost(created_at: datetime | None, *, half_life_days: float = 14.0) -> float:
    if created_at is None:
        return 0.5
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    age_days = max((datetime.now(UTC) - created_at).total_seconds() / 86400.0, 0.0)
    return math.exp(-math.log(2) * age_days / half_life_days)


def combine_retrieval_score(
    *,
    similarity: float,
    importance: float,
    created_at: datetime | None,
    access_count: int,
) -> float:
    """Blend vector similarity with importance, recency, and mild popularity."""
    popularity = 1.0 + min(access_count, 20) * 0.01
    return max(similarity, 0.0) * max(importance, 0.05) * recency_boost(created_at) * popularity
