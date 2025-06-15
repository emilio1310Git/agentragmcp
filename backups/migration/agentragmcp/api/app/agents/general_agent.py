"""
Agente general para consultas diversas sobre plantas
"""
import re
from typing import Dict, List, Optional, Tuple, Any

from agentragmcp.api.app.agents.base_agent import BaseAgent
from agentragmcp.api.app.services.rag_service import RAGService
from agentragmcp.core.monitoring import logger, get_logger_with_context

class GeneralAgent(BaseAgent):
    """
    Agente general para consultas que no requieren especialización específica.
    
    Se enfoca en:
    - Consultas generales sobre plantas
    - Preguntas educativas básicas
    - Información divulgativa
    - Fallback para otros agentes
    """
    
    def __init__(self, rag_service: RAGService):
        super().__init__(
            name="general",
            description="Asistente general para consultas diversas sobre plantas y botánica",
            topics=["general"],
            rag_service=rag_service
        )
        
        # Palabras clave generales y educativas
        self.general_keywords = {
            # Consultas educativas
            "qué es", "qué son", "cómo funciona", "por qué", "para qué",
            "explicar", "explica", "definir", "definición", "concepto",
            "diferencia", "diferencias", "comparar", "tipos", "clases",
            
            # Términos amplios de botánica
            "botánica", "biología", "naturaleza", "ecosistema", "medio ambiente",
            "biodiversidad", "evolución", "adaptación", "clasificación",
            "taxonomía", "filogenia", "ecología",
            
            # Consultas generales
            "plantas", "vegetales", "flora", "reino vegetal", "mundo vegetal",
            "curiosidades", "datos", "información", "conocer", "aprender",
            
            # Procesos básicos
            "fotosíntesis", "respiración", "transpiración", "absorción",
            "nutrición", "reproducción", "polinización", "dispersión"
        }
        
        # Patrones de consultas educativas
        self.educational_patterns = [
            r"qué.*es.*la?\w+",
            r"cómo.*funciona",
            r"por.*qué.*las?\s*plantas",
            r"diferencia.*entre",
            r"tipos.*de.*plantas",
            r"clasificación.*de",
            r"curiosidades.*sobre",
            r"datos.*interesantes",
            r"información.*general"
        ]
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """
        Evalúa si puede manejar la pregunta general.
        
        El agente general tiene una confianza base baja para actuar como fallback,
        pero puede aumentar para consultas claramente educativas o generales.
        
        Returns:
            float: Confianza entre 0.0 y 1.0
        """
        question_lower = question.lower()
        confidence = 0.2  # Confianza base como fallback
        
        # 1. Palabras clave generales
        keyword_matches = sum(1 for keyword in self.general_keywords if keyword in question_lower)
        if keyword_matches > 0:
            confidence += 0.2 + (keyword_matches * 0.05)  # Máximo +0.4
        
        # 2. Patrones educativos
        pattern_matches = sum(1 for pattern in self.educational_patterns 
                            if re.search(pattern, question_lower))
        if pattern_matches > 0:
            confidence += 0.3 + (pattern_matches * 0.1)  # Máximo +0.5
        
        # 3. Consultas muy generales (bonus)
        general_indicators = ["plantas en general", "todo sobre", "información básica", 
                             "para principiantes", "conceptos básicos"]
        if any(indicator in question_lower for indicator in general_indicators):
            confidence += 0.4
        
        # 4. Consultas científicas generales
        scientific_terms = ["reino plantae", "eucarióticas", "autótrofas", "organismos",
                           "seres vivos", "vida en la tierra"]
        scientific_matches = sum(1 for term in scientific_terms if term in question_lower)
        if scientific_matches > 0:
            confidence += 0.3 + (scientific_matches * 0.1)
        
        # 5. Bonus por contexto
        if context:
            topic = context.get("topic", "").lower()
            if topic in ["general", "education", "basic"]:
                confidence += 0.2
        
        # 6. Penalización por especificidad
        # Si la pregunta es muy específica sobre especies o patologías,
        # reducir confianza para dejar paso a agentes especializados
        specific_indicators = [
            "malus domestica", "vitis vinifera", "solanum lycopersicum",
            "enfermedad", "hongo", "plaga", "tratamiento", "fungicida"
        ]
        
        specific_matches = sum(1 for indicator in specific_indicators if indicator in question_lower)
        if specific_matches > 0:
            confidence -= specific_matches * 0.15  # Reducir para temas específicos
        
        # Asegurar que esté en el rango válido
        return max(0.1, min(confidence, 1.0))  # Mínimo 0.1 para mantener como fallback
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        Procesa la pregunta usando el RAG general.
        
        Args:
            question: Pregunta del usuario
            session_id: ID de la sesión
            **kwargs: include_sources, context, etc.
            
        Returns:
            Tuple[str, Dict]: (respuesta, metadatos)
        """
        context_logger = get_logger_with_context(
            chat_session_id=session_id,
            agent_type=self.name,
            topic="general"
        )
        
        try:
            context_logger.info(f"Procesando pregunta general: {question[:100]}...")
            
            # Procesar con el RAG general
            answer, metadata = self.rag_service.query(
                question=question,
                topic="general",
                session_id=session_id,
                include_sources=kwargs.get("include_sources", False)
            )
            
            # Enriquecer respuesta con información educativa
            enhanced_answer = self._enhance_educational_answer(answer, question)
            
            # Agregar metadatos específicos del agente
            metadata.update({
                "agent_type": self.name,
                "agent_description": self.description,
                "specialization": "conocimiento_general",
                "enhanced": enhanced_answer != answer,
                "educational_level": self._assess_educational_level(question),
                "is_fallback": self._is_fallback_case(question)
            })
            
            context_logger.info("Pregunta procesada exitosamente por GeneralAgent")
            
            return enhanced_answer, metadata
            
        except Exception as e:
            context_logger.error(f"Error en GeneralAgent: {e}")
            raise
    
    def _enhance_educational_answer(self, answer: str, question: str) -> str:
        """
        Mejora la respuesta añadiendo contexto educativo.
        
        Args:
            answer: Respuesta original del RAG
            question: Pregunta original
            
        Returns:
            str: Respuesta mejorada
        """
        question_lower = question.lower()
        
        # Añadir contexto para consultas básicas
        basic_questions = ["qué es", "qué son", "cómo funciona"]
        if any(q in question_lower for q in basic_questions) and len(answer) < 400:
            answer += "\n\n📚 **Para saber más**: Si te interesa profundizar en este tema, puedes preguntar sobre aspectos específicos o relacionados."
        
        # Añadir curiosidades para temas científicos
        scientific_terms = ["fotosíntesis", "evolución", "adaptación", "clasificación"]
        if any(term in question_lower for term in scientific_terms):
            if "interesante" not in answer.lower() and len(answer) < 500:
                answer += "\n\n🔬 **Dato curioso**: Las plantas han desarrollado estrategias fascinantes para sobrevivir y adaptarse a diferentes ambientes a lo largo de millones de años."
        
        # Añadir enlaces conceptuales
        if "diferencia" in question_lower or "tipos" in question_lower:
            if len(answer) < 400:
                answer += "\n\n🌿 **Conexión**: Estas diferencias son resultado de la evolución y adaptación a diferentes nichos ecológicos."
        
        # Sugerir temas relacionados para preguntas muy generales
        if len(question) < 50 and any(word in question_lower for word in ["plantas", "botánica", "información"]):
            answer += "\n\n💡 **Sugerencias**: Puedes preguntar sobre temas específicos como cuidados, especies concretas, enfermedades, o procesos biológicos."
        
        return answer
    
    def _assess_educational_level(self, question: str) -> str:
        """
        Evalúa el nivel educativo aparente de la pregunta.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            str: Nivel educativo estimado
        """
        question_lower = question.lower()
        
        # Términos técnicos avanzados
        advanced_terms = ["filogenia", "taxonomía", "metabolismo secundario", 
                         "sistemática", "biogeografía", "especiación"]
        if any(term in question_lower for term in advanced_terms):
            return "avanzado"
        
        # Términos técnicos intermedios
        intermediate_terms = ["fotosíntesis", "respiración celular", "clasificación",
                             "evolución", "adaptación", "biodiversidad"]
        if any(term in question_lower for term in intermediate_terms):
            return "intermedio"
        
        # Preguntas básicas
        basic_patterns = ["qué es", "qué son", "cómo funciona", "por qué"]
        if any(pattern in question_lower for pattern in basic_patterns):
            return "básico"
        
        return "general"
    
    def _is_fallback_case(self, question: str) -> bool:
        """
        Determina si esta es una respuesta fallback.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            bool: True si es un caso fallback
        """
        # Si la confianza es muy baja (cerca del mínimo), probablemente es fallback
        confidence = self.can_handle(question)
        return confidence <= 0.3
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Devuelve las capacidades específicas de este agente.
        
        Returns:
            Dict con información detallada de capacidades
        """
        return {
            **super().get_capabilities(),
            "specializations": [
                "Información general de botánica",
                "Conceptos educativos básicos",
                "Consultas divulgativas",
                "Preguntas científicas generales",
                "Agente fallback"
            ],
            "educational_levels": [
                "Básico - Conceptos fundamentales",
                "Intermedio - Procesos biológicos", 
                "Avanzado - Términos científicos",
                "General - Información divulgativa"
            ],
            "query_types": [
                "Definiciones y conceptos",
                "Procesos biológicos generales",
                "Clasificación y taxonomía básica",
                "Curiosidades y datos interesantes",
                "Información educativa"
            ],
            "supported_queries": [
                "¿Qué es la fotosíntesis?",
                "¿Cómo se clasifican las plantas?",
                "Diferencias entre tipos de plantas",
                "Curiosidades sobre el reino vegetal",
                "Información general sobre botánica"
            ],
            "fallback_role": True
        }