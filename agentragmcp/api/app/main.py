
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi

from senfast.api.app.db import database
from senfast.core.monitoring import setup_logging, add_request_id
from senfast.core.config import get_settings
# from senfast.core.routes import router
# from senfast.api.app.routers import health, docs, info, metrics_route, data_sobreeixidors, data_taigua
from senfast.api.app.routers import health, docs, info, metrics_route
from senfast.api.app.routers import data_sobreeixidors, data_taigua
from senfast.core.metrics import setup_metrics
from fastapi import Request, HTTPException

# settings = get_settings()
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        database.POOL = database.create_connection_pool()
        print("Pool de conexiones creado OK")
    except Exception as e:
        print(f"Error al crear el pool de conexiones: {e}")
        # Lanzar excepción para evitar que la app arranque sin pool
        raise RuntimeError("No se pudo crear el pool de conexiones, la aplicación no puede arrancar.") from e
    yield
    # Shutdown
    if database.POOL:
        try:
            database.POOL.close()
            print("Pool de conexiones cerrado correctamente")
        except Exception as e:
            print(f"Error al cerrar el pool de conexiones: {e}")

def get_api() -> FastAPI:
    """Return the FastAPI app, configured for the environment.

    Add endpoint profiler or monitoring setup based on environment.
    """
    api = get_application()
    
    return api

def get_application() -> FastAPI:
    """Get the FastAPI app instance, with settings."""
    settings = get_settings()
    _app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        # license_info={
        #     "name": "AGPL-3.0-only",
        #     "url": "https://raw.githubusercontent.com/hotosm/fmtm/main/LICENSE.md",
        # },
        debug=settings.DEBUG,
        lifespan=lifespan,
        root_path=settings.API_PREFIX,
        # Desactivamos las rutas por defecto para personalizarlas
        docs_url=None,
        redoc_url=None,
        openapi_url=None,        
        # NOTE REST APIs should not have trailing slashes
        redirect_slashes=False,
    )
    def custom_openapi():
        if _app.openapi_schema:
            return _app.openapi_schema
        openapi_schema = get_openapi(
            title=_app.title,
            version=_app.version,
            description=_app.description,
            routes=_app.routes,
        )
        openapi_schema["servers"] = [{"url": "/senfast/api"}]
        _app.openapi_schema = openapi_schema
        return _app.openapi_schema
    
    _app.openapi = custom_openapi

    # Set custom logger
    logger = setup_logging()
    _app.logger = logger
    # Configurar métricas de Prometheus
    setup_metrics(_app) 
       
    # Configuración CORS segura
    if settings.ENVIRONMENT == "development":
        # En desarrollo, usar configuración más permisiva
        allowed_origins = settings.EXTRA_CORS_ORIGINS if settings.EXTRA_CORS_ORIGINS else ["*"]
    else:
        # En producción, ser más restrictivo
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        # Si no hay configuración, usar un valor predeterminado seguro
        if not allowed_origins or not allowed_origins[0]:
            allowed_origins = ["https://example.com"]
    
    _app.add_middleware(
        CORSMiddleware,
        # allow_origins=settings.EXTRA_CORS_ORIGINS,
        allow_origins = allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )

    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    if os.path.exists(static_dir):
        _app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Endpoints personalizados para documentación OpenAPI
    # docs_router = APIRouter()
    

    @_app.get("/")
    async def root(request: Request):
        if hasattr(_app, 'logger') and _app.logger:
            _app.logger.info(f"Request ID: {request.state.request_id} - Acceso a endpoint raíz")
        return {
            "message": f"API de {_app.title} / {_app.version}",
            "docs": "/docs",
            "redoc": "/redoc", 
            "health_check": "/health"
            } 
    
    @_app.get('/favicon.ico', include_in_schema=False)
    async def favicon():
        from fastapi.responses import FileResponse
        favicon_path = os.path.join(static_dir, "favicon.ico")
        if os.path.exists(favicon_path):
            return FileResponse(favicon_path)
        else:
            raise HTTPException(status_code=404)  

    _app.middleware("http")(add_request_id)
    # _app.include_router(docs_router, prefix="/api")
    _app.include_router(health.router)
    _app.include_router(docs.router)
    _app.include_router(info.router)
    _app.include_router(metrics_route.router)
    # _app.include_router(data_taigua.router)
    # _app.include_router(data_sobreeixidors.router)
    _app.include_router(data_taigua.router)
    _app.include_router(data_sobreeixidors.router)    
    # _app.include_router(router)
    # for router in [health.router, metrics.router, docs.router, info.router, data_barris.router]:
    #     _app.include_router(router)

    return _app

app = get_api()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("senfast.api.app.main:app", host="localhost", port=8000, reload=True)