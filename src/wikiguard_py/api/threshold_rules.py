"""HTTP CRUD for threshold rules."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wikiguard_py.persistence.database import get_session
from wikiguard_py.persistence.models import ThresholdRuleModel
from wikiguard_py.persistence.schemas import (
    ThresholdRuleCreate,
    ThresholdRuleRead,
    ThresholdRuleUpdate,
)

router = APIRouter(prefix="/threshold-rules", tags=["threshold-rules"])


@router.post("", response_model=ThresholdRuleRead, status_code=201)
async def create_threshold_rule(
    payload: ThresholdRuleCreate, session: AsyncSession = Depends(get_session)
) -> ThresholdRuleModel:
    rule = ThresholdRuleModel(**payload.model_dump())
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


@router.get("", response_model=list[ThresholdRuleRead])
async def list_threshold_rules(
    session: AsyncSession = Depends(get_session),
) -> list[ThresholdRuleModel]:
    result = await session.execute(select(ThresholdRuleModel))
    return list(result.scalars())


@router.get("/{rule_id}", response_model=ThresholdRuleRead)
async def get_threshold_rule(
    rule_id: int, session: AsyncSession = Depends(get_session)
) -> ThresholdRuleModel:
    rule = await session.get(ThresholdRuleModel, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Threshold rule not found")
    return rule


@router.patch("/{rule_id}", response_model=ThresholdRuleRead)
async def update_threshold_rule(
    rule_id: int, payload: ThresholdRuleUpdate, session: AsyncSession = Depends(get_session)
) -> ThresholdRuleModel:
    rule = await session.get(ThresholdRuleModel, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Threshold rule not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    await session.commit()
    await session.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_threshold_rule(
    rule_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    rule = await session.get(ThresholdRuleModel, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Threshold rule not found")

    await session.delete(rule)
    await session.commit()
