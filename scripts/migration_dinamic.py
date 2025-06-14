#!/usr/bin/env python3
"""
Script de migración para convertir el sistema AgentRagMCP 
de configuración hardcodeada a sistema dinámico
"""

import os
import sys
import yaml
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from agentragmcp.core.dynamic_config import ConfigManager

class AgentRagMCPMigrator:
    """Migrador del sistema AgentRagMCP a configuración dinámica"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.config_manager = ConfigManager(str(self.base_path / "data" / "configs"))
        
        print(f"🔄 Iniciando migración en: {self.base_path}")
    
    def migrate_full_system(self):
        """Migra todo el sistema al nuevo formato"""
        print("\n" + "="*60)
        print("🚀 MIGRACIÓN COMPLETA A SISTEMA DINÁMICO")
        print("="*60)
        
        steps = [
            ("📁 Crear estructura de directorios", self.setup_directory_structure),
            ("📋 Migrar configuraciones RAG", self.migrate_rag_configs),
            ("🤖 Migrar configuraciones de agentes", self.migrate_agent_configs),
            ("📚 Crear ejemplos personalizados", self.create_custom_examples),
            ("✅ Validar migración", self.validate_migration),
            ("📖 Crear documentación", self.create_migration_docs)
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            try:
                step_func()
                print(f"✅ {step_name} completado")
            except Exception as e:
                print(f"❌ Error en {step_name}: {e}")
                raise
        
        print(f"\n🎉 ¡Migración completada exitosamente!")
        print(f"📍 Configuraciones en: {self.config_manager.config_base_path}")
    
    def setup_directory_structure(self):
        """Crea la estructura de directorios para el sistema dinámico"""
        directories = [
            "data/configs/rags",
            "data/configs/agents",
            "data/configs/custom",
            "data/documents/eco_agriculture",
            "data/documents/urban_gardening", 
            "data/documents/permaculture",
            "data/vectorstores/eco_agriculture",
            "data/vectorstores/urban_gardening",
            "data/vectorstores/permaculture",
            "agentragmcp/custom_agents"
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   📁 {directory}")
        
        # Crear archivo __init__.py para custom_agents
        init_file = self.base_path / "agentragmcp" / "custom_agents" / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Custom agents module\n")
    
    def migrate_rag_configs(self):
        """Migra las configuraciones RAG hardcodeadas a archivos individuales"""
        
        # Configuración base extraída del código existente
        rag_configs = {
            "plants": {
                "display_name": "Plantas y Botánica General",
                "description": "Información general sobre plantas, cultivo, cuidados y botánica",
                "enabled": True,
                "priority": 1,
                "vectorstore": {
                    "type": "chroma",
                    "path": "./data/vectorstores/plants",
                    "collection_name": "plants_collection",
                    "chunk_size": 1000,
                    "chunk_overlap": 200,
                    "embedding_model": "llama3.1",
                    "embedding_base_url": "http://localhost:11434"
                },
                "retrieval": {
                    "search_type": "mmr",
                    "k": 5,
                    "fetch_k": 20,
                    "lambda_mult": 0.7,
                    "score_threshold": 0.5
                },
                "system_prompt": """Eres un especialista en botánica y plantas. Tu conocimiento incluye:

**Especialidades principales:**
- Información botánica general de plantas
- Cuidados y técnicas de cultivo
- Características de especies específicas (especialmente Malus domestica, Prunus cerasus, Vitis vinifera, Citrus aurantium, Prunus persica, Fragaria vesca, Solanum lycopersicum, Psidium guajava, Syzygium cumini, Citrus limon, Mangifera indica, Punica granatum, Prunus armeniaca, Vaccinium macrocarpon, Pyrus communis)
- Técnicas de jardinería y horticultura

**Instrucciones de respuesta:**
- Proporciona información práctica y científicamente fundamentada
- Incluye consejos de cuidado cuando sea relevante
- Menciona condiciones ambientales necesarias
- Responde en español de España, de forma clara y educativa

{context}""",
                "categories": ["botánica_general", "cultivo_plantas", "cuidados_plantas", "especies_específicas"],
                "keywords": {
                    "primary": ["planta", "cultivo", "botánica", "jardín", "especie"],
                    "secondary": ["cuidado", "riego", "fertilización", "poda", "reproducción"]
                },
                "source_paths": ["./data/documents/plants"],
                "custom_settings": {
                    "specific_species": [
                        "Malus domestica", "Prunus cerasus", "Vitis vinifera", 
                        "Citrus aurantium", "Prunus persica", "Fragaria vesca", 
                        "Solanum lycopersicum", "Psidium guajava", "Syzygium cumini",
                        "Citrus limon", "Mangifera indica", "Punica granatum",
                        "Prunus armeniaca", "Vaccinium macrocarpon", "Pyrus communis"
                    ]
                }
            },
            
            "pathology": {
                "display_name": "Patologías y Enfermedades de Plantas",
                "description": "Diagnóstico, tratamiento y prevención de enfermedades y plagas en plantas",
                "enabled": True,
                "priority": 1,
                "vectorstore": {
                    "type": "chroma",
                    "path": "./data/vectorstores/pathology",
                    "collection_name": "pathology_collection",
                    "chunk_size": 800,
                    "chunk_overlap": 150,
                    "embedding_model": "llama3.1"
                },
                "retrieval": {
                    "search_type": "similarity_score_threshold",
                    "k": 7,
                    "score_threshold": 0.4
                },
                "system_prompt": """Eres un especialista en fitopatología y sanidad vegetal. Tu experiencia incluye:

**Especialidades principales:**
- Diagnóstico de enfermedades de plantas
- Identificación de plagas y patógenos
- Tratamientos fitosanitarios
- Estrategias de prevención y control integrado
- Patologías específicas en Malus domestica, Vitis vinifera, Citrus aurantium, Solanum lycopersicum

**Instrucciones de respuesta:**
- Proporciona diagnósticos basados en síntomas descritos
- Recomienda tratamientos apropiados y seguros
- Incluye medidas preventivas
- Advierte sobre el uso seguro de productos fitosanitarios

**IMPORTANTE:** Siempre incluye advertencias de seguridad para productos químicos.

{context}""",
                "categories": ["diagnóstico_enfermedades", "identificación_plagas", "tratamientos_fitosanitarios", "prevención_patologías"],
                "keywords": {
                    "primary": ["enfermedad", "plaga", "síntomas", "tratamiento", "control"],
                    "secondary": ["hongo", "bacteria", "virus", "insecto", "prevención"]
                },
                "source_paths": ["./data/documents/pathology"],
                "custom_settings": {
                    "target_species": ["Malus domestica", "Vitis vinifera", "Citrus aurantium", "Solanum lycopersicum"],
                    "safety_warnings": True
                }
            },
            
            "general": {
                "display_name": "Conocimiento General de Plantas",
                "description": "Información educativa y divulgativa sobre el mundo vegetal",
                "enabled": True,
                "priority": 2,
                "vectorstore": {
                    "type": "chroma",
                    "path": "./data/vectorstores/general",
                    "collection_name": "general_collection",
                    "chunk_size": 1200,
                    "chunk_overlap": 250
                },
                "retrieval": {
                    "search_type": "mmr",
                    "k": 4,
                    "fetch_k": 15,
                    "lambda_mult": 0.8
                },
                "system_prompt": """Eres un educador y divulgador científico especializado en botánica.

**Especialidades principales:**
- Educación botánica general
- Divulgación científica del mundo vegetal
- Conceptos fundamentales de biología vegetal
- Historia natural y evolución de plantas

**Instrucciones de respuesta:**
- Explica conceptos complejos de manera accesible
- Proporciona ejemplos concretos y analogías
- Incluye datos curiosos e interesantes
- Responde de forma clara, educativa y motivadora

{context}""",
                "categories": ["educación_botánica", "conceptos_básicos", "divulgación_científica"],
                "keywords": {
                    "primary": ["qué es", "cómo funciona", "por qué", "explicar", "botánica"],
                    "secondary": ["definición", "concepto", "información", "curiosidades", "aprender"]
                },
                "source_paths": ["./data/documents/general"]
            }
        }
        
        # Guardar cada configuración en su archivo
        rags_path = self.config_manager.config_base_path / "rags"
        for rag_name, config in rag_configs.items():
            config_file = rags_path / f"{rag_name}.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"   📄 {rag_name}.yaml")
        
        print(f"   ✅ {len(rag_configs)} configuraciones RAG migradas")
    
    def migrate_agent_configs(self):
        """Migra las configuraciones de agentes hardcodeadas"""
        
        agents_config = {
            "agents": {
                "plants": {
                    "description": "Especialista en información general de plantas, cultivo y botánica",
                    "class": "PlantsAgent",
                    "topics": ["plants"],
                    "enabled": True,
                    "priority": 1,
                    "config": {
                        "max_confidence": 1.0,
                        "min_confidence": 0.1,
                        "fallback_enabled": False,
                        "primary_keywords": [
                            "planta", "plantas", "árbol", "árboles", "cultivo", "cultivar",
                            "sembrar", "plantar", "jardín", "huerto", "botánica", "especie",
                            "fruto", "hoja", "flor", "raíz", "crecimiento", "cuidado"
                        ],
                        "patterns": [
                            "cómo.*cultivar", "cuándo.*plantar", "qué.*planta",
                            "características.*de", "cuidados.*de", "información.*sobre"
                        ],
                        "target_species": [
                            "Malus domestica", "Prunus cerasus", "Vitis vinifera",
                            "Citrus aurantium", "Prunus persica", "Fragaria vesca",
                            "Solanum lycopersicum"
                        ],
                        "common_names": [
                            "manzano", "manzana", "cerezo", "cereza", "vid", "uva",
                            "naranjo", "naranja", "tomate", "tomatera"
                        ]
                    }
                },

                "pathology": {
                    "description": "Especialista en patologías, enfermedades, plagas y tratamientos de plantas",
                    "class": "PathologyAgent",
                    "topics": ["pathology"],
                    "enabled": True,
                    "priority": 2,
                    "config": {
                        "max_confidence": 1.0,
                    }
                },
                
                "pathology": {
                    "description": "Especialista en patologías, enfermedades, plagas y tratamientos de plantas",
                    "class": "PathologyAgent",
                    "topics": ["pathology"],
                    "enabled": True,
                    "priority": 2,
                    "config": {
                        "max_confidence": 1.0,
                        "min_confidence": 0.1,
                        "fallback_enabled": False,
                        "primary_keywords": [
                            "enfermedad", "enfermedades", "patología", "patologías",
                            "plaga", "plagas", "hongo", "hongos", "bacteria", "bacterias",
                            "virus", "tratamiento", "síntomas", "control", "mancha", "manchas"
                        ],
                        "patterns": [
                            "qué.*enfermedad", "cómo.*tratar", "síntomas.*de",
                            "problema.*con", "se.*está.*muriendo", "hojas.*amarillas"
                        ],
                        "target_species": [
                            "Malus domestica", "Vitis vinifera", 
                            "Citrus aurantium", "Solanum lycopersicum"
                        ]
                    },
                    "thresholds": {
                        "keyword_weight": 0.5,
                        "symptom_weight": 0.3,
                        "species_weight": 0.3,
                        "pattern_weight": 0.4
                    }
                },
                
                "general": {
                    "description": "Asistente general para consultas diversas sobre plantas y botánica",
                    "class": "GeneralAgent",
                    "topics": ["general"],
                    "enabled": True,
                    "priority": 3,
                    "config": {
                        "max_confidence": 0.8,
                        "min_confidence": 0.1,
                        "fallback_enabled": True,
                        "primary_keywords": [
                            "qué es", "qué son", "cómo funciona", "por qué",
                            "explicar", "definir", "botánica", "información"
                        ],
                        "patterns": [
                            "qué.*es.*la?", "cómo.*funciona", "por.*qué.*las?.*plantas",
                            "diferencia.*entre", "tipos.*de.*plantas"
                        ]
                    },
                    "thresholds": {
                        "base_confidence": 0.2,
                        "educational_bonus": 0.3,
                        "general_bonus": 0.2
                    }
                }
            },
            
            "selector": {
                "selection_method": "hybrid",
                "rule_based": {
                    "enabled": True,
                    "confidence_threshold": 0.3
                },
                "llm_based": {
                    "enabled": True,
                    "min_agents_for_llm": 3,
                    "temperature": 0.1
                },
                "hybrid": {
                    "primary_method": "rule_based",
                    "fallback_method": "llm_based",
                    "llm_threshold": 0.5
                }
            },
            
            "metrics": {
                "track_agent_performance": True,
                "track_selection_accuracy": True,
                "log_confidence_scores": True,
                "alerts": {
                    "low_success_rate": 0.5,
                    "high_error_rate": 0.2
                }
            }
        }
        
        # Guardar configuración de agentes
        agents_file = self.config_manager.config_base_path / "agents.yaml"
        with open(agents_file, 'w', encoding='utf-8') as f:
            yaml.dump(agents_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"   📄 agents.yaml creado con {len(agents_config['agents'])} agentes")
    
    def create_custom_examples(self):
        """Crea ejemplos de RAGs y agentes personalizados"""
        
        # 1. RAG personalizado: Agricultura Ecológica
        eco_agriculture_config = {
            "display_name": "Agricultura Ecológica y Sostenible",
            "description": "Técnicas de agricultura ecológica, sostenible y permacultura",
            "enabled": True,
            "priority": 2,
            "vectorstore": {
                "type": "chroma",
                "path": "./data/vectorstores/eco_agriculture",
                "collection_name": "eco_agriculture_collection",
                "chunk_size": 1200,
                "chunk_overlap": 300,
                "embedding_model": "llama3.1"
            },
            "retrieval": {
                "search_type": "mmr",
                "k": 6,
                "fetch_k": 25,
                "lambda_mult": 0.8,
                "score_threshold": 0.5
            },
            "system_prompt": """Eres un especialista en agricultura ecológica y sostenible.

**Especialidades principales:**
- Técnicas de agricultura ecológica certificada
- Permacultura y diseño sostenible
- Manejo natural de plagas y enfermedades
- Mejora de la salud del suelo sin químicos
- Biodiversidad y conservación

**Enfoque:**
- Prioriza siempre métodos naturales y sostenibles
- Explica el impacto ambiental de las prácticas
- Incluye aspectos de certificación orgánica cuando sea relevante
- Fomenta la biodiversidad y el equilibrio ecológico

{context}""",
            "categories": ["agricultura_ecológica", "sostenibilidad", "permacultura", "biodiversidad"],
            "keywords": {
                "primary": ["ecológico", "orgánico", "sostenible", "permacultura", "natural"],
                "secondary": ["compost", "biodiversidad", "equilibrio", "certificado", "sin químicos"]
            },
            "source_paths": ["./data/documents/eco_agriculture"],
            "custom_settings": {
                "certification_standards": ["EU_Organic", "USDA_Organic", "JAS_Organic"],
                "focus_areas": ["soil_health", "biodiversity", "water_conservation", "energy_efficiency"],
                "avoid_recommendations": ["synthetic_pesticides", "chemical_fertilizers", "gmo_seeds"]
            }
        }
        
        # 2. RAG personalizado: Jardinería Urbana
        urban_gardening_config = {
            "display_name": "Jardinería Urbana y Espacios Pequeños",
            "description": "Cultivo en espacios urbanos, balcones, terrazas y jardines pequeños",
            "enabled": True,
            "priority": 2,
            "vectorstore": {
                "type": "chroma",
                "path": "./data/vectorstores/urban_gardening",
                "collection_name": "urban_gardening_collection",
                "chunk_size": 900,
                "chunk_overlap": 180
            },
            "retrieval": {
                "search_type": "similarity_score_threshold",
                "k": 5,
                "score_threshold": 0.6
            },
            "system_prompt": """Eres un especialista en jardinería urbana y cultivo en espacios reducidos.

**Especialidades principales:**
- Cultivo en macetas, contenedores y espacios pequeños
- Jardinería vertical y sistemas hidropónicos caseros
- Plantas adaptadas a ambientes urbanos
- Optimización de luz, agua y nutrientes en espacios limitados
- Jardines en balcones, terrazas y azoteas

**Enfoque:**
- Adapta todas las recomendaciones a espacios limitados
- Considera restricciones urbanas (luz, viento, espacio)
- Sugiere variedades compactas y de rápido crecimiento
- Incluye soluciones creativas para maximizar el espacio

{context}""",
            "categories": ["jardinería_urbana", "espacios_pequeños", "cultivo_contenedores", "jardines_verticales"],
            "keywords": {
                "primary": ["urbano", "balcón", "terraza", "maceta", "contenedor", "pequeño"],
                "secondary": ["vertical", "hidropónico", "compacto", "apartamento", "ciudad"]
            },
            "source_paths": ["./data/documents/urban_gardening"],
            "custom_settings": {
                "space_constraints": True,
                "container_focus": True,
                "recommended_plants": ["herbs", "microgreens", "cherry_tomatoes", "lettuce"],
                "urban_challenges": ["limited_light", "wind_exposure", "pollution", "space_restrictions"]
            }
        }
        
        # Guardar configuraciones personalizadas
        rags_path = self.config_manager.config_base_path / "rags"
        
        configs_to_save = [
            ("eco_agriculture", eco_agriculture_config),
            ("urban_gardening", urban_gardening_config)
        ]
        
        for name, config in configs_to_save:
            config_file = rags_path / f"{name}.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"   📄 {name}.yaml (RAG personalizado)")
        
        # 3. Crear agente personalizado
        self._create_custom_agent_example()
        
        # 4. Crear documentos de ejemplo
        self._create_example_documents()
    
    def _create_custom_agent_example(self):
        """Crea un ejemplo de agente personalizado"""
        
        custom_agent_code = '''"""
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
'''
        
        # Guardar el código del agente personalizado
        custom_agents_path = self.base_path / "agentragmcp" / "custom_agents"
        agent_file = custom_agents_path / "eco_agriculture_agent.py"
        
        with open(agent_file, 'w', encoding='utf-8') as f:
            f.write(custom_agent_code)
        
        print(f"   🤖 eco_agriculture_agent.py (agente personalizado)")
        
        # Añadir configuración del agente personalizado al archivo de agentes
        agents_file = self.config_manager.config_base_path / "agents.yaml"
        
        with open(agents_file, 'r', encoding='utf-8') as f:
            agents_config = yaml.safe_load(f)
        
        # Agregar agente personalizado
        agents_config["agents"]["eco_agriculture"] = {
            "description": "Especialista en agricultura ecológica y sostenible",
            "class": "EcoAgricultureAgent",
            "module_path": "./agentragmcp/custom_agents/eco_agriculture_agent.py",
            "topics": ["eco_agriculture"],
            "enabled": True,
            "priority": 2,
            "config": {
                "max_confidence": 0.9,
                "min_confidence": 0.1,
                "fallback_enabled": False,
                "primary_keywords": [
                    "ecológico", "orgánico", "sostenible", "natural", "biodiversidad",
                    "permacultura", "compost", "biológico", "certificado"
                ],
                "patterns": [
                    "agricultura.*ecológica", "método.*natural", "sin.*químicos",
                    "cultivo.*orgánico", "permacultura"
                ]
            },
            "thresholds": {
                "keyword_weight": 0.4,
                "sustainability_weight": 0.4,
                "pattern_weight": 0.2
            }
        }
        
        # Guardar configuración actualizada
        with open(agents_file, 'w', encoding='utf-8') as f:
            yaml.dump(agents_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"   📄 Agente eco_agriculture añadido a agents.yaml")
    
    def _create_example_documents(self):
        """Crea documentos de ejemplo para los nuevos RAGs"""
        
        # Documento para agricultura ecológica
        eco_doc = """# Principios de Agricultura Ecológica

## Introducción
La agricultura ecológica es un sistema de producción que mantiene la salud de los suelos, ecosistemas y personas. Se basa en procesos ecológicos, biodiversidad y ciclos adaptados a las condiciones locales.

## Principios Básicos

### 1. Salud del Suelo
- Uso de compost y abonos orgánicos
- Rotación de cultivos para mantener fertilidad
- Cobertura vegetal permanente (mulch)
- Evitar el laboreo excesivo

### 2. Biodiversidad
- Cultivos asociados y policultivos
- Setos y corredores ecológicos  
- Plantas autóctonas y variedades locales
- Conservación de polinizadores

### 3. Control Natural de Plagas
- Fomento de depredadores naturales
- Plantas repelentes y atrayentes
- Extractos vegetales y preparados naturales
- Trampas ecológicas

## Certificación Ecológica
Los productos ecológicos deben cumplir estándares estrictos:
- Prohibición de pesticidas sintéticos
- No uso de fertilizantes químicos
- Semillas no modificadas genéticamente
- Rotaciones obligatorias
- Período de conversión de 3 años

## Técnicas Específicas

### Compostaje
El compost es fundamental en agricultura ecológica:
- Mezcla equilibrada de materiales verdes y marrones
- Volteo regular para oxigenación
- Temperatura controlada (50-70°C)
- Tiempo de maduración: 6-12 meses

### Rotación de Cultivos
Secuencia planificada de cultivos:
- Leguminosas → Cereales → Hortalizas de hoja → Barbecho
- Mejora la fertilidad del suelo
- Rompe ciclos de plagas y enfermedades
- Optimiza el uso de nutrientes
"""
        
        # Documento para jardinería urbana
        urban_doc = """# Jardinería Urbana en Espacios Pequeños

## Introducción
La jardinería urbana permite cultivar plantas comestibles y ornamentales en espacios limitados como balcones, terrazas y patios pequeños.

## Consideraciones Básicas

### Evaluación del Espacio
- **Luz disponible**: Mínimo 4-6 horas de sol directo
- **Viento**: Protección necesaria en pisos altos
- **Peso soportado**: Verificar capacidad de carga
- **Acceso al agua**: Proximidad a tomas de agua

### Contenedores y Macetas
- **Material**: Plástico ligero, madera tratada, fibra de coco
- **Drenaje**: Orificios en la base obligatorios
- **Tamaño**: Mínimo 20cm profundidad para hortalizas
- **Movilidad**: Ruedas para contenedores grandes

## Técnicas de Cultivo Urbano

### Jardín Vertical
- Aprovecha espacios verticales
- Sistemas modulares colgantes
- Riego por goteo integrado
- Plantas de peso ligero

### Cultivo en Mesa
- Altura ergonómica (80-90cm)
- Mejor drenaje y aireación
- Fácil mantenimiento
- Protección de plagas del suelo

### Hidroponía Casera
- Sistema NFT (Nutrient Film Technique)
- Cultivo en agua con nutrientes
- Mayor productividad en menos espacio
- Control preciso de condiciones

## Plantas Recomendadas

### Hortalizas Compactas
- **Lechugas**: Variedades de hoja suelta
- **Rábanos**: Crecimiento rápido (30 días)
- **Espinacas**: Toleran sombra parcial
- **Tomates cherry**: Variedades determinadas

### Hierbas Aromáticas
- **Albahaca**: Necesita calor y sol
- **Perejil**: Tolera sombra parcial
- **Tomillo**: Resistente a sequía
- **Menta**: Crecimiento vigoroso (contener)

### Plantas Trepadoras
- **Judías verdes**: Aprovechan altura
- **Guisantes**: Crecimiento en frío
- **Pepinos**: Variedades compactas

## Manejo del Riego

### Sistema de Goteo
- Ahorro de agua del 50%
- Riego uniforme y controlado
- Automatización con temporizadores
- Adaptable a cualquier contenedor

### Captación de Agua
- Recolección de agua de lluvia
- Sistemas de drenaje reutilizable
- Bandejas de captación
- Depósitos de almacenamiento
"""
        
        # Guardar documentos
        documents = [
            ("eco_agriculture", "agricultura_ecologica_principios.txt", eco_doc),
            ("urban_gardening", "jardineria_urbana_basicos.txt", urban_doc)
        ]
        
        for topic, filename, content in documents:
            doc_path = self.base_path / "data" / "documents" / topic / filename
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   📄 {topic}/{filename}")
    
    def validate_migration(self):
        """Valida que la migración se completó correctamente"""
        
        validation_results = {
            "rag_configs": 0,
            "agent_configs": 0,
            "custom_agents": 0,
            "documents": 0,
            "errors": []
        }
        
        # Verificar configuraciones RAG
        rags_path = self.config_manager.config_base_path / "rags"
        if rags_path.exists():
            rag_files = list(rags_path.glob("*.yaml"))
            validation_results["rag_configs"] = len(rag_files)
            print(f"   ✅ {len(rag_files)} configuraciones RAG encontradas")
        else:
            validation_results["errors"].append("Directorio de configuraciones RAG no existe")
        
        # Verificar configuración de agentes
        agents_file = self.config_manager.config_base_path / "agents.yaml"
        if agents_file.exists():
            with open(agents_file, 'r') as f:
                agents_data = yaml.safe_load(f)
            validation_results["agent_configs"] = len(agents_data.get("agents", {}))
            print(f"   ✅ {validation_results['agent_configs']} agentes configurados")
        else:
            validation_results["errors"].append("Archivo de configuración de agentes no existe")
        
        # Verificar agentes personalizados
        custom_agents_path = self.base_path / "agentragmcp" / "custom_agents"
        if custom_agents_path.exists():
            custom_files = list(custom_agents_path.glob("*.py"))
            # Excluir __init__.py
            custom_files = [f for f in custom_files if f.name != "__init__.py"]
            validation_results["custom_agents"] = len(custom_files)
            print(f"   ✅ {len(custom_files)} agentes personalizados encontrados")
        
        # Verificar documentos
        docs_path = self.base_path / "data" / "documents"
        if docs_path.exists():
            total_docs = 0
            for topic_dir in docs_path.iterdir():
                if topic_dir.is_dir():
                    docs = list(topic_dir.glob("*.txt"))
                    total_docs += len(docs)
            validation_results["documents"] = total_docs
            print(f"   ✅ {total_docs} documentos de ejemplo encontrados")
        
        # Mostrar resumen
        if validation_results["errors"]:
            print(f"\n   ⚠️ Errores encontrados:")
            for error in validation_results["errors"]:
                print(f"     • {error}")
        
        print(f"\n   📊 Resumen de validación:")
        print(f"     • RAG configs: {validation_results['rag_configs']}")
        print(f"     • Agent configs: {validation_results['agent_configs']}")
        print(f"     • Custom agents: {validation_results['custom_agents']}")
        print(f"     • Example docs: {validation_results['documents']}")
        
        return len(validation_results["errors"]) == 0
    
    def create_migration_docs(self):
        """Crea documentación sobre el sistema migrado"""
        
        readme_content = f"""# 🌱 AgentRagMCP - Sistema Dinámico de Configuración

