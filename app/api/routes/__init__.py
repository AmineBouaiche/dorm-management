from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.bookings import router as bookings_router
from app.api.routes.buildings import router as buildings_router
from app.api.routes.rooms import router as rooms_router
from app.api.routes.students import router as students_router

__all__ = [
    "admin_router",
    "auth_router",
    "bookings_router",
    "buildings_router",
    "rooms_router",
    "students_router",
]
