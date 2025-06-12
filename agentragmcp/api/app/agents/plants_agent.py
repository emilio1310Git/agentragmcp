"""
Agente especializado en información general de plantas
"""
import re
from typing import Dict, List, Optional, Tuple, Any

from agentragmcp.api.app.agents.base_agent import BaseAgent
from agentragmcp.api.app.services.rag_service import RAGService
from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger, get_logger_with_context

class PlantsAgent(BaseAgent):
    """
    Agente especializado en información general de plantas.
    
    Se enfoca en:
    - Información botánica general
    - Cuidados y cultivo
    - Características de especies específicas
    - Técnicas de jardinería
    """
    
    def __init__(self, rag_service: RAGService):
        super().__init__(
            name="plants",
            description="Especialista en información general de plantas, cultivo y botánica",
            topics=["plants"],
            rag_service=rag_service
        )
        
        settings = get_settings()
        
        # Palabras clave generales sobre plantas
        self.plant_keywords = {
            # Términos botánicos básicos
            "planta", "plantas", "árbol", "árboles", "arbusto", "arbustos",
            "hierba", "hierbas", "vegetal", "vegetales", "botánica", "botánico",
            
            # Partes de las plantas
            "hoja", "hojas", "flor", "flores", "fruto", "frutos", "fruta", "frutas",
            "raíz", "raíces", "tallo", "tallos", "rama", "ramas", "corteza",
            "semilla", "semillas", "brote", "brotes", "yema", "yemas",
            
            # Cultivo y cuidados
            "cultivo", "cultivar", "sembrar", "plantar", "trasplantar",
            "riego", "regar", "fertilizar", "fertilizante", "abono", "abonar",
            "poda", "podar", "injerto", "injertar", "reproducción",
            
            # Espacios de cultivo
            "jardín", "huerto", "maceta", "tiesto", "invernadero",
            "terraza", "balcón", "campo", "plantación",
            
            # Procesos biológicos
            "crecimiento", "germinación", "floración", "fructificación",
            "fotosíntesis", "respiración", "transpiración",
            
            # Condiciones ambientales
            "luz", "sombra", "sol", "temperatura", "humedad", "suelo",
            "tierra", "substrato", "pH", "nutrientes", "agua"
        }
        
        # Especies específicas configuradas
        self.specific_species = set()
        for species in settings.SPECIFIC_SPECIES:
            # Agregar nombre completo y partes separadas
            self.specific_species.add(species.lower())
            # Agregar género y especie por separado
            parts = species.split()
            if len(parts) >= 2:
                self.specific_species.add(parts[0].lower())  # Género
                self.specific_species.add(parts[1].lower())  # Especie
        
        # Nombres comunes de especies importantes
        self.common_names = {
            "manzano", "manzana", "cerezo", "cereza", "vid", "uva",
            "naranjo", "naranja", "melocotonero", "melocotón", "durazno",
            "fresa", "fresón", "tomate", "tomatera", "guayaba", "guayabo",
            "limón", "limonero", "mango", "granado", "granada",
            "albaricoque", "damasco", "arándano", "pera", "peral"
        }
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """
        Evalúa si puede manejar la pregunta sobre plantas.
        
        Returns:
            float: Confianza entre 0.0 y 1.0
        """
        question_lower = question.lower()
        confidence = 0.0
        
        # 1. Buscar palabras clave generales (peso base)
        keyword_matches = sum(1 for keyword in self.plant_keywords if keyword in question_lower)
        if keyword_matches > 0:
            confidence += 0.3 + (keyword_matches * 0.05)  # Máximo +0.5
        
        # 2. Buscar especies específicas (peso alto)
        species_matches = sum(1 for species in self.specific_species if species in question_lower)
        if species_matches > 0:
            confidence += 0.4 + (species_matches * 0.1)  # Máximo +0.7
        
        # 3. Buscar nombres comunes (peso medio)
        common_matches = sum(1 for name in self.common_names if name in question_lower)
        if common_matches > 0:
            confidence += 0.3 + (common_matches * 0.1)  # Máximo +0.5
        
        # 4. Patrones específicos de consultas sobre plantas
        plant_patterns = [
            r"cómo.*cultivar",
            r"cuándo.*plantar",
            r"qué.*planta",
            r"características.*de.*\w+",
            r"cuidados.*de",
            r"información.*sobre.*\w+",
            r"variedades.*de",
            r"especies.*de",
            r"tipos.*de.*plantas",
            r"plantas.*para",
            r"necesita.*luz",
            r"regar.*cada",
            r"mejor.*época.*para"
        ]
        
        pattern_matches = sum(1 for pattern in plant_patterns if re.search(pattern, question_lower))
        if pattern_matches > 0:
            confidence += 0.2 + (pattern_matches * 0.1)  # Máximo +0.5
        
        # 5. Bonus por contexto específico
        if context:
            topic = context.get("topic", "").lower()
            if topic in ["plants", "botany", "gardening"]:
                confidence += 0.2
        
        # 6. Penalización por palabras de otros dominios
        penalty_keywords = {
            "enfermedad", "enfermo", "plaga", "hongo", "bacteria", "virus",
            "tratamiento", "fungicida", "insecticida", "síntomas", "infección"
        }
        
        penalty_matches = sum(1 for keyword in penalty_keywords if keyword in question_lower)
        if penalty_matches > 0:
            confidence -= penalty_matches * 0.1  # Reducir confianza para temas de patología
        
        # Asegurar que esté en el rango válido
        return max(0.0, min(confidence, 1.0))
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        Procesa la pregunta usando el RAG de plantas.
        
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
            topic="plants"
        )
        
        try:
            context_logger.info(f"Procesando pregunta sobre plantas: {question[:100]}...")
            
            # Procesar con el RAG de plantas
            answer, metadata = self.rag_service.query(
                question=question,
                topic="plants",
                session_id=session_id,
                include_sources=kwargs.get("include_sources", False)
            )
            
            # Enriquecer respuesta si es necesario
            enhanced_answer = self._enhance_answer(answer, question)
            
            # Agregar metadatos específicos del agente
            metadata.update({
                "agent_type": self.name,
                "agent_description": self.description,
                "specialization": "plantas_generales",
                "enhanced": enhanced_answer != answer
            })
            
            context_logger.info("Pregunta procesada exitosamente por PlantsAgent")
            
            return enhanced_answer, metadata
            
        except Exception as e:
            context_logger.error(f"Error en PlantsAgent: {e}")
            raise
    
    def _enhance_answer(self, answer: str, question: str) -> str:
        """
        Mejora la respuesta añadiendo información contextual específica.
        
        Args:
            answer: Respuesta original del RAG
            question: Pregunta original
            
        Returns:
            str: Respuesta mejorada
        """
        question_lower = question.lower()
        
        # Añadir consejos específicos para cuidados básicos
        care_keywords = ["cuidar", "cuidado", "mantener", "cultivar"]
        if any(keyword in question_lower for keyword in care_keywords):
            if "riego" not in answer.lower() and len(answer) < 500:
                answer += "\n\n💡 **Consejo adicional**: Recuerda que la mayoría de plantas necesitan un riego regular pero sin encharcar, y es mejor regar por la mañana temprano."
        
        # Añadir información estacional
        season_keywords = ["cuándo", "época", "momento", "temporada"]
        if any(keyword in question_lower for keyword in season_keywords):
            if "primavera" not in answer.lower() and len(answer) < 500:
                answer += "\n\n🌱 **Nota estacional**: Ten en cuenta que muchas actividades de jardinería están influenciadas por la estación del año y tu zona climática."
        
        # Añadir advertencias sobre especies específicas
        toxic_plants = ["ricino", "adelfa", "tejo", "digital"]
        if any(plant in question_lower for plant in toxic_plants):
            if "tóxico" not in answer.lower() and "venenoso" not in answer.lower():
                answer += "\n\n⚠️ **Importante**: Esta planta puede ser tóxica. Mantén alejada de niños y mascotas."
        
        return answer
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Devuelve las capacidades específicas de este agente.
        
        Returns:
            Dict con información detallada de capacidades
        """
        return {
            **super().get_capabilities(),
            "specializations": [
                "Información botánica general",
                "Cuidados y cultivo de plantas",
                "Técnicas de jardinería",
                "Características de especies",
                "Reproducción y propagación"
            ],
            "species_coverage": len(self.specific_species),
            "keyword_categories": [
                "Términos botánicos",
                "Partes de plantas", 
                "Técnicas de cultivo",
                "Espacios de cultivo",
                "Procesos biológicos",
                "Condiciones ambientales"
            ],
            "supported_queries": [
                "¿Cómo cuidar [planta]?",
                "¿Cuándo plantar [especie]?",
                "Características de [planta]",
                "Técnicas de propagación",
                "Condiciones de cultivo"
            ]
        }