"""Add embedding id to AI reports

Revision ID: 20260803_embedding_id
Revises: 20260803_initial
Create Date: 2026-08-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260803_embedding_id"
down_revision = "20260803_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ai_reports",
        sa.Column("embedding_id", sa.String(length=100), nullable=True),
    )
    op.create_index(
        op.f("ix_ai_reports_embedding_id"),
        "ai_reports",
        ["embedding_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_reports_embedding_id"), table_name="ai_reports")
    op.drop_column("ai_reports", "embedding_id")
