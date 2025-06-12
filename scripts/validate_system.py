#!/usr/bin/env python3
"""
Script de validación completa del sistema AgentRagMCP
Ejecuta una serie de tests para verificar que todo funciona correctamente
"""
import os
import sys
import time
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
import httpx

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import setup_logging

class SystemValidator:
    """Validador completo del sistema AgentRagMCP"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.logger = setup_logging()
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "errors": [],
            "warnings": []
        }
    
    def log_result(self, test_name: str, success: bool, message: str = "", warning: bool = False):
        """Registra el resultado de un test"""
        self.results["total_tests"] += 1
        
        if success:
            self.results["passed_tests"] += 1
            status = "✅ PASS"
        else:
            self.results["failed_tests"] += 1
            status = "❌ FAIL"
            if message:
                self.results["errors"].append(f"{test_name}: {message}")
        
        if warning:
            self.results["warnings"].append(f"{test_name}: {message}")
            status += " ⚠️"
        
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
    
    async def test_health_endpoints(self) -> bool:
        """Test de endpoints de health check"""
        print("\n=== TESTING HEALTH ENDPOINTS ===")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test health básico
                response = await client.get(f"{self.base_url}/health/")
                success = response.status_code == 200
                self.log_result(
                    "Health Check Básico", 
                    success,
                    f"Status: {response.status_code}" if not success else ""
                )
                
                if success:
                    data = response.json()
                    self.log_result(
                        "Health Check Response Structure",
                        "status" in data,
                        "Estructura de respuesta válida"
                    )
                
                # Test health detallado
                try:
                    response = await client.get(f"{self.base_url}/health/detailed")
                    success = response.status_code == 200
                    self.log_result(
                        "Health Check Detallado",
                        success,
                        f"Status: {response.status_code}" if not success else ""
                    )
                except Exception as e:
                    self.log_result("Health Check Detallado", False, str(e))
                
                return True
                
        except Exception as e:
            self.log_result("Health Endpoints", False, f"Error de conexión: {e}")
            return False
    
    async def test_basic_chat(self) -> bool:
        """Test de funcionalidad básica de chat"""
        print("\n=== TESTING BASIC CHAT FUNCTIONALITY ===")
        
        test_questions = [
            {
                "question": "¿Cómo cuidar un manzano?",
                "expected_agent": "plants",
                "test_name": "Chat - Pregunta de Plantas"
            },
            {
                "question": "¿Qué enfermedad causa hojas amarillas?",
                "expected_agent": "pathology",
                "test_name": "Chat - Pregunta de Patología"
            },
            {
                "question": "¿Qué es la fotosíntesis?",
                "expected_agent": "general",
                "test_name": "Chat - Pregunta General"
            }
        ]
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for test_case in test_questions:
                    try:
                        response = await client.post(
                            f"{self.base_url}/chat/",
                            json={
                                "question": test_case["question"],
                                "include_sources": True
                            }
                        )
                        
                        success = response.status_code == 200
                        if success:
                            data = response.json()
                            # Verificar estructura de respuesta
                            required_fields = ["answer", "session_id", "agent_type", "topic"]
                            has_required_fields = all(field in data for field in required_fields)
                            
                            if has_required_fields:
                                answer_length = len(data["answer"])
                                agent_correct = data["agent_type"] == test_case["expected_agent"]
                                
                                self.log_result(
                                    test_case["test_name"],
                                    answer_length > 50 and agent_correct,
                                    f"Agente: {data['agent_type']}, Respuesta: {answer_length} chars",
                                    warning=not agent_correct
                                )
                            else:
                                self.log_result(
                                    test_case["test_name"],
                                    False,
                                    "Campos requeridos faltantes en respuesta"
                                )
                        else:
                            self.log_result(
                                test_case["test_name"],
                                False,
                                f"HTTP {response.status_code}"
                            )
                            
                    except Exception as e:
                        self.log_result(test_case["test_name"], False, str(e))
                
                return True
                
        except Exception as e:
            self.log_result("Basic Chat", False, f"Error general: {e}")
            return False
    
    async def test_agent_selection(self) -> bool:
        """Test del sistema de selección de agentes"""
        print("\n=== TESTING AGENT SELECTION ===")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Test obtener agentes disponibles
                response = await client.get(f"{self.base_url}/chat/agents")
                success = response.status_code == 200
                
                if success:
                    agents = response.json()
                    expected_agents = {"plants", "pathology", "general"}
                    available_agents = {agent["name"] for agent in agents}
                    
                    self.log_result(
                        "Agentes Disponibles",
                        expected_agents.issubset(available_agents),
                        f"Encontrados: {available_agents}"
                    )
                else:
                    self.log_result("Agentes Disponibles", False, f"HTTP {response.status_code}")
                
                # Test selección específica de agente
                test_selection = {
                    "question": "¿Cómo tratar el mildiu?",
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/agent/select",
                    json=test_selection
                )
                
                success = response.status_code == 200
                if success:
                    data = response.json()
                    confidence = data.get("confidence", 0)
                    selected_agent = data.get("selected_agent", "")
                    
                    self.log_result(
                        "Selección de Agente",
                        confidence > 0.5 and selected_agent == "pathology",
                        f"Agente: {selected_agent}, Confianza: {confidence:.2f}"
                    )
                else:
                    self.log_result("Selección de Agente", False, f"HTTP {response.status_code}")
                
                return True
                
        except Exception as e:
            self.log_result("Agent Selection", False, str(e))
            return False
    
    async def test_rag_queries(self) -> bool:
        """Test de consultas directas a RAG"""
        print("\n=== TESTING RAG QUERIES ===")
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                # Test obtener topics
                response = await client.get(f"{self.base_url}/chat/topics")
                success = response.status_code == 200
                
                if success:
                    topics = response.json()
                    expected_topics = {"plants", "pathology", "general"}
                    available_topics = set(topics)
                    
                    self.log_result(
                        "Topics Disponibles",
                        expected_topics.issubset(available_topics),
                        f"Encontrados: {available_topics}"
                    )
                    
                    # Test consulta RAG para cada topic
                    for topic in expected_topics:
                        if topic in available_topics:
                            rag_response = await client.post(
                                f"{self.base_url}/chat/rag/query",
                                json={
                                    "query": f"información sobre {topic}",
                                    "topic": topic
                                }
                            )
                            
                            rag_success = rag_response.status_code == 200
                            if rag_success:
                                rag_data = rag_response.json()
                                has_documents = "documents" in rag_data
                                
                                self.log_result(
                                    f"RAG Query - {topic.title()}",
                                    has_documents,
                                    f"Documentos: {len(rag_data.get('documents', []))}"
                                )
                            else:
                                self.log_result(
                                    f"RAG Query - {topic.title()}",
                                    False,
                                    f"HTTP {rag_response.status_code}"
                                )
                else:
                    self.log_result("Topics Disponibles", False, f"HTTP {response.status_code}")
                
                return True
                
        except Exception as e:
            self.log_result("RAG Queries", False, str(e))
            return False
    
    async def test_session_management(self) -> bool:
        """Test de gestión de sesiones"""
        print("\n=== TESTING SESSION MANAGEMENT ===")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                session_id = "test-validation-session"
                
                # Crear sesión con una pregunta
                response = await client.post(
                    f"{self.base_url}/chat/",
                    json={
                        "question": "¿Cómo plantar tomates?",
                        "session_id": session_id
                    }
                )
                
                session_created = response.status_code == 200
                self.log_result(
                    "Creación de Sesión",
                    session_created,
                    f"HTTP {response.status_code}" if not session_created else ""
                )
                
                if session_created:
                    # Obtener información de la sesión
                    info_response = await client.get(f"{self.base_url}/chat/session/{session_id}")
                    
                    info_success = info_response.status_code == 200
                    self.log_result(
                        "Información de Sesión",
                        info_success,
                        f"HTTP {info_response.status_code}" if not info_success else "Sesión encontrada"
                    )
                    
                    # Limpiar sesión
                    clear_response = await client.delete(f"{self.base_url}/chat/session/{session_id}")
                    
                    clear_success = clear_response.status_code == 200
                    self.log_result(
                        "Limpieza de Sesión",
                        clear_success,
                        f"HTTP {clear_response.status_code}" if not clear_success else "Sesión eliminada"
                    )
                
                return True
                
        except Exception as e:
            self.log_result("Session Management", False, str(e))
            return False
    
    async def test_error_handling(self) -> bool:
        """Test de manejo de errores"""
        print("\n=== TESTING ERROR HANDLING ===")
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test pregunta vacía
                response = await client.post(
                    f"{self.base_url}/chat/",
                    json={"question": ""}
                )
                
                self.log_result(
                    "Manejo de Pregunta Vacía",
                    response.status_code == 422,  # Validation Error
                    f"Código esperado: 422, obtenido: {response.status_code}"
                )
                
                # Test agente inválido
                response = await client.post(
                    f"{self.base_url}/chat/",
                    json={
                        "question": "¿Cómo plantar?",
                        "agent_type": "invalid_agent"
                    }
                )
                
                self.log_result(
                    "Manejo de Agente Inválido",
                    response.status_code == 400,  # Bad Request
                    f"Código esperado: 400, obtenido: {response.status_code}"
                )
                
                # Test topic inválido
                response = await client.post(
                    f"{self.base_url}/chat/rag/query",
                    json={
                        "query": "test",
                        "topic": "invalid_topic"
                    }
                )
                
                self.log_result(
                    "Manejo de Topic Inválido",
                    response.status_code == 400,  # Bad Request
                    f"Código esperado: 400, obtenido: {response.status_code}"
                )
                
                return True
                
        except Exception as e:
            self.log_result("Error Handling", False, str(e))
            return False
    
    async def test_performance(self) -> bool:
        """Test básico de rendimiento"""
        print("\n=== TESTING PERFORMANCE ===")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test tiempo de respuesta
                start_time = time.time()
                
                response = await client.post(
                    f"{self.base_url}/chat/",
                    json={"question": "¿Qué es una planta?"}
                )
                
                end_time = time.time()
                response_time = end_time - start_time
                
                success = response.status_code == 200 and response_time < 10.0
                self.log_result(
                    "Tiempo de Respuesta",
                    success,
                    f"{response_time:.2f}s ({'OK' if response_time < 5.0 else 'LENTO'})"
                )
                
                # Test múltiples requests
                start_time = time.time()
                
                tasks = []
                for i in range(3):
                    task = client.post(
                        f"{self.base_url}/chat/",
                        json={"question": f"Pregunta de test {i}"}
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                end_time = time.time()
                
                successful_responses = sum(
                    1 for r in responses 
                    if not isinstance(r, Exception) and r.status_code == 200
                )
                
                total_time = end_time - start_time
                
                self.log_result(
                    "Múltiples Requests",
                    successful_responses == 3,
                    f"{successful_responses}/3 exitosas en {total_time:.2f}s"
                )
                
                return True
                
        except Exception as e:
            self.log_result("Performance", False, str(e))
            return False
    
    def test_configuration(self) -> bool:
        """Test de configuración del sistema"""
        print("\n=== TESTING CONFIGURATION ===")
        
        try:
            settings = get_settings()
            
            # Test configuración básica
            self.log_result(
                "Configuración Cargada",
                hasattr(settings, 'APP_NAME'),
                f"App: {getattr(settings, 'APP_NAME', 'N/A')}"
            )
            
            # Test configuración LLM
            llm_configured = all([
                hasattr(settings, 'LLM_MODEL'),
                hasattr(settings, 'LLM_BASE_URL'),
                hasattr(settings, 'EMBEDDING_MODEL')
            ])
            
            self.log_result(
                "Configuración LLM",
                llm_configured,
                f"Modelo: {getattr(settings, 'LLM_MODEL', 'N/A')}"
            )
            
            # Test configuración RAG
            rag_configured = all([
                hasattr(settings, 'RAG_TOPICS'),
                hasattr(settings, 'VECTORSTORE_BASE_PATH'),
                len(settings.RAG_TOPICS) > 0
            ])
            
            self.log_result(
                "Configuración RAG",
                rag_configured,
                f"Topics: {getattr(settings, 'RAG_TOPICS', [])}"
            )
            
            return True
            
        except Exception as e:
            self.log_result("Configuration", False, str(e))
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todos los tests de validación"""
        print("🚀 Iniciando validación completa del sistema AgentRagMCP\n")
        print(f"🎯 Objetivo: {self.base_url}")
        
        # Tests de configuración (síncronos)
        self.test_configuration()
        
        # Tests asíncronos
        await self.test_health_endpoints()
        await self.test_basic_chat()
        await self.test_agent_selection()
        await self.test_rag_queries()
        await self.test_session_management()
        await self.test_error_handling()
        await self.test_performance()
        
        return self.results
    
    def print_summary(self):
        """Imprime resumen de resultados"""
        results = self.results
        
        print(f"\n{'='*50}")
        print("📊 RESUMEN DE VALIDACIÓN")
        print(f"{'='*50}")
        
        print(f"✅ Tests pasados: {results['passed_tests']}")
        print(f"❌ Tests fallidos: {results['failed_tests']}")
        print(f"📈 Total tests: {results['total_tests']}")
        
        if results['total_tests'] > 0:
            success_rate = (results['passed_tests'] / results['total_tests']) * 100
            print(f"📊 Tasa de éxito: {success_rate:.1f}%")
        
        if results['warnings']:
            print(f"\n⚠️  Advertencias ({len(results['warnings'])}):")
            for warning in results['warnings']:
                print(f"   • {warning}")
        
        if results['errors']:
            print(f"\n❌ Errores ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"   • {error}")
        
        print(f"\n{'='*50}")
        
        if results['failed_tests'] == 0:
            print("🎉 ¡VALIDACIÓN EXITOSA! El sistema está funcionando correctamente.")
        elif results['failed_tests'] < results['total_tests'] / 2:
            print("⚠️  VALIDACIÓN PARCIAL. Algunos componentes necesitan atención.")
        else:
            print("💥 VALIDACIÓN FALLIDA. El sistema tiene problemas críticos.")
        
        return results['failed_tests'] == 0

async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Validación completa de AgentRagMCP")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="URL base de la API (default: http://localhost:8000)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Timeout para tests en segundos (default: 30)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Modo verbose")
    
    args = parser.parse_args()
    
    # Configurar el validador
    validator = SystemValidator(args.url)
    
    try:
        # Ejecutar todos los tests
        results = await validator.run_all_tests()
        
        # Mostrar resumen
        success = validator.print_summary()
        
        # Código de salida
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Validación interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error crítico durante la validación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())