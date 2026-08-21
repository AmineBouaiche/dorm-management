from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    admin_router,
    auth_router,
    bookings_router,
    buildings_router,
    rooms_router,
    students_router,
)
from app.core.config import Settings, settings
from app.core.security_headers import SecurityHeadersMiddleware

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"


def create_app(app_settings: Settings = settings) -> FastAPI:
    application = FastAPI(
        title=app_settings.app_name,
        version="0.6.1",
        docs_url=None if app_settings.is_production else "/docs",
        redoc_url=None if app_settings.is_production else "/redoc",
        openapi_url=None if app_settings.is_production else "/openapi.json",
    )
    application.add_middleware(
        SecurityHeadersMiddleware,
        allow_swagger_assets=not app_settings.is_production,
    )

    application.include_router(auth_router, prefix="/api")
    application.include_router(buildings_router, prefix="/api")
    application.include_router(rooms_router, prefix="/api")
    application.include_router(students_router, prefix="/api")
    application.include_router(bookings_router, prefix="/api")
    application.include_router(admin_router, prefix="/api")

    application.mount("/static", StaticFiles(directory=FRONTEND_ROOT), name="static")

    @application.get("/", include_in_schema=False)
    def frontend_index() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "student" / "dashboard.html")

    if not app_settings.is_production:
        @application.get("/style-guide", include_in_schema=False)
        def frontend_style_guide() -> FileResponse:
            return FileResponse(FRONTEND_ROOT / "style-guide.html")

    @application.get("/login", include_in_schema=False)
    def frontend_login() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "auth" / "login.html")

    @application.get("/register", include_in_schema=False)
    def frontend_register() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "auth" / "register.html")

    @application.get("/admin", include_in_schema=False)
    def frontend_admin_overview() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "admin" / "overview.html")

    @application.get("/admin/rooms", include_in_schema=False)
    def frontend_admin_rooms() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "admin" / "rooms.html")

    @application.get("/admin/residences", include_in_schema=False)
    def frontend_admin_residences() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "admin" / "residences.html")

    @application.get("/admin/students", include_in_schema=False)
    def frontend_admin_students() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "admin" / "students.html")

    @application.get("/admin/students/{student_id}", include_in_schema=False)
    def frontend_admin_student_detail(student_id: int) -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "admin" / "student-detail.html")

    @application.get("/admin/bookings", include_in_schema=False)
    def frontend_admin_bookings() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "admin" / "bookings.html")

    @application.get("/admin/bookings/{booking_id}", include_in_schema=False)
    def frontend_admin_booking_detail(booking_id: int) -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "admin" / "booking-detail.html")

    @application.get("/rooms", include_in_schema=False)
    def frontend_rooms() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "rooms" / "index.html")

    @application.get("/rooms/{room_id}", include_in_schema=False)
    def frontend_room_detail(room_id: int) -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "rooms" / "detail.html")

    @application.get("/booking/confirm", include_in_schema=False)
    def frontend_booking_handoff() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "rooms" / "booking-handoff.html")

    @application.get("/booking/submitted", include_in_schema=False)
    def frontend_booking_submitted() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "rooms" / "booking-submitted.html")

    @application.get("/bookings", include_in_schema=False)
    def frontend_bookings() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "student" / "bookings.html")

    @application.get("/bookings/{booking_id}", include_in_schema=False)
    def frontend_booking_detail(booking_id: int) -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "student" / "booking-detail.html")

    @application.get("/account", include_in_schema=False)
    def frontend_account() -> FileResponse:
        return FileResponse(FRONTEND_ROOT / "student" / "account.html")

    @application.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
