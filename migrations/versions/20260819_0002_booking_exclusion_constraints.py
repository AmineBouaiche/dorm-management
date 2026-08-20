"""Protect booking overlap invariants in PostgreSQL.

Revision ID: 20260819_0002
Revises: 20260819_0001
Create Date: 2026-08-19
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260819_0002"
down_revision: Union[str, None] = "20260819_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # btree_gist supplies GiST equality operators for integer IDs, allowing us
    # to combine an ID equality check with a date-range overlap check.
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT excl_booking_room_overlap
        EXCLUDE USING gist (
            room_id WITH =,
            daterange(start_date, end_date, '[)') WITH &&
        )
        WHERE (status IN ('PENDING', 'CONFIRMED'))
        """
    )
    op.execute(
        """
        ALTER TABLE bookings
        ADD CONSTRAINT excl_booking_student_overlap
        EXCLUDE USING gist (
            student_id WITH =,
            daterange(start_date, end_date, '[)') WITH &&
        )
        WHERE (status IN ('PENDING', 'CONFIRMED'))
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS excl_booking_student_overlap")
    op.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS excl_booking_room_overlap")
