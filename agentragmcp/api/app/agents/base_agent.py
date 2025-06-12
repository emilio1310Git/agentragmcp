"""
Clase base abstracta para todos los agentes del sistema
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from agentragmcp.core.config import get_settings

class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes del sistema AgentRagMCP.
    
    Define la interfaz común que deben implementar todos los agentes especializados
    y proporciona funcionalidades básicas compartidas.
    """
    
    def __init__(
        self, 
        name: str, 
        description: str, 
        topics: List[str],
        rag_service: 'RAGService'
    ):
        """
        Inicializa el agente base.
        
        Args:
            name: Nombre único del agente
            description: Descripción de las capacidades del agente
            topics: Lista de temáticas que maneja el agente
            rag_service: Servicio RAG para consultas
        """
        self.name = name
        self.description = description
        self.topics = topics
        self.rag_service = rag_service
        self.settings = get_settings()
        
        # Métricas del agente
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "average_confidence": 0.0,
            "last_used": None,
            "created_at": datetime.now()
        }
    
    @abstractmethod
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """
        Determina si el agente puede manejar la pregunta.
        
        Args:
            question: Pregunta del usuario
            context: Contexto adicional opcional
            
        Returns:
            float: Confianza entre 0.0 y 1.0
                  0.0 = No puede manejar la pregunta
                  1.0 = Máxima confianza para manejar la pregunta
        """
        pass
    
    @abstractmethod
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        Procesa la pregunta y devuelve la respuesta.
        
        Args:
            question: Pregunta del usuario
            session_id: ID de la sesión de chat
            **kwargs: Argumentos adicionales (include_sources, context, etc.)
            
        Returns:
            Tuple[str, Dict]: (respuesta, metadatos)
        """
        pass
    
    def update_stats(self, confidence: float, success: bool = True):
        """
        Actualiza las estadísticas del agente.
        
        Args:
            confidence: Confianza de la consulta procesada
            success: Si la consulta fue exitosa
        """
        self.stats["total_queries"] += 1
        self.stats["last_used"] = datetime.now()
        
        if success:
            self.stats["successful_queries"] += 1
        else:
            self.stats["failed_queries"] += 1
        
        # Actualizar promedio de confianza
        total_successful = self.stats["successful_queries"]
        if total_successful > 0:
            current_avg = self.stats["average_confidence"]
            self.stats["average_confidence"] = (
                (current_avg * (total_successful - 1) + confidence) / total_successful
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene las estadísticas del agente.
        
        Returns:
            Dict con estadísticas de uso
        """
        success_rate = 0.0
        if self.stats["total_queries"] > 0:
            success_rate = self.stats["successful_queries"] / self.stats["total_queries"]
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "name": self.name,
            "description": self.description
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Devuelve información sobre las capacidades del agente.
        
        Returns:
            Dict con información de capacidades
        """
        return {
            "name": self.name,
            "description": self.description,
            "topics": self.topics,
            "agent_type": type(self).__name__,
            "stats": self.get_stats(),
            "status": "active" if self.is_healthy() else "degraded"
        }
    
    def is_healthy(self) -> bool:
        """
        Verifica si el agente está en estado saludable.
        
        Returns:
            bool: True si el agente está saludable
        """
        try:
            # Verificar que el RAG service está disponible
            if not self.rag_service:
                return False
            
            # Verificar que las temáticas están disponibles
            available_topics = self.rag_service.get_available_topics()
            topics_available = any(topic in available_topics for topic in self.topics)
            
            # Verificar tasa de éxito si hay estadísticas
            success_rate = 1.0  # Por defecto saludable si no hay estadísticas
            if self.stats["total_queries"] > 0:
                success_rate = self.stats["successful_queries"] / self.stats["total_queries"]
            
            return topics_available and success_rate >= 0.5
            
        except Exception:
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Realiza un health check detallado del agente.
        
        Returns:
            Dict con estado de salud detallado
        """
        health_status = {
            "agent": self.name,
            "status": "healthy",
            "checks": {},
            "topics": {},
            "stats": self.get_stats()
        }
        
        try:
            # Verificar RAG service
            if self.rag_service:
                health_status["checks"]["rag_service"] = "ok"
                
                # Verificar cada temática
                available_topics = self.rag_service.get_available_topics()
                for topic in self.topics:
                    if topic in available_topics:
                        health_status["topics"][topic] = "available"
                    else:
                        health_status["topics"][topic] = "unavailable"
                        health_status["status"] = "degraded"
            else:
                health_status["checks"]["rag_service"] = "failed"
                health_status["status"] = "unhealthy"
            
            # Verificar tasa de éxito
            if self.stats["total_queries"] > 0:
                success_rate = self.stats["successful_queries"] / self.stats["total_queries"]
                health_status["checks"]["success_rate"] = success_rate
                
                if success_rate < 0.5:
                    health_status["status"] = "degraded"
                elif success_rate < 0.2:
                    health_status["status"] = "unhealthy"
            else:
                health_status["checks"]["success_rate"] = "no_data"
            
            # Verificar uso reciente
            if self.stats["last_used"]:
                time_since_last = datetime.now() - self.stats["last_used"]
                health_status["checks"]["last_used_hours"] = time_since_last.total_seconds() / 3600
            
        except Exception as e:
            health_status["status"] = "error"
            health_status["error"] = str(e)
        
        return health_status
    
    def validate_question(self, question: str) -> Tuple[bool, Optional[str]]:
        """
        Valida si la pregunta es adecuada para procesar.
        
        Args:
            question: Pregunta a validar
            
        Returns:
            Tuple[bool, Optional[str]]: (es_válida, mensaje_error)
        """
        if not question or not question.strip():
            return False, "La pregunta no puede estar vacía"
        
        if len(question.strip()) < 3:
            return False, "La pregunta es demasiado corta"
        
        if len(question) > 2000:
            return False, "La pregunta es demasiado larga (máximo 2000 caracteres)"
        
        return True, None
    
    def prepare_context(self, question: str, session_id: str, **kwargs) -> Dict[str, Any]:
        """
        Prepara el contexto para el procesamiento de la pregunta.
        
        Args:
            question: Pregunta del usuario
            session_id: ID de la sesión
            **kwargs: Argumentos adicionales
            
        Returns:
            Dict con contexto preparado
        """
        context = {
            "agent_name": self.name,
            "agent_type": type(self).__name__,
            "session_id": session_id,
            "question_length": len(question),
            "timestamp": datetime.now().isoformat(),
            "topics": self.topics
        }
        
        # Agregar contexto adicional de kwargs
        if "context" in kwargs and isinstance(kwargs["context"], dict):
            context.update(kwargs["context"])
        
        return context
    
    def __str__(self) -> str:
        """Representación string del agente."""
        return f"{self.__class__.__name__}(name='{self.name}', topics={self.topics})"
    
    def __repr__(self) -> str:
        """Representación detallada del agente."""
        return (f"{self.__class__.__name__}("
                f"name='{self.name}', "
                f"description='{self.description[:50]}...', "
                f"topics={self.topics}, "
                f"queries={self.stats['total_queries']})")