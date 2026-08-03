from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.infrastructure.memory.scoring import combine_retrieval_score, recency_boost


def test_recency_boost_recent_is_near_one() -> None:
    now = datetime.now(UTC)
    assert recency_boost(now) > 0.95


def test_recency_boost_old_decays() -> None:
    old = datetime.now(UTC) - timedelta(days=30)
    assert recency_boost(old) < 0.5


def test_combine_retrieval_score_orders_importance() -> None:
    now = datetime.now(UTC)
    low = combine_retrieval_score(
        similarity=0.9, importance=0.2, created_at=now, access_count=0
    )
    high = combine_retrieval_score(
        similarity=0.9, importance=0.9, created_at=now, access_count=0
    )
    assert high > low
