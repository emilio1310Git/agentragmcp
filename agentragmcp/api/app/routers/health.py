import time
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger

router = APIRouter(prefix="/health", tags=["Health"])

# Tiempo de inicio para métricas
start_time = time.time()

@router.get("/")
async def healthcheck():
    """Health check básico del servicio"""
    return {
        "status": "healthy",
        "service": "agentragmcp",
        "version": get_settings().APP_VERSION,
        "uptime": time.time() - start_time
    }

@router.get("/detailed")
async def detailed_health_check():
    """Health check detallado de todos los componentes"""
    try:
        # Importar servicios dinámicamente para evitar dependencias circulares
        from agentragmcp.api.app.routers.chat import dynamic_system, mcp_service
        
        settings = get_settings()
        uptime = time.time() - start_time
        
        system_health = dynamic_system.health_check()
        
        # Verificar MCP Service (si está habilitado)
        mcp_health = None
        if settings.MCP_ENABLED:
            mcp_health = mcp_service.health_check()
        
        # Estado general
        components_status = [system_health.get("status")]
        if mcp_health:
            components_status.append(mcp_health.get("status"))
        
        overall_status = "healthy"
        if "error" in components_status or "unhealthy" in components_status:
            overall_status = "unhealthy"
        elif "degraded" in components_status:
            overall_status = "degraded"
        
        health_data = {
            "status": overall_status,
            "service": "agentragmcp",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "uptime": uptime,
            "components": {
                "system_health": system_health
            }
        }
        
        if mcp_health:
            health_data["components"]["mcp_service"] = mcp_health
        
        # Retornar código de estado apropiado
        status_code = 200
        if overall_status == "unhealthy":
            status_code = 503
        elif overall_status == "degraded":
            status_code = 200  # Degraded pero funcional
        
        return JSONResponse(content=health_data, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Error en health check detallado: {e}")
        
        error_response = {
            "status": "unhealthy",
            "service": "agentragmcp",
            "version": get_settings().APP_VERSION,
            "error": str(e),
            "uptime": time.time() - start_time
        }
        
        return JSONResponse(content=error_response, status_code=503)

@router.get("/components/rag")
async def rag_health():
    """Health check específico del servicio RAG"""
    try:
        from agentragmcp.api.app.routers.chat import dynamic_system
        return dynamic_system.health_check()
    except Exception as e:
        logger.error(f"Error en health check RAG: {e}")
        raise HTTPException(status_code=503, detail=f"Error en servicio RAG: {str(e)}")

@router.get("/components/agents")
async def agents_health():
    """Health check específico del servicio de agentes"""
    try:
        from agentragmcp.api.app.routers.chat import dynamic_system
        return dynamic_system.health_check()
    except Exception as e:
        logger.error(f"Error en health check agentes: {e}")
        raise HTTPException(status_code=503, detail=f"Error en servicio de agentes: {str(e)}")

@router.get("/components/mcp")
async def mcp_health():
    """Health check específico del servicio MCP"""
    settings = get_settings()
    
    if not settings.MCP_ENABLED:
        return {
            "status": "disabled",
            "message": "Servicio MCP no habilitado"
        }
    
    try:
        from agentragmcp.api.app.routers.chat import mcp_service
        return mcp_service.health_check()
    except Exception as e:
        logger.error(f"Error en health check MCP: {e}")
        raise HTTPException(status_code=503, detail=f"Error en servicio MCP: {str(e)}")

@router.get("/ready")
async def readiness_check():
    """
    Readiness check para Kubernetes
    Verifica que todos los servicios críticos estén listos
    """
    try:
        from agentragmcp.api.app.routers.chat import rag_service, agent_service
        
        # Verificar que RAG service tenga al menos un RAG cargado
        available_topics = rag_service.get_available_topics()
        if not available_topics:
            return JSONResponse(
                content={"ready": False, "reason": "No hay RAGs disponibles"},
                status_code=503
            )
        
        # Verificar que agent service tenga agentes cargados
        available_agents = agent_service.get_available_agents()
        if not available_agents:
            return JSONResponse(
                content={"ready": False, "reason": "No hay agentes disponibles"}, 
                status_code=503
            )
        
        return {
            "ready": True,
            "topics": len(available_topics),
            "agents": len(available_agents),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error en readiness check: {e}")
        return JSONResponse(
            content={"ready": False, "reason": str(e)},
            status_code=503
        )

@router.get("/live")
async def liveness_check():
    """
    Liveness check para Kubernetes
    Verifica que la aplicación esté viva y respondiendo
    """
    return {
        "alive": True,
        "service": "agentragmcp", 
        "uptime": time.time() - start_time,
        "timestamp": time.time()
    }
