from enum import StrEnum


class UserRole(StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


class RoomType(StrEnum):
    SINGLE = "single"
    SHARED = "shared"
    STUDIO = "studio"


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
