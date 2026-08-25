"""Backfill workspaces for existing users

Revision ID: a7e52fde2081
Revises: af33b4f1562a
Create Date: 2026-08-25 16:45:53.578545

"""
import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a7e52fde2081"
down_revision = "af33b4f1562a"
branch_labels = None
depends_on = None


def _workspace_name(email: str) -> str:
    _, separator, domain = email.partition("@")
    if separator and domain:
        label = domain.split(".")[0].strip()
        if label:
            return label.capitalize()[:255]
    local = email.partition("@")[0].strip()
    return (local or "Workspace")[:255]


def upgrade():
    conn = op.get_bind()
    rows = conn.execute(
        sa.text('SELECT id, email FROM "user" WHERE workspace_id IS NULL')
    ).fetchall()
    for user_id, email in rows:
        workspace_id = uuid.uuid4()
        conn.execute(
            sa.text(
                "INSERT INTO workspace (id, name, created_at) "
                "VALUES (:id, :name, :created_at)"
            ),
            {
                "id": workspace_id,
                "name": _workspace_name(email),
                "created_at": datetime.now(UTC),
            },
        )
        conn.execute(
            sa.text(
                'UPDATE "user" SET workspace_id = :workspace_id, role = :role '
                "WHERE id = :user_id"
            ),
            {
                "workspace_id": workspace_id,
                "role": "admin",
                "user_id": user_id,
            },
        )


def downgrade():
    # Cannot distinguish backfilled workspaces from later signups.
    pass
