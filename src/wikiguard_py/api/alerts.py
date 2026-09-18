"""HTTP read access to alert history — read-only, never written to from here."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wikiguard_py.persistence.database import get_session
from wikiguard_py.persistence.models import FiredAlertModel
from wikiguard_py.persistence.schemas import FiredAlertRead

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[FiredAlertRead])
async def list_alerts(session: AsyncSession = Depends(get_session)) -> list[FiredAlertModel]:
    result = await session.execute(
        select(FiredAlertModel).order_by(FiredAlertModel.fired_at.desc())
    )
    return list(result.scalars())
