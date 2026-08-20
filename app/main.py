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
from app.core.config import settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"

app = FastAPI(title=settings.app_name, version="0.5.0")
app.include_router(auth_router, prefix="/api")
app.include_router(buildings_router, prefix="/api")
app.include_router(rooms_router, prefix="/api")
app.include_router(students_router, prefix="/api")
app.include_router(bookings_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

app.mount("/static", StaticFiles(directory=FRONTEND_ROOT), name="static")


@app.get("/", include_in_schema=False)
def frontend_index() -> FileResponse:
    return FileResponse(FRONTEND_ROOT / "index.html")


@app.get("/style-guide", include_in_schema=False)
def frontend_style_guide() -> FileResponse:
    return FileResponse(FRONTEND_ROOT / "style-guide.html")


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
