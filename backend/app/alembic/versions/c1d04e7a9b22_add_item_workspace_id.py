"""Add workspace_id to item

Revision ID: c1d04e7a9b22
Revises: b4c91e8f6a10
Create Date: 2026-08-25 22:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c1d04e7a9b22"
down_revision = "b4c91e8f6a10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("item", sa.Column("workspace_id", sa.Uuid(), nullable=True))
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE item SET workspace_id = u.workspace_id "
            'FROM "user" u WHERE item.owner_id = u.id AND u.workspace_id IS NOT NULL'
        )
    )
    conn.execute(
        sa.text(
            "UPDATE item SET workspace_id = m.workspace_id "
            "FROM workspace_membership m "
            "WHERE item.owner_id = m.user_id AND item.workspace_id IS NULL "
            "AND m.is_active IS TRUE"
        )
    )
    conn.execute(sa.text("DELETE FROM item WHERE workspace_id IS NULL"))
    op.alter_column("item", "workspace_id", nullable=False)
    op.create_index(
        op.f("ix_item_workspace_id"), "item", ["workspace_id"], unique=False
    )
    op.create_foreign_key(
        "item_workspace_id_fkey",
        "item",
        "workspace",
        ["workspace_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("item_workspace_id_fkey", "item", type_="foreignkey")
    op.drop_index(op.f("ix_item_workspace_id"), table_name="item")
    op.drop_column("item", "workspace_id")
