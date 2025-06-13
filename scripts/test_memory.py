#!/usr/bin/env python3
"""
Script para probar la memoria conversacional de AgentRagMCP
"""
import asyncio
import httpx
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from uuid import uuid4

@dataclass
class ConversationTest:
    name: str
    questions: List[str]
    expected_memory_indicators: List[str]
    description: str

class ConversationalMemoryTester:
    """Tester especializado para memoria conversacional"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session_id = str(uuid4())
        self.conversation_history = []
        
    async def send_question(self, question: str) -> Dict[str, Any]:
        """Envía una pregunta y devuelve la respuesta"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/",
                json={
                    "question": question,
                    "session_id": self.session_id,
                    "include_sources": True
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.conversation_history.append({
                    "question": question,
                    "answer": data["answer"],
                    "agent_type": data["agent_type"],
                    "session_id": data["session_id"]
                })
                return data
            else:
                raise Exception(f"Error {response.status_code}: {response.text}")
    
    def analyze_memory_continuity(self, test: ConversationTest) -> Dict[str, Any]:
        """Analiza la continuidad de memoria en la conversación"""
        analysis = {
            "test_name": test.name,
            "memory_indicators_found": [],
            "context_references": [],
            "session_consistency": True,
            "agent_consistency": [],
            "overall_score": 0.0
        }
        
        if len(self.conversation_history) < 2:
            analysis["overall_score"] = 0.0
            return analysis
        
        # 1. Verificar consistencia de sesión
        session_ids = [conv["session_id"] for conv in self.conversation_history]
        analysis["session_consistency"] = len(set(session_ids)) == 1
        
        # 2. Analizar referencias contextuales
        for i, conv in enumerate(self.conversation_history[1:], 1):
            answer = conv["answer"].lower()
            
            # Buscar pronombres y referencias
            context_refs = []
            pronouns = ["eso", "esto", "él", "ella", "lo", "la", "los", "las", 
                       "dicha", "dicho", "mencionado", "anterior", "previamente"]
            
            for pronoun in pronouns:
                if pronoun in answer:
                    context_refs.append(f"Pregunta {i+1}: usa '{pronoun}'")
            
            # Buscar referencias específicas a información previa
            prev_questions = [c["question"].lower() for c in self.conversation_history[:i]]
            prev_answers = [c["answer"].lower() for c in self.conversation_history[:i]]
            
            # Buscar si menciona conceptos de respuestas anteriores
            for j, prev_answer in enumerate(prev_answers):
                words_prev = set(prev_answer.split())
                words_current = set(answer.split())
                
                # Buscar overlap semántico (palabras compartidas)
                overlap = words_prev.intersection(words_current)
                if len(overlap) > 5:  # Umbral de palabras compartidas
                    context_refs.append(f"Pregunta {i+1}: referencia a respuesta {j+1}")
            
            analysis["context_references"].extend(context_refs)
        
        # 3. Verificar indicadores específicos del test
        all_answers = " ".join([conv["answer"].lower() for conv in self.conversation_history])
        for indicator in test.expected_memory_indicators:
            if indicator.lower() in all_answers:
                analysis["memory_indicators_found"].append(indicator)
        
        # 4. Analizar consistencia de agentes
        agents_used = [conv["agent_type"] for conv in self.conversation_history]
        analysis["agent_consistency"] = agents_used
        
        # 5. Calcular score general
        score_components = []
        
        # Consistencia de sesión (30%)
        score_components.append(0.3 if analysis["session_consistency"] else 0.0)
        
        # Referencias contextuales (40%)
        if len(self.conversation_history) > 1:
            ref_score = min(len(analysis["context_references"]) / len(self.conversation_history), 1.0)
            score_components.append(0.4 * ref_score)
        
        # Indicadores específicos encontrados (30%)
        if test.expected_memory_indicators:
            ind_score = len(analysis["memory_indicators_found"]) / len(test.expected_memory_indicators)
            score_components.append(0.3 * ind_score)
        
        analysis["overall_score"] = sum(score_components)
        
        return analysis
    
    async def run_conversation_test(self, test: ConversationTest) -> Dict[str, Any]:
        """Ejecuta un test completo de conversación"""
        print(f"\n🧪 Ejecutando test: {test.name}")
        print(f"📝 Descripción: {test.description}")
        print("-" * 50)
        
        # Reiniciar historial para este test
        self.conversation_history = []
        self.session_id = str(uuid4())
        
        # Ejecutar preguntas secuencialmente
        for i, question in enumerate(test.questions, 1):
            print(f"\n❓ Pregunta {i}: {question}")
            
            try:
                start_time = time.time()
                response = await self.send_question(question)
                response_time = time.time() - start_time
                
                print(f"🤖 Respuesta ({response_time:.1f}s): {response['answer'][:150]}...")
                print(f"🎯 Agente: {response['agent_type']}")
                
                # Pausa entre preguntas para simular conversación natural
                if i < len(test.questions):
                    await asyncio.sleep(1)
                    
            except Exception as e:
                print(f"❌ Error en pregunta {i}: {e}")
                return {"error": str(e)}
        
        # Analizar memoria conversacional
        analysis = self.analyze_memory_continuity(test)
        
        print(f"\n📊 Análisis completado:")
        print(f"   • Score general: {analysis['overall_score']:.2f}")
        print(f"   • Consistencia de sesión: {'✅' if analysis['session_consistency'] else '❌'}")
        print(f"   • Referencias contextuales: {len(analysis['context_references'])}")
        print(f"   • Indicadores encontrados: {len(analysis['memory_indicators_found'])}")
        
        return analysis
    
    async def clear_session(self):
        """Limpia la sesión actual"""
        try:
            async with httpx.AsyncClient() as client:
                await client.delete(f"{self.base_url}/chat/session/{self.session_id}")
            print(f"🗑️ Sesión {self.session_id[:8]}... limpiada")
        except Exception as e:
            print(f"⚠️ No se pudo limpiar la sesión: {e}")

def create_test_scenarios() -> List[ConversationTest]:
    """Crea escenarios de test predefinidos"""
    return [
        ConversationTest(
            name="Continuidad Básica - Manzano",
            questions=[
                "¿Cómo cuidar un manzano Malus domestica?",
                "¿Cuándo debo podarlo?",
                "¿Y el riego cómo debe ser?",
                "¿Qué fertilizante le va mejor?"
            ],
            expected_memory_indicators=[
                "manzano", "podarlo", "riego", "fertilizante"
            ],
            description="Test básico de continuidad conversacional sobre cuidados del manzano"
        ),
        
        ConversationTest(
            name="Referencias Contextuales - Enfermedad",
            questions=[
                "Mi tomate tiene hojas amarillas",
                "¿Qué enfermedad puede ser?",
                "¿Cómo puedo tratarla?",
                "¿Es contagiosa para otras plantas?"
            ],
            expected_memory_indicators=[
                "hojas amarillas", "enfermedad", "tratarla", "contagiosa"
            ],
            description="Test de referencias contextuales usando pronombres y contexto previo"
        ),
        
        ConversationTest(
            name="Profundización Temática - Fotosíntesis",
            questions=[
                "¿Qué es la fotosíntesis?",
                "¿Qué factores la afectan?",
                "Dame ejemplos de plantas que la realizan de forma especial",
                "¿Cómo puedo optimizarla en mi jardín?"
            ],
            expected_memory_indicators=[
                "fotosíntesis", "factores", "plantas", "optimizar"
            ],
            description="Test de profundización progresiva en un tema científico"
        ),
        
        ConversationTest(
            name="Cambio de Contexto - Múltiples Plantas",
            questions=[
                "Cuéntame sobre el cultivo de vid",
                "¿Y qué diferencias tiene con el manzano?",
                "¿Cuál de los dos es más fácil de cuidar?",
                "¿Puedo plantarlos juntos en el mismo huerto?"
            ],
            expected_memory_indicators=[
                "vid", "manzano", "diferencias", "fácil", "juntos"
            ],
            description="Test de mantenimiento de contexto con múltiples plantas"
        ),
        
        ConversationTest(
            name="Diagnóstico Progresivo",
            questions=[
                "Las hojas de mi planta se están poniendo amarillas",
                "También hay unas manchas marrones en los bordes",
                "¿Qué puede estar pasando?",
                "¿Cómo lo soluciono?"
            ],
            expected_memory_indicators=[
                "amarillas", "manchas marrones", "bordes", "soluciono"
            ],
            description="Test de diagnóstico progresivo acumulando síntomas"
        )
    ]

async def run_comprehensive_memory_test():
    """Ejecuta una batería completa de tests de memoria conversacional"""
    print("🧠 SISTEMA DE TESTS DE MEMORIA CONVERSACIONAL")
    print("=" * 60)
    
    tester = ConversationalMemoryTester()
    test_scenarios = create_test_scenarios()
    
    results = []
    
    # Verificar conectividad
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            health_response = await client.get(f"{tester.base_url}/health/")
            if health_response.status_code != 200:
                print("❌ API no disponible")
                return
        print("✅ Conexión con API verificada")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    
    # Ejecutar cada test
    for i, test in enumerate(test_scenarios, 1):
        print(f"\n{'='*20} TEST {i}/{len(test_scenarios)} {'='*20}")
        
        try:
            result = await tester.run_conversation_test(test)
            results.append(result)
            
            # Limpiar sesión entre tests
            await tester.clear_session()
            
            # Pausa entre tests
            if i < len(test_scenarios):
                print("\n⏳ Pausa entre tests...")
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ Error en test {test.name}: {e}")
            results.append({"test_name": test.name, "error": str(e)})
    
    # Generar reporte final
    print_final_report(results)

def print_final_report(results: List[Dict[str, Any]]):
    """Imprime el reporte final de todos los tests"""
    print(f"\n{'='*60}")
    print("📊 REPORTE FINAL DE MEMORIA CONVERSACIONAL")
    print(f"{'='*60}")
    
    successful_tests = [r for r in results if "error" not in r]
    failed_tests = [r for r in results if "error" in r]
    
    print(f"\n📈 RESUMEN GENERAL:")
    print(f"   • Tests ejecutados: {len(results)}")
    print(f"   • Tests exitosos: {len(successful_tests)}")
    print(f"   • Tests fallidos: {len(failed_tests)}")
    
    if successful_tests:
        avg_score = sum(r["overall_score"] for r in successful_tests) / len(successful_tests)
        print(f"   • Score promedio: {avg_score:.2f}")
        
        print(f"\n📋 RESULTADOS DETALLADOS:")
        print("-" * 40)
        
        for result in successful_tests:
            score = result["overall_score"]
            status_emoji = "🟢" if score >= 0.7 else "🟡" if score >= 0.4 else "🔴"
            
            print(f"\n{status_emoji} {result['test_name']}")
            print(f"   Score: {score:.2f}")
            print(f"   Sesión consistente: {'✅' if result['session_consistency'] else '❌'}")
            print(f"   Referencias contextuales: {len(result['context_references'])}")
            print(f"   Indicadores encontrados: {len(result['memory_indicators_found'])}")
            
            if result['context_references']:
                print(f"   Referencias detectadas:")
                for ref in result['context_references'][:3]:  # Mostrar solo las primeras 3
                    print(f"     • {ref}")
    
    if failed_tests:
        print(f"\n❌ TESTS FALLIDOS:")
        for result in failed_tests:
            print(f"   • {result['test_name']}: {result['error']}")
    
    # Recomendaciones
    print(f"\n💡 INTERPRETACIÓN DE RESULTADOS:")
    print(f"   🟢 Score ≥ 0.7: Memoria conversacional excelente")
    print(f"   🟡 Score 0.4-0.7: Memoria conversacional aceptable")
    print(f"   🔴 Score < 0.4: Memoria conversacional deficiente")
    
    print(f"\n🔍 QUÉ VERIFICAR EN LA MEMORIA CONVERSACIONAL:")
    print(f"   1. Las respuestas usan información de preguntas anteriores")
    print(f"   2. Los pronombres (eso, lo, él) se resuelven correctamente")
    print(f"   3. No se repite información ya proporcionada")
    print(f"   4. El contexto se mantiene entre intercambios")
    print(f"   5. La sesión se mantiene consistente")

async def run_interactive_test():
    """Ejecuta un test interactivo donde el usuario hace preguntas"""
    print("🎮 MODO INTERACTIVO - TEST DE MEMORIA CONVERSACIONAL")
    print("=" * 55)
    print("Instrucciones:")
    print("- Haz preguntas secuenciales que dependan del contexto")
    print("- Usa pronombres y referencias a respuestas anteriores")
    print("- Escribe 'salir' para terminar")
    print("- Escribe 'analizar' para ver el análisis de memoria")
    print("-" * 55)
    
    tester = ConversationalMemoryTester()
    question_count = 0
    
    while True:
        try:
            user_input = input(f"\n❓ Pregunta {question_count + 1}: ").strip()
            
            if user_input.lower() in ['salir', 'exit', 'quit']:
                break
            elif user_input.lower() == 'analizar':
                if tester.conversation_history:
                    # Crear test temporal para análisis
                    temp_test = ConversationTest(
                        name="Test Interactivo",
                        questions=[conv["question"] for conv in tester.conversation_history],
                        expected_memory_indicators=[],
                        description="Test interactivo del usuario"
                    )
                    analysis = tester.analyze_memory_continuity(temp_test)
                    
                    print(f"\n📊 ANÁLISIS DE MEMORIA ACTUAL:")
                    print(f"   Score: {analysis['overall_score']:.2f}")
                    print(f"   Referencias contextuales: {len(analysis['context_references'])}")
                    print(f"   Preguntas realizadas: {len(tester.conversation_history)}")
                    
                    if analysis['context_references']:
                        print(f"   Referencias detectadas:")
                        for ref in analysis['context_references']:
                            print(f"     • {ref}")
                else:
                    print("⚠️ No hay conversación para analizar")
                continue
            elif not user_input:
                continue
            
            # Enviar pregunta
            start_time = time.time()
            response = await tester.send_question(user_input)
            response_time = time.time() - start_time
            
            print(f"\n🤖 Respuesta ({response_time:.1f}s):")
            print(f"   {response['answer']}")
            print(f"   [Agente: {response['agent_type']} | Sesión: {response['session_id'][:8]}...]")
            
            question_count += 1
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n👋 Test interactivo finalizado con {question_count} preguntas")
    await tester.clear_session()

def main():
    """Función principal con menú de opciones"""
    print("🧠 TESTER DE MEMORIA CONVERSACIONAL - AgentRagMCP")
    print("=" * 50)
    print("Opciones disponibles:")
    print("1. Ejecutar tests automáticos completos")
    print("2. Ejecutar test interactivo")
    print("3. Ejecutar test específico")
    print("4. Salir")
    
    while True:
        try:
            choice = input("\n🎯 Selecciona una opción (1-4): ").strip()
            
            if choice == "1":
                asyncio.run(run_comprehensive_memory_test())
            elif choice == "2":
                asyncio.run(run_interactive_test())
            elif choice == "3":
                # Mostrar tests disponibles
                tests = create_test_scenarios()
                print("\nTests disponibles:")
                for i, test in enumerate(tests, 1):
                    print(f"{i}. {test.name} - {test.description}")
                
                try:
                    test_num = int(input("Número del test: ")) - 1
                    if 0 <= test_num < len(tests):
                        tester = ConversationalMemoryTester()
                        result = asyncio.run(tester.run_conversation_test(tests[test_num]))
                        print_final_report([result])
                    else:
                        print("❌ Número de test inválido")
                except ValueError:
                    print("❌ Ingresa un número válido")
            elif choice == "4":
                print("👋 ¡Hasta luego!")
                break
            else:
                print("❌ Opción inválida. Selecciona 1-4.")
                
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()