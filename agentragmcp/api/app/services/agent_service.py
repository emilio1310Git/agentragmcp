import re
import time
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from chatplants.core.config import get_settings
from chatplants.core.monitoring import logger, chat_metrics, get_logger_with_context
from chatplants.core.exceptions import (
    AgentError, 
    AgentNotFoundError, 
    AgentSelectionError,
    handle_langchain_error
)
from chatplants.api.app.services.rag_service import RAGService

class BaseAgent(ABC):
    """Clase base abstracta para todos los agentes"""
    
    def __init__(self, name: str, description: str, topics: List[str]):
        self.name = name
        self.description = description
        self.topics = topics
        self.settings = get_settings()
    
    @abstractmethod
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """
        Determina si el agente puede manejar la pregunta.
        
        Returns:
            float: Confianza entre 0.0 y 1.0
        """
        pass
    
    @abstractmethod
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        Procesa la pregunta y devuelve la respuesta.
        
        Returns:
            Tuple[str, Dict]: (respuesta, metadatos)
        """
        pass

class PlantsAgent(BaseAgent):
    """Agente especializado en información general de plantas"""
    
    def __init__(self, rag_service: RAGService):
        super().__init__(
            name="plants",
            description="Especialista en información general de plantas",
            topics=["plants"]
        )
        self.rag_service = rag_service
        
        # Palabras clave que indican consultas sobre plantas
        self.plant_keywords = [
            "planta", "plantas", "árbol", "árboles", "cultivo", "cultivar",
            "sembrar", "plantar", "jardín", "huerto", "botánica", "especie",
            "variedad", "fruto", "frutos", "hoja", "hojas", "flor", "flores",
            "raíz", "raíces", "crecimiento", "cuidado", "riego", "fertilizar",
            "poda", "injerto", "semilla", "semillas"
        ]
        
        # Especies específicas
        self.specific_species = [name.lower() for name in self.settings.SPECIFIC_SPECIES]
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """Evalúa si puede manejar la pregunta sobre plantas"""
        question_lower = question.lower()
        confidence = 0.0
        
        # Buscar palabras clave generales
        keyword_matches = sum(1 for keyword in self.plant_keywords if keyword in question_lower)
        if keyword_matches > 0:
            confidence += 0.3 + (keyword_matches * 0.1)
        
        # Buscar especies específicas
        species_matches = sum(1 for species in self.specific_species if species in question_lower)
        if species_matches > 0:
            confidence += 0.5 + (species_matches * 0.2)
        
        # Patrones específicos de plantas
        plant_patterns = [
            r"cómo.*cultivar",
            r"cuándo.*plantar",
            r"qué.*planta",
            r"características.*de.*\w+",
            r"cuidados.*de",
            r"información.*sobre.*\w+"
        ]
        
        for pattern in plant_patterns:
            if re.search(pattern, question_lower):
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Procesa la pregunta usando el RAG de plantas"""
        try:
            answer, metadata = self.rag_service.query(
                question=question,
                topic="plants",
                session_id=session_id,
                include_sources=kwargs.get("include_sources", False)
            )
            
            metadata.update({
                "agent_type": self.name,
                "agent_description": self.description
            })
            
            return answer, metadata
            
        except Exception as e:
            logger.error(f"Error en PlantsAgent: {e}")
            raise

class PathologyAgent(BaseAgent):
    """Agente especializado en patologías y enfermedades de plantas"""
    
    def __init__(self, rag_service: RAGService):
        super().__init__(
            name="pathology",
            description="Especialista en patologías, enfermedades y tratamientos de plantas",
            topics=["pathology"]
        )
        self.rag_service = rag_service
        
        # Palabras clave relacionadas con patologías
        self.pathology_keywords = [
            "enfermedad", "enfermedades", "patología", "patologías", "plaga", "plagas",
            "hongo", "hongos", "bacteria", "bacterias", "virus", "insecto", "insectos",
            "tratamiento", "tratar", "curar", "síntomas", "prevenir", "prevención",
            "fungicida", "insecticida", "pesticida", "control", "mancha", "manchas",
            "podredumbre", "marchitez", "amarilleo", "necrosis", "lesión", "lesiones"
        ]
        
        # Especies con patologías específicas
        self.pathology_species = [name.lower() for name in self.settings.PATHOLOGY_SPECIES]
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """Evalúa si puede manejar la pregunta sobre patologías"""
        question_lower = question.lower()
        confidence = 0.0
        
        # Buscar palabras clave de patologías
        keyword_matches = sum(1 for keyword in self.pathology_keywords if keyword in question_lower)
        if keyword_matches > 0:
            confidence += 0.4 + (keyword_matches * 0.15)
        
        # Buscar especies específicas para patologías
        species_matches = sum(1 for species in self.pathology_species if species in question_lower)
        if species_matches > 0:
            confidence += 0.3 + (species_matches * 0.2)
        
        # Patrones específicos de patologías
        pathology_patterns = [
            r"qué.*enfermedad",
            r"cómo.*tratar",
            r"síntomas.*de",
            r"problema.*con",
            r"se.*está.*muriendo",
            r"hojas.*amarillas",
            r"manchas.*en"
        ]
        
        for pattern in pathology_patterns:
            if re.search(pattern, question_lower):
                confidence += 0.3
        
        return min(confidence, 1.0)
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Procesa la pregunta usando el RAG de patologías"""
        try:
            answer, metadata = self.rag_service.query(
                question=question,
                topic="pathology",
                session_id=session_id,
                include_sources=kwargs.get("include_sources", False)
            )
            
            metadata.update({
                "agent_type": self.name,
                "agent_description": self.description
            })
            
            return answer, metadata
            
        except Exception as e:
            logger.error(f"Error en PathologyAgent: {e}")
            raise

class GeneralAgent(BaseAgent):
    """Agente general para consultas que no requieren especialización"""
    
    def __init__(self, rag_service: RAGService):
        super().__init__(
            name="general",
            description="Asistente general para consultas diversas sobre plantas",
            topics=["general"]
        )
        self.rag_service = rag_service
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """El agente general siempre puede manejar cualquier pregunta como fallback"""
        # Confianza base baja para que otros agentes especializados tengan preferencia
        return 0.2
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Procesa la pregunta usando el RAG general"""
        try:
            answer, metadata = self.rag_service.query(
                question=question,
                topic="general",
                session_id=session_id,
                include_sources=kwargs.get("include_sources", False)
            )
            
            metadata.update({
                "agent_type": self.name,
                "agent_description": self.description
            })
            
            return answer, metadata
            
        except Exception as e:
            logger.error(f"Error en GeneralAgent: {e}")
            raise

class AgentSelector:
    """Selector inteligente de agentes basado en la pregunta"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Inicializar LLM para selección de agentes si está configurado
        if hasattr(self.settings, 'AGENT_SELECTION_MODEL'):
            try:
                self.selection_llm = ChatOllama(
                    model=self.settings.AGENT_SELECTION_MODEL,
                    base_url=self.settings.LLM_BASE_URL,
                    temperature=0.1  # Baja temperatura para selección consistente
                )
                self.use_llm_selection = True
            except Exception as e:
                logger.warning(f"No se pudo inicializar LLM para selección: {e}")
                self.use_llm_selection = False
        else:
            self.use_llm_selection = False
    
    def select_agent(
        self, 
        question: str, 
        available_agents: List[BaseAgent],
        context: Optional[Dict] = None
    ) -> Tuple[BaseAgent, float]:
        """
        Selecciona el agente más apropiado para la pregunta
        
        Returns:
            Tuple[BaseAgent, float]: (agente_seleccionado, confianza)
        """
        start_time = time.time()
        
        try:
            if self.use_llm_selection and len(available_agents) > 2:
                # Usar LLM para selección inteligente
                return self._llm_based_selection(question, available_agents, context)
            else:
                # Usar selección basada en reglas
                return self._rule_based_selection(question, available_agents, context)
                
        except Exception as e:
            logger.error(f"Error en selección de agente: {e}")
            # Fallback al agente por defecto
            default_agent = self._get_default_agent(available_agents)
            return default_agent, 0.1
        finally:
            selection_time = time.time() - start_time
            logger.debug(f"Tiempo de selección de agente: {selection_time:.3f}s")
    
    def _rule_based_selection(
        self, 
        question: str, 
        available_agents: List[BaseAgent],
        context: Optional[Dict] = None
    ) -> Tuple[BaseAgent, float]:
        """Selección basada en reglas y confianza de cada agente"""
        
        agent_scores = []
        
        for agent in available_agents:
            try:
                confidence = agent.can_handle(question, context)
                agent_scores.append((agent, confidence))
                logger.debug(f"Agente {agent.name}: confianza = {confidence:.3f}")
            except Exception as e:
                logger.warning(f"Error evaluando agente {agent.name}: {e}")
                agent_scores.append((agent, 0.0))
        
        # Ordenar por confianza descendente
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        if not agent_scores or agent_scores[0][1] == 0:
            # Usar agente por defecto si ninguno tiene confianza
            default_agent = self._get_default_agent(available_agents)
            return default_agent, 0.1
        
        best_agent, best_confidence = agent_scores[0]
        
        # Log de selección para métricas
        chat_metrics.log_agent_selection(
            session_id="selection",  # No tenemos session_id en esta fase
            question=question,
            selected_agent=best_agent.name,
            confidence=best_confidence
        )
        
        return best_agent, best_confidence
    
    def _llm_based_selection(
        self, 
        question: str, 
        available_agents: List[BaseAgent],
        context: Optional[Dict] = None
    ) -> Tuple[BaseAgent, float]:
        """Selección basada en LLM para casos complejos"""
        
        # Preparar información de agentes
        agents_info = "\n".join([
            f"- {agent.name}: {agent.description} (temas: {', '.join(agent.topics)})"
            for agent in available_agents
        ])
        
        selection_prompt = ChatPromptTemplate.from_template("""
Eres un selector de agentes experto. Dada la siguiente pregunta del usuario y la lista de agentes disponibles, 
selecciona el agente más apropiado y proporciona una puntuación de confianza.

Pregunta del usuario: {question}

Agentes disponibles:
{agents_info}

Responde SOLO con el nombre del agente seleccionado y la confianza (0.0-1.0) en este formato:
AGENTE: nombre_del_agente
CONFIANZA: 0.X

Considera:
- Especialización del agente en el tema
- Palabras clave en la pregunta
- Complejidad de la consulta
""")
        
        try:
            chain = selection_prompt | self.selection_llm
            response = chain.invoke({
                "question": question,
                "agents_info": agents_info
            })
            
            # Parsear respuesta
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extraer agente y confianza
            agent_match = re.search(r"AGENTE:\s*(\w+)", content)
            confidence_match = re.search(r"CONFIANZA:\s*(0?\.\d+|1\.0)", content)
            
            if agent_match and confidence_match:
                selected_agent_name = agent_match.group(1)
                confidence = float(confidence_match.group(1))
                
                # Encontrar el agente correspondiente
                for agent in available_agents:
                    if agent.name == selected_agent_name:
                        return agent, confidence
            
            # Si no se pudo parsear, fallback a selección basada en reglas
            logger.warning("No se pudo parsear respuesta del LLM, usando selección basada en reglas")
            return self._rule_based_selection(question, available_agents, context)
            
        except Exception as e:
            logger.error(f"Error en selección basada en LLM: {e}")
            return self._rule_based_selection(question, available_agents, context)
    
    def _get_default_agent(self, available_agents: List[BaseAgent]) -> BaseAgent:
        """Obtiene el agente por defecto"""
        default_name = self.settings.DEFAULT_AGENT
        
        for agent in available_agents:
            if agent.name == default_name:
                return agent
        
        # Si no se encuentra el por defecto, devolver el primero
        return available_agents[0] if available_agents else None

class AgentService:
    """Servicio principal para gestión de agentes"""
    
    def __init__(self, rag_service: RAGService):
        self.rag_service = rag_service
        self.settings = get_settings()
        
        # Inicializar agentes
        self.agents = {
            "plants": PlantsAgent(rag_service),
            "pathology": PathologyAgent(rag_service),
            "general": GeneralAgent(rag_service)
        }
        
        # Inicializar selector
        self.selector = AgentSelector()
        
        logger.info(f"AgentService inicializado con {len(self.agents)} agentes")
    
    def process_question(
        self, 
        question: str, 
        session_id: str,
        agent_type: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Procesa una pregunta seleccionando automáticamente el agente apropiado
        
        Args:
            question: Pregunta del usuario
            session_id: ID de la sesión
            agent_type: Tipo específico de agente (opcional)
            **kwargs: Argumentos adicionales
            
        Returns:
            Tuple[str, Dict]: (respuesta, metadatos)
        """
        start_time = time.time()
        context_logger = get_logger_with_context(chat_session_id=session_id)
        
        try:
            # Si se especifica un agente, usarlo directamente
            if agent_type:
                if agent_type not in self.agents:
                    raise AgentNotFoundError(agent_type)
                
                selected_agent = self.agents[agent_type]
                confidence = 1.0  # Confianza máxima para selección manual
                context_logger.info(f"Usando agente especificado: {agent_type}")
            else:
                # Selección automática
                available_agents = list(self.agents.values())
                selected_agent, confidence = self.selector.select_agent(
                    question, 
                    available_agents,
                    kwargs.get("context")
                )
                context_logger.info(f"Agente seleccionado automáticamente: {selected_agent.name} (confianza: {confidence:.3f})")
            
            # Procesar la pregunta con el agente seleccionado
            answer, metadata = selected_agent.process(
                question=question,
                session_id=session_id,
                **kwargs
            )
            
            # Agregar información de selección a los metadatos
            metadata.update({
                "agent_selection_confidence": confidence,
                "agent_selection_method": "manual" if agent_type else "automatic",
                "total_processing_time": time.time() - start_time
            })
            
            return answer, metadata
            
        except Exception as e:
            processing_time = time.time() - start_time
            context_logger.error(f"Error procesando pregunta: {e}")
            
            # Log de métricas de error
            chat_metrics.log_chat_interaction(
                session_id=session_id,
                question=question,
                agent_type=agent_type or "auto",
                topic="unknown",
                response_time=processing_time,
                success=False,
                error=str(e)
            )
            
            raise
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Devuelve información de los agentes disponibles"""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "topics": agent.topics
            }
            for agent in self.agents.values()
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """Health check del servicio de agentes"""
        return {
            "status": "healthy",
            "total_agents": len(self.agents),
            "agents": {
                name: {
                    "status": "ok",
                    "description": agent.description,
                    "topics": agent.topics
                }
                for name, agent in self.agents.items()
            },
            "selector": {
                "status": "ok",
                "llm_selection_enabled": self.selector.use_llm_selection
            }
        }