"""Create initial dorm management schema.

Revision ID: 20260819_0001
Revises:
Create Date: 2026-08-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260819_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_role = postgresql.ENUM("STUDENT", "ADMIN", name="user_role", create_type=False)
room_type = postgresql.ENUM("SINGLE", "SHARED", "STUDIO", name="room_type", create_type=False)
booking_status = postgresql.ENUM(
    "PENDING", "CONFIRMED", "CANCELLED", name="booking_status", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    room_type.create(bind, checkfirst=True)
    booking_status.create(bind, checkfirst=True)

    op.create_table(
        "buildings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "rooms",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("building_id", sa.Integer(), nullable=False),
        sa.Column("room_number", sa.String(length=20), nullable=False),
        sa.Column("room_type", room_type, nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("capacity > 0", name="ck_room_capacity_positive"),
        sa.CheckConstraint("price >= 0", name="ck_room_price_non_negative"),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("building_id", "room_number", name="uq_room_building_number"),
    )
    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_students_student_id"), "students", ["student_id"], unique=True)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", booking_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("amount >= 0", name="ck_booking_amount_non_negative"),
        sa.CheckConstraint("start_date < end_date", name="ck_booking_valid_date_range"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_room_id"), "bookings", ["room_id"], unique=False)
    op.create_index(op.f("ix_bookings_status"), "bookings", ["status"], unique=False)
    op.create_index(op.f("ix_bookings_student_id"), "bookings", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_student_id"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_status"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_room_id"), table_name="bookings")
    op.drop_table("bookings")
    op.drop_index(op.f("ix_students_student_id"), table_name="students")
    op.drop_table("students")
    op.drop_table("rooms")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
    op.drop_table("buildings")

    bind = op.get_bind()
    booking_status.drop(bind, checkfirst=True)
    room_type.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
