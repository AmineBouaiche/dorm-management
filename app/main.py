from fastapi import FastAPI

from app.api.routes import (
    admin_router,
    auth_router,
    bookings_router,
    buildings_router,
    rooms_router,
    students_router,
)
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.4.0")
app.include_router(auth_router, prefix="/api")
app.include_router(buildings_router, prefix="/api")
app.include_router(rooms_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(bookings_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
