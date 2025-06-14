"""
Sistema de agentes dinámico que se carga basándose en configuraciones
Permite agregar nuevos agentes sin modificar código
"""
import re
import time
import importlib
import inspect
from typing import List, Dict, Any, Optional, Tuple, Type
from abc import ABC, abstractmethod
from datetime import datetime

from agentragmcp.core.dynamic_config import config_manager, AgentConfig
from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger, chat_metrics, get_logger_with_context
from agentragmcp.core.exceptions import (
    AgentError, AgentNotFoundError, AgentSelectionError,
    handle_langchain_error
)

class ConfigurableAgent(ABC):
    """Clase base para agentes configurables dinámicamente"""
    
    def __init__(self, config: AgentConfig, rag_service):
        self.config = config
        self.name = config.name
        self.description = config.description
        self.topics = config.topics
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
        
        # Compilar patrones regex para eficiencia
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in config.patterns
        ]
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """
        Implementación base de evaluación de confianza usando configuración
        Los agentes pueden sobrescribir este método para lógica personalizada
        """
        question_lower = question.lower()
        confidence = self.config.base_confidence
        
        # 1. Palabras clave primarias
        primary_matches = sum(1 for keyword in self.config.primary_keywords 
                            if keyword.lower() in question_lower)
        if primary_matches > 0:
            confidence += self.config.keyword_weight * min(primary_matches * 0.2, 1.0)
        
        # 2. Palabras clave secundarias (peso menor)
        secondary_matches = sum(1 for keyword in self.config.secondary_keywords 
                              if keyword.lower() in question_lower)
        if secondary_matches > 0:
            confidence += self.config.keyword_weight * 0.5 * min(secondary_matches * 0.1, 0.5)
        
        # 3. Especies objetivo
        species_matches = sum(1 for species in self.config.target_species 
                            if species.lower() in question_lower)
        if species_matches > 0:
            confidence += self.config.species_weight * min(species_matches * 0.3, 1.0)
        
        # 4. Nombres comunes
        common_matches = sum(1 for name in self.config.common_names 
                           if name.lower() in question_lower)
        if common_matches > 0:
            confidence += self.config.species_weight * 0.5 * min(common_matches * 0.2, 0.6)
        
        # 5. Patrones regex
        pattern_matches = sum(1 for pattern in self._compiled_patterns 
                            if pattern.search(question_lower))
        if pattern_matches > 0:
            confidence += self.config.pattern_weight * min(pattern_matches * 0.3, 1.0)
        
        # 6. Bonus por contexto
        if context:
            topic = context.get("topic", "").lower()
            if topic in [t.lower() for t in self.topics]:
                confidence += self.config.context_bonus
        
        # Aplicar límites de confianza
        confidence = max(self.config.min_confidence, 
                        min(confidence, self.config.max_confidence))
        
        return confidence
    
    @abstractmethod
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Procesa la pregunta y devuelve respuesta"""
        pass
    
    def update_stats(self, confidence: float, success: bool = True):
        """Actualiza estadísticas del agente"""
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
    
    def get_info(self) -> Dict[str, Any]:
        """Información completa del agente"""
        return {
            "name": self.name,
            "description": self.description,
            "class_name": self.config.class_name,
            "topics": self.topics,
            "enabled": self.config.enabled,
            "priority": self.config.priority,
            "stats": self.stats,
            "config_summary": {
                "keywords": len(self.config.primary_keywords + self.config.secondary_keywords),
                "patterns": len(self.config.patterns),
                "species": len(self.config.target_species),
                "weights": {
                    "keyword": self.config.keyword_weight,
                    "species": self.config.species_weight,
                    "pattern": self.config.pattern_weight
                }
            }
        }

class GenericRAGAgent(ConfigurableAgent):
    """Agente genérico que puede manejar cualquier temática RAG"""
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Procesa usando el primer topic configurado"""
        context_logger = get_logger_with_context(
            chat_session_id=session_id,
            agent_type=self.name
        )
        
        try:
            # Usar el primer topic como principal
            main_topic = self.topics[0] if self.topics else "general"
            
            context_logger.info(f"Procesando con agente genérico {self.name} - Topic: {main_topic}")
            
            # Procesar con RAG
            answer, metadata = self.rag_service.query(
                question=question,
                topic=main_topic,
                session_id=session_id,
                include_sources=kwargs.get("include_sources", False)
            )
            
            # Enriquecer metadatos
            metadata.update({
                "agent_type": self.name,
                "agent_description": self.description,
                "agent_class": "GenericRAGAgent",
                "config_based": True
            })
            
            return answer, metadata
            
        except Exception as e:
            context_logger.error(f"Error en agente genérico {self.name}: {e}")
            raise

class DynamicAgentLoader:
    """Cargador dinámico de agentes basado en configuración"""
    
    def __init__(self):
        self.agent_classes: Dict[str, Type[ConfigurableAgent]] = {
            "GenericRAGAgent": GenericRAGAgent
        }
        self.custom_modules = {}
        
        # Registrar agentes existentes si están disponibles
        self._register_existing_agents()
    
    def _register_existing_agents(self):
        """Registra agentes existentes en el sistema"""
        try:
            # Intentar importar agentes existentes
            from agentragmcp.api.app.agents.plants_agent import PlantsAgent
            from agentragmcp.api.app.agents.pathology_agent import PathologyAgent
            from agentragmcp.api.app.agents.general_agent import GeneralAgent
            
            # Adaptar agentes existentes para usar configuración
            self.agent_classes.update({
                "PlantsAgent": self._create_adapter_class(PlantsAgent),
                "PathologyAgent": self._create_adapter_class(PathologyAgent),
                "GeneralAgent": self._create_adapter_class(GeneralAgent)
            })
            
            logger.info("Agentes existentes registrados con adaptador de configuración")
            
        except ImportError as e:
            logger.warning(f"No se pudieron cargar agentes existentes: {e}")
    
    def _create_adapter_class(self, original_class):
        """Crea una clase adaptadora para agentes existentes"""
        
        class ConfigurableAdapter(ConfigurableAgent):
            def __init__(self, config: AgentConfig, rag_service):
                super().__init__(config, rag_service)
                # Crear instancia del agente original
                self._original_agent = original_class(rag_service)
            
            def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
                # Usar método original si existe, sino usar el configurable
                if hasattr(self._original_agent, 'can_handle'):
                    return self._original_agent.can_handle(question, context)
                else:
                    return super().can_handle(question, context)
            
            def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
                # Usar método original
                return self._original_agent.process(question, session_id, **kwargs)
        
        return ConfigurableAdapter
    
    def load_custom_agent(self, module_path: str, class_name: str) -> Optional[Type[ConfigurableAgent]]:
        """Carga un agente personalizado desde un módulo"""
        try:
            if module_path not in self.custom_modules:
                spec = importlib.util.spec_from_file_location("custom_agent", module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.custom_modules[module_path] = module
            
            module = self.custom_modules[module_path]
            agent_class = getattr(module, class_name)
            
            # Verificar que hereda de ConfigurableAgent
            if not issubclass(agent_class, ConfigurableAgent):
                logger.error(f"Clase {class_name} no hereda de ConfigurableAgent")
                return None
            
            return agent_class
            
        except Exception as e:
            logger.error(f"Error cargando agente personalizado {class_name}: {e}")
            return None
    
    def create_agent(self, config: AgentConfig, rag_service) -> Optional[ConfigurableAgent]:
        """Crea una instancia de agente basada en configuración"""
        
        # Determinar la clase a usar
        agent_class = None
        
        if config.module_path:
            # Agente personalizado
            agent_class = self.load_custom_agent(config.module_path, config.class_name)
        elif config.class_name in self.agent_classes:
            # Agente registrado
            agent_class = self.agent_classes[config.class_name]
        else:
            # Usar agente genérico como fallback
            logger.warning(f"Clase de agente {config.class_name} no encontrada, usando GenericRAGAgent")
            agent_class = GenericRAGAgent
        
        if not agent_class:
            logger.error(f"No se pudo determinar clase para agente {config.name}")
            return None
        
        try:
            # Crear instancia
            agent = agent_class(config, rag_service)
            logger.info(f"Agente creado: {config.name} ({config.class_name})")
            return agent
            
        except Exception as e:
            logger.error(f"Error creando agente {config.name}: {e}")
            return None

class DynamicAgentService:
    """Servicio de agentes con carga dinámica basada en configuración"""
    
    def __init__(self, rag_service):
        self.rag_service = rag_service
        self.settings = get_settings()
        
        # Componentes
        self.agent_loader = DynamicAgentLoader()
        self.agents: Dict[str, ConfigurableAgent] = {}
        self.selector = DynamicAgentSelector()
        
        # Control de recarga
        self.last_config_check = 0
        self.config_check_interval = 30  # segundos
        
        # Cargar agentes iniciales
        self._discover_and_load_agents()
        
        logger.info(f"DynamicAgentService inicializado con {len(self.agents)} agentes")
    
    def _discover_and_load_agents(self):
        """Descubre y carga agentes basándose en configuración"""
        
        # Crear configuración de ejemplo si no existe
        agents_file = config_manager.config_base_path / "agents.yaml"
        if not agents_file.exists():
            logger.info("Creando configuración de agentes de ejemplo...")
            config_manager.create_sample_configs()
        
        # Cargar configuraciones de agentes
        try:
            import yaml
            with open(agents_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            agents_data = data.get("agents", {})
            
            for agent_name in agents_data.keys():
                self._load_agent(agent_name)
                
        except Exception as e:
            logger.error(f"Error cargando configuraciones de agentes: {e}")
    
    def _load_agent(self, agent_name: str) -> bool:
        """Carga un agente específico"""
        config = config_manager.load_agent_config(agent_name)
        if not config or not config.enabled:
            logger.info(f"Agente {agent_name} deshabilitado o no configurado")
            return False
        
        # Crear agente
        agent = self.agent_loader.create_agent(config, self.rag_service)
        if agent:
            self.agents[agent_name] = agent
            logger.info(f"Agente cargado: {agent_name}")
            return True
        else:
            logger.error(f"No se pudo crear agente: {agent_name}")
            return False
    
    def check_and_reload_configs(self) -> List[str]:
        """Verifica y recarga configuraciones de agentes si han cambiado"""
        current_time = time.time()
        
        # Solo verificar periódicamente
        if current_time - self.last_config_check < self.config_check_interval:
            return []
        
        self.last_config_check = current_time
        
        # Verificar cambios en configuración
        reloaded = config_manager.reload_if_changed()
        
        agents_reloaded = []
        for item in reloaded:
            if item.startswith("agents:"):
                # Recargar todos los agentes
                logger.info("Recargando todos los agentes...")
                self.agents.clear()
                self._discover_and_load_agents()
                agents_reloaded = list(self.agents.keys())
                break
        
        return agents_reloaded
    
    async def process_question(
        self, 
        question: str, 
        session_id: str,
        agent_type: Optional[str] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Procesa pregunta con agentes dinámicos"""
        start_time = time.time()
        context_logger = get_logger_with_context(chat_session_id=session_id)
        
        try:
            # Verificar y recargar configuraciones
            self.check_and_reload_configs()
            
            # Seleccionar agente
            if agent_type:
                # Agente específico
                if agent_type not in self.agents:
                    raise AgentNotFoundError(agent_type)
                selected_agent = self.agents[agent_type]
                confidence = 1.0
                context_logger.info(f"Usando agente especificado: {agent_type}")
            else:
                # Selección automática
                available_agents = [agent for agent in self.agents.values() if agent.config.enabled]
                selected_agent, confidence = self.selector.select_agent(
                    question, 
                    available_agents,
                    kwargs.get("context")
                )
                context_logger.info(f"Agente seleccionado: {selected_agent.name} (confianza: {confidence:.3f})")
            
            # Procesar pregunta
            answer, metadata = selected_agent.process(
                question=question,
                session_id=session_id,
                **kwargs
            )
            
            # Actualizar estadísticas del agente
            selected_agent.update_stats(confidence, success=True)
            
            # Enriquecer metadatos
            metadata.update({
                "agent_selection_confidence": confidence,
                "agent_selection_method": "manual" if agent_type else "automatic",
                "total_processing_time": time.time() - start_time,
                "agent_config_based": True
            })
            
            return answer, metadata
            
        except Exception as e:
            processing_time = time.time() - start_time
            context_logger.error(f"Error procesando pregunta: {e}")
            
            # Actualizar estadísticas de error si hay agente seleccionado
            if 'selected_agent' in locals():
                selected_agent.update_stats(0.0, success=False)
            
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
        """Devuelve información de agentes disponibles"""
        self.check_and_reload_configs()
        
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "topics": agent.topics,
                "enabled": agent.config.enabled,
                "priority": agent.config.priority,
                "class_name": agent.config.class_name,
                "stats": agent.stats
            }
            for agent in self.agents.values()
            if agent.config.enabled
        ]
    
    def get_agent_details(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Obtiene detalles completos de un agente"""
        agent = self.agents.get(agent_name)
        if not agent:
            return None
        
        return agent.get_info()
    
    def add_new_agent(self, agent_config_data: Dict[str, Any]) -> bool:
        """Añade un nuevo agente dinámicamente"""
        try:
            # Cargar configuración actual
            agents_file = config_manager.config_base_path / "agents.yaml"
            
            import yaml
            if agents_file.exists():
                with open(agents_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                data = {"agents": {}}
            
            # Añadir nueva configuración
            agent_name = agent_config_data["name"]
            data["agents"][agent_name] = agent_config_data
            
            # Guardar configuración
            with open(agents_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            # Cargar agente inmediatamente
            success = self._load_agent(agent_name)
            
            if success:
                logger.info(f"Nuevo agente añadido: {agent_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error añadiendo nuevo agente: {e}")
            return False
    
    def reload_agent(self, agent_name: str) -> bool:
        """Recarga un agente específico"""
        try:
            # Eliminar agente actual
            if agent_name in self.agents:
                del self.agents[agent_name]
            
            # Recargar
            return self._load_agent(agent_name)
            
        except Exception as e:
            logger.error(f"Error recargando agente {agent_name}: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Health check del servicio de agentes dinámico"""
        self.check_and_reload_configs()
        
        total_agents = len(self.agents)
        enabled_agents = len([a for a in self.agents.values() if a.config.enabled])
        
        agent_health = {}
        for name, agent in self.agents.items():
            agent_health[name] = {
                "enabled": agent.config.enabled,
                "topics": agent.topics,
                "total_queries": agent.stats["total_queries"],
                "success_rate": (agent.stats["successful_queries"] / agent.stats["total_queries"]) 
                               if agent.stats["total_queries"] > 0 else 0.0,
                "class": agent.config.class_name
            }
        
        return {
            "status": "healthy" if enabled_agents > 0 else "degraded",
            "service_type": "dynamic_agents",
            "total_agents": total_agents,
            "enabled_agents": enabled_agents,
            "agents": agent_health,
            "selector": {
                "type": "dynamic",
                "available": True
            }
        }

class DynamicAgentSelector:
    """Selector de agentes dinámico"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def select_agent(
        self, 
        question: str, 
        available_agents: List[ConfigurableAgent],
        context: Optional[Dict] = None
    ) -> Tuple[ConfigurableAgent, float]:
        """Selecciona el agente más apropiado basándose en configuración"""
        
        if not available_agents:
            raise AgentSelectionError("No hay agentes disponibles")
        
        # Evaluar todos los agentes
        agent_scores = []
        for agent in available_agents:
            try:
                confidence = agent.can_handle(question, context)
                agent_scores.append((agent, confidence))
                logger.debug(f"Agente {agent.name}: confianza = {confidence:.3f}")
            except Exception as e:
                logger.warning(f"Error evaluando agente {agent.name}: {e}")
                agent_scores.append((agent, 0.0))
        
        # Ordenar por confianza y prioridad
        agent_scores.sort(key=lambda x: (x[1], -x[0].config.priority), reverse=True)
        
        if not agent_scores or agent_scores[0][1] == 0:
            # Buscar agente fallback
            fallback_agent = self._get_fallback_agent(available_agents)
            if fallback_agent:
                return fallback_agent, 0.1
            else:
                # Usar el primero disponible
                return available_agents[0], 0.05
        
        best_agent, best_confidence = agent_scores[0]
        
        # Log de selección para métricas
        chat_metrics.log_agent_selection(
            session_id="selection",
            question=question,
            selected_agent=best_agent.name,
            confidence=best_confidence
        )
        
        return best_agent, best_confidence
    
    def _get_fallback_agent(self, available_agents: List[ConfigurableAgent]) -> Optional[ConfigurableAgent]:
        """Obtiene agente fallback configurado"""
        # Buscar agente con fallback_enabled
        for agent in available_agents:
            if agent.config.fallback_enabled:
                return agent
        
        # Buscar agente general o con menor prioridad
        general_agents = [a for a in available_agents if "general" in a.name.lower()]
        if general_agents:
            return general_agents[0]
        
        # Usar el de menor prioridad (número más alto)
        if available_agents:
            return max(available_agents, key=lambda a: a.config.priority)
        
        return None

# Ejemplo de agente personalizado que se puede cargar dinámicamente
class EcoAgricultureAgent(ConfigurableAgent):
    """Agente personalizado para agricultura ecológica"""
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """Lógica personalizada de evaluación"""
        # Usar evaluación base
        base_confidence = super().can_handle(question, context)
        
        # Añadir lógica específica para agricultura ecológica
        question_lower = question.lower()
        
        eco_terms = ["ecológico", "orgánico", "sostenible", "biodiversidad", 
                    "permacultura", "compost", "natural", "sin químicos"]
        
        eco_matches = sum(1 for term in eco_terms if term in question_lower)
        if eco_matches > 0:
            base_confidence += eco_matches * 0.15
        
        # Penalizar por términos de química convencional
        chemical_terms = ["pesticida", "químico", "sintético", "industrial"]
        chemical_matches = sum(1 for term in chemical_terms if term in question_lower)
        if chemical_matches > 0:
            base_confidence -= chemical_matches * 0.1
        
        return max(self.config.min_confidence, 
                  min(base_confidence, self.config.max_confidence))
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Procesa pregunta con enfoque en agricultura ecológica"""
        context_logger = get_logger_with_context(
            chat_session_id=session_id,
            agent_type=self.name
        )
        
        try:
            context_logger.info(f"Procesando con agente de agricultura ecológica")
            
            # Usar RAG específico si está disponible en topics
            topic = "eco_agriculture" if "eco_agriculture" in self.topics else self.topics[0]
            
            answer, metadata = self.rag_service.query(
                question=question,
                topic=topic,
                session_id=session_id,
                include_sources=kwargs.get("include_sources", False)
            )
            
            # Enriquecer respuesta con enfoque ecológico
            enhanced_answer = self._enhance_eco_answer(answer, question)
            
            metadata.update({
                "agent_type": self.name,
                "agent_description": self.description,
                "specialization": "agricultura_ecologica",
                "enhanced": enhanced_answer != answer
            })
            
            return enhanced_answer, metadata
            
        except Exception as e:
            context_logger.error(f"Error en EcoAgricultureAgent: {e}")
            raise
    
    def _enhance_eco_answer(self, answer: str, question: str) -> str:
        """Mejora la respuesta con enfoque ecológico"""
        question_lower = question.lower()
        
        # Añadir consejos ecológicos
        if any(word in question_lower for word in ["cómo", "cultivar", "plantar"]):
            if "ecológico" not in answer.lower() and len(answer) < 500:
                answer += "\n\n🌱 **Enfoque ecológico**: Considera usar métodos naturales como compost, rotación de cultivos y control biológico de plagas."
        
        # Advertencia sobre químicos si se mencionan
        if any(word in question_lower for word in ["pesticida", "químico", "fertilizante"]):
            if "natural" not in answer.lower():
                answer += "\n\n🌿 **Alternativa ecológica**: Explora opciones orgánicas y naturales antes de usar productos químicos sintéticos."
        
        return answer