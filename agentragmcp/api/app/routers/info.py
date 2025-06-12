from fastapi import APIRouter
from senfast.api.app.db import database
router = APIRouter(prefix="/info", tags=["Info"])
# router = APIRouter(tags=["Info"])

@router.get("/version", summary="Versión de la app")
def version():
    return {"version": database.settings.APP_NAME}

@router.get("/config", summary="Configuración relevante (sin secretos)")
def config():
    settings = database.settings
    return {
        "db_host": settings.DB_HOST,
        "db_name": settings.DB_NAME,
        "pool_min": settings.POOL_MIN_CONN,
        "pool_max": settings.POOL_MAX_CONN,
        # etc, nunca password
    }