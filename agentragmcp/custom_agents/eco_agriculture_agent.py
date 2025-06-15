"""
Agente especializado en agricultura ecológica y sostenible
"""

from typing import List, Optional, Dict, Any
from agentragmcp.api.app.agents.dinamic_agent import DynamicAgent

class EcoAgricultureAgent(DynamicAgent):
    """Agente especializado en agricultura ecológica"""
    
    def __init__(self, config: Dict[str, Any], rag_service):
        super().__init__("eco_agriculture", config, rag_service)
        self.focus_areas = config.get("focus_areas", [])
    
    def calculate_confidence(self, question: str) -> float:
        """Calcula confianza específica para agricultura ecológica"""
        confidence = super().calculate_confidence(question)
        
        # Bonus por términos específicos de agricultura ecológica
        eco_terms = [
            "ecológico", "orgánico", "sostenible", "biodiversidad",
            "permacultura", "compost", "rotación", "natural"
        ]
        
        question_lower = question.lower()
        eco_matches = sum(1 for term in eco_terms if term in question_lower)
        
        if eco_matches > 0:
            eco_bonus = min(eco_matches * 0.2, 0.4)
            confidence += eco_bonus
        
        return min(confidence, 1.0)
    
    def enhance_response(self, response: str, question: str) -> str:
        """Mejora la respuesta con enfoque ecológico"""
        enhanced = response
        
        # Añadir consideraciones ecológicas
        if any(term in question.lower() for term in ["tratamiento", "control", "plaga"]):
            enhanced += "\n\n🌱 **Enfoque Ecológico**: Considera siempre alternativas naturales y sostenibles."
        
        if "cultivo" in question.lower():
            enhanced += "\n\n♻️ **Sostenibilidad**: Recuerda mantener la salud del suelo y la biodiversidad."
        
        return enhanced
