"""
Agente personalizado para agricultura ecológica
Ejemplo de cómo crear agentes especializados
"""
from typing import Dict, List, Optional, Tuple, Any
import re

from agentragmcp.api.app.services.dynamic_agent_system import ConfigurableAgent
from agentragmcp.core.monitoring import get_logger_with_context

class EcoAgricultureAgent(ConfigurableAgent):
    """
    Agente especializado en agricultura ecológica y sostenible
    Ejemplo de agente personalizado configurable
    """
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """Evaluación personalizada para agricultura ecológica"""
        
        # Usar evaluación base de configuración
        base_confidence = super().can_handle(question, context)
        
        question_lower = question.lower()
        
        # Términos específicos de agricultura ecológica
        eco_terms = [
            "ecológico", "orgánico", "sostenible", "natural", "biodiversidad",
            "permacultura", "compost", "biológico", "sin químicos", "certificado"
        ]
        
        eco_matches = sum(1 for term in eco_terms if term in question_lower)
        if eco_matches > 0:
            base_confidence += eco_matches * 0.15
        
        # Bonus por métodos sostenibles
        sustainable_methods = [
            "rotación", "cultivos asociados", "abono verde", "mulch",
            "depredadores naturales", "extractos vegetales"
        ]
        
        method_matches = sum(1 for method in sustainable_methods if method in question_lower)
        if method_matches > 0:
            base_confidence += method_matches * 0.1
        
        # Penalización por química convencional
        chemical_terms = ["pesticida", "herbicida", "químico sintético", "fertilizante químico"]
        chemical_matches = sum(1 for term in chemical_terms if term in question_lower)
        if chemical_matches > 0:
            base_confidence -= chemical_matches * 0.1
        
        # Aplicar límites
        return max(self.config.min_confidence, 
                  min(base_confidence, self.config.max_confidence))
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """Procesa pregunta con enfoque ecológico"""
        
        context_logger = get_logger_with_context(
            chat_session_id=session_id,
            agent_type=self.name
        )
        
        try:
            context_logger.info("Procesando con agente de agricultura ecológica")
            
            # Usar RAG específico de agricultura ecológica
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
                "enhanced": enhanced_answer != answer,
                "custom_agent": True
            })
            
            return enhanced_answer, metadata
            
        except Exception as e:
            context_logger.error(f"Error en EcoAgricultureAgent: {e}")
            raise
    
    def _enhance_eco_answer(self, answer: str, question: str) -> str:
        """Mejora respuesta con enfoque ecológico"""
        
        question_lower = question.lower()
        
        # Añadir consejos ecológicos
        if any(word in question_lower for word in ["cómo", "cultivar", "plantar", "tratar"]):
            if "ecológico" not in answer.lower() and len(answer) < 500:
                answer += "\\n\\n🌱 **Enfoque ecológico**: Considera métodos naturales como compost, rotación de cultivos y control biológico."
        
        # Advertir sobre productos químicos
        if any(word in question_lower for word in ["pesticida", "químico", "fertilizante"]):
            if "alternativa" not in answer.lower():
                answer += "\\n\\n🌿 **Alternativa sostenible**: Explora opciones orgánicas y naturales antes de usar productos químicos sintéticos."
        
        # Información sobre certificación
        if "certificado" in question_lower or "orgánico" in question_lower:
            if len(answer) < 400:
                answer += "\\n\\n📜 **Certificación**: Consulta los estándares de agricultura ecológica de tu región para cumplir requisitos oficiales."
        
        return answer