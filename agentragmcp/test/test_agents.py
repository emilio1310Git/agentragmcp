"""
Tests para los agentes especializados de AgentRagMCP
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from agentragmcp.api.app.agents.plants_agent import PlantsAgent
from agentragmcp.api.app.agents.pathology_agent import PathologyAgent
from agentragmcp.api.app.agents.general_agent import GeneralAgent
from agentragmcp.api.app.services.agent_service import AgentService, AgentSelector

class TestPlantsAgent:
    """Tests para el agente especializado en plantas"""
    
    @pytest.fixture
    def plants_agent(self, mock_rag_service):
        return PlantsAgent(mock_rag_service)
    
    def test_can_handle_plant_questions(self, plants_agent):
        """Test que el agente puede manejar preguntas sobre plantas"""
        
        # Preguntas que SÍ debe manejar con alta confianza
        plant_questions = [
            "¿Cómo cuidar un manzano?",
            "¿Cuándo plantar tomates?",
            "Características del Malus domestica",
            "¿Qué necesita una planta para crecer?",
            "Técnicas de poda para frutales"
        ]
        
        for question in plant_questions:
            confidence = plants_agent.can_handle(question)
            assert confidence > 0.5, f"Baja confianza para pregunta de plantas: {question}"
    
    def test_rejects_pathology_questions(self, plants_agent):
        """Test que el agente rechaza preguntas de patologías"""
        
        pathology_questions = [
            "¿Qué enfermedad tiene mi planta?",
            "¿Cómo tratar el mildiu?",
            "Síntomas de infección por hongos",
            "Mi planta está enferma"
        ]
        
        for question in pathology_questions:
            confidence = plants_agent.can_handle(question)
            assert confidence < 0.7, f"Alta confianza para pregunta de patología: {question}"
    
    def test_species_recognition(self, plants_agent):
        """Test reconocimiento de especies específicas"""
        
        species_questions = [
            "Cuidados del Malus domestica",
            "¿Cómo cultivar Vitis vinifera?",
            "Información sobre Solanum lycopersicum"
        ]
        
        for question in species_questions:
            confidence = plants_agent.can_handle(question)
            assert confidence > 0.6, f"No reconoce especie en: {question}"
    
    @pytest.mark.asyncio
    async def test_process_question(self, plants_agent, mock_rag_service):
        """Test procesamiento de pregunta"""
        
        question = "¿Cómo cuidar un manzano?"
        session_id = "test-session"
        
        # Configurar mock del RAG service
        mock_rag_service.query = AsyncMock(return_value=(
            "Para cuidar un manzano necesitas...",
            {"topic": "plants", "num_sources": 2}
        ))
        
        answer, metadata = await plants_agent.process(question, session_id)
        
        assert "manzano" in answer.lower() or "cuidar" in answer.lower()
        assert metadata["agent_type"] == "plants"
        assert metadata["topic"] == "plants"

class TestPathologyAgent:
    """Tests para el agente especializado en patologías"""
    
    @pytest.fixture
    def pathology_agent(self, mock_rag_service):
        return PathologyAgent(mock_rag_service)
    
    def test_can_handle_pathology_questions(self, pathology_agent):
        """Test que el agente puede manejar preguntas sobre patologías"""
        
        pathology_questions = [
            "¿Qué enfermedad tiene mi planta?",
            "¿Cómo tratar el mildiu en vid?",
            "Síntomas de oídio en tomate",
            "Mi planta tiene hojas amarillas",
            "Control de plagas en manzano"
        ]
        
        for question in pathology_questions:
            confidence = pathology_agent.can_handle(question)
            assert confidence > 0.6, f"Baja confianza para pregunta de patología: {question}"
    
    def test_disease_recognition(self, pathology_agent):
        """Test reconocimiento de enfermedades específicas"""
        
        disease_questions = [
            "¿Cómo tratar el mildiu?",
            "Síntomas de oídio",
            "Información sobre botritis",
            "Control de fusarium"
        ]
        
        for question in disease_questions:
            confidence = pathology_agent.can_handle(question)
            assert confidence > 0.7, f"No reconoce enfermedad en: {question}"
    
    def test_symptom_recognition(self, pathology_agent):
        """Test reconocimiento de síntomas"""
        
        symptom_questions = [
            "Mi planta tiene manchas en las hojas",
            "¿Por qué se están amarillando las hojas?",
            "Hojas con puntos negros",
            "La planta se está marchitando"
        ]
        
        for question in symptom_questions:
            confidence = pathology_agent.can_handle(question)
            assert confidence > 0.5, f"No reconoce síntomas en: {question}"
    
    @pytest.mark.asyncio
    async def test_process_pathology_question(self, pathology_agent, mock_rag_service):
        """Test procesamiento de pregunta de patología"""
        
        question = "¿Cómo tratar el mildiu en vid?"
        session_id = "test-session"
        
        mock_rag_service.query = AsyncMock(return_value=(
            "El mildiu se puede tratar con fungicidas...",
            {"topic": "pathology", "num_sources": 3}
        ))
        
        answer, metadata = await pathology_agent.process(question, session_id)
        
        assert "mildiu" in answer.lower() or "tratar" in answer.lower()
        assert metadata["agent_type"] == "pathology"
        assert metadata["topic"] == "pathology"

class TestGeneralAgent:
    """Tests para el agente general"""
    
    @pytest.fixture
    def general_agent(self, mock_rag_service):
        return GeneralAgent(mock_rag_service)
    
    def test_can_handle_general_questions(self, general_agent):
        """Test que el agente puede manejar preguntas generales"""
        
        general_questions = [
            "¿Qué es la fotosíntesis?",
            "¿Cómo se clasifican las plantas?",
            "¿Por qué las plantas son verdes?",
            "Diferencias entre monocotiledóneas y dicotiledóneas",
            "¿Qué es la botánica?"
        ]
        
        for question in general_questions:
            confidence = general_agent.can_handle(question)
            assert confidence > 0.2, f"No puede manejar pregunta general: {question}"
    
    def test_fallback_behavior(self, general_agent):
        """Test comportamiento como agente fallback"""
        
        # Incluso preguntas no relacionadas deben tener confianza mínima
        random_questions = [
            "¿Cuál es la capital de Francia?",
            "¿Cómo cocinar pasta?",
            "¿Qué hora es?"
        ]
        
        for question in random_questions:
            confidence = general_agent.can_handle(question)
            assert confidence >= 0.1, f"Confianza demasiado baja para fallback: {question}"
    
    def test_educational_questions_bonus(self, general_agent):
        """Test que preguntas educativas tienen bonus de confianza"""
        
        educational_questions = [
            "¿Qué es la botánica?",
            "Explícame la fotosíntesis",
            "¿Cómo funciona la reproducción en plantas?",
            "Definición de taxonomía vegetal"
        ]
        
        for question in educational_questions:
            confidence = general_agent.can_handle(question)
            assert confidence > 0.4, f"Baja confianza para pregunta educativa: {question}"
    
    @pytest.mark.asyncio
    async def test_process_general_question(self, general_agent, mock_rag_service):
        """Test procesamiento de pregunta general"""
        
        question = "¿Qué es la fotosíntesis?"
        session_id = "test-session"
        
        mock_rag_service.query = AsyncMock(return_value=(
            "La fotosíntesis es el proceso por el cual...",
            {"topic": "general", "num_sources": 1}
        ))
        
        answer, metadata = await general_agent.process(question, session_id)
        
        assert "fotosíntesis" in answer.lower()
        assert metadata["agent_type"] == "general"
        assert metadata["topic"] == "general"

class TestAgentSelector:
    """Tests para el selector de agentes"""
    
    @pytest.fixture
    def agent_selector(self):
        return AgentSelector()
    
    @pytest.fixture
    def mock_agents(self, mock_rag_service):
        """Agentes mock para testing"""
        return [
            PlantsAgent(mock_rag_service),
            PathologyAgent(mock_rag_service), 
            GeneralAgent(mock_rag_service)
        ]
    
    def test_select_plants_agent(self, agent_selector, mock_agents):
        """Test selección del agente de plantas"""
        
        plant_questions = [
            "¿Cómo cuidar un manzano?",
            "¿Cuándo plantar tomates?",
            "Información sobre Malus domestica"
        ]
        
        for question in plant_questions:
            agent, confidence = agent_selector.select_agent(question, mock_agents)
            assert agent.name == "plants", f"No seleccionó agente de plantas para: {question}"
            assert confidence > 0.5, f"Baja confianza para selección: {confidence}"
    
    def test_select_pathology_agent(self, agent_selector, mock_agents):
        """Test selección del agente de patologías"""
        
        pathology_questions = [
            "¿Qué enfermedad tiene mi planta?",
            "¿Cómo tratar el mildiu?",
            "Mi planta tiene hojas amarillas"
        ]
        
        for question in pathology_questions:
            agent, confidence = agent_selector.select_agent(question, mock_agents)
            assert agent.name == "pathology", f"No seleccionó agente de patología para: {question}"
            assert confidence > 0.5, f"Baja confianza para selección: {confidence}"
    
    def test_fallback_to_general(self, agent_selector, mock_agents):
        """Test que preguntas ambiguas van al agente general"""
        
        ambiguous_questions = [
            "¿Qué es la botánica?",
            "Información sobre plantas",
            "Pregunta muy vaga"
        ]
        
        for question in ambiguous_questions:
            agent, confidence = agent_selector.select_agent(question, mock_agents)
            # Puede ir a plants o general, pero no a pathology
            assert agent.name in ["plants", "general"], f"Selección incorrecta para: {question}"

class TestAgentService:
    """Tests para el servicio de agentes"""
    
    @pytest.fixture
    def agent_service(self, mock_rag_service):
        return AgentService(mock_rag_service)
    
    def test_agent_initialization(self, agent_service):
        """Test inicialización correcta de agentes"""
        
        assert "plants" in agent_service.agents
        assert "pathology" in agent_service.agents
        assert "general" in agent_service.agents
        
        assert len(agent_service.agents) == 3
    
    def test_get_available_agents(self, agent_service):
        """Test obtener agentes disponibles"""
        
        agents = agent_service.get_available_agents()
        
        assert len(agents) == 3
        assert all("name" in agent for agent in agents)
        assert all("description" in agent for agent in agents)
        assert all("topics" in agent for agent in agents)
    
    @pytest.mark.asyncio
    async def test_process_question_with_agent_type(self, agent_service, mock_rag_service):
        """Test procesamiento con tipo de agente específico"""
        
        question = "¿Cómo cuidar plantas?"
        session_id = "test-session"
        agent_type = "plants"
        
        # Mock del RAG service
        mock_rag_service.query = AsyncMock(return_value=(
            "Para cuidar plantas necesitas...",
            {"topic": "plants", "num_sources": 1}
        ))
        
        answer, metadata = await agent_service.process_question(
            question=question,
            session_id=session_id,
            agent_type=agent_type
        )
        
        assert "cuidar" in answer.lower() or "plantas" in answer.lower()
        assert metadata["agent_type"] == "plants"
        assert metadata["agent_selection_method"] == "manual"
        assert metadata["agent_selection_confidence"] == 1.0
    
    @pytest.mark.asyncio
    async def test_process_question_automatic_selection(self, agent_service, mock_rag_service):
        """Test procesamiento con selección automática"""
        
        question = "¿Qué enfermedad causa hojas amarillas?"
        session_id = "test-session"
        
        mock_rag_service.query = AsyncMock(return_value=(
            "Las hojas amarillas pueden indicar...",
            {"topic": "pathology", "num_sources": 2}
        ))
        
        answer, metadata = await agent_service.process_question(
            question=question,
            session_id=session_id
        )
        
        assert "amarillas" in answer.lower() or "hojas" in answer.lower()
        assert metadata["agent_type"] == "pathology"
        assert metadata["agent_selection_method"] == "automatic"
        assert metadata["agent_selection_confidence"] > 0.0
    
    def test_health_check(self, agent_service):
        """Test health check del servicio"""
        
        health = agent_service.health_check()
        
        assert health["status"] == "healthy"
        assert health["total_agents"] == 3
        assert "agents" in health
        assert "selector" in health

class TestAgentIntegration:
    """Tests de integración entre agentes"""
    
    @pytest.fixture
    def all_agents(self, mock_rag_service):
        return [
            PlantsAgent(mock_rag_service),
            PathologyAgent(mock_rag_service),
            GeneralAgent(mock_rag_service)
        ]
    
    def test_agent_confidence_ordering(self, all_agents):
        """Test que la confianza se ordena correctamente"""
        
        test_cases = [
            ("¿Cómo cuidar un manzano?", "plants"),
            ("¿Qué enfermedad tiene mi vid?", "pathology"),
            ("¿Qué es la fotosíntesis?", ["general", "plants"]),  # Puede ir a cualquiera
        ]
        
        for question, expected_agent in test_cases:
            confidences = []
            for agent in all_agents:
                confidence = agent.can_handle(question)
                confidences.append((agent.name, confidence))
            
            # Ordenar por confianza
            confidences.sort(key=lambda x: x[1], reverse=True)
            best_agent = confidences[0][0]
            
            if isinstance(expected_agent, list):
                assert best_agent in expected_agent, f"Agente {best_agent} no esperado para: {question}"
            else:
                assert best_agent == expected_agent, f"Esperado {expected_agent}, obtenido {best_agent} para: {question}"
    
    def test_no_agent_has_zero_confidence(self, all_agents):
        """Test que al menos un agente siempre puede manejar cualquier pregunta"""
        
        random_questions = [
            "Pregunta completamente aleatoria",
            "¿Cómo hacer una pizza?",
            "¿Cuál es la capital de Mongolia?",
            "123 números aleatorios 456"
        ]
        
        for question in random_questions:
            max_confidence = max(agent.can_handle(question) for agent in all_agents)
            assert max_confidence > 0.0, f"Ningún agente puede manejar: {question}"
    
    def test_agent_specialization_boundaries(self, all_agents):
        """Test que los agentes respetan sus límites de especialización"""
        
        # Preguntas claramente de un dominio específico
        clear_boundaries = [
            ("Síntomas de mildiu en Vitis vinifera", "pathology"),  # Claramente patología
            ("Técnicas de injerto en frutales", "plants"),         # Claramente cultivo
            ("¿Qué es la clasificación taxonómica?", "general")    # Claramente educativo
        ]
        
        for question, expected_domain in clear_boundaries:
            confidences = {}
            for agent in all_agents:
                confidences[agent.name] = agent.can_handle(question)
            
            # El agente especializado debe tener mayor confianza
            expected_confidence = confidences[expected_domain]
            other_confidences = [conf for name, conf in confidences.items() if name != expected_domain]
            
            assert expected_confidence > max(other_confidences), \
                f"Agente {expected_domain} no tiene mayor confianza para: {question}"

class TestAgentMetrics:
    """Tests para métricas y estadísticas de agentes"""
    
    @pytest.fixture
    def plants_agent_with_stats(self, mock_rag_service):
        agent = PlantsAgent(mock_rag_service)
        
        # Simular algunas estadísticas
        agent.update_stats(0.8, success=True)
        agent.update_stats(0.9, success=True)
        agent.update_stats(0.6, success=False)
        
        return agent
    
    def test_agent_stats_tracking(self, plants_agent_with_stats):
        """Test seguimiento de estadísticas"""
        
        stats = plants_agent_with_stats.get_stats()
        
        assert stats["total_queries"] == 3
        assert stats["successful_queries"] == 2
        assert stats["failed_queries"] == 1
        assert stats["success_rate"] == 2/3
        assert stats["average_confidence"] > 0.0
        assert stats["last_used"] is not None
    
    def test_agent_health_check(self, plants_agent_with_stats):
        """Test health check individual del agente"""
        
        health = plants_agent_with_stats.health_check()
        
        assert health["agent"] == "plants"
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "checks" in health
        assert "topics" in health
        assert "stats" in health
    
    def test_agent_capabilities(self, plants_agent_with_stats):
        """Test información de capacidades"""
        
        capabilities = plants_agent_with_stats.get_capabilities()
        
        assert capabilities["name"] == "plants"
        assert "description" in capabilities
        assert "topics" in capabilities
        assert "agent_type" in capabilities
        assert "stats" in capabilities
        assert "status" in capabilities

# Tests parametrizados para diferentes escenarios
@pytest.mark.parametrize("question,expected_agent,min_confidence", [
    ("¿Cómo plantar tomates?", "plants", 0.6),
    ("Mi planta tiene manchas negras", "pathology", 0.7),
    ("¿Qué es la botánica?", "general", 0.4),
    ("Cuidados del Malus domestica", "plants", 0.8),
    ("Tratamiento para oídio", "pathology", 0.8),
    ("Clasificación de plantas", "general", 0.5),
])
def test_agent_selection_parametrized(question, expected_agent, min_confidence, mock_rag_service):
    """Test parametrizado para selección de agentes"""
    
    agents = {
        "plants": PlantsAgent(mock_rag_service),
        "pathology": PathologyAgent(mock_rag_service),
        "general": GeneralAgent(mock_rag_service)
    }
    
    target_agent = agents[expected_agent]
    confidence = target_agent.can_handle(question)
    
    assert confidence >= min_confidence, \
        f"Confianza {confidence} menor que {min_confidence} para '{question}'"

@pytest.mark.parametrize("agent_class,topic", [
    (PlantsAgent, "plants"),
    (PathologyAgent, "pathology"),
    (GeneralAgent, "general"),
])
def test_agent_topic_consistency(agent_class, topic, mock_rag_service):
    """Test que los agentes tienen consistencia con sus temas"""
    
    agent = agent_class(mock_rag_service)
    
    assert topic in agent.topics, f"Agente {agent.name} no incluye topic {topic}"
    assert agent.name == topic, f"Nombre de agente {agent.name} no coincide con topic {topic}"

# Tests de rendimiento y límites
class TestAgentPerformance:
    """Tests de rendimiento y límites de agentes"""
    
    def test_agent_response_time(self, mock_rag_service):
        """Test que los agentes responden en tiempo razonable"""
        import time
        
        agent = PlantsAgent(mock_rag_service)
        question = "¿Cómo cuidar plantas?"
        
        start_time = time.time()
        confidence = agent.can_handle(question)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 0.1, f"Tiempo de respuesta muy alto: {response_time}s"
        assert confidence >= 0.0, "Confianza inválida"
    
    def test_agent_handles_long_questions(self, mock_rag_service):
        """Test que los agentes manejan preguntas largas"""
        
        agent = PlantsAgent(mock_rag_service)
        
        # Pregunta muy larga
        long_question = "¿Cómo cuidar plantas? " * 100
        
        confidence = agent.can_handle(long_question)
        assert 0.0 <= confidence <= 1.0, "Confianza fuera de rango para pregunta larga"
    
    def test_agent_handles_empty_questions(self, mock_rag_service):
        """Test que los agentes manejan preguntas vacías"""
        
        agent = PlantsAgent(mock_rag_service)
        
        empty_questions = ["", "   ", "\n\t", None]
        
        for question in empty_questions:
            if question is None:
                continue
                
            confidence = agent.can_handle(question)
            assert confidence == 0.0, f"Confianza no cero para pregunta vacía: '{question}'"