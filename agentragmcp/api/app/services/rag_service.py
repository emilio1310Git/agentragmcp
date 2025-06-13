import os
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Importar configuración de ChromaDB ANTES que cualquier otra cosa
from agentragmcp.core.chroma_config import configure_chroma

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger, chat_metrics, get_logger_with_context
from agentragmcp.core.exceptions import (
    VectorStoreError, 
    VectorStoreNotFoundError, 
    LLMError,
    RetrievalError,
    handle_langchain_error
)

class RAGService:
    """Servicio principal para gestión de RAG multi-temático"""
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = None
        self.llm = None
        self.retrievers = {}
        self.chains = {}
        self.chat_histories = {}
        
        # Configurar ChromaDB antes de cualquier inicialización
        configure_chroma()
        
        # Inicializar componentes
        self._initialize_embeddings()
        self._initialize_llm()
        self._initialize_retrievers()
        self._initialize_chains()
    
    def _initialize_embeddings(self):
        """Inicializa el modelo de embeddings"""
        try:
            self.embeddings = OllamaEmbeddings(
                model=self.settings.EMBEDDING_MODEL,
                base_url=self.settings.LLM_BASE_URL
            )
            logger.info(f"Embeddings inicializados: {self.settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            raise handle_langchain_error(e)
    
    def _initialize_llm(self):
        """Inicializa el modelo de lenguaje"""
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
    
    def _initialize_retrievers(self):
        """Inicializa los retrievers para cada temática"""
        for topic in self.settings.available_topics:
            try:
                retriever = self._load_retriever(topic)
                if retriever:
                    self.retrievers[topic] = retriever
                    logger.info(f"Retriever inicializado para temática: {topic}")
                else:
                    logger.warning(f"No se pudo cargar retriever para temática: {topic}")
            except Exception as e:
                logger.error(f"Error inicializando retriever para {topic}: {e}")
                # Continuar con otras temáticas
                continue
    
    def _load_retriever(self, topic: str):
        """Carga un retriever específico para una temática"""
        try:
            vectorstore_path = self.settings.get_vectorstore_path(topic)
            
            # Verificar que existe el directorio
            if not os.path.exists(vectorstore_path):
                logger.warning(f"Vectorstore no encontrado para {topic} en: {vectorstore_path}")
                return None
            
            # Verificar que tiene contenido (ChromaDB crea varios archivos)
            chroma_files = list(Path(vectorstore_path).glob("*"))
            if not chroma_files:
                logger.warning(f"Vectorstore vacío para {topic} en: {vectorstore_path}")
                return None
            
            # Cargar vectorstore con configuración mejorada
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=self.embeddings
            )
            
            # Verificar que tiene documentos
            try:
                test_results = vectorstore.similarity_search("test", k=1)
                if not test_results:
                    logger.warning(f"Vectorstore {topic} no contiene documentos")
                    return None
            except Exception as e:
                logger.warning(f"Error probando vectorstore {topic}: {e}")
                return None
            
            # Crear retriever con configuración optimizada
            retriever = vectorstore.as_retriever(
                search_type=self.settings.RETRIEVAL_TYPE,
                search_kwargs={
                    "k": self.settings.RETRIEVAL_K,
                    "score_threshold": 0.5  # Filtrar resultados con baja similaridad
                }
            )
            
            return retriever
            
        except Exception as e:
            logger.error(f"Error cargando retriever para {topic}: {e}")
            raise VectorStoreError(f"Error cargando vectorstore para {topic}: {str(e)}")
    
    def _initialize_chains(self):
        """Inicializa las cadenas RAG para cada temática"""
        for topic, retriever in self.retrievers.items():
            try:
                chain = self._create_rag_chain(topic, retriever)
                self.chains[topic] = chain
                logger.info(f"Cadena RAG inicializada para: {topic}")
            except Exception as e:
                logger.error(f"Error inicializando cadena para {topic}: {e}")
                continue
    
    def _create_rag_chain(self, topic: str, retriever):
        """Crea una cadena RAG para una temática específica"""
        
        # Prompt para contextualización de preguntas con historial
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
        
        # Prompt del sistema especializado por temática
        system_prompt = self._get_system_prompt(topic)
        
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
    
    def _get_system_prompt(self, topic: str) -> str:
        """Obtiene el prompt del sistema específico para cada temática"""
        
        base_prompt = """
Eres un asistente especializado llamado AgentRagMCP. 
Si no sabes la respuesta, simplemente di "No lo sé", pero no inventes una respuesta.
Las respuestas deben ser concisas, de máximo tres o cuatro párrafos.
Responde en castellano (español de España) a menos que se te pida explícitamente otro idioma.
Usa el contexto proporcionado y el historial de conversación para dar la mejor respuesta posible.

{context}
"""
        
        if topic == "plants":
            specific_prompt = """
Especialízate en información general sobre plantas, especialmente estas especies:
- Malus domestica, Prunus cerasus, Vitis vinifera, Citrus aurantium
- Prunus persica, Fragaria vesca, Solanum lycopersicum, Psidium guajava
- Syzygium cumini, Citrus limon, Mangifera indica, Punica granatum
- Prunus armeniaca, Vaccinium macrocarpon, Pyrus communis

Proporciona información sobre cultivo, cuidados, características botánicas y usos.
"""
        
        elif topic == "pathology":
            specific_prompt = """
Especialízate en patologías, enfermedades, tratamientos y problemas de estas especies:
- Malus domestica (manzano)
- Vitis vinifera (vid)
- Citrus aurantium (naranjo amargo)
- Solanum lycopersicum (tomate)

Incluye información sobre síntomas, diagnóstico, tratamientos y prevención.
"""
        
        elif topic == "general":
            specific_prompt = """
Proporciona información general sobre plantas, jardinería, botánica y agricultura.
Puedes responder preguntas amplias sobre el mundo vegetal.
"""
        
        else:
            specific_prompt = f"""
Especialízate en la temática: {topic}
Proporciona información específica y detallada sobre este tema.
"""
        
        return base_prompt + "\n" + specific_prompt
    
    def _get_session_history(self, session_id: str) -> BaseChatMessageHistory:
        """Obtiene o crea el historial para una sesión"""
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = ChatMessageHistory()
        return self.chat_histories[session_id]
    
    def query(
        self, 
        question: str, 
        topic: str, 
        session_id: str,
        include_sources: bool = False
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Realiza una consulta al RAG específico
        
        Args:
            question: Pregunta del usuario
            topic: Temática del RAG a usar
            session_id: ID de la sesión
            include_sources: Si incluir las fuentes en la respuesta
            
        Returns:
            Tuple con (respuesta, metadatos)
        """
        start_time = time.time()
        context_logger = get_logger_with_context(
            chat_session_id=session_id,
            topic=topic
        )
        
        try:
            # Verificar que existe la cadena para la temática
            if topic not in self.chains:
                available_topics = list(self.chains.keys())
                raise RetrievalError(
                    f"Temática '{topic}' no disponible. Disponibles: {available_topics}"
                )
            
            context_logger.info(f"Iniciando consulta RAG - Temática: {topic}")
            
            # Ejecutar la cadena
            chain = self.chains[topic]
            result = chain.invoke(
                {"input": question},
                config={"configurable": {"session_id": session_id}}
            )
            
            response_time = time.time() - start_time
            
            # Extraer información de la respuesta
            answer = result.get("answer", "No se pudo generar respuesta")
            context_docs = result.get("context", [])
            
            # Preparar metadatos
            metadata = {
                "topic": topic,
                "session_id": session_id,
                "response_time": response_time,
                "num_sources": len(context_docs),
                "sources": []
            }
            
            # Incluir fuentes si se solicita
            if include_sources and context_docs:
                metadata["sources"] = [
                    {
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in context_docs[:3]  # Limitar a 3 fuentes principales
                ]
            
            # Logging de métricas
            chat_metrics.log_chat_interaction(
                session_id=session_id,
                question=question,
                agent_type="rag",
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
            
            context_logger.info(f"Consulta RAG completada exitosamente - Tiempo: {response_time:.2f}s")
            
            return answer, metadata
            
        except Exception as e:
            response_time = time.time() - start_time
            
            # Logging de error
            context_logger.error(f"Error en consulta RAG: {str(e)}")
            chat_metrics.log_chat_interaction(
                session_id=session_id,
                question=question,
                agent_type="rag",
                topic=topic,
                response_time=response_time,
                success=False,
                error=str(e)
            )
            
            raise handle_langchain_error(e)
    
    def get_available_topics(self) -> List[str]:
        """Devuelve las temáticas disponibles"""
        return list(self.chains.keys())
    
    def health_check(self) -> Dict[str, Any]:
        """Realiza un health check del servicio RAG"""
        health_status = {
            "status": "healthy",
            "embeddings": "ok" if self.embeddings else "error",
            "llm": "ok" if self.llm else "error",
            "topics": {}
        }
        
        # Verificar cada temática
        for topic in self.settings.available_topics:
            topic_status = {
                "retriever": "ok" if topic in self.retrievers else "error",
                "chain": "ok" if topic in self.chains else "error",
                "vectorstore_path": self.settings.get_vectorstore_path(topic)
            }
            health_status["topics"][topic] = topic_status
        
        # Determinar estado general
        all_components_ok = (
            health_status["embeddings"] == "ok" and
            health_status["llm"] == "ok" and
            len(self.chains) > 0
        )
        
        health_status["status"] = "healthy" if all_components_ok else "degraded"
        
        return health_status
    
    def clear_session_history(self, session_id: str):
        """Limpia el historial de una sesión específica"""
        if session_id in self.chat_histories:
            del self.chat_histories[session_id]
            logger.info(f"Historial eliminado para sesión: {session_id}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Obtiene un resumen de la sesión"""
        if session_id not in self.chat_histories:
            return {"session_id": session_id, "messages": 0, "exists": False}
        
        history = self.chat_histories[session_id]
        return {
            "session_id": session_id,
            "messages": len(history.messages),
            "exists": True,
            "last_message": history.messages[-1] if history.messages else None
        }
    
    def reload_vectorstore(self, topic: str) -> bool:
        """Recarga un vectorstore específico"""
        try:
            logger.info(f"Recargando vectorstore para temática: {topic}")
            
            # Eliminar retriever y cadena existentes
            if topic in self.retrievers:
                del self.retrievers[topic]
            if topic in self.chains:
                del self.chains[topic]
            
            # Cargar nuevamente
            retriever = self._load_retriever(topic)
            if retriever:
                self.retrievers[topic] = retriever
                chain = self._create_rag_chain(topic, retriever)
                self.chains[topic] = chain
                logger.info(f"Vectorstore {topic} recargado exitosamente")
                return True
            else:
                logger.error(f"No se pudo recargar vectorstore para {topic}")
                return False
                
        except Exception as e:
            logger.error(f"Error recargando vectorstore {topic}: {e}")
            return False