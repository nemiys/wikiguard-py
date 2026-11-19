"""HTTP CRUD for threshold rules."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wikiguard_py.api.rule_crud import apply_update, delete_rule, get_rule_or_404, save_new_rule
from wikiguard_py.persistence.database import get_session
from wikiguard_py.persistence.models import ThresholdRuleModel
from wikiguard_py.persistence.schemas import (
    ThresholdRuleCreate,
    ThresholdRuleRead,
    ThresholdRuleUpdate,
)

router = APIRouter(prefix="/threshold-rules", tags=["threshold-rules"])

NOT_FOUND = "Threshold rule not found"


@router.post("", response_model=ThresholdRuleRead, status_code=201)
async def create_threshold_rule(
    payload: ThresholdRuleCreate, session: AsyncSession = Depends(get_session)
) -> ThresholdRuleModel:
    return await save_new_rule(session, ThresholdRuleModel(**payload.model_dump()))


@router.get("", response_model=list[ThresholdRuleRead])
async def list_threshold_rules(
    session: AsyncSession = Depends(get_session),
) -> list[ThresholdRuleModel]:
    result = await session.execute(select(ThresholdRuleModel).order_by(ThresholdRuleModel.id))
    return list(result.scalars())


@router.get("/{rule_id}", response_model=ThresholdRuleRead)
async def get_threshold_rule(
    rule_id: int, session: AsyncSession = Depends(get_session)
) -> ThresholdRuleModel:
    return await get_rule_or_404(session, ThresholdRuleModel, rule_id, NOT_FOUND)


@router.patch("/{rule_id}", response_model=ThresholdRuleRead)
async def update_threshold_rule(
    rule_id: int, payload: ThresholdRuleUpdate, session: AsyncSession = Depends(get_session)
) -> ThresholdRuleModel:
    rule = await get_rule_or_404(session, ThresholdRuleModel, rule_id, NOT_FOUND)
    return await apply_update(session, rule, payload)


@router.delete("/{rule_id}", status_code=204)
async def delete_threshold_rule(rule_id: int, session: AsyncSession = Depends(get_session)) -> None:
    rule = await get_rule_or_404(session, ThresholdRuleModel, rule_id, NOT_FOUND)
    await delete_rule(session, rule)
