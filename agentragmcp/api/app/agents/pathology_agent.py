"""
Agente especializado en patologías y enfermedades de plantas
"""
import re
from typing import Dict, List, Optional, Tuple, Any

from agentragmcp.api.app.agents.base_agent import BaseAgent
from agentragmcp.api.app.services.rag_service import RAGService
from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger, get_logger_with_context

class PathologyAgent(BaseAgent):
    """
    Agente especializado en patologías, enfermedades y tratamientos de plantas.
    
    Se enfoca en:
    - Diagnóstico de enfermedades
    - Identificación de plagas
    - Tratamientos y control
    - Prevención de problemas
    """
    
    def __init__(self, rag_service: RAGService):
        super().__init__(
            name="pathology",
            description="Especialista en patologías, enfermedades, plagas y tratamientos de plantas",
            topics=["pathology"],
            rag_service=rag_service
        )
        
        settings = get_settings()
        
        # Palabras clave relacionadas con patologías
        self.pathology_keywords = {
            # Tipos de patógenos
            "enfermedad", "enfermedades", "patología", "patologías",
            "hongo", "hongos", "fúngico", "micosis",
            "bacteria", "bacterias", "bacteriano", "bacteriosis",
            "virus", "viral", "virosis", "virótico",
            "fitoplasma", "nematodo", "nematodos",
            
            # Plagas y insectos
            "plaga", "plagas", "insecto", "insectos", "parásito", "parásitos",
            "pulgón", "pulgones", "cochinilla", "trips", "mosca", "moscas",
            "araña", "ácaros", "orugas", "larvas", "gusano", "gusanos",
            "minador", "barrenador", "perforador",
            
            # Síntomas visibles
            "mancha", "manchas", "lesión", "lesiones", "necrosis",
            "amarilleo", "amarillamiento", "clorosis", "decoloración",
            "marchitez", "marchitamiento", "podredumbre", "pudrición",
            "chancro", "cancro", "tumor", "agalla", "deformación",
            "enrollamiento", "rizado", "mosaico", "rayado",
            
            # Tratamientos y control
            "tratamiento", "tratar", "curar", "controlar", "control",
            "fungicida", "bactericida", "insecticida", "acaricida",
            "pesticida", "fitosanitario", "prevenir", "prevención",
            "resistencia", "inmunidad", "tolerancia",
            
            # Estados de la planta
            "enfermo", "enferma", "infectado", "afectado", "dañado",
            "débil", "muerto", "muriendo", "deterioro", "decline"
        }
        
        # Especies con conocimiento específico de patologías
        self.pathology_species = set()
        for species in settings.PATHOLOGY_SPECIES:
            self.pathology_species.add(species.lower())
            # Agregar nombres por partes
            parts = species.split()
            if len(parts) >= 2:
                self.pathology_species.add(parts[0].lower())
                self.pathology_species.add(parts[1].lower())
        
        # Nombres comunes de especies con patologías conocidas
        self.pathology_common_names = {
            "manzano", "manzana", "vid", "uva", "parra",
            "naranjo", "naranja", "cítrico", "cítricos",
            "tomate", "tomatera", "jitomate"
        }
        
        # Enfermedades específicas conocidas
        self.specific_diseases = {
            "mildiu", "oídio", "roya", "antracnosis", "botritis",
            "fusarium", "verticillium", "pythium", "phytophthora",
            "alternaria", "septoria", "cercospora", "stemphylium",
            "cladosporium", "penicillium", "rhizoctonia", "sclerotinia",
            "erwinia", "pseudomonas", "xanthomonas", "agrobacterium",
            "virus y", "virus x", "virus del mosaico", "tristeza"
        }
    
    def can_handle(self, question: str, context: Optional[Dict] = None) -> float:
        """
        Evalúa si puede manejar la pregunta sobre patologías.
        
        Returns:
            float: Confianza entre 0.0 y 1.0
        """
        question_lower = question.lower()
        confidence = 0.0
        
        # 1. Palabras clave de patologías (peso alto)
        pathology_matches = sum(1 for keyword in self.pathology_keywords if keyword in question_lower)
        if pathology_matches > 0:
            confidence += 0.5 + (pathology_matches * 0.08)  # Máximo +0.9
        
        # 2. Especies específicas para patologías (peso alto)
        species_matches = sum(1 for species in self.pathology_species if species in question_lower)
        if species_matches > 0:
            confidence += 0.3 + (species_matches * 0.15)  # Máximo +0.6
        
        # 3. Nombres comunes de especies con patologías (peso medio)
        common_matches = sum(1 for name in self.pathology_common_names if name in question_lower)
        if common_matches > 0:
            confidence += 0.3 + (common_matches * 0.1)  # Máximo +0.5
        
        # 4. Enfermedades específicas (peso muy alto)
        disease_matches = sum(1 for disease in self.specific_diseases if disease in question_lower)
        if disease_matches > 0:
            confidence += 0.6 + (disease_matches * 0.1)  # Máximo +0.8
        
        # 5. Patrones específicos de consultas sobre patologías
        pathology_patterns = [
            r"qué.*enfermedad",
            r"cómo.*tratar",
            r"síntomas.*de",
            r"problema.*con",
            r"se.*está.*muriendo",
            r"hojas.*amarillas",
            r"manchas.*en",
            r"por.*qué.*se.*muere",
            r"está.*enferm[oa]",
            r"tiene.*\w+.*manchas",
            r"control.*de.*plagas",
            r"fungicida.*para",
            r"prevenir.*enfermedades"
        ]
        
        pattern_matches = sum(1 for pattern in pathology_patterns if re.search(pattern, question_lower))
        if pattern_matches > 0:
            confidence += 0.4 + (pattern_matches * 0.1)  # Máximo +0.7
        
        # 6. Indicadores visuales de problemas
        visual_indicators = [
            "amarill", "marchit", "seca", "negro", "marrón", "blanco",
            "punto", "raya", "agujero", "deform", "encog", "curl"
        ]
        
        visual_matches = sum(1 for indicator in visual_indicators 
                           if indicator in question_lower and len(question_lower) > 20)
        if visual_matches > 0:
            confidence += 0.2 + (visual_matches * 0.05)  # Máximo +0.4
        
        # 7. Bonus por contexto específico
        if context:
            topic = context.get("topic", "").lower()
            if topic in ["pathology", "disease", "pest", "treatment"]:
                confidence += 0.3
        
        # 8. Bonus por términos técnicos
        technical_terms = [
            "fitopatología", "fitosanitario", "etiología", "diagnóstico",
            "profilaxis", "epidemiología", "resistencia genética"
        ]
        
        tech_matches = sum(1 for term in technical_terms if term in question_lower)
        if tech_matches > 0:
            confidence += tech_matches * 0.2  # Máximo +0.4
        
        # Asegurar que esté en el rango válido
        return max(0.0, min(confidence, 1.0))
    
    def process(self, question: str, session_id: str, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        Procesa la pregunta usando el RAG de patologías.
        
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
            topic="pathology"
        )
        
        try:
            context_logger.info(f"Procesando pregunta sobre patologías: {question[:100]}...")
            
            # Procesar con el RAG de patologías
            answer, metadata = self.rag_service.query(
                question=question,
                topic="pathology",
                session_id=session_id,
                include_sources=kwargs.get("include_sources", False)
            )
            
            # Enriquecer respuesta con información específica de patologías
            enhanced_answer = self._enhance_pathology_answer(answer, question)
            
            # Agregar metadatos específicos del agente
            metadata.update({
                "agent_type": self.name,
                "agent_description": self.description,
                "specialization": "patologias_plantas",
                "enhanced": enhanced_answer != answer,
                "diagnostic_context": self._extract_diagnostic_context(question)
            })
            
            context_logger.info("Pregunta procesada exitosamente por PathologyAgent")
            
            return enhanced_answer, metadata
            
        except Exception as e:
            context_logger.error(f"Error en PathologyAgent: {e}")
            raise
    
    def _enhance_pathology_answer(self, answer: str, question: str) -> str:
        """
        Mejora la respuesta añadiendo información específica de patologías.
        
        Args:
            answer: Respuesta original del RAG
            question: Pregunta original
            
        Returns:
            str: Respuesta mejorada
        """
        question_lower = question.lower()
        
        # Añadir recordatorios sobre prevención
        if any(word in question_lower for word in ["tratar", "curar", "tratamiento"]):
            if "prevención" not in answer.lower() and len(answer) < 600:
                answer += "\n\n🛡️ **Prevención**: Recuerda que prevenir es mejor que curar. Mantén buenas prácticas de higiene, ventilación adecuada y evita el exceso de humedad."
        
        # Añadir advertencias sobre productos químicos
        chemical_words = ["fungicida", "insecticida", "pesticida", "químico"]
        if any(word in question_lower for word in chemical_words):
            if "seguridad" not in answer.lower() and "protección" not in answer.lower():
                answer += "\n\n⚠️ **Seguridad**: Usa siempre equipos de protección al aplicar productos fitosanitarios y respeta los tiempos de seguridad."
        
        # Añadir información sobre resistencias
        if "resistencia" in question_lower or "inmune" in question_lower:
            if len(answer) < 500:
                answer += "\n\n🧬 **Resistencia genética**: Considera variedades resistentes como la mejor estrategia a largo plazo."
        
        # Añadir consejos de diagnóstico
        diagnostic_words = ["síntomas", "diagnóstico", "identificar", "qué enfermedad"]
        if any(word in question_lower for word in diagnostic_words):
            if "observar" not in answer.lower() and len(answer) < 500:
                answer += "\n\n🔍 **Diagnóstico**: Observa patrones de síntomas, condiciones ambientales y momento de aparición para un diagnóstico más preciso."
        
        return answer
    
    def _extract_diagnostic_context(self, question: str) -> Dict[str, Any]:
        """
        Extrae contexto diagnóstico de la pregunta.
        
        Args:
            question: Pregunta del usuario
            
        Returns:
            Dict con contexto diagnóstico
        """
        question_lower = question.lower()
        context = {
            "symptoms_mentioned": [],
            "species_mentioned": [],
            "timing_mentioned": False,
            "treatment_focus": False
        }
        
        # Síntomas mencionados
        symptoms = ["mancha", "amarillo", "marchito", "seco", "negro", "blanco", "podredumbre"]
        context["symptoms_mentioned"] = [s for s in symptoms if s in question_lower]
        
        # Especies mencionadas
        context["species_mentioned"] = [s for s in self.pathology_species if s in question_lower]
        
        # Referencias temporales
        timing_words = ["cuándo", "época", "ahora", "primavera", "verano", "otoño", "invierno"]
        context["timing_mentioned"] = any(word in question_lower for word in timing_words)
        
        # Enfoque en tratamiento
        treatment_words = ["tratar", "curar", "control", "fungicida", "tratamiento"]
        context["treatment_focus"] = any(word in question_lower for word in treatment_words)
        
        return context
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Devuelve las capacidades específicas de este agente.
        
        Returns:
            Dict con información detallada de capacidades
        """
        return {
            **super().get_capabilities(),
            "specializations": [
                "Diagnóstico de enfermedades",
                "Identificación de plagas", 
                "Tratamientos fitosanitarios",
                "Estrategias de prevención",
                "Control integrado de plagas"
            ],
            "pathogen_types": [
                "Hongos y enfermedades fúngicas",
                "Bacterias fitopatógenas", 
                "Virus de plantas",
                "Insectos plaga",
                "Ácaros y nematodos"
            ],
            "target_species": list(self.pathology_species),
            "diagnostic_capabilities": [
                "Análisis de síntomas",
                "Identificación de patógenos",
                "Evaluación de daños",
                "Recomendaciones de tratamiento"
            ],
            "supported_queries": [
                "¿Qué enfermedad tiene mi [planta]?",
                "¿Cómo tratar [enfermedad]?",
                "Síntomas de [patología]",
                "Control de [plaga] en [cultivo]",
                "Prevenir enfermedades en [especie]"
            ]
        }