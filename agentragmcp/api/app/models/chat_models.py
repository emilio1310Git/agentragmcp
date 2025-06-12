from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from uuid import uuid4
from datetime import datetime

class ChatRequest(BaseModel):
    """Modelo para solicitudes de chat"""
    
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=2000,
        description="Pregunta del usuario"
    )
    session_id: Optional[str] = Field(
        None,
        description="ID de sesión. Si es None o 'nuevo', se crea una nueva sesión"
    )
    agent_type: Optional[str] = Field(
        None,
        description="Tipo de agente específico a usar (opcional, se auto-selecciona si no se especifica)"
    )
    topic: Optional[str] = Field(
        None,
        description="Temática específica del RAG a usar (opcional)"
    )
    include_sources: bool = Field(
        default=False,
        description="Incluir fuentes de los documentos en la respuesta"
    )
    language: str = Field(
        default="es",
        description="Idioma de respuesta (es, en, ca, etc.)"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contexto adicional para la consulta"
    )

    @validator('session_id', pre=True)
    def validate_session_id(cls, v):
        """Valida y normaliza el session_id"""
        if v is None or v == "" or v.lower() == "nuevo":
            return str(uuid4())
        return v

    @validator('question')
    def validate_question(cls, v):
        """Valida la pregunta"""
        v = v.strip()
        if not v:
            raise ValueError("La pregunta no puede estar vacía")
        return v

class ChatResponse(BaseModel):
    """Modelo para respuestas de chat"""
    
    answer: str = Field(..., description="Respuesta del asistente")
    session_id: str = Field(..., description="ID de la sesión")
    agent_type: str = Field(..., description="Tipo de agente que generó la respuesta")
    topic: str = Field(..., description="Temática del RAG utilizado")
    confidence: Optional[float] = Field(
        None, 
        ge=0.0, 
        le=1.0,
        description="Confianza en la selección del agente (0-1)"
    )
    sources: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Fuentes de información utilizadas"
    )
    response_time: Optional[float] = Field(
        None,
        description="Tiempo de respuesta en segundos"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de la respuesta"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadatos adicionales de la respuesta"
    )

class ChatHistory(BaseModel):
    """Modelo para historial de chat"""
    
    session_id: str = Field(..., description="ID de la sesión")
    messages: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Lista de mensajes (role: user/assistant, content: texto)"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de creación de la sesión"
    )
    last_activity: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de última actividad"
    )

class AgentSelectionRequest(BaseModel):
    """Modelo para solicitudes de selección de agente"""
    
    question: str = Field(..., description="Pregunta para determinar el agente")
    available_agents: List[str] = Field(
        default_factory=list,
        description="Lista de agentes disponibles"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contexto adicional para la selección"
    )

class AgentSelectionResponse(BaseModel):
    """Modelo para respuestas de selección de agente"""
    
    selected_agent: str = Field(..., description="Agente seleccionado")
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confianza en la selección (0-1)"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Explicación del proceso de selección"
    )
    alternative_agents: Optional[List[str]] = Field(
        None,
        description="Agentes alternativos considerados"
    )

class RAGQueryRequest(BaseModel):
    """Modelo para consultas específicas a RAG"""
    
    query: str = Field(..., description="Consulta para el RAG")
    topic: str = Field(..., description="Temática del RAG")
    k: Optional[int] = Field(
        default=5,
        ge=1,
        le=20,
        description="Número de documentos a recuperar"
    )
    score_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Umbral mínimo de score de similitud"
    )

class RAGQueryResponse(BaseModel):
    """Modelo para respuestas de consultas RAG"""
    
    documents: List[Dict[str, Any]] = Field(..., description="Documentos recuperados")
    query: str = Field(..., description="Consulta original")
    topic: str = Field(..., description="Temática utilizada")
    total_results: int = Field(..., description="Número total de resultados")
    retrieval_time: float = Field(..., description="Tiempo de recuperación en segundos")

class HealthCheck(BaseModel):
    """Modelo para health checks"""
    
    status: str = Field(..., description="Estado general del servicio")
    version: str = Field(..., description="Versión de la aplicación")
    uptime: float = Field(..., description="Tiempo activo en segundos")
    components: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Estado de componentes individuales"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del health check"
    )

class ErrorResponse(BaseModel):
    """Modelo para respuestas de error"""
    
    error: str = Field(..., description="Tipo de error")
    message: str = Field(..., description="Mensaje de error")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detalles adicionales del error"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp del error"
    )
    request_id: Optional[str] = Field(
        None,
        description="ID de la request que causó el error"
    )