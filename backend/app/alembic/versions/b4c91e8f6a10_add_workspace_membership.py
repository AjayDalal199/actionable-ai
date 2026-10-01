"""Add workspace memberships and created_by; drop user.role

Revision ID: b4c91e8f6a10
Revises: a7e52fde2081
Create Date: 2026-08-25 21:20:00.000000

"""
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b4c91e8f6a10"
down_revision = "a7e52fde2081"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "workspace_membership",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["workspace_id"], ["workspace.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "workspace_id"),
    )
    op.create_index(
        op.f("ix_workspace_membership_workspace_id"),
        "workspace_membership",
        ["workspace_id"],
        unique=False,
    )
    op.add_column("workspace", sa.Column("created_by_id", sa.Uuid(), nullable=True))
    op.create_index(
        op.f("ix_workspace_created_by_id"),
        "workspace",
        ["created_by_id"],
        unique=True,
    )
    op.create_foreign_key(
        "workspace_created_by_id_fkey",
        "workspace",
        "user",
        ["created_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    conn = op.get_bind()
    now = datetime.now(UTC)
    rows = conn.execute(
        sa.text(
            'SELECT id, workspace_id, role FROM "user" '
            "WHERE workspace_id IS NOT NULL AND role IS NOT NULL"
        )
    ).fetchall()
    for user_id, workspace_id, role in rows:
        conn.execute(
            sa.text(
                "INSERT INTO workspace_membership "
                "(user_id, workspace_id, role, is_active, created_at) "
                "VALUES (:user_id, :workspace_id, :role, true, :created_at)"
            ),
            {
                "user_id": user_id,
                "workspace_id": workspace_id,
                "role": role,
                "created_at": now,
            },
        )

    workspaces = conn.execute(sa.text("SELECT id FROM workspace")).fetchall()
    for (workspace_id,) in workspaces:
        admin = conn.execute(
            sa.text(
                "SELECT m.user_id FROM workspace_membership m "
                'JOIN "user" u ON u.id = m.user_id '
                "WHERE m.workspace_id = :workspace_id AND m.role = 'admin' "
                "ORDER BY u.created_at ASC LIMIT 1"
            ),
            {"workspace_id": workspace_id},
        ).fetchone()
        if admin:
            conn.execute(
                sa.text(
                    "UPDATE workspace SET created_by_id = :user_id WHERE id = :workspace_id"
                ),
                {"user_id": admin[0], "workspace_id": workspace_id},
            )

    op.drop_column("user", "role")


def downgrade():
    op.add_column("user", sa.Column("role", sa.String(length=32), nullable=True))
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            'SELECT u.id, u.workspace_id, m.role FROM "user" u '
            "JOIN workspace_membership m ON m.user_id = u.id "
            "AND m.workspace_id = u.workspace_id"
        )
    ).fetchall()
    for user_id, _workspace_id, role in rows:
        conn.execute(
            sa.text('UPDATE "user" SET role = :role WHERE id = :user_id'),
            {"role": role, "user_id": user_id},
        )
    op.drop_constraint("workspace_created_by_id_fkey", "workspace", type_="foreignkey")
    op.drop_index(op.f("ix_workspace_created_by_id"), table_name="workspace")
    op.drop_column("workspace", "created_by_id")
    op.drop_index(
        op.f("ix_workspace_membership_workspace_id"),
        table_name="workspace_membership",
    )
    op.drop_table("workspace_membership")
