"""Add invitation status and must_set_password

Revision ID: e8f3c1a04b77
Revises: c1d04e7a9b22
Create Date: 2026-08-25 22:40:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e8f3c1a04b77"
down_revision = "c1d04e7a9b22"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "workspace_membership",
        sa.Column("invitation_status", sa.String(length=32), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE workspace_membership SET invitation_status = 'accepted' "
            "WHERE invitation_status IS NULL"
        )
    )
    op.alter_column(
        "workspace_membership",
        "invitation_status",
        existing_type=sa.String(length=32),
        nullable=False,
    )
    op.add_column(
        "user",
        sa.Column("must_set_password", sa.Boolean(), nullable=True),
    )
    op.execute(sa.text('UPDATE "user" SET must_set_password = false'))
    op.alter_column(
        "user",
        "must_set_password",
        existing_type=sa.Boolean(),
        nullable=False,
    )


def downgrade():
    op.drop_column("user", "must_set_password")
    op.drop_column("workspace_membership", "invitation_status")
