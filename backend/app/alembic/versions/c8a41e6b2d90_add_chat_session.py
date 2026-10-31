"""Add chat session and message tables

Revision ID: c8a41e6b2d90
Revises: b7e2a1c94d08
Create Date: 2026-10-30 23:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "c8a41e6b2d90"
down_revision = "b7e2a1c94d08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chat_session",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("channel", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_session_workspace_id", "chat_session", ["workspace_id"])
    op.create_table(
        "chat_message",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"], ["chat_session.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_message_session_id", "chat_message", ["session_id"])
    op.create_index("ix_chat_message_workspace_id", "chat_message", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_chat_message_workspace_id", table_name="chat_message")
    op.drop_index("ix_chat_message_session_id", table_name="chat_message")
    op.drop_table("chat_message")
    op.drop_index("ix_chat_session_workspace_id", table_name="chat_session")
    op.drop_table("chat_session")
