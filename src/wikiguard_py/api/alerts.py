"""HTTP read access to alert history — read-only, never written to from here.

Paginated, sorted, and filtered server-side (not a bare unbounded list):
fired_alerts grows without bound as the consumer runs, so returning the
whole table on every poll doesn't scale — see chat for the 3.1MB/request
measurement that surfaced this.
"""

from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Integer, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from wikiguard_py.persistence.database import get_session
from wikiguard_py.persistence.models import FiredAlertModel
from wikiguard_py.persistence.schemas import FiredAlertRead

router = APIRouter(prefix="/alerts", tags=["alerts"])

MAX_LIMIT = 200

SortColumn = Literal["fired_at", "byte_change", "rule_type", "wiki", "user"]
SeverityLevel = Literal["low", "medium", "high"]

# Same abs(byte_change) bands the dashboard already uses client-side
# (severityOf() in dashboard.html) — kept in sync by hand, not shared code,
# since one side is Python and the other JS.
SEVERITY_BANDS = {
    "high": lambda col: func.abs(col) >= 5000,
    "medium": lambda col: func.abs(col).between(500, 4999),
    "low": lambda col: func.abs(col) < 500,
}

# Maps the query-param name to an actual SQLAlchemy column — never build
# ORDER BY from a raw string, even one already validated by Literal above.
SORTABLE_COLUMNS = {
    "fired_at": FiredAlertModel.fired_at,
    "byte_change": FiredAlertModel.byte_change,
    "rule_type": FiredAlertModel.rule_type,
    "wiki": FiredAlertModel.wiki,
    "user": FiredAlertModel.user,
}


class AlertsPage(BaseModel):
    items: list[FiredAlertRead]
    total: int


@router.get("", response_model=AlertsPage)
async def list_alerts(
    sort: SortColumn = "fired_at",
    order: Literal["asc", "desc"] = "desc",
    rule_type: str | None = None,
    wiki: str | None = None,
    severity: SeverityLevel | None = None,
    since_minutes: int | None = None,
    limit: int = Query(default=50, gt=0, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> AlertsPage:
    conditions = []
    if rule_type:
        conditions.append(FiredAlertModel.rule_type == rule_type)
    if wiki:
        conditions.append(FiredAlertModel.server_name == wiki)
    if severity:
        conditions.append(SEVERITY_BANDS[severity](FiredAlertModel.byte_change))
    if since_minutes is not None:
        # fired_at is stored naive (no tz) — compare against a naive UTC
        # value, not an aware one, or asyncpg rejects the comparison.
        cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=since_minutes)
        conditions.append(FiredAlertModel.fired_at >= cutoff)

    base_query = select(FiredAlertModel)
    count_query = select(func.count()).select_from(FiredAlertModel)
    for condition in conditions:
        base_query = base_query.where(condition)
        count_query = count_query.where(condition)

    total = (await session.execute(count_query)).scalar_one()

    order_column = SORTABLE_COLUMNS[sort]
    order_clause = order_column.asc() if order == "asc" else order_column.desc()
    result = await session.execute(base_query.order_by(order_clause).limit(limit).offset(offset))

    return AlertsPage(items=list(result.scalars()), total=total)


@router.get("/rate", response_model=list[int])
async def alert_rate(
    minutes: int = Query(default=30, gt=0, le=1440),
    buckets: int = Query(default=10, gt=0, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[int]:
    """Counts per trailing time bucket (oldest first, newest last) — computed
    with a single grouped SQL query, not by fetching rows and counting them
    client-side. Fetching rows for this breaks down once volume is high: a
    row-limited fetch's "200 most recent" can all land in the last minute,
    making every other bucket read zero (see chat)."""
    now = datetime.now(UTC).replace(tzinfo=None)
    window_start = now - timedelta(minutes=minutes)
    bucket_seconds = (minutes * 60) / buckets

    seconds_ago = func.extract("epoch", now - FiredAlertModel.fired_at)
    bucket_index = (buckets - 1 - func.floor(seconds_ago / bucket_seconds)).cast(Integer)

    result = await session.execute(
        select(bucket_index.label("bucket"), func.count())
        .where(FiredAlertModel.fired_at >= window_start)
        .group_by("bucket")
    )

    counts = [0] * buckets
    for bucket, count in result.all():
        if 0 <= bucket < buckets:
            counts[bucket] = count
    return counts


@router.get("/wikis", response_model=list[str])
async def list_alert_wikis(session: AsyncSession = Depends(get_session)) -> list[str]:
    """Distinct server_name values seen in fired_alerts — feeds the wiki
    filter dropdown with real values instead of free-text guessing."""
    result = await session.execute(
        select(FiredAlertModel.server_name).distinct().order_by(FiredAlertModel.server_name)
    )
    return list(result.scalars())
