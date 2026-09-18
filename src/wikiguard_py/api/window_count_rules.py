"""HTTP CRUD for window-count rules — same shape as threshold_rules.py."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wikiguard_py.persistence.database import get_session
from wikiguard_py.persistence.models import WindowCountRuleModel
from wikiguard_py.persistence.schemas import (
    WindowCountRuleCreate,
    WindowCountRuleRead,
    WindowCountRuleUpdate,
)

router = APIRouter(prefix="/window-count-rules", tags=["window-count-rules"])


@router.post("", response_model=WindowCountRuleRead, status_code=201)
async def create_window_count_rule(
    payload: WindowCountRuleCreate, session: AsyncSession = Depends(get_session)
) -> WindowCountRuleModel:
    rule = WindowCountRuleModel(**payload.model_dump())
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


@router.get("", response_model=list[WindowCountRuleRead])
async def list_window_count_rules(
    session: AsyncSession = Depends(get_session),
) -> list[WindowCountRuleModel]:
    result = await session.execute(select(WindowCountRuleModel))
    return list(result.scalars())


@router.get("/{rule_id}", response_model=WindowCountRuleRead)
async def get_window_count_rule(
    rule_id: int, session: AsyncSession = Depends(get_session)
) -> WindowCountRuleModel:
    rule = await session.get(WindowCountRuleModel, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Window-count rule not found")
    return rule


@router.patch("/{rule_id}", response_model=WindowCountRuleRead)
async def update_window_count_rule(
    rule_id: int, payload: WindowCountRuleUpdate, session: AsyncSession = Depends(get_session)
) -> WindowCountRuleModel:
    rule = await session.get(WindowCountRuleModel, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Window-count rule not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)

    await session.commit()
    await session.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204)
async def delete_window_count_rule(
    rule_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    rule = await session.get(WindowCountRuleModel, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Window-count rule not found")

    await session.delete(rule)
    await session.commit()
