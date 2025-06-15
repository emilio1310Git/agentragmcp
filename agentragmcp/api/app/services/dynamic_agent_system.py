"""
Sistema de agentes dinámico completo para AgentRagMCP
Gestiona RAGs y agentes de forma dinámica basándose en configuración
"""

import time
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts import ChatPromptTemplate
from pathlib import Path

from agentragmcp.core.dynamic_config import config_manager, RAGTopicConfig, AgentConfig
from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger, get_logger_with_context
from agentragmcp.core.exceptions import (
    AgentError, AgentNotFoundError, AgentSelectionError,
    handle_langchain_error
)
from agentragmcp.api.app.agents.dinamic_agent import (
    ConfigurableAgent, DynamicAgentLoader, DynamicAgent
)

class DynamicRAGService:
    """Servicio de RAG dinámico que carga configuraciones automáticamente"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Componentes principales
        self.llm = None
        self.embeddings_cache: Dict[str, OllamaEmbeddings] = {}
        self.retrievers: Dict[str, Any] = {}
        self.chains: Dict[str, Any] = {}
        self.chat_histories: Dict[str, BaseChatMessageHistory] = {}
        
        # Cache de configuraciones
        self.loaded_configs: Dict[str, RAGTopicConfig] = {}
        self.last_config_check = 0
        self.config_check_interval = 30  # segundos
        
        # Inicializar
        self._initialize_llm()
        self._discover_and_load_rags()
    
    def _initialize_llm(self):
        """Inicializa el modelo de lenguaje principal"""
        try:
            self.llm = ChatOllama(
                model=self.settings.LLM_MODEL,
                base_url=self.settings.LLM_BASE_URL,
                temperature=self.settings.LLM_TEMPERATURE
            )
            logger.info(f"LLM inicializado: {self.settings.LLM_MODEL}")
        except Exception as e:
            logger.error(f"Error inicializando LLM: {e}")
            raise handle_langchain_error(e)
    
    def _get_embeddings(self, config: RAGTopicConfig) -> OllamaEmbeddings:
        """Obtiene embeddings específicos para una configuración"""
        cache_key = f"{config.vectorstore.embedding_model}:{config.vectorstore.embedding_base_url}"
        
        if cache_key not in self.embeddings_cache:
            try:
                embeddings = OllamaEmbeddings(
                    model=config.vectorstore.embedding_model,
                    base_url=config.vectorstore.embedding_base_url
                )
                self.embeddings_cache[cache_key] = embeddings
                logger.info(f"Embeddings creados: {config.vectorstore.embedding_model}")
            except Exception as e:
                logger.error(f"Error creando embeddings: {e}")
                raise handle_langchain_error(e)
        
        return self.embeddings_cache[cache_key]
    
    def _discover_and_load_rags(self):
        """Descubre y carga automáticamente todos los RAGs configurados"""
        logger.info("Descubriendo configuraciones RAG...")
        
        # Crear configuraciones de ejemplo si no existen
        discovered = config_manager.discover_rag_configs()
        if not discovered:
            logger.info("No se encontraron configuraciones, creando ejemplos...")
            config_manager.create_sample_configs()
            discovered = config_manager.discover_rag_configs()
        
        # Cargar todas las configuraciones disponibles
        for topic_name in discovered:
            try:
                self._load_rag_topic(topic_name)
            except Exception as e:
                logger.error(f"Error cargando RAG {topic_name}: {e}")
                continue
        
        logger.info(f"RAGs cargados: {list(self.chains.keys())}")
    
    def _load_rag_topic(self, topic_name: str) -> bool:
        """Carga un RAG específico basado en su configuración"""
        config = config_manager.load_rag_config(topic_name)
        if not config or not config.enabled:
            logger.info(f"RAG {topic_name} deshabilitado o no configurado")
            return False
        
        try:
            # Validar configuración
            validation = config_manager.validate_config(topic_name)
            if not validation["valid"]:
                logger.error(f"Configuración inválida para {topic_name}: {validation['errors']}")
                return False
            
            if validation["warnings"]:
                logger.warning(f"Advertencias para {topic_name}: {validation['warnings']}")
            
            # Cargar retriever
            retriever = self._load_retriever(config)
            if not retriever:
                logger.warning(f"No se pudo cargar retriever para {topic_name}")
                return False
            
            self.retrievers[topic_name] = retriever
            
            # Crear cadena RAG
            chain = self._create_rag_chain(config, retriever)
            self.chains[topic_name] = chain
            
            # Almacenar configuración
            self.loaded_configs[topic_name] = config
            
            logger.info(f"RAG cargado exitosamente: {topic_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando RAG {topic_name}: {e}")
            return False
    
    def _load_retriever(self, config: RAGTopicConfig):
        """Carga retriever basado en configuración"""
        try:
            vectorstore_path = config.vectorstore.path
            
            # Verificar que existe el vectorstore
            if not os.path.exists(vectorstore_path):
                logger.warning(f"Vectorstore no encontrado: {vectorstore_path}")
                return None
            
            # Verificar contenido
            chroma_files = list(Path(vectorstore_path).glob("*"))
            if not chroma_files:
                logger.warning(f"Vectorstore vacío: {vectorstore_path}")
                return None
            
            # Obtener embeddings específicos
            embeddings = self._get_embeddings(config)
            
            # Cargar vectorstore
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=embeddings,
                collection_name=config.vectorstore.collection_name
            )
            
            # Verificar contenido
            try:
                test_results = vectorstore.similarity_search("test", k=1)
                if not test_results:
                    logger.warning(f"Vectorstore {config.name} parece estar vacío")
                    return None
            except Exception as e:
                logger.warning(f"Error verificando contenido de vectorstore {config.name}: {e}")
                return None
            
            # Crear retriever con configuración específica
            if config.retrieval.search_type == "mmr":
                retriever = vectorstore.as_retriever(
                    search_type="mmr",
                    search_kwargs={
                        "k": config.retrieval.k,
                        "fetch_k": config.retrieval.fetch_k,
                        "lambda_mult": config.retrieval.lambda_mult
                    }
                )
            else:
                retriever = vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={
                        "k": config.retrieval.k,
                        "score_threshold": config.retrieval.score_threshold
                    }
                )
            
            return retriever
            
        except Exception as e:
            logger.error(f"Error cargando retriever para {config.name}: {e}")
            return None
    
    def _create_rag_chain(self, config: RAGTopicConfig, retriever):
        """Crea cadena RAG con configuración específica"""
        try:
            # Crear prompt personalizado
            if config.system_prompt:
                system_template = config.system_prompt
            else:
                system_template = f"""Eres un asistente especializado en {config.display_name}.

{config.description}

Usa el siguiente contexto para responder la pregunta del usuario:

{{context}}

Pregunta: {{question}}
Respuesta:"""
            
            # Crear prompt template
            prompt = ChatPromptTemplate.from_template(system_template)
            
            # Crear cadena conversacional
            chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=retriever,
                return_source_documents=True,
                verbose=False,
                combine_docs_chain_kwargs={"prompt": prompt}
            )
            
            return chain
            
        except Exception as e:
            logger.error(f"Error creando cadena RAG para {config.name}: {e}")
            return None
    
    def query(self, question: str, topic: str, session_id: str, include_sources: bool = False) -> Tuple[str, Dict[str, Any]]:
        """Ejecuta consulta en un RAG específico"""
        
        # Verificar que el RAG existe
        if topic not in self.chains:
            raise AgentError(f"RAG no disponible: {topic}")
        
        # Obtener o crear historial de chat
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = ChatMessageHistory()
        
        chat_history = self.chat_histories[session_id]
        
        try:
            # Ejecutar consulta
            chain = self.chains[topic]
            result = chain({
                "question": question,
                "chat_history": chat_history.messages
            })
            
            # Extraer respuesta
            answer = result["answer"]
            
            # Preparar metadatos
            metadata = {
                "topic": topic,
                "num_sources": len(result.get("source_documents", [])),
                "session_id": session_id
            }
            
            # Incluir fuentes si se solicita
            if include_sources and "source_documents" in result:
                sources = []
                for doc in result["source_documents"]:
                    sources.append({
                        "content": doc.page_content[:500],  # Limitar tamaño
                        "metadata": doc.metadata
                    })
                metadata["sources"] = sources
            
            # Actualizar historial
            chat_history.add_user_message(question)
            chat_history.add_ai_message(answer)
            
            return answer, metadata
            
        except Exception as e:
            logger.error(f"Error en consulta RAG {topic}: {e}")
            raise handle_langchain_error(e)
    
    def get_available_topics(self) -> List[str]:
        """Obtiene lista de temáticas RAG disponibles"""
        return list(self.chains.keys())
    
    def health_check(self) -> Dict[str, Any]:
        """Health check del servicio RAG"""
        return {
            "status": "healthy" if self.chains else "degraded",
            "service_type": "dynamic_rag",
            "available_topics": len(self.chains),
            "loaded_configs": len(self.loaded_configs),
            "topics": list(self.chains.keys())
        }

class DynamicAgentService:
    """Servicio de agentes con carga dinámica basada en configuración"""
    
    def __init__(self, rag_service: DynamicRAGService):
        self.rag_service = rag_service
        self.settings = get_settings()
        
        # Componentes
        self.agent_loader = DynamicAgentLoader()
        self.agents: Dict[str, ConfigurableAgent] = {}
        
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
            
            for agent_name, agent_config in agents_data.items():
                if agent_config.get("enabled", True):
                    success = self._load_agent(agent_name)
                    if success:
                        logger.info(f"Agente cargado: {agent_name}")
                    else:
                        logger.warning(f"No se pudo cargar agente: {agent_name}")
            
        except Exception as e:
            logger.error(f"Error cargando agentes: {e}")
    
    def _load_agent(self, agent_name: str) -> bool:
        """Carga un agente específico"""
        try:
            # Cargar configuración del agente
            agent_config = config_manager.load_agent_config(agent_name)
            if not agent_config:
                logger.error(f"No se pudo cargar configuración para agente: {agent_name}")
                return False
            
            # Crear instancia del agente
            agent = self.agent_loader.create_agent(agent_config, self.rag_service)
            if not agent:
                logger.error(f"No se pudo crear instancia del agente: {agent_name}")
                return False
            
            # Registrar agente
            self.agents[agent_name] = agent
            return True
            
        except Exception as e:
            logger.error(f"Error cargando agente {agent_name}: {e}")
            return False
    
    def select_agent(self, question: str, context: Optional[Dict] = None) -> Tuple[ConfigurableAgent, float]:
        """Selecciona el agente más apropiado para una pregunta"""
        
        available_agents = [agent for agent in self.agents.values() if agent.config.enabled]
        
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
        
        # Ordenar por confianza
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        best_agent, best_confidence = agent_scores[0]
        
        logger.info(f"Agente seleccionado: {best_agent.name} (confianza: {best_confidence:.3f})")
        
        return best_agent, best_confidence
    
    async def process_question(
        self, 
        question: str, 
        session_id: str, 
        agent_type: Optional[str] = None,
        include_sources: bool = False,
        context: Optional[Dict] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Procesa una pregunta usando el agente apropiado"""
        
        try:
            # Seleccionar agente
            if agent_type:
                # Usar agente específico
                if agent_type not in self.agents:
                    raise AgentNotFoundError(f"Agente no encontrado: {agent_type}")
                agent = self.agents[agent_type]
                confidence = agent.can_handle(question, context)
            else:
                # Selección automática
                agent, confidence = self.select_agent(question, context)
            
            # Procesar pregunta
            answer, metadata = agent.process(
                question=question,
                session_id=session_id,
                include_sources=include_sources,
                context=context
            )
            
            # Enriquecer metadatos
            metadata.update({
                "agent_selection_confidence": confidence,
                "agent_selection_method": "manual" if agent_type else "automatic"
            })
            
            return answer, metadata
            
        except Exception as e:
            logger.error(f"Error procesando pregunta: {e}")
            raise
    
    def get_available_agents(self) -> List[ConfigurableAgent]:
        """Devuelve lista de agentes disponibles"""
        return [agent for agent in self.agents.values() if agent.config.enabled]
    
    def health_check(self) -> Dict[str, Any]:
        """Health check del servicio de agentes"""
        
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
            "agents": agent_health
        }

class DynamicAgentSystem:
    """Sistema completo de agentes y RAGs dinámicos"""
    
    def __init__(self):
        logger.info("Inicializando DynamicAgentSystem...")
        
        # Inicializar servicios
        self.rag_service = DynamicRAGService()
        self.agent_service = DynamicAgentService(self.rag_service)
        
        logger.info("DynamicAgentSystem inicializado exitosamente")
    
    async def process_question(
        self, 
        question: str, 
        session_id: str, 
        agent_type: Optional[str] = None,
        include_sources: bool = False,
        context: Optional[Dict] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Procesa una pregunta usando el sistema completo"""
        return await self.agent_service.process_question(
            question, session_id, agent_type, include_sources, context
        )
    
    def get_available_topics(self) -> List[str]:
        """Obtiene temáticas RAG disponibles"""
        return self.rag_service.get_available_topics()
    
    def get_available_agents(self) -> List[ConfigurableAgent]:
        """Obtiene agentes disponibles"""
        return self.agent_service.get_available_agents()
    
    def health_check(self) -> Dict[str, Any]:
        """Health check del sistema completo"""
        rag_health = self.rag_service.health_check()
        agent_health = self.agent_service.health_check()
        
        overall_status = "healthy"
        if rag_health["status"] != "healthy" or agent_health["status"] != "healthy":
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "rag_service": rag_health,
            "agent_service": agent_health,
            "system_info": {
                "available_topics": len(self.get_available_topics()),
                "available_agents": len(self.get_available_agents())
            }
        }