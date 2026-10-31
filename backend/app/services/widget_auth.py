"""Verify a host-minted end-user JWT. Dashboard tokens are never accepted."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.models import Workspace

SIGN_IN_NOTICE = "Sign in to run actions. I can still answer questions."
EXPIRED_NOTICE = (
    "Your session expired. I can still answer questions, but I can't run actions."
)
INVALID_NOTICE = "This session can't run actions. I can still answer questions."

PREVIEW_TOKEN_MINUTES = 15


class WidgetWorkspaceNotFound(Exception):
    """No workspace uses this public widget key."""


@dataclass(frozen=True, kw_only=True)
class WidgetAccess:
    workspace: Workspace
    subject: str | None
    email: str | None
    token: str | None
    notice: str | None

    @property
    def writes(self) -> bool:
        return self.token is not None


def issue_widget_token(
    *,
    secret: str,
    subject: str,
    email: str | None = None,
    minutes: int = PREVIEW_TOKEN_MINUTES,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    if email:
        payload["email"] = email
    encoded = jwt.encode(payload, secret, algorithm=security.ALGORITHM)
    return encoded if isinstance(encoded, str) else encoded.decode()


def resolve_widget_access(
    session: Session, *, workspace_key: uuid.UUID, token: str | None
) -> WidgetAccess:
    workspace = session.exec(
        select(Workspace).where(Workspace.widget_key == workspace_key)
    ).first()
    if workspace is None:
        raise WidgetWorkspaceNotFound
    if not token or not token.strip():
        return _readonly(workspace, SIGN_IN_NOTICE)
    raw = token.strip()
    if _is_dashboard_token(raw):
        return _readonly(workspace, INVALID_NOTICE)
    try:
        payload = jwt.decode(
            raw,
            workspace.widget_secret,
            algorithms=[security.ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
    except ExpiredSignatureError:
        return _readonly(workspace, EXPIRED_NOTICE)
    except InvalidTokenError:
        return _readonly(workspace, INVALID_NOTICE)
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        return _readonly(workspace, INVALID_NOTICE)
    email = payload.get("email")
    return WidgetAccess(
        workspace=workspace,
        subject=subject.strip(),
        email=email.strip() if isinstance(email, str) and email.strip() else None,
        token=raw,
        notice=None,
    )


def _readonly(workspace: Workspace, notice: str) -> WidgetAccess:
    return WidgetAccess(
        workspace=workspace,
        subject=None,
        email=None,
        token=None,
        notice=notice,
    )


def _is_dashboard_token(token: str) -> bool:
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
    except InvalidTokenError:
        return False
    return True
