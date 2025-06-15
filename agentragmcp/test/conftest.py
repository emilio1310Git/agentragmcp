"""
Configuración global para tests de AgentRagMCP
"""
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

from agentragmcp.api.app.main import create_application
from agentragmcp.core.config import get_settings

@pytest.fixture(scope="session")
def event_loop():
    """Fixture para el loop de eventos asyncio"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session") 
def temp_data_dir():
    """Directorio temporal para datos de test"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture(scope="session")
def test_settings(temp_data_dir):
    """Configuración de test"""
    import os
    
    # Configurar variables de entorno para testing
    os.environ.update({
        "ENVIRONMENT": "testing",
        "DEBUG": "true",
        "LOG_LEVEL": "debug",
        "VECTORSTORE_BASE_PATH": str(temp_data_dir / "vectorstores"),
        "LLM_BASE_URL": "http://localhost:11434",  # Asumir Ollama local
        # "LLM_MODEL": "llama3.1",
        "LLM_MODEL": "hdnh2006/salamandra-7b-instruct:latest",        
        "RAG_TOPICS": "plants,pathology,general",
        "MCP_ENABLED": "false"
    })
    
    return get_settings()

@pytest.fixture
def mock_embeddings():
    """Mock de embeddings para tests"""
    mock = MagicMock()
    mock.embed_documents.return_value = [[0.1, 0.2, 0.3] * 100]  # Vector de 300 dims
    mock.embed_query.return_value = [0.1, 0.2, 0.3] * 100
    return mock

@pytest.fixture
def mock_llm():
    """Mock de LLM para tests"""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content="Respuesta de prueba del LLM")
    return mock

@pytest.fixture
def mock_vectorstore():
    """Mock de vectorstore para tests"""
    mock = MagicMock()
    
    # Mock de documentos de ejemplo
    mock_doc = MagicMock()
    mock_doc.page_content = "Contenido de ejemplo sobre plantas"
    mock_doc.metadata = {"source": "test_document.pdf", "page": 1}
    
    mock.similarity_search.return_value = [mock_doc]
    mock.as_retriever.return_value = mock
    mock.get_relevant_documents.return_value = [mock_doc]
    
    return mock

@pytest.fixture
def mock_rag_service(mock_vectorstore, mock_llm):
    """Mock del servicio RAG"""
    from agentragmcp.api.app.services.rag_service import RAGService
    
    mock_service = MagicMock(spec=RAGService)
    mock_service.get_available_topics.return_value = ["plants", "pathology", "general"]
    
    # Mock del método query
    async def mock_query(question, topic, session_id, include_sources=False):
        return (
            f"Respuesta de prueba para '{question}' en topic '{topic}'",
            {
                "topic": topic,
                "session_id": session_id,
                "num_sources": 1,
                "sources": [{"content": "Fuente de prueba", "metadata": {}}] if include_sources else []
            }
        )
    
    mock_service.query = mock_query
    mock_service.clear_session_history = MagicMock()
    mock_service.get_session_summary = MagicMock(return_value={"messages": 0, "exists": False})
    mock_service.health_check = MagicMock(return_value={"status": "healthy"})
    
    return mock_service

@pytest.fixture
def mock_agent_service(mock_rag_service):
    """Mock del servicio de agentes"""
    from agentragmcp.api.app.services.agent_service import AgentService
    
    mock_service = MagicMock(spec=AgentService)
    
    # Mock de agentes disponibles
    mock_service.get_available_agents.return_value = [
        {"name": "plants", "description": "Especialista en plantas"},
        {"name": "pathology", "description": "Especialista en patologías"},
        {"name": "general", "description": "Asistente general"}
    ]
    
    # Mock del método process_question
    async def mock_process_question(question, session_id, agent_type=None, **kwargs):
        selected_agent = agent_type or "general"
        return (
            f"Respuesta del agente {selected_agent} para: {question}",
            {
                "agent_type": selected_agent,
                "agent_selection_confidence": 0.8,
                "topic": "plants" if selected_agent == "plants" else "general",
                "agent_selection_method": "manual" if agent_type else "automatic"
            }
        )
    
    mock_service.process_question = mock_process_question
    mock_service.health_check = MagicMock(return_value={"status": "healthy"})
    
    return mock_service

@pytest.fixture
def mock_mcp_service():
    """Mock del servicio MCP"""
    from agentragmcp.api.app.services.mcp_service import MCPService
    
    mock_service = MagicMock(spec=MCPService)
    mock_service.get_available_tools.return_value = []
    mock_service.health_check.return_value = {"status": "disabled", "enabled": False}
    
    return mock_service

@pytest.fixture
def app_with_mocks(mock_rag_service, mock_agent_service, mock_mcp_service, monkeypatch):
    """Aplicación FastAPI con servicios mockeados"""
    
    # Mockear los servicios globales en el módulo chat
    monkeypatch.setattr("agentragmcp.api.app.routers.chat.rag_service", mock_rag_service)
    monkeypatch.setattr("agentragmcp.api.app.routers.chat.agent_service", mock_agent_service)
    monkeypatch.setattr("agentragmcp.api.app.routers.chat.mcp_service", mock_mcp_service)
    
    # Crear aplicación
    app = create_application()
    return app

@pytest.fixture
def client(app_with_mocks):
    """Cliente de test para FastAPI"""
    with TestClient(app_with_mocks) as client:
        yield client

@pytest.fixture
def sample_questions():
    """Preguntas de ejemplo para tests"""
    return {
        "plants": [
            "¿Cómo cuidar un manzano?",
            "¿Cuándo plantar tomates?",
            "Características del Malus domestica",
        ],
        "pathology": [
            "¿Qué enfermedad tiene mi planta con hojas amarillas?",
            "¿Cómo tratar el mildiu en vid?",
            "Síntomas de infección por hongos",
        ],
        "general": [
            "¿Qué es la fotosíntesis?",
            "¿Cómo se clasifican las plantas?",
            "Diferencias entre monocotiledóneas y dicotiledóneas",
        ]
    }

@pytest.fixture
def sample_chat_requests():
    """Requests de chat de ejemplo"""
    return [
        {
            "question": "¿Cómo cuidar un manzano?",
            "session_id": "test-session-1"
        },
        {
            "question": "¿Qué enfermedad causa hojas amarillas?",
            "agent_type": "pathology",
            "include_sources": True
        },
        {
            "question": "¿Qué es la botánica?",
            "topic": "general"
        }
    ]

# Fixtures para tests de integración
@pytest.fixture
def real_settings():
    """Configuración real para tests de integración"""
    return get_settings()

@pytest.fixture
def ollama_available():
    """Verifica si Ollama está disponible para tests de integración"""
    import httpx
    
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get("http://localhost:11434/api/tags")
            return response.status_code == 200
    except:
        return False

@pytest.fixture
def skip_if_no_ollama(ollama_available):
    """Salta tests que requieren Ollama si no está disponible"""
    if not ollama_available:
        pytest.skip("Ollama no disponible - saltando test de integración")

# Fixtures para tests de datos
@pytest.fixture
def sample_documents():
    """Documentos de ejemplo para tests"""
    return [
        {
            "content": "El manzano (Malus domestica) es un árbol frutal...",
            "metadata": {"source": "manual_fruticultura.pdf", "topic": "plants"}
        },
        {
            "content": "El mildiu es una enfermedad fúngica que afecta...",
            "metadata": {"source": "guia_patologias.pdf", "topic": "pathology"}
        },
        {
            "content": "La fotosíntesis es el proceso por el cual las plantas...",
            "metadata": {"source": "botanica_general.pdf", "topic": "general"}
        }
    ]

@pytest.fixture
def create_test_vectorstore(temp_data_dir, sample_documents):
    """Helper para crear vectorstores de test"""
    def _create_vectorstore(topic: str):
        vectorstore_path = temp_data_dir / "vectorstores" / topic
        vectorstore_path.mkdir(parents=True, exist_ok=True)
        
        # Simular la creación de un vectorstore con datos de ejemplo
        # En un test real, aquí crearías un vectorstore de Chroma
        return str(vectorstore_path)
    
    return _create_vectorstore