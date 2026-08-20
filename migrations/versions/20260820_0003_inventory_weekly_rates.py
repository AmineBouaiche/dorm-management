"""weekly rates and active inventory

Revision ID: 20260820_0003
Revises: 20260819_0002
Create Date: 2026-08-20
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260820_0003"
down_revision: str | None = "20260819_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("buildings", sa.Column("image_url", sa.String(length=500), nullable=True))
    op.add_column(
        "buildings",
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )

    op.drop_constraint("ck_room_price_non_negative", "rooms", type_="check")
    op.alter_column("rooms", "price", new_column_name="weekly_rate")
    # Existing development data used an incompatible whole-booking price semantic.
    # Normalize those synthetic records to sensible weekly rates during the semantic migration.
    op.execute(
        sa.text(
            """
            UPDATE rooms
            SET weekly_rate = CASE room_type::text
                WHEN 'SHARED' THEN 150.00
                WHEN 'STUDIO' THEN 225.00
                ELSE 185.00
            END
            """
        )
    )
    op.create_check_constraint("ck_room_weekly_rate_non_negative", "rooms", "weekly_rate >= 0")
    op.add_column(
        "rooms",
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("rooms", "is_active")
    op.drop_constraint("ck_room_weekly_rate_non_negative", "rooms", type_="check")
    op.alter_column("rooms", "weekly_rate", new_column_name="price")
    op.create_check_constraint("ck_room_price_non_negative", "rooms", "price >= 0")

    op.drop_column("buildings", "is_active")
    op.drop_column("buildings", "image_url")
