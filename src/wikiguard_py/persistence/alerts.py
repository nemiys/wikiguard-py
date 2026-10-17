"""Writes the permanent record of an alert that actually fired."""

from wikiguard_py.persistence.database import async_session_factory
from wikiguard_py.persistence.models import FiredAlertModel


async def record_alert(
    rule_type: str,
    rule_id: int,
    page_title: str,
    wiki: str,
    server_name: str,
    user: str,
    byte_change: int,
    edit_count: int | None = None,
) -> None:
    async with async_session_factory() as session:
        session.add(
            FiredAlertModel(
                rule_type=rule_type,
                rule_id=rule_id,
                page_title=page_title,
                wiki=wiki,
                server_name=server_name,
                user=user,
                byte_change=byte_change,
                edit_count=edit_count,
            )
        )
        await session.commit()
