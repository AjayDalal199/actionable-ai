import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.models import Workspace
from app.services.widget_auth import (
    INVALID_NOTICE,
    SIGN_IN_NOTICE,
    WidgetWorkspaceNotFound,
    issue_widget_token,
    resolve_widget_access,
)


def _workspace(db: Session, *, secret: str | None = None) -> Workspace:
    row = Workspace(
        name=f"Widget {uuid.uuid4()}", widget_secret=secret or "widget-secret"
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_missing_token_is_read_only(db: Session) -> None:
    workspace = _workspace(db)
    access = resolve_widget_access(db, workspace_key=workspace.widget_key, token=None)
    assert access.writes is False
    assert access.token is None
    assert access.notice == SIGN_IN_NOTICE


def test_dashboard_token_is_not_an_end_user(db: Session) -> None:
    workspace = _workspace(db, secret=settings.SECRET_KEY)
    dashboard = jwt.encode(
        {"sub": str(uuid.uuid4()), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    access = resolve_widget_access(
        db, workspace_key=workspace.widget_key, token=dashboard
    )
    assert access.writes is False
    assert access.token is None
    assert access.notice == INVALID_NOTICE


def test_valid_end_user_token_can_run_actions(db: Session) -> None:
    workspace = _workspace(db)
    token = issue_widget_token(
        secret=workspace.widget_secret, subject="user-1", email="ada@example.com"
    )
    access = resolve_widget_access(db, workspace_key=workspace.widget_key, token=token)
    assert access.writes is True
    assert access.token == token
    assert access.subject == "user-1"
    assert access.email == "ada@example.com"
    assert access.notice is None


def test_expired_token_cannot_run_actions(db: Session) -> None:
    workspace = _workspace(db)
    expired = jwt.encode(
        {"sub": "user-1", "exp": datetime.now(UTC) - timedelta(minutes=5)},
        workspace.widget_secret,
        algorithm=security.ALGORITHM,
    )
    access = resolve_widget_access(
        db, workspace_key=workspace.widget_key, token=expired
    )
    assert access.writes is False


def test_unknown_widget_key_is_rejected(db: Session) -> None:
    _workspace(db)
    with pytest.raises(WidgetWorkspaceNotFound):
        resolve_widget_access(db, workspace_key=uuid.uuid4(), token=None)
