
import os
import logging
import uuid
from datetime import datetime
from logging.handlers import RotatingFileHandler
from fastapi import Request
from typing import Optional

from agentragmcp.core.config import get_settings

global_settings = get_settings()

class RequestIDFilter(logging.Filter):
    """Filtro para inyectar un ID de request único en cada registro de log."""
    
    def filter(self, record):
        # Asegurar que TODOS los campos requeridos están presentes
        record.request_id = getattr(record, 'request_id', 'NO_REQUEST_ID')
        record.agent_type = getattr(record, 'agent_type', 'UNKNOWN')
        record.topic = getattr(record, 'topic', 'UNKNOWN')
        record.chat_session_id = getattr(record, 'chat_session_id', 'NO_SESSION')
        
        # Crear session corto para el formatter
        if hasattr(record, 'chat_session_id') and record.chat_session_id != 'NO_SESSION':
            record.session = record.chat_session_id[:8] if len(record.chat_session_id) > 8 else record.chat_session_id
        else:
            record.session = 'NO_SESSION'
            
        return True

class AgentRagMCPFormatter(logging.Formatter):
    """Formatter personalizado para AgentRagMCP con información contextual"""
    
    def format(self, record):
        # Agregar información contextual al record
        if hasattr(record, 'chat_session_id'):
            record.session = record.chat_session_id[:8] if record.chat_session_id else 'NO_SESSION'
        else:
            record.session = 'NO_SESSION'
            
        return super().format(record)

async def add_request_id(request: Request, call_next):
    """Middleware para añadir un identificador único a cada request"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log de inicio de request
    logger.info(
        f"Request started - {request.method} {request.url.path}",
        extra={
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'client_ip': request.client.host if request.client else 'unknown'
        }
    )
    
    try:
        response = await call_next(request)
        
        # Log de finalización exitosa
        logger.info(
            f"Request completed - Status: {response.status_code}",
            extra={
                'request_id': request_id,
                'status_code': response.status_code,
                'response_time': 'calculated_in_middleware'
            }
        )
        
    except Exception as e:
        # Log de error en request
        logger.error(
            f"Request failed - {str(e)}",
            extra={
                'request_id': request_id,
                'error': str(e),
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        raise
    
    response.headers['X-Request-ID'] = request_id
    return response

def setup_logging() -> logging.Logger:
    """Configura el logging para AgentRagMCP."""
    
    # Evitar configuración múltiple
    if hasattr(setup_logging, 'executed'):
        return logging.getLogger(global_settings.APP_NAME)
    setup_logging.executed = True
    
    # Crear directorio de logs
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.join(base_dir, "logs", global_settings.APP_NAME)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar logger principal
    logger = logging.getLogger(global_settings.APP_NAME)
    
    # Limpiar handlers existentes
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Establecer nivel de logging
    level = getattr(global_settings, "LOG_LEVEL", "INFO").upper()
    logger.setLevel(level)
    
    # Añadir filtros
    logger.addFilter(RequestIDFilter())
    
    # Formato estructurado para análisis
    formatter = AgentRagMCPFormatter(
        '%(asctime)s|%(levelname)s|%(name)s|%(module)s|%(funcName)s|'
        'REQUEST:%(request_id)s|SESSION:%(session)s|AGENT:%(agent_type)s|'
        'TOPIC:%(topic)s|%(message)s'
    )
    
    # Handler para archivo (rotativo)
    log_filename = os.path.join(
        log_dir, 
        f"{global_settings.APP_NAME}_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = RotatingFileHandler(
        log_filename, 
        maxBytes=1024*1024*10,  # 10MB
        backupCount=7,  # Una semana de logs
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola en desarrollo
    if not global_settings.is_production:
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s|%(levelname)s|%(name)s|%(funcName)s|%(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

def get_logger_with_context(
    request_id: Optional[str] = None,
    chat_session_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    topic: Optional[str] = None
) -> logging.LoggerAdapter:
    """
    Obtiene un logger con contexto específico para logging estructurado
    
    Args:
        request_id: ID de la request HTTP
        chat_session_id: ID de la sesión de chat
        agent_type: Tipo de agente utilizado
        topic: Temática o RAG utilizado
    
    Returns:
        LoggerAdapter con contexto configurado
    """
    logger = logging.getLogger(global_settings.APP_NAME)
    
    extra_context = {
        'request_id': request_id or 'NO_REQUEST',
        'chat_session_id': chat_session_id or 'NO_SESSION',
        'agent_type': agent_type or 'UNKNOWN',
        'topic': topic or 'UNKNOWN'
    }
    
    return logging.LoggerAdapter(logger, extra_context)

class ChatMetrics:
    """Clase para métricas específicas de chat"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{global_settings.APP_NAME}.metrics")
    
    def log_chat_interaction(
        self,
        session_id: str,
        question: str,
        agent_type: str,
        topic: str,
        response_time: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log de interacción de chat para métricas"""
        self.logger.info(
            "Chat interaction",
            extra={
                'event_type': 'chat_interaction',
                'chat_session_id': session_id,
                'agent_type': agent_type,
                'topic': topic,
                'question_length': len(question),
                'response_time': response_time,
                'success': success,
                'error': error
            }
        )
    
    def log_agent_selection(
        self,
        session_id: str,
        question: str,
        selected_agent: str,
        confidence: float
    ):
        """Log de selección de agente"""
        self.logger.info(
            "Agent selection",
            extra={
                'event_type': 'agent_selection',
                'chat_session_id': session_id,
                'selected_agent': selected_agent,
                'confidence': confidence,
                'question_preview': question[:100]
            }
        )
    
    def log_rag_retrieval(
        self,
        session_id: str,
        topic: str,
        query: str,
        num_results: int,
        retrieval_time: float
    ):
        """Log de recuperación RAG"""
        self.logger.info(
            "RAG retrieval",
            extra={
                'event_type': 'rag_retrieval',
                'chat_session_id': session_id,
                'topic': topic,
                'query_length': len(query),
                'num_results': num_results,
                'retrieval_time': retrieval_time
            }
        )

# Inicializar logging y métricas globales
logger = setup_logging()
chat_metrics = ChatMetrics()

logger.info("AgentRagMCP logging system initialized")