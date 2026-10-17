"""Pydantic schemas — the public shape exposed over HTTP (see ADR-0005).

Separate from the SQLAlchemy models in models.py on purpose: these control
exactly what a client can send in and what they get back, independent of
how a row is actually stored.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ThresholdRuleCreate(BaseModel):
    byte_threshold: int
    is_active: bool = True


class ThresholdRuleUpdate(BaseModel):
    byte_threshold: int | None = None
    is_active: bool | None = None


class ThresholdRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    byte_threshold: int
    is_active: bool
    created_at: datetime


class WindowCountRuleCreate(BaseModel):
    window_seconds: int
    edit_count_threshold: int
    is_active: bool = True


class WindowCountRuleUpdate(BaseModel):
    window_seconds: int | None = None
    edit_count_threshold: int | None = None
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
    fired_at: datetime
