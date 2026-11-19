"""Pydantic schemas — the public shape exposed over HTTP (see ADR-0004).

Separate from the SQLAlchemy models in models.py on purpose: these control
exactly what a client can send in and what they get back, independent of
how a row is actually stored.
"""

from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

# A rule with a threshold or window of 0 fires on every edit or never fires at all.
Positive = Annotated[int, Field(gt=0)]


class RuleUpdate(BaseModel):
    """PATCH semantics: a field may be left out, but not set to null (the columns are NOT
    NULL; without this check an explicit null reaches the database and fails as a 500)."""

    @model_validator(mode="after")
    def _reject_explicit_nulls(self) -> Self:
        nulls = sorted(name for name in self.model_fields_set if getattr(self, name) is None)
        if nulls:
            raise ValueError(f"{', '.join(nulls)} cannot be null")
        return self


class ThresholdRuleCreate(BaseModel):
    byte_threshold: Positive
    is_active: bool = True


class ThresholdRuleUpdate(RuleUpdate):
    byte_threshold: Positive | None = None
    is_active: bool | None = None


class ThresholdRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    byte_threshold: int
    is_active: bool
    created_at: datetime


class WindowCountRuleCreate(BaseModel):
    window_seconds: Positive
    edit_count_threshold: Positive
    is_active: bool = True


class WindowCountRuleUpdate(RuleUpdate):
    window_seconds: Positive | None = None
    edit_count_threshold: Positive | None = None
    is_active: bool | None = None


class WindowCountRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    window_seconds: int
    edit_count_threshold: int
    is_active: bool
    created_at: datetime


class FiredAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rule_type: str
    rule_id: int
    page_title: str
    wiki: str
    server_name: str
    user: str
    byte_change: int
    edit_count: int | None
    fired_at: datetime
