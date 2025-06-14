"""
RAGService actualizado con configuración dinámica
Carga RAGs basándose en archivos de configuración personalizados
"""
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# Importar nuestro gestor de configuración
from agentragmcp.core.dynamic_config import config_manager, RAGTopicConfig
from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger, chat_metrics, get_logger_with_context
from agentragmcp.core.exceptions import (
    VectorStoreError, VectorStoreNotFoundError, LLMError,
    RetrievalError, handle_langchain_error
)

class DynamicRAGService:
    """Servicio RAG con configuración dinámica y carga automática"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.settings = get_settings()
        
        # Configurar el gestor de configuración
        if config_path:
            global config_manager
            from agentragmcp.core.dynamic_config import ConfigManager
            config_manager = ConfigManager(config_path)
        
        # Componentes principales
        self.embeddings_cache: Dict[str, OllamaEmbeddings] = {}
        self.llm = None
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
        if not config_manager.discover_rag_configs():
            logger.info("No se encontraron configuraciones, creando ejemplos...")
            config_manager.create_sample_configs()
        
        # Cargar todas las configuraciones disponibles
        topic_names = config_manager.discover_rag_configs()
        
        for topic_name in topic_names:
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
                    logger.warning(f"Vectorstore {config.name} no contiene documentos")
                    return None
            except Exception as e:
                logger.warning(f"Error probando vectorstore {config.name}: {e}")
                return None
            
            # Crear retriever con configuración específica
            search_kwargs = {
                "k": config.retrieval.k
            }
            
            # Configuración específica según tipo de búsqueda
            if config.retrieval.search_type == "mmr":
                search_kwargs.update({
                    "fetch_k": config.retrieval.fetch_k,
                    "lambda_mult": config.retrieval.lambda_mult
                })
            elif config.retrieval.search_type == "similarity_score_threshold":
                search_kwargs["score_threshold"] = config.retrieval.score_threshold
            
            retriever = vectorstore.as_retriever(
                search_type=config.retrieval.search_type,
                search_kwargs=search_kwargs
            )
            
            return retriever
            
        except Exception as e:
            logger.error(f"Error cargando retriever para {config.name}: {e}")
            raise VectorStoreError(f"Error cargando vectorstore para {config.name}: {str(e)}")
    
    def _create_rag_chain(self, config: RAGTopicConfig, retriever):
        """Crea cadena RAG con configuración personalizada"""
        
        # Prompt para contextualización (estándar)
        contextualize_q_system_prompt = (
            "Dado un historial de chat y la última pregunta del usuario "
            "que podría hacer referencia al contexto en el historial de chat, "
            "formular una pregunta independiente que pueda entenderse "
            "sin el historial de chat. NO respondas la pregunta, "
            "simplemente reformúlala si es necesario y, en caso contrario, devuélvela tal como está."
        )
        
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # Crear retriever consciente del historial
        history_aware_retriever = create_history_aware_retriever(
            self.llm, 
            retriever, 
            contextualize_q_prompt
        )
        
        # Usar prompt personalizado si está configurado
        system_prompt = config.system_prompt if config.system_prompt else self._get_default_prompt(config.name)
        
        # Reemplazar template de contexto si está personalizado
        if config.context_template and "{context}" not in system_prompt:
            system_prompt += f"\n\n{config.context_template}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        # Crear cadenas
        question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        
        # Crear cadena con historial
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            self._get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        
        return conversational_rag_chain
    
    def _get_default_prompt(self, topic_name: str) -> str:
        """Obtiene prompt por defecto para una temática"""
        base_prompt = """
Eres un asistente especializado llamado AgentRagMCP. 
Si no sabes la respuesta, simplemente di "No lo sé", pero no inventes una respuesta.
Las respuestas deben ser concisas, de máximo tres o cuatro párrafos.
Responde en castellano (español de España) a menos que se te pida explícitamente otro idioma.
Usa el contexto proporcionado y el historial de conversación para dar la mejor respuesta posible.

{context}
"""
        return base_prompt
    
    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Obtiene o crea historial para una sesión"""
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = ChatMessageHistory()
        return self.chat_histories[session_id]
    
    def check_and_reload_configs(self) -> List[str]:
        """Verifica y recarga configuraciones si han cambiado"""
        current_time = time.time()
        
        # Solo verificar periódicamente
        if current_time - self.last_config_check < self.config_check_interval:
            return []
        
        self.last_config_check = current_time
        
        # Verificar cambios
        reloaded = config_manager.reload_if_changed()
        
        if reloaded:
            logger.info(f"Recargando RAGs debido a cambios: {reloaded}")
            
            # Recargar RAGs afectados
            for item in reloaded:
                if item.startswith("rag:"):
                    topic_name = item.split(":", 1)[1]
                    # Limpiar y recargar
                    if topic_name in self.chains:
                        del self.chains[topic_name]
                    if topic_name in self.retrievers:
                        del self.retrievers[topic_name]
                    
                    self._load_rag_topic(topic_name)
        
        return reloaded
    
    def query(
        self, 
        question: str, 
        topic: str, 
        session_id: str,
        include_sources: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Realiza consulta con verificación automática de configuración
        """
        start_time = time.time()
        context_logger = get_logger_with_context(
            chat_session_id=session_id,
            topic=topic
        )
        
        try:
            # Verificar y recargar configuraciones si es necesario
            self.check_and_reload_configs()
            
            # Verificar que existe la cadena
            if topic not in self.chains:
                available_topics = list(self.chains.keys())
                raise RetrievalError(
                    f"Temática '{topic}' no disponible. Disponibles: {available_topics}"
                )
            
            context_logger.info(f"Consulta RAG dinámica - Temática: {topic}")
            
            # Obtener configuración específica
            config = self.loaded_configs.get(topic)
            
            # Ejecutar cadena
            chain = self.chains[topic]
            result = chain.invoke(
                {"input": question},
                config={"configurable": {"session_id": session_id}}
            )
            
            response_time = time.time() - start_time
            
            # Extraer información
            answer = result.get("answer", "No se pudo generar respuesta")
            context_docs = result.get("context", [])
            
            # Preparar metadatos con información de configuración
            metadata = {
                "topic": topic,
                "session_id": session_id,
                "response_time": response_time,
                "num_sources": len(context_docs),
                "sources": [],
                "rag_config": {
                    "display_name": config.display_name if config else topic,
                    "search_type": config.retrieval.search_type if config else "unknown",
                    "k": config.retrieval.k if config else "unknown",
                    "model": config.vectorstore.embedding_model if config else "unknown"
                }
            }
            
            # Incluir fuentes si se solicita
            if include_sources and context_docs:
                metadata["sources"] = [
                    {
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in context_docs[:3]
                ]
            
            # Logging de métricas
            chat_metrics.log_chat_interaction(
                session_id=session_id,
                question=question,
                agent_type="dynamic_rag",
                topic=topic,
                response_time=response_time,
                success=True
            )
            
            chat_metrics.log_rag_retrieval(
                session_id=session_id,
                topic=topic,
                query=question,
                num_results=len(context_docs),
                retrieval_time=response_time
            )
            
            context_logger.info(f"Consulta RAG dinámica completada - Tiempo: {response_time:.2f}s")
            
            return answer, metadata
            
        except Exception as e:
            response_time = time.time() - start_time
            context_logger.error(f"Error en consulta RAG dinámica: {str(e)}")
            chat_metrics.log_chat_interaction(
                session_id=session_id,
                question=question,
                agent_type="dynamic_rag",
                topic=topic,
                response_time=response_time,
                success=False,
                error=str(e)
            )
            raise handle_langchain_error(e)
    
    def get_available_topics(self) -> List[str]:
        """Devuelve temáticas disponibles con recarga automática"""
        self.check_and_reload_configs()
        return list(self.chains.keys())
    
    def get_topic_info(self, topic: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada de una temática"""
        config = self.loaded_configs.get(topic)
        if not config:
            return None
        
        return {
            "name": config.name,
            "display_name": config.display_name,
            "description": config.description,
            "enabled": config.enabled,
            "priority": config.priority,
            "categories": config.categories,
            "keywords": config.keywords,
            "vectorstore_config": {
                "type": config.vectorstore.type,
                "path": config.vectorstore.path,
                "chunk_size": config.vectorstore.chunk_size,
                "embedding_model": config.vectorstore.embedding_model
            },
            "retrieval_config": {
                "search_type": config.retrieval.search_type,
                "k": config.retrieval.k,
                "score_threshold": config.retrieval.score_threshold
            },
            "custom_settings": config.custom_settings
        }
    
    def get_all_topics_info(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene información de todas las temáticas"""
        return {
            topic: self.get_topic_info(topic)
            for topic in self.get_available_topics()
        }
    
    def add_new_rag(self, topic_name: str, config_data: Dict[str, Any]) -> bool:
        """Añade un nuevo RAG dinámicamente"""
        try:
            # Guardar configuración
            rags_path = config_manager.config_base_path / "rags"
            config_file = rags_path / f"{topic_name}.yaml"
            
            import yaml
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            # Cargar inmediatamente
            success = self._load_rag_topic(topic_name)
            
            if success:
                logger.info(f"Nuevo RAG añadido: {topic_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error añadiendo nuevo RAG {topic_name}: {e}")
            return False
    
    def reload_rag(self, topic_name: str) -> bool:
        """Recarga un RAG específico"""
        try:
            # Limpiar configuración actual
            if topic_name in self.chains:
                del self.chains[topic_name]
            if topic_name in self.retrievers:
                del self.retrievers[topic_name]
            if topic_name in self.loaded_configs:
                del self.loaded_configs[topic_name]
            
            # Recargar
            return self._load_rag_topic(topic_name)
            
        except Exception as e:
            logger.error(f"Error recargando RAG {topic_name}: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Health check del servicio RAG dinámico"""
        health_status = {
            "status": "healthy",
            "service_type": "dynamic_rag",
            "embeddings_cache": len(self.embeddings_cache),
            "llm": "ok" if self.llm else "error",
            "topics": {}
        }
        
        # Verificar cada temática
        for topic_name in self.get_available_topics():
            config = self.loaded_configs.get(topic_name)
            topic_status = {
                "retriever": "ok" if topic_name in self.retrievers else "error",
                "chain": "ok" if topic_name in self.chains else "error",
                "config_loaded": config is not None,
                "enabled": config.enabled if config else False,
                "vectorstore_path": config.vectorstore.path if config else "unknown"
            }
            health_status["topics"][topic_name] = topic_status
        
        # Determinar estado general
        active_topics = len([t for t in health_status["topics"].values() 
                           if t["retriever"] == "ok" and t["chain"] == "ok"])
        
        if active_topics == 0:
            health_status["status"] = "unhealthy"
        elif active_topics < len(health_status["topics"]):
            health_status["status"] = "degraded"
        
        health_status["active_topics"] = active_topics
        health_status["total_configured"] = len(health_status["topics"])
        
        return health_status
    
    def clear_session_history(self, session_id: str):
        """Limpia historial de sesión"""
        if session_id in self.chat_histories:
            del self.chat_histories[session_id]
            logger.info(f"Historial eliminado para sesión: {session_id}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Obtiene resumen de sesión"""
        if session_id not in self.chat_histories:
            return {"session_id": session_id, "messages": 0, "exists": False}
        
        history = self.chat_histories[session_id]
        return {
            "session_id": session_id,
            "messages": len(history.messages),
            "exists": True,
            "last_message": history.messages[-1] if history.messages else None
        }