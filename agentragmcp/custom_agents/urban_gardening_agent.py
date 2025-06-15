"""
Agente especializado en jardinería urbana y espacios reducidos
"""

from typing import List, Optional, Dict, Any
from agentragmcp.api.app.agents.dinamic_agent import DynamicAgent

class UrbanGardeningAgent(DynamicAgent):
    """Agente especializado en jardinería urbana"""
    
    def __init__(self, config: Dict[str, Any], rag_service):
        super().__init__("urban_gardening", config, rag_service)
        self.space_types = config.get("space_types", [])
    
    def calculate_confidence(self, question: str) -> float:
        """Calcula confianza específica para jardinería urbana"""
        confidence = super().calculate_confidence(question)
        
        # Bonus por términos de espacios urbanos
        urban_terms = [
            "balcón", "terraza", "interior", "urbano", "maceta",
            "apartamento", "espacio pequeño", "vertical"
        ]
        
        question_lower = question.lower()
        urban_matches = sum(1 for term in urban_terms if term in question_lower)
        
        if urban_matches > 0:
            space_bonus = min(urban_matches * 0.15, 0.3)
            confidence += space_bonus
        
        return min(confidence, 1.0)
    
    def enhance_response(self, response: str, question: str) -> str:
        """Mejora la respuesta con enfoque urbano"""
        enhanced = response
        
        # Añadir consideraciones de espacio
        if any(term in question.lower() for term in ["cultivar", "plantar"]):
            enhanced += "\n\n🏙️ **Adaptación Urbana**: Considera las limitaciones de espacio y contenedores."
        
        if "riego" in question.lower():
            enhanced += "\n\n💧 **Riego Urbano**: Sistemas de autorriego son ideales para balcones."
        
        return enhanced
