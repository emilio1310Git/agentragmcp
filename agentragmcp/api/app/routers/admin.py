from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger

router = APIRouter(prefix="/admin", tags=["Administration"])
security = HTTPBearer()

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """
    Verificación básica de token de administrador
    En producción, implementar verificación real con JWT o similar
    """
    settings = get_settings()
    
    # En desarrollo, permitir cualquier token que contenga "admin"
    if settings.ENVIRONMENT == "development":
        if "admin" in credentials.credentials.lower():
            return credentials
    
    # En producción, verificar token real
    # TODO: Implementar verificación JWT real
    if credentials.credentials == "admin_secret_token":
        return credentials
    
    raise HTTPException(
        status_code=401,
        detail="Token de administrador inválido",
        headers={"WWW-Authenticate": "Bearer"}
    )

@router.get("/info")
async def get_system_info(token: str = Depends(verify_admin_token)):
    """Información general del sistema"""
    try:
        from agentragmcp.api.app.routers.chat import rag_service, agent_service, mcp_service
        
        settings = get_settings()
        
        system_info = {
            "service": "agentragmcp",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "configuration": {
                "llm_model": settings.LLM_MODEL,
                "embedding_model": settings.EMBEDDING_MODEL,
                "vectorstore_type": settings.VECTORSTORE_TYPE,
                "rag_topics": settings.RAG_TOPICS,
                "mcp_enabled": settings.MCP_ENABLED,
                "default_agent": settings.DEFAULT_AGENT
            },
            "services": {
                "rag": {
                    "available_topics": rag_service.get_available_topics(),
                    "total_topics": len(rag_service.get_available_topics())
                },
                "agents": {
                    "available_agents": [agent["name"] for agent in agent_service.get_available_agents()],
                    "total_agents": len(agent_service.get_available_agents())
                }
            }
        }
        
        if settings.MCP_ENABLED:
            system_info["services"]["mcp"] = {
                "total_servers": len(settings.MCP_SERVERS),
                "available_tools": len(mcp_service.get_available_tools())
            }
        
        return system_info
        
    except Exception as e:
        logger.error(f"Error obteniendo información del sistema: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo información del sistema")

@router.get("/rag/topics")
async def list_rag_topics(token: str = Depends(verify_admin_token)):
    """Lista detallada de temáticas RAG disponibles"""
    try:
        from agentragmcp.api.app.routers.chat import rag_service
        
        settings = get_settings()
        topics_info = {}
        
        for topic in settings.RAG_TOPICS:
            vectorstore_path = settings.get_vectorstore_path(topic)
            is_available = topic in rag_service.get_available_topics()
            
            topics_info[topic] = {
                "available": is_available,
                "vectorstore_path": vectorstore_path,
                "status": "loaded" if is_available else "not_loaded"
            }
        
        return {
            "total_configured": len(settings.RAG_TOPICS),
            "total_available": len(rag_service.get_available_topics()),
            "topics": topics_info
        }
        
    except Exception as e:
        logger.error(f"Error listando temáticas RAG: {e}")
        raise HTTPException(status_code=500, detail="Error listando temáticas RAG")

@router.get("/agents/details")
async def get_agents_details(token: str = Depends(verify_admin_token)):
    """Información detallada de todos los agentes"""
    try:
        from agentragmcp.api.app.routers.chat import agent_service
        
        agents_info = agent_service.get_available_agents()
        
        # Agregar información adicional de cada agente
        detailed_info = {}
        for agent_info in agents_info:
            agent_name = agent_info["name"]
            agent = agent_service.agents.get(agent_name)
            
            if agent:
                detailed_info[agent_name] = {
                    **agent_info,
                    "class_name": type(agent).__name__,
                    "can_handle_example": "Test de funcionalidad del agente"
                }
        
        return {
            "total_agents": len(detailed_info),
            "agents": detailed_info,
            "selector_info": {
                "llm_selection_enabled": agent_service.selector.use_llm_selection,
                "default_agent": get_settings().DEFAULT_AGENT
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo detalles de agentes: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo detalles de agentes")

@router.post("/agents/test/{agent_name}")
async def test_agent_selection(
    agent_name: str,
    test_question: str,
    token: str = Depends(verify_admin_token)
):
    """Prueba la capacidad de un agente específico para manejar una pregunta"""
    try:
        from agentragmcp.api.app.routers.chat import agent_service
        
        if agent_name not in agent_service.agents:
            raise HTTPException(status_code=404, detail=f"Agente '{agent_name}' no encontrado")
        
        agent = agent_service.agents[agent_name]
        confidence = agent.can_handle(test_question)
        
        return {
            "agent": agent_name,
            "question": test_question,
            "confidence": confidence,
            "can_handle": confidence > 0.3,  # Umbral arbitrario
            "agent_info": {
                "description": agent.description,
                "topics": agent.topics
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error probando agente {agent_name}: {e}")
        raise HTTPException(status_code=500, detail="Error probando agente")

@router.get("/sessions")
async def list_active_sessions(token: str = Depends(verify_admin_token)):
    """Lista las sesiones de chat activas"""
    try:
        from agentragmcp.api.app.routers.chat import rag_service
        
        active_sessions = {}
        for session_id in rag_service.chat_histories.keys():
            session_info = rag_service.get_session_summary(session_id)
            active_sessions[session_id] = session_info
        
        return {
            "total_sessions": len(active_sessions),
            "sessions": active_sessions
        }
        
    except Exception as e:
        logger.error(f"Error listando sesiones activas: {e}")
        raise HTTPException(status_code=500, detail="Error listando sesiones activas")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    token: str = Depends(verify_admin_token)
):
    """Elimina una sesión específica"""
    try:
        from agentragmcp.api.app.routers.chat import rag_service
        
        if session_id not in rag_service.chat_histories:
            raise HTTPException(status_code=404, detail=f"Sesión '{session_id}' no encontrada")
        
        rag_service.clear_session_history(session_id)
        
        return {
            "message": f"Sesión '{session_id}' eliminada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando sesión {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Error eliminando sesión")

@router.delete("/sessions")
async def clear_all_sessions(token: str = Depends(verify_admin_token)):
    """Elimina todas las sesiones activas"""
    try:
        from agentragmcp.api.app.routers.chat import rag_service
        
        session_count = len(rag_service.chat_histories)
        rag_service.chat_histories.clear()
        
        return {
            "message": f"{session_count} sesiones eliminadas exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error eliminando todas las sesiones: {e}")
        raise HTTPException(status_code=500, detail="Error eliminando sesiones")

# Endpoints MCP admin (si está habilitado)
@router.get("/mcp/servers")
async def list_mcp_servers(token: str = Depends(verify_admin_token)):
    """Lista los servidores MCP configurados"""
    settings = get_settings()
    
    if not settings.MCP_ENABLED:
        return {
            "enabled": False,
            "message": "Servicio MCP no habilitado"
        }
    
    try:
        from agentragmcp.api.app.routers.chat import mcp_service
        
        server_details = {}
        for server_name, client in mcp_service.clients.items():
            server_details[server_name] = {
                "url": client.server_url,
                "connected": client.is_connected,
                "available_tools": len(client.available_tools),
                "tools": list(client.available_tools.keys())
            }
        
        return {
            "enabled": True,
            "total_servers": len(server_details),
            "servers": server_details
        }
        
    except Exception as e:
        logger.error(f"Error listando servidores MCP: {e}")
        raise HTTPException(status_code=500, detail="Error listando servidores MCP")

@router.post("/mcp/reconnect/{server_name}")
async def reconnect_mcp_server(
    server_name: str,
    token: str = Depends(verify_admin_token)
):
    """Reconecta a un servidor MCP específico"""
    settings = get_settings()
    
    if not settings.MCP_ENABLED:
        raise HTTPException(status_code=400, detail="Servicio MCP no habilitado")
    
    try:
        from agentragmcp.api.app.routers.chat import mcp_service
        
        if server_name not in mcp_service.clients:
            raise HTTPException(status_code=404, detail=f"Servidor MCP '{server_name}' no encontrado")
        
        client = mcp_service.clients[server_name]
        
        # Desconectar si está conectado
        if client.is_connected:
            await client.disconnect()
        
        # Reconectar
        success = await client.connect()
        
        return {
            "server": server_name,
            "reconnection_successful": success,
            "status": "connected" if success else "failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reconectando servidor MCP {server_name}: {e}")
        raise HTTPException(status_code=500, detail="Error reconectando servidor MCP")

@router.get("/config")
async def get_current_config(token: str = Depends(verify_admin_token)):
    """Obtiene la configuración actual (sin información sensible)"""
    settings = get_settings()
    
    # Configuración segura para mostrar (sin tokens, passwords, etc.)
    safe_config = {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL
        },
        "api": {
            "host": settings.API_HOST,
            "port": settings.API_PORT,
            "prefix": settings.API_PREFIX
        },
        "llm": {
            "model": settings.LLM_MODEL,
            "base_url": settings.LLM_BASE_URL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "temperature": settings.LLM_TEMPERATURE
        },
        "rag": {
            "vectorstore_type": settings.VECTORSTORE_TYPE,
            "vectorstore_base_path": settings.VECTORSTORE_BASE_PATH,
            "retrieval_k": settings.RETRIEVAL_K,
            "retrieval_type": settings.RETRIEVAL_TYPE,
            "topics": settings.RAG_TOPICS
        },
        "agents": {
            "default_agent": settings.DEFAULT_AGENT
        },
        "mcp": {
            "enabled": settings.MCP_ENABLED,
            "servers_count": len(settings.MCP_SERVERS)
        },
        "species": {
            "specific_species_count": len(settings.SPECIFIC_SPECIES),
            "pathology_species_count": len(settings.PATHOLOGY_SPECIES)
        }
    }
    
    return safe_config