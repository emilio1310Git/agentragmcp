

from fastapi import HTTPException, status
from typing import Optional, Any, Dict

class AgentRagMCPException(Exception):
    """Excepción base para AgentRagMCP"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class AgentRagMCPHTTPException(HTTPException):
    """Excepción HTTP base para AgentRagMCP con logging automático"""
    
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        headers: Optional[Dict[str, Any]] = None,
        log_level: str = "error"
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.log_level = log_level

# Excepciones de configuración
class ConfigurationError(AgentRagMCPException):
    """Error en la configuración de la aplicación"""
    pass

class InvalidTopicError(AgentRagMCPHTTPException):
    """Error cuando se especifica una temática no válida"""
    
    def __init__(self, topic: str, available_topics: list):
        detail = f"Temática '{topic}' no válida. Disponibles: {', '.join(available_topics)}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

# Excepciones de RAG y vectorstores
class VectorStoreError(AgentRagMCPHTTPException):
    """Error en operaciones con vectorstore"""
    
    def __init__(self, detail: str = "Error en vectorstore"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

class VectorStoreNotFoundError(VectorStoreError):
    """Error cuando no se encuentra el vectorstore"""
    
    def __init__(self, topic: str, path: str):
        detail = f"Vectorstore para temática '{topic}' no encontrado en: {path}"
        super().__init__(detail=detail)

class RetrievalError(AgentRagMCPHTTPException):
    """Error durante la recuperación de documentos"""
    
    def __init__(self, detail: str = "Error en recuperación de documentos"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

# Excepciones de LLM
class LLMError(AgentRagMCPHTTPException):
    """Error en operaciones con LLM"""
    
    def __init__(self, detail: str = "Error en modelo de lenguaje"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

class LLMConnectionError(LLMError):
    """Error de conexión con el LLM"""
    
    def __init__(self, base_url: str):
        detail = f"No se puede conectar con el LLM en: {base_url}"
        super().__init__(detail=detail)

class LLMTimeoutError(LLMError):
    """Error de timeout en LLM"""
    
    def __init__(self, timeout_seconds: int):
        detail = f"Timeout del LLM después de {timeout_seconds} segundos"
        super().__init__(detail=detail)

# Excepciones de agentes
class AgentError(AgentRagMCPHTTPException):
    """Error en operaciones con agentes"""
    
    def __init__(self, detail: str = "Error en agente"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class AgentNotFoundError(AgentError):
    """Error cuando no se encuentra el agente"""
    
    def __init__(self, agent_type: str):
        detail = f"Agente '{agent_type}' no encontrado"
        super().__init__(detail=detail)

class AgentSelectionError(AgentError):
    """Error en la selección automática de agente"""
    
    def __init__(self, question: str):
        detail = f"No se pudo determinar el agente apropiado para: {question[:100]}..."
        super().__init__(detail=detail)

# Excepciones de chat
class ChatSessionError(AgentRagMCPHTTPException):
    """Error en gestión de sesiones de chat"""
    
    def __init__(self, detail: str = "Error en sesión de chat"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class InvalidSessionError(ChatSessionError):
    """Error cuando la sesión no es válida"""
    
    def __init__(self, session_id: str):
        detail = f"Sesión inválida: {session_id}"
        super().__init__(detail=detail)

class ChatHistoryError(AgentRagMCPHTTPException):
    """Error en gestión del historial de chat"""
    
    def __init__(self, detail: str = "Error en historial de chat"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

# Excepciones MCP
class MCPError(AgentRagMCPHTTPException):
    """Error en operaciones MCP"""
    
    def __init__(self, detail: str = "Error en protocolo MCP"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )

class MCPServerNotFoundError(MCPError):
    """Error cuando no se encuentra el servidor MCP"""
    
    def __init__(self, server_name: str):
        detail = f"Servidor MCP '{server_name}' no encontrado"
        super().__init__(detail=detail)

class MCPConnectionError(MCPError):
    """Error de conexión con servidor MCP"""
    
    def __init__(self, server_name: str, server_url: str):
        detail = f"No se puede conectar con servidor MCP '{server_name}' en: {server_url}"
        super().__init__(detail=detail)

# Excepciones de validación
class ValidationError(AgentRagMCPHTTPException):
    """Error de validación de datos"""
    
    def __init__(self, detail: str = "Error de validación"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )

class EmptyQuestionError(ValidationError):
    """Error cuando la pregunta está vacía"""
    
    def __init__(self):
        detail = "La pregunta no puede estar vacía"
        super().__init__(detail=detail)

class QuestionTooLongError(ValidationError):
    """Error cuando la pregunta es demasiado larga"""
    
    def __init__(self, max_length: int, actual_length: int):
        detail = f"Pregunta demasiado larga. Máximo: {max_length}, actual: {actual_length}"
        super().__init__(detail=detail)

# Utilidades para manejo de excepciones
def handle_langchain_error(e: Exception) -> AgentRagMCPHTTPException:
    """Convierte errores de LangChain a excepciones de AgentRagMCP"""
    error_message = str(e)
    
    # Errores de conexión
    if "connection" in error_message.lower() or "connect" in error_message.lower():
        return LLMConnectionError("localhost:11434")  # URL por defecto
    
    # Errores de timeout
    if "timeout" in error_message.lower():
        return LLMTimeoutError(30)  # timeout por defecto
    
    # Errores de vectorstore
    if "chroma" in error_message.lower() or "vector" in error_message.lower():
        return VectorStoreError(f"Error en vectorstore: {error_message}")
    
    # Error genérico de LLM
    return LLMError(f"Error en LLM: {error_message}")

def handle_file_not_found_error(e: FileNotFoundError, context: str = "") -> AgentRagMCPHTTPException:
    """Maneja errores de archivo no encontrado según el contexto"""
    file_path = str(e)
    
    if "vectorstore" in file_path.lower() or "chroma" in file_path.lower():
        # Extraer topic del path si es posible
        parts = file_path.split("/")
        topic = "unknown"
        if "vectorstores" in parts:
            idx = parts.index("vectorstores")
            if idx + 1 < len(parts):
                topic = parts[idx + 1]
        return VectorStoreNotFoundError(topic, file_path)
    
    # Error genérico de configuración
    return ConfigurationError(f"Archivo no encontrado: {file_path}")