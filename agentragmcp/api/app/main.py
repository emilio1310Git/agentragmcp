
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import setup_logging, add_request_id, logger
from agentragmcp.core.exceptions import AgentRagMCPHTTPException
from agentragmcp.api.app.routers import health, chat, admin

# Inicializar servicios globales (se hace lazy loading en los routers)
settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    logger.info("Iniciando AgentRagMCP...")
    
    try:
        # Inicializar servicios MCP si están habilitados
        if settings.MCP_ENABLED:
            from agentragmcp.api.app.routers.chat import mcp_service
            await mcp_service.start()
            logger.info("Servicios MCP iniciados")
        
        logger.info("Aplicación iniciada correctamente")
        
    except Exception as e:
        logger.error(f"Error durante el startup: {e}")
        raise RuntimeError(f"No se pudo iniciar la aplicación: {e}") from e
    
    yield
    
    # Shutdown
    logger.info("Cerrando AgentRagMCP...")
    
    try:
        if settings.MCP_ENABLED:
            from agentragmcp.api.app.routers.chat import mcp_service
            await mcp_service.stop()
            logger.info("Servicios MCP detenidos")
            
        logger.info("Aplicación cerrada correctamente")
        
    except Exception as e:
        logger.error(f"Error durante el shutdown: {e}")

def create_application() -> FastAPI:
    """Crea y configura la aplicación FastAPI"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        root_path=settings.API_PREFIX,
        # Personalizar documentación
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        # No trailing slashes
        redirect_slashes=False,
    )
    
    # Configurar OpenAPI personalizado
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
            
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Personalizar esquema
        openapi_schema["info"]["x-logo"] = {
            "url": "/static/logo.png"
        }
        openapi_schema["servers"] = [
            {"url": f"{settings.API_PREFIX}", "description": "API Server"}
        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Configurar logging
    app_logger = setup_logging()
    app.logger = app_logger
    
    # Configurar CORS
    if settings.ENVIRONMENT == "development":
        # En desarrollo, usar configuración más permisiva
        allowed_origins = ["*"]  # Permitir todos los orígenes en desarrollo
        allow_credentials = False  # No credentials con "*"
    else:
        # En producción, ser más restrictivo
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        if not allowed_origins or not allowed_origins[0]:
            allowed_origins = ["https://example.com"]
        allow_credentials = True
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition", "X-Request-ID"],
    )
    
    # Middleware para request ID
    app.middleware("http")(add_request_id)
    
    # Montar archivos estáticos si existen
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Manejador global de excepciones
    @app.exception_handler(AgentRagMCPHTTPException)
    async def agentragmcp_exception_handler(request: Request, exc: AgentRagMCPHTTPException):
        """Manejador para excepciones específicas de AgentRagMCP"""
        request_id = getattr(request.state, "request_id", "unknown")
        
        # Log según el nivel configurado
        if exc.log_level == "error":
            logger.error(f"Request {request_id} - {exc.detail}")
        elif exc.log_level == "warning":
            logger.warning(f"Request {request_id} - {exc.detail}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": type(exc).__name__,
                "message": exc.detail,
                "request_id": request_id
            },
            headers=exc.headers
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Manejador para excepciones generales"""
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.error(f"Request {request_id} - Error no manejado: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "Error interno del servidor",
                "request_id": request_id
            }
        )
    
    # Endpoint raíz
    @app.get("/", include_in_schema=False)
    async def root(request: Request):
        """Endpoint de información básica"""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(f"Request {request_id} - Acceso a endpoint raíz")
        
        return {
            "service": app.title,
            "version": app.version,
            "status": "running",
            "description": "Asistente IA especializado en plantas con múltiples RAGs",
            "endpoints": {
                "health": "/health",
                "chat": "/chat",
                "docs": "/docs" if not settings.is_production else "disabled",
                "admin": "/admin" if not settings.is_production else "restricted"
            },
            "request_id": request_id
        }
    
    # Favicon
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Servir favicon"""
        favicon_path = os.path.join(static_dir, "favicon.ico") if os.path.exists(static_dir) else None
        if favicon_path and os.path.exists(favicon_path):
            from fastapi.responses import FileResponse
            return FileResponse(favicon_path)
        else:
            raise HTTPException(status_code=404, detail="Favicon not found")
    
    # Incluir routers
    app.include_router(health.router)
    app.include_router(chat.router)
    
    # Router de admin solo en desarrollo o con autenticación
    if not settings.is_production or os.getenv("ENABLE_ADMIN", "false").lower() == "true":
        app.include_router(admin.router)
    
    return app

# Crear la aplicación
app = create_application()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "agentragmcp.api.app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )