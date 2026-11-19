"""The steps every rule router shares, so both rule types behave the same.

The routers themselves stay explicit, one per rule type, so each endpoint keeps its own
typed request and response schema in the API docs.
"""

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from wikiguard_py.persistence.models import ThresholdRuleModel, WindowCountRuleModel

RuleModel = ThresholdRuleModel | WindowCountRuleModel


async def get_rule_or_404[M: RuleModel](
    session: AsyncSession, model: type[M], rule_id: int, not_found: str
) -> M:
    rule = await session.get(model, rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=not_found)
    return rule


async def save_new_rule[M: RuleModel](session: AsyncSession, rule: M) -> M:
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def apply_update[M: RuleModel](session: AsyncSession, rule: M, payload: BaseModel) -> M:
    # Only the fields the client actually sent: PATCH leaves the rest as they are.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    await session.commit()
    await session.refresh(rule)
    return rule


async def delete_rule(session: AsyncSession, rule: RuleModel) -> None:
    await session.delete(rule)
    await session.commit()
