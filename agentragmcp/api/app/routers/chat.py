import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger, get_logger_with_context
from agentragmcp.api.app.models.chat_models import (
    ChatRequest, 
    ChatResponse, 
    RAGQueryRequest, 
    RAGQueryResponse,
    AgentSelectionRequest,
    AgentSelectionResponse
)
from agentragmcp.api.app.services.rag_service import RAGService
from agentragmcp.api.app.services.agent_service import AgentService
from agentragmcp.api.app.services.mcp_service import MCPService
from agentragmcp.core.exceptions import (
    EmptyQuestionError,
    QuestionTooLongError,
    InvalidTopicError,
    AgentNotFoundError,
    ValidationError,
    AgentRagMCPHTTPException
)

# Inicialización de servicios globales
settings = get_settings()
rag_service = RAGService()
agent_service = AgentService(rag_service)
mcp_service = MCPService()

router = APIRouter(prefix="/chat", tags=["Chat"])

async def get_request_context(request: Request):
    """Dependencia para obtener contexto de la request"""
    return {
        "request_id": getattr(request.state, "request_id", None),
        "client_ip": request.client.host if request.client else "unknown"
    }

@router.post(
    "/",
    response_model=ChatResponse,
    summary="Chat principal",
    description="""
    Endpoint principal para interacciones de chat. 
    Selecciona automáticamente el agente más apropiado o usa el especificado.
    """
)
async def chat(
    chat_request: ChatRequest,
    request_context: dict = Depends(get_request_context)
):
    """Endpoint principal de chat con selección automática de agentes"""
    start_time = time.time()
    
    # Validaciones básicas
    if not chat_request.question.strip():
        raise EmptyQuestionError()
    
    if len(chat_request.question) > 2000:
        raise QuestionTooLongError(2000, len(chat_request.question))
    
    # ASEGURAR que session_id nunca sea None
    if not chat_request.session_id:
        from uuid import uuid4
        chat_request.session_id = str(uuid4())
    
    # Validar topic si se especifica
    if chat_request.topic and chat_request.topic not in rag_service.get_available_topics():
        raise InvalidTopicError(chat_request.topic, rag_service.get_available_topics())
    
    # Validar agent_type si se especifica
    available_agents = [agent["name"] for agent in agent_service.get_available_agents()]
    if chat_request.agent_type and chat_request.agent_type not in available_agents:
        raise AgentNotFoundError(chat_request.agent_type)
    
    # Configurar logging contextual
    context_logger = get_logger_with_context(
        request_id=request_context.get("request_id"),
        chat_session_id=chat_request.session_id
    )
    
    try:
        context_logger.info(
            f"Solicitud de chat recibida - Pregunta: {chat_request.question[:100]}..."
        )
        
        # Procesar pregunta con el servicio de agentes
        answer, metadata = await agent_service.process_question(
            question=chat_request.question,
            session_id=chat_request.session_id,
            agent_type=chat_request.agent_type,
            include_sources=chat_request.include_sources,
            context=chat_request.context
        )
        
        response_time = time.time() - start_time
        
        # Construir respuesta - ASEGURAR que todos los campos requeridos están presentes
        chat_response = ChatResponse(
            answer=answer,
            session_id=chat_request.session_id,  # YA validado que no es None
            agent_type=metadata.get("agent_type", "unknown"),
            topic=metadata.get("topic", "unknown"),
            confidence=metadata.get("agent_selection_confidence"),
            sources=metadata.get("sources"),
            response_time=response_time,
            metadata=metadata
        )
        
        context_logger.info(
            f"Chat completado exitosamente - Agente: {chat_response.agent_type}, "
            f"Tiempo: {response_time:.2f}s"
        )
        
        return chat_response
        
    except AgentRagMCPHTTPException:
        # Re-lanzar excepciones HTTP específicas
        raise
    except Exception as e:
        response_time = time.time() - start_time
        context_logger.error(f"Error inesperado en chat: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor procesando la consulta"
        )

@router.post(
    "/rag/query",
    response_model=RAGQueryResponse,
    summary="Consulta directa a RAG",
    description="""
    Endpoint para consultas directas a un RAG específico sin selección de agentes.
    Útil para testing y casos específicos donde se conoce la temática exacta.
    """
)
async def rag_query(
    rag_request: RAGQueryRequest,
    request_context: dict = Depends(get_request_context)
):
    """Consulta directa a un RAG específico"""
    start_time = time.time()
    
    # Validar topic
    if rag_request.topic not in rag_service.get_available_topics():
        raise InvalidTopicError(rag_request.topic, rag_service.get_available_topics())
    
    context_logger = get_logger_with_context(
        request_id=request_context.get("request_id"),
        topic=rag_request.topic
    )
    
    try:
        context_logger.info(f"Consulta RAG directa - Topic: {rag_request.topic}")
        
        # Generar session_id temporal para la consulta
        temp_session_id = f"rag_query_{int(time.time())}"
        
        answer, metadata = rag_service.query(
            question=rag_request.query,
            topic=rag_request.topic,
            session_id=temp_session_id,
            include_sources=True
        )
        
        retrieval_time = time.time() - start_time
        
        # Construir respuesta RAG
        response = RAGQueryResponse(
            documents=metadata.get("sources", []),
            query=rag_request.query,
            topic=rag_request.topic,
            total_results=metadata.get("num_sources", 0),
            retrieval_time=retrieval_time
        )
        
        context_logger.info(f"Consulta RAG completada - Tiempo: {retrieval_time:.2f}s")
        
        return response
        
    except Exception as e:
        context_logger.error(f"Error en consulta RAG: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en consulta RAG: {str(e)}"
        )

@router.post(
    "/agent/select",
    response_model=AgentSelectionResponse,
    summary="Selección de agente",
    description="""
    Endpoint para probar la selección automática de agentes sin ejecutar la consulta.
    Útil para debugging y análisis del sistema de selección.
    """
)
async def select_agent(
    selection_request: AgentSelectionRequest,
    request_context: dict = Depends(get_request_context)
):
    """Prueba la selección automática de agentes"""
    
    context_logger = get_logger_with_context(
        request_id=request_context.get("request_id")
    )
    
    try:
        context_logger.info("Solicitud de selección de agente")
        
        available_agents = list(agent_service.agents.values())
        selected_agent, confidence = agent_service.selector.select_agent(
            question=selection_request.question,
            available_agents=available_agents,
            context=selection_request.context
        )
        
        # Obtener agentes alternativos ordenados por confianza
        all_scores = []
        for agent in available_agents:
            score = agent.can_handle(selection_request.question, selection_request.context)
            all_scores.append((agent.name, score))
        
        all_scores.sort(key=lambda x: x[1], reverse=True)
        alternative_agents = [name for name, score in all_scores[1:4]]  # Top 3 alternativos
        
        response = AgentSelectionResponse(
            selected_agent=selected_agent.name,
            confidence=confidence,
            reasoning=f"Seleccionado basado en análisis de palabras clave y especialización",
            alternative_agents=alternative_agents
        )
        
        context_logger.info(f"Agente seleccionado: {selected_agent.name} (confianza: {confidence:.3f})")
        
        return response
        
    except Exception as e:
        context_logger.error(f"Error en selección de agente: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en selección de agente: {str(e)}"
        )

@router.get(
    "/topics",
    response_model=List[str],
    summary="Obtener temáticas disponibles",
    description="Devuelve la lista de temáticas RAG disponibles en el sistema"
)
async def get_topics():
    """Obtiene las temáticas RAG disponibles"""
    return rag_service.get_available_topics()

@router.get(
    "/agents",
    summary="Obtener agentes disponibles",
    description="Devuelve información de todos los agentes disponibles"
)
async def get_agents():
    """Obtiene información de los agentes disponibles"""
    return agent_service.get_available_agents()

@router.delete(
    "/session/{session_id}",
    summary="Limpiar historial de sesión",
    description="Elimina el historial de chat de una sesión específica"
)
async def clear_session(
    session_id: str,
    request_context: dict = Depends(get_request_context)
):
    """Limpia el historial de una sesión específica"""
    context_logger = get_logger_with_context(
        request_id=request_context.get("request_id"),
        chat_session_id=session_id
    )
    
    try:
        rag_service.clear_session_history(session_id)
        context_logger.info(f"Historial de sesión eliminado: {session_id}")
        
        return {"message": f"Historial de sesión {session_id} eliminado exitosamente"}
        
    except Exception as e:
        context_logger.error(f"Error eliminando historial de sesión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error eliminando historial de sesión"
        )

@router.get(
    "/session/{session_id}",
    summary="Obtener información de sesión",
    description="Devuelve información y resumen de una sesión específica"
)
async def get_session_info(session_id: str):
    """Obtiene información de una sesión específica"""
    try:
        session_info = rag_service.get_session_summary(session_id)
        return session_info
        
    except Exception as e:
        logger.error(f"Error obteniendo información de sesión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo información de sesión"
        )

# Endpoints MCP (si está habilitado)
if settings.MCP_ENABLED:
    
    @router.get(
        "/mcp/tools",
        summary="Obtener herramientas MCP disponibles",
        description="Devuelve las herramientas disponibles de todos los servidores MCP"
    )
    async def get_mcp_tools():
        """Obtiene las herramientas MCP disponibles"""
        try:
            tools = mcp_service.get_available_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "server": tool.server,
                    "parameters": tool.parameters
                }
                for tool in tools
            ]
        except Exception as e:
            logger.error(f"Error obteniendo herramientas MCP: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Error obteniendo herramientas MCP"
            )
    
    @router.post(
        "/mcp/call/{tool_name}",
        summary="Ejecutar herramienta MCP",
        description="Ejecuta una herramienta específica de un servidor MCP"
    )
    async def call_mcp_tool(
        tool_name: str,
        tool_args: dict,
        server_name: Optional[str] = None
    ):
        """Ejecuta una herramienta MCP"""
        try:
            result = await mcp_service.call_tool(
                tool_name=tool_name,
                server_name=server_name,
                **tool_args
            )
            return result
        except Exception as e:
            logger.error(f"Error ejecutando herramienta MCP {tool_name}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error ejecutando herramienta MCP: {str(e)}"
            )