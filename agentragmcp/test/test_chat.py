"""
Tests para los endpoints de chat de AgentRagMCP
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock

class TestChatEndpoints:
    """Tests para los endpoints principales de chat"""
    
    def test_chat_endpoint_basic(self, client):
        """Test básico del endpoint de chat"""
        
        response = client.post(
            "/chat/",
            json={
                "question": "¿Cómo cuidar un manzano?",
                "session_id": "test-session"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "answer" in data
        assert "session_id" in data
        assert "agent_type" in data
        assert "topic" in data
        assert data["session_id"] == "test-session"
    
    def test_chat_endpoint_automatic_session(self, client):
        """Test que se crea sesión automáticamente si no se proporciona"""
        
        response = client.post(
            "/chat/",
            json={
                "question": "¿Qué es la fotosíntesis?"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["session_id"] is not None
        assert len(data["session_id"]) > 10  # UUID tiene más de 10 caracteres
    
    def test_chat_endpoint_with_agent_type(self, client):
        """Test especificando tipo de agente"""
        
        response = client.post(
            "/chat/",
            json={
                "question": "¿Cómo tratar enfermedades?",
                "agent_type": "pathology"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["agent_type"] == "pathology"
    
    def test_chat_endpoint_with_sources(self, client):
        """Test incluyendo fuentes en la respuesta"""
        
        response = client.post(
            "/chat/",
            json={
                "question": "¿Cómo plantar tomates?",
                "include_sources": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sources" in data
        assert isinstance(data["sources"], list)
    
    def test_chat_endpoint_invalid_agent(self, client):
        """Test con tipo de agente inválido"""
        
        response = client.post(
            "/chat/",
            json={
                "question": "¿Cómo plantar?",
                "agent_type": "invalid_agent"
            }
        )
        
        assert response.status_code == 400  # Bad Request
    
    def test_chat_endpoint_empty_question(self, client):
        """Test con pregunta vacía"""
        
        response = client.post(
            "/chat/",
            json={
                "question": ""
            }
        )
        
        assert response.status_code == 422  # Validation Error
    
    def test_chat_endpoint_too_long_question(self, client):
        """Test con pregunta demasiado larga"""
        
        long_question = "¿Cómo cuidar plantas? " * 200  # > 2000 caracteres
        
        response = client.post(
            "/chat/",
            json={
                "question": long_question
            }
        )
        
        assert response.status_code == 422  # Validation Error

class TestRAGQueryEndpoint:
    """Tests para el endpoint de consulta directa a RAG"""
    
    def test_rag_query_basic(self, client):
        """Test básico de consulta RAG"""
        
        response = client.post(
            "/chat/rag/query",
            json={
                "query": "información sobre plantas",
                "topic": "plants"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "documents" in data
        assert "topic" in data
        assert "total_results" in data
        assert data["topic"] == "plants"
    
    def test_rag_query_invalid_topic(self, client):
        """Test con topic inválido"""
        
        response = client.post(
            "/chat/rag/query",
            json={
                "query": "información general",
                "topic": "invalid_topic"
            }
        )
        
        assert response.status_code == 400  # Bad Request
    
    def test_rag_query_all_topics(self, client):
        """Test con todos los topics válidos"""
        
        topics = ["plants", "pathology", "general"]
        
        for topic in topics:
            response = client.post(
                "/chat/rag/query",
                json={
                    "query": f"información sobre {topic}",
                    "topic": topic
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["topic"] == topic

class TestAgentSelectionEndpoint:
    """Tests para el endpoint de selección de agentes"""
    
    def test_agent_selection_basic(self, client):
        """Test básico de selección de agente"""
        
        response = client.post(
            "/chat/agent/select",
            json={
                "question": "¿Cómo cuidar plantas?"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "selected_agent" in data
        assert "confidence" in data
        assert "reasoning" in data
        assert 0.0 <= data["confidence"] <= 1.0
    
    def test_agent_selection_pathology_question(self, client):
        """Test selección para pregunta de patología"""
        
        response = client.post(
            "/chat/agent/select",
            json={
                "question": "¿Qué enfermedad tiene mi planta?"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Debería seleccionar el agente de patología
        assert data["selected_agent"] == "pathology"
        assert data["confidence"] > 0.5

class TestTopicsAndAgentsEndpoints:
    """Tests para endpoints de información"""
    
    def test_get_topics(self, client):
        """Test obtener temáticas disponibles"""
        
        response = client.get("/chat/topics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert "plants" in data
        assert "pathology" in data  
        assert "general" in data
    
    def test_get_agents(self, client):
        """Test obtener agentes disponibles"""
        
        response = client.get("/chat/agents")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Verificar estructura de cada agente
        for agent in data:
            assert "name" in agent
            assert "description" in agent
            assert "topics" in agent

class TestSessionManagement:
    """Tests para gestión de sesiones"""
    
    def test_clear_session(self, client):
        """Test limpiar historial de sesión"""
        
        session_id = "test-session-clear"
        
        # Primero hacer una pregunta para crear la sesión
        client.post(
            "/chat/",
            json={
                "question": "¿Cómo plantar?",
                "session_id": session_id
            }
        )
        
        # Luego limpiar la sesión
        response = client.delete(f"/chat/session/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert session_id in data["message"]
    
    def test_get_session_info(self, client):
        """Test obtener información de sesión"""
        
        session_id = "test-session-info"
        
        # Crear sesión con una pregunta
        client.post(
            "/chat/",
            json={
                "question": "¿Cómo cuidar plantas?",
                "session_id": session_id
            }
        )
        
        # Obtener información de la sesión
        response = client.get(f"/chat/session/{session_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data or "messages" in data

class TestErrorHandling:
    """Tests para manejo de errores"""
    
    def test_malformed_json(self, client):
        """Test con JSON malformado"""
        
        response = client.post(
            "/chat/",
            data="{'malformed': json}",  # JSON inválido
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, client):
        """Test con campos requeridos faltantes"""
        
        response = client.post(
            "/chat/",
            json={}  # Sin campo 'question'
        )
        
        assert response.status_code == 422  # Validation Error
    
    def test_invalid_data_types(self, client):
        """Test con tipos de datos inválidos"""
        
        response = client.post(
            "/chat/",
            json={
                "question": 123,  # Debería ser string
                "include_sources": "yes"  # Debería ser boolean
            }
        )
        
        assert response.status_code == 422  # Validation Error

class TestResponseValidation:
    """Tests para validación de respuestas"""
    
    def test_chat_response_structure(self, client):
        """Test estructura completa de respuesta de chat"""
        
        response = client.post(
            "/chat/",
            json={
                "question": "¿Cómo cuidar plantas?",
                "include_sources": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Campos obligatorios
        required_fields = [
            "answer", "session_id", "agent_type", "topic"
        ]
        
        for field in required_fields:
            assert field in data, f"Campo requerido '{field}' no encontrado"
        
        # Campos opcionales que deberían estar presentes
        optional_fields = ["confidence", "sources", "response_time", "metadata"]
        
        for field in optional_fields:
            if field in data:
                # Verificar tipo correcto
                if field == "confidence":
                    assert isinstance(data[field], (int, float))
                    assert 0.0 <= data[field] <= 1.0
                elif field == "sources":
                    assert isinstance(data[field], list)
                elif field == "response_time":
                    assert isinstance(data[field], (int, float))
                    assert data[field] >= 0
                elif field == "metadata":
                    assert isinstance(data[field], dict)
    
    def test_rag_query_response_structure(self, client):
        """Test estructura de respuesta RAG"""
        
        response = client.post(
            "/chat/rag/query",
            json={
                "query": "información sobre plantas",
                "topic": "plants"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        required_fields = [
            "documents", "query", "topic", "total_results", "retrieval_time"
        ]
        
        for field in required_fields:
            assert field in data, f"Campo requerido '{field}' no encontrado"
        
        # Verificar tipos
        assert isinstance(data["documents"], list)
        assert isinstance(data["query"], str)
        assert isinstance(data["topic"], str)
        assert isinstance(data["total_results"], int)
        assert isinstance(data["retrieval_time"], (int, float))

class TestConcurrency:
    """Tests para manejo de concurrencia"""
    
    def test_multiple_simultaneous_requests(self, client):
        """Test múltiples requests simultáneas"""
        import concurrent.futures
        import threading
        
        def make_request(question_num):
            return client.post(
                "/chat/",
                json={
                    "question": f"¿Pregunta número {question_num}?",
                    "session_id": f"session-{question_num}"
                }
            )
        
        # Hacer 5 requests simultáneas
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i) for i in range(5)]
            responses = [future.result() for future in futures]
        
        # Todas deberían ser exitosas
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "session_id" in data

@pytest.mark.integration
class TestChatIntegration:
    """Tests de integración que requieren servicios reales"""
    
    @pytest.mark.skipif(
        not pytest.config.option.integration,
        reason="Requiere --integration flag"
    )
    def test_real_ollama_integration(self, real_settings, skip_if_no_ollama):
        """Test de integración real con Ollama"""
        
        # Este test solo se ejecuta con --integration y si Ollama está disponible
        from agentragmcp.api.app.main import create_application
        
        app = create_application()
        
        with TestClient(app) as client:
            response = client.post(
                "/chat/",
                json={
                    "question": "¿Qué es una planta?",
                    "include_sources": False
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            # Verificar que realmente hay una respuesta del LLM
            assert len(data["answer"]) > 50  # Respuesta sustancial
            assert "planta" in data["answer"].lower()

# Configuración para tests de integración
def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true", 
        default=False,
        help="Ejecutar tests de integración"
    )