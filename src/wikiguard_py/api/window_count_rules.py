"""HTTP CRUD for window-count rules — same shape as threshold_rules.py."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from wikiguard_py.api.rule_crud import apply_update, delete_rule, get_rule_or_404, save_new_rule
from wikiguard_py.persistence.database import get_session
from wikiguard_py.persistence.models import WindowCountRuleModel
from wikiguard_py.persistence.schemas import (
    WindowCountRuleCreate,
    WindowCountRuleRead,
    WindowCountRuleUpdate,
)

router = APIRouter(prefix="/window-count-rules", tags=["window-count-rules"])

NOT_FOUND = "Window-count rule not found"


@router.post("", response_model=WindowCountRuleRead, status_code=201)
async def create_window_count_rule(
    payload: WindowCountRuleCreate, session: AsyncSession = Depends(get_session)
) -> WindowCountRuleModel:
    return await save_new_rule(session, WindowCountRuleModel(**payload.model_dump()))


@router.get("", response_model=list[WindowCountRuleRead])
async def list_window_count_rules(
    session: AsyncSession = Depends(get_session),
) -> list[WindowCountRuleModel]:
    result = await session.execute(select(WindowCountRuleModel).order_by(WindowCountRuleModel.id))
    return list(result.scalars())


@router.get("/{rule_id}", response_model=WindowCountRuleRead)
async def get_window_count_rule(
    rule_id: int, session: AsyncSession = Depends(get_session)
) -> WindowCountRuleModel:
    return await get_rule_or_404(session, WindowCountRuleModel, rule_id, NOT_FOUND)


@router.patch("/{rule_id}", response_model=WindowCountRuleRead)
async def update_window_count_rule(
    rule_id: int, payload: WindowCountRuleUpdate, session: AsyncSession = Depends(get_session)
) -> WindowCountRuleModel:
    rule = await get_rule_or_404(session, WindowCountRuleModel, rule_id, NOT_FOUND)
    return await apply_update(session, rule, payload)


@router.delete("/{rule_id}", status_code=204)
async def delete_window_count_rule(
    rule_id: int, session: AsyncSession = Depends(get_session)
) -> None:
    rule = await get_rule_or_404(session, WindowCountRuleModel, rule_id, NOT_FOUND)
    await delete_rule(session, rule)
