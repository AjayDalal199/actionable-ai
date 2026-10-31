"""Add the public widget key and end-user JWT secret

Revision ID: d4e8b1c07a55
Revises: c8a41e6b2d90
Create Date: 2026-10-31 16:40:00.000000

"""

import secrets
import uuid

import sqlalchemy as sa
from alembic import op

revision = "d4e8b1c07a55"
down_revision = "c8a41e6b2d90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workspace", sa.Column("widget_key", sa.Uuid(), nullable=True))
    op.add_column(
        "workspace", sa.Column("widget_secret", sa.String(length=128), nullable=True)
    )
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id FROM workspace")).fetchall()
    for (workspace_id,) in rows:
        connection.execute(
            sa.text(
                "UPDATE workspace SET widget_key = :widget_key, "
                "widget_secret = :widget_secret WHERE id = :id"
            ),
            {
                "widget_key": uuid.uuid4(),
                "widget_secret": secrets.token_urlsafe(32),
                "id": workspace_id,
            },
        )
    op.alter_column("workspace", "widget_key", nullable=False)
    op.alter_column("workspace", "widget_secret", nullable=False)
    op.create_index(
        "ix_workspace_widget_key", "workspace", ["widget_key"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_widget_key", table_name="workspace")
    op.drop_column("workspace", "widget_secret")
    op.drop_column("workspace", "widget_key")
