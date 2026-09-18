"""SQLAlchemy models — the DB-side shape of things (see ADR-0005: kept
separate from the Pydantic schemas the API exposes).

One table per rule type (not one shared table with nullable columns) — same
reasoning as ADR-0006: each rule type owns its own data, and adding a new
rule type later shouldn't touch existing tables at all.
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from wikiguard_py.persistence.database import Base


class ThresholdRuleModel(Base):
    __tablename__ = "threshold_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    byte_threshold: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class WindowCountRuleModel(Base):
    __tablename__ = "window_count_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    window_seconds: Mapped[int]
    edit_count_threshold: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class FiredAlertModel(Base):
    """One row per alert that actually fired — never one row per raw event
    (see architecture-plan.md principle #5). rule_type + rule_id point at a
    row in whichever rules table fired this, with no DB-enforced foreign
    key — a deliberate, agreed simplification (see chat)."""

    __tablename__ = "fired_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_type: Mapped[str]
    rule_id: Mapped[int]
    page_title: Mapped[str]
    fired_at: Mapped[datetime] = mapped_column(server_default=func.now())
