"""Integration tests for the SQLAlchemy repositories against a real SQLite DB.

Exercises the repository implementations and the dialect-agnostic GUID/JSON
types end-to-end on SQLite. Uses an isolated in-memory SQLite engine per test.
"""

from __future__ import annotations

import time
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.application.auth.rbac import permissions_for_role
from app.core import security
from app.domain.entities.alert import Alert
from app.domain.entities.user import User
from app.domain.enums import (
    AlertCategory,
    AlertSource,
    AlertStatus,
    MitreTactic,
    RoleName,
    Severity,
)
from app.domain.repositories.alert_repository import AlertFilter
from app.domain.repositories.audit_repository import AuditEntry
from app.domain.value_objects.confidence import ConfidenceScore
from app.domain.value_objects.evidence import Evidence
from app.domain.value_objects.mitre import MitreTechnique
from app.infrastructure.db.base import Base
from app.infrastructure.db.models.user import RoleModel
from app.infrastructure.db.repositories import (
    SqlAlchemyAlertRepository,
    SqlAlchemyAuditLogRepository,
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyRoleRepository,
    SqlAlchemyUserRepository,
)

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def session():  # type: ignore[no-untyped-def]
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as s:
        s.add(
            RoleModel(
                name=RoleName.ANALYST.value,
                description="analyst",
                permissions=sorted(p.value for p in permissions_for_role(RoleName.ANALYST)),
            )
        )
        await s.commit()
        yield s
    await engine.dispose()


def _alert() -> Alert:
    return Alert(
        id=uuid.uuid4(),
        title="Encoded PowerShell",
        description="winword spawned encoded powershell",
        category=AlertCategory.LOTL,
        severity=Severity.HIGH,
        confidence=ConfidenceScore(78),
        source=AlertSource.AI,
        host="WIN-001",
        evidence=[Evidence(summary="cmd", event_id="e1", source="sysmon")],
        techniques=[MitreTechnique("T1059.001", "PowerShell", MitreTactic.EXECUTION)],
    )


async def test_user_create_and_fetch(session) -> None:  # type: ignore[no-untyped-def]
    repo = SqlAlchemyUserRepository(session)
    roles_repo = SqlAlchemyRoleRepository(session)
    analyst = await roles_repo.get_by_name(RoleName.ANALYST)
    assert analyst is not None

    user = User(id=uuid.uuid4(), email="a@corp.com", full_name="A", roles=[analyst])
    created = await repo.add(user, hashed_password=security.hash_password("x" * 12))
    await session.commit()

    fetched = await repo.get_by_email("a@corp.com")
    assert fetched is not None
    assert RoleName.ANALYST.value in fetched.role_names
    by_id = await repo.get_by_id(created.id)
    assert by_id is not None and by_id.email == "a@corp.com"


async def test_refresh_token_lifecycle(session) -> None:  # type: ignore[no-untyped-def]
    repo = SqlAlchemyRefreshTokenRepository(session)
    uid = uuid.uuid4()
    await repo.store(
        user_id=uid, token_hash="hash123", expires_at_epoch=int(time.time()) + 3600,
        user_agent="pytest", ip="127.0.0.1",
    )
    await session.commit()
    assert await repo.is_valid("hash123") is True
    await repo.revoke("hash123")
    await session.commit()
    assert await repo.is_valid("hash123") is False


async def test_alert_add_search_update(session) -> None:  # type: ignore[no-untyped-def]
    repo = SqlAlchemyAlertRepository(session)
    alert = _alert()
    await repo.add(alert)
    await session.commit()

    # JSON columns (evidence, techniques) round-trip via the dialect-agnostic type.
    fetched = await repo.get_by_id(alert.id)
    assert fetched is not None
    assert fetched.evidence and fetched.evidence[0].event_id == "e1"
    assert fetched.techniques and fetched.techniques[0].technique_id == "T1059.001"

    # Filtered search.
    found, total = await repo.search(AlertFilter(severity=Severity.HIGH))
    assert total == 1 and found[0].host == "WIN-001"

    # Update status.
    alert.status = AlertStatus.RESOLVED
    await repo.update(alert)
    await session.commit()
    again = await repo.get_by_id(alert.id)
    assert again is not None and again.status == AlertStatus.RESOLVED

    # Aggregations.
    by_sev = await repo.count_by_severity()
    assert by_sev.get(Severity.HIGH) == 1


async def test_audit_append_and_query(session) -> None:  # type: ignore[no-untyped-def]
    repo = SqlAlchemyAuditLogRepository(session)
    await repo.record(
        AuditEntry(actor_id=None, actor_label="system", action="alert.close",
                   resource_type="alert", resource_id="a1", metadata={"k": "v"})
    )
    await session.commit()
    items, total = await repo.query(action="alert.close")
    assert total == 1 and items[0]["action"] == "alert.close"
