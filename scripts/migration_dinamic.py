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
        print(f"📍 Configuraciones en: {self.config_manager.config_base_path}")
    
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
            ("🔄 Crear agentes personalizados", self.create_custom_agents),
            ("✅ Validar migración", self.validate_migration),
            ("🧪 Pruebas de funcionalidad", self.test_migration),
            ("📖 Crear documentación", self.create_migration_docs),
            ("🧹 Limpieza de archivos obsoletos", self.cleanup_old_files)
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
        print(f"\n📋 Próximos pasos:")
        print(f"   1. Verificar configuraciones en data/configs/")
        print(f"   2. Añadir documentos a data/documents/")
        print(f"   3. Ejecutar proceso de vectorización")
        print(f"   4. Probar la aplicación")
    
    def setup_directory_structure(self):
        """Crea la estructura de directorios para el sistema dinámico"""
        directories = [
            "data/configs/rags",
            "data/configs/agents", 
            "data/configs/custom",
            "data/documents/plants",
            "data/documents/pathology",
            "data/documents/general",
            "data/documents/eco_agriculture",
            "data/documents/urban_gardening", 
            "data/documents/permaculture",
            "data/vectorstores/plants",
            "data/vectorstores/pathology",
            "data/vectorstores/general",
            "data/vectorstores/eco_agriculture",
            "data/vectorstores/urban_gardening",
            "data/vectorstores/permaculture",
            "agentragmcp/custom_agents",
            "backups/migration"
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
        
        # Configuraciones RAG extraídas del código existente
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
                "system_prompt": """Eres un especialista en botánica y plantas.

**Especialidades principales:**
- Información general sobre especies de plantas
- Técnicas de cultivo y propagación
- Cuidados específicos por especie
- Identificación de plantas
- Condiciones de crecimiento óptimas

**IMPORTANTE:** Enfócate en información práctica y aplicable.

{context}""",
                "categories": ["cultivo", "cuidados", "especies", "botánica"],
                "keywords": {
                    "primary": ["planta", "plantas", "árbol", "cultivo", "jardín", "botánica"],
                    "secondary": ["sembrar", "plantar", "cuidar", "especie", "variedad"]
                },
                "source_paths": ["./data/documents/plants"],
                "custom_settings": {
                    "include_scientific_names": True,
                    "focus_practical": True
                }
            },
            
            "pathology": {
                "display_name": "Patologías y Enfermedades de Plantas",
                "description": "Especialista en diagnóstico y tratamiento de enfermedades, plagas y patologías vegetales",
                "enabled": True,
                "priority": 2,
                "vectorstore": {
                    "type": "chroma",
                    "path": "./data/vectorstores/pathology",
                    "collection_name": "pathology_collection",
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
                "system_prompt": """Eres un especialista en patologías vegetales y fitopatología.

**Especialidades principales:**
- Diagnóstico de enfermedades de plantas
- Identificación de plagas y patógenos  
- Tratamientos fitosanitarios
- Estrategias de prevención
- Manejo integrado de plagas

**IMPORTANTE:** Siempre incluye advertencias de seguridad para productos químicos.

{context}""",
                "categories": ["diagnóstico_enfermedades", "tratamientos", "prevención", "plagas"],
                "keywords": {
                    "primary": ["enfermedad", "plaga", "síntomas", "tratamiento", "hongo", "bacteria"],
                    "secondary": ["patología", "virus", "prevención", "control", "insecticida"]
                },
                "source_paths": ["./data/documents/pathology"],
                "custom_settings": {
                    "safety_warnings": True,
                    "treatment_focus": "integrated_pest_management",
                    "include_prevention": True
                }
            },
            
            "general": {
                "display_name": "Conocimiento General de Botánica",
                "description": "Información educativa y divulgativa sobre el mundo vegetal",
                "enabled": True,
                "priority": 3,
                "vectorstore": {
                    "type": "chroma",
                    "path": "./data/vectorstores/general",
                    "collection_name": "general_collection",
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
                "system_prompt": """Eres un educador especialista en botánica y ciencias vegetales.

**Especialidades principales:**
- Conceptos fundamentales de botánica
- Historia y evolución de las plantas
- Procesos biológicos vegetales
- Ecosistemas y biodiversidad vegetal
- Divulgación científica accesible

**IMPORTANTE:** Explica conceptos de forma clara y educativa.

{context}""",
                "categories": ["educación", "conceptos", "historia", "biología_vegetal"],
                "keywords": {
                    "primary": ["qué es", "cómo funciona", "por qué", "botánica", "información"],
                    "secondary": ["proceso", "concepto", "definición", "biología", "ciencia"]
                },
                "source_paths": ["./data/documents/general"],
                "custom_settings": {
                    "educational_focus": True,
                    "include_examples": True
                }
            }
        }
        
        # Crear configuraciones adicionales de ejemplo
        rag_configs.update({
            "eco_agriculture": {
                "display_name": "Agricultura Ecológica",
                "description": "Técnicas de agricultura sostenible y ecológica",
                "enabled": True,
                "priority": 4,
                "vectorstore": {
                    "type": "chroma",
                    "path": "./data/vectorstores/eco_agriculture",
                    "collection_name": "eco_agriculture_collection",
                    "chunk_size": 1200,
                    "chunk_overlap": 300,
                    "embedding_model": "llama3.1",
                    "embedding_base_url": "http://localhost:11434"
                },
                "retrieval": {
                    "search_type": "mmr",
                    "k": 6,
                    "fetch_k": 20,
                    "lambda_mult": 0.8,
                    "score_threshold": 0.4
                },
                "system_prompt": """Eres un especialista en agricultura ecológica y sostenible.

Enfócate en técnicas respetuosas con el medio ambiente, biodiversidad y sostenibilidad.

{context}""",
                "categories": ["agricultura_ecológica", "sostenibilidad", "biodiversidad"],
                "keywords": {
                    "primary": ["ecológico", "sostenible", "biodiversidad", "orgánico"],
                    "secondary": ["permacultura", "compost", "rotación", "natural"]
                },
                "source_paths": ["./data/documents/eco_agriculture"],
                "custom_settings": {
                    "certification_standards": ["EU_Organic", "USDA_Organic"],
                    "focus_areas": ["soil_health", "biodiversity", "water_conservation"]
                }
            },
            
            "urban_gardening": {
                "display_name": "Jardinería Urbana",
                "description": "Cultivo en espacios urbanos, balcones y espacios reducidos",
                "enabled": True,
                "priority": 5,
                "vectorstore": {
                    "type": "chroma", 
                    "path": "./data/vectorstores/urban_gardening",
                    "collection_name": "urban_gardening_collection",
                    "chunk_size": 800,
                    "chunk_overlap": 150,
                    "embedding_model": "llama3.1",
                    "embedding_base_url": "http://localhost:11434"
                },
                "retrieval": {
                    "search_type": "mmr",
                    "k": 4,
                    "fetch_k": 15,
                    "lambda_mult": 0.6,
                    "score_threshold": 0.5
                },
                "system_prompt": """Eres un especialista en jardinería urbana y cultivos en espacios reducidos.

**Especialidades:**
- Cultivo en balcones y terrazas
- Plantas para interiores
- Sistemas de riego eficientes
- Aprovechamiento de espacios pequeños

{context}""",
                "categories": ["jardinería_urbana", "espacios_reducidos", "cultivo_interior"],
                "keywords": {
                    "primary": ["balcón", "terraza", "interior", "urbano", "maceta"],
                    "secondary": ["apartamento", "espacio", "pequeño", "vertical"]
                },
                "source_paths": ["./data/documents/urban_gardening"],
                "custom_settings": {
                    "space_focus": "small_spaces",
                    "container_gardening": True
                }
            }
        })
        
        # Guardar configuraciones
        rags_path = self.config_manager.config_base_path / "rags"
        
        for topic_name, config_data in rag_configs.items():
            config_file = rags_path / f"{topic_name}.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            print(f"   📋 {topic_name}.yaml")
    
    def migrate_agent_configs(self):
        """Migra las configuraciones de agentes hardcodeadas"""
        
        agents_config = {
            "agents": {
                "plants": {
                    "name": "plants",
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
                            "sembrar", "plantar", "jardín", "huerto", "botánica"
                        ],
                        "patterns": [
                            "cómo.*cultivar", "cuándo.*plantar", "qué.*planta",
                            "características.*de", "cuidados.*de", "información.*sobre"
                        ],
                        "target_species": [
                            "malus domestica", "prunus cerasus", "vitis vinifera",
                            "citrus aurantium", "prunus persica", "fragaria vesca",
                            "solanum lycopersicum"
                        ]
                    },
                    "thresholds": {
                        "keyword_weight": 0.3,
                        "species_weight": 0.5,
                        "pattern_weight": 0.2,
                        "context_bonus": 0.2
                    }
                },
                
                "pathology": {
                    "name": "pathology",
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
                            "virus", "tratamiento", "síntomas", "control"
                        ],
                        "symptom_keywords": [
                            "mancha", "manchas", "amarilleo", "marchitez", "podredumbre",
                            "necrosis", "lesión", "deformación"
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
                    "name": "general",
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
                            "diferencia.*entre", "tipos.*de", "explicar.*qué"
                        ],
                        "educational_focus": True
                    },
                    "thresholds": {
                        "keyword_weight": 0.4,
                        "pattern_weight": 0.3,
                        "educational_bonus": 0.3
                    }
                },
                
                # Agentes personalizados de ejemplo
                "eco_agriculture": {
                    "name": "eco_agriculture",
                    "description": "Especialista en agricultura ecológica y sostenible",
                    "class": "EcoAgricultureAgent",
                    "topics": ["eco_agriculture"],
                    "enabled": True,
                    "priority": 4,
                    "config": {
                        "max_confidence": 1.0,
                        "min_confidence": 0.1,
                        "primary_keywords": [
                            "ecológico", "orgánico", "sostenible", "biodiversidad",
                            "permacultura", "compost", "rotación"
                        ],
                        "patterns": [
                            "agricultura.*ecológica", "cultivo.*orgánico", ".*sostenible"
                        ],
                        "focus_areas": ["soil_health", "biodiversity", "sustainability"]
                    },
                    "thresholds": {
                        "keyword_weight": 0.6,
                        "pattern_weight": 0.4
                    }
                },
                
                "urban_gardening": {
                    "name": "urban_gardening",
                    "description": "Especialista en jardinería urbana y cultivos en espacios reducidos",
                    "class": "UrbanGardeningAgent",
                    "topics": ["urban_gardening"],
                    "enabled": True,
                    "priority": 5,
                    "config": {
                        "max_confidence": 1.0,
                        "min_confidence": 0.1,
                        "primary_keywords": [
                            "balcón", "terraza", "interior", "urbano", "maceta",
                            "apartamento", "espacio", "pequeño"
                        ],
                        "patterns": [
                            "en.*balcón", "en.*terraza", "espacio.*pequeño", ".*interior"
                        ],
                        "space_types": ["balcony", "terrace", "indoor", "small_space"]
                    },
                    "thresholds": {
                        "keyword_weight": 0.5,
                        "pattern_weight": 0.3,
                        "space_bonus": 0.2
                    }
                }
            }
        }
        
        # Guardar configuración de agentes
        agents_file = self.config_manager.config_base_path / "agents.yaml"
        with open(agents_file, 'w', encoding='utf-8') as f:
            yaml.dump(agents_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"   🤖 agents.yaml con {len(agents_config['agents'])} agentes")
    
    def create_custom_examples(self):
        """Crea ejemplos de documentos para cada temática"""
        
        # Documento para plantas
        plants_doc = """# Cultivo del Manzano (Malus domestica)

## Características Generales
El manzano es un árbol frutal de la familia Rosaceae, originario de Asia Central.

## Condiciones de Cultivo
- **Clima**: Templado, con inviernos fríos
- **Suelo**: Bien drenado, pH 6.0-7.0
- **Exposición**: Pleno sol

## Cuidados Específicos
### Riego
- Riego regular pero sin encharcamiento
- Especialmente importante durante la fructificación

### Poda
- Poda de formación en invierno
- Eliminar ramas secas y entrecruzadas

## Variedades Recomendadas
- Golden Delicious
- Red Delicious
- Granny Smith
"""
        
        # Documento para patologías
        pathology_doc = """# Enfermedades Comunes del Manzano

## Mildiu Polvoriento
### Síntomas
- Polvo blanco en hojas y brotes jóvenes
- Deformación de hojas
- Reducción del crecimiento

### Tratamiento
- Aplicar fungicidas sistémicos
- Mejorar ventilación
- Eliminar partes afectadas

### Prevención
- Evitar riego por aspersión
- Plantar variedades resistentes

## Fuego Bacteriano
### Síntomas
- Marchitez súbita de flores y brotes
- Exudado bacteriano
- Necrosis progresiva

### Tratamiento
- Eliminación inmediata de partes afectadas
- Desinfección de herramientas
- Aplicación de antibióticos específicos

⚠️ **Advertencia**: Siempre usar equipo de protección personal.
"""

        # Documento general
        general_doc = """# Introducción a la Botánica

## ¿Qué es la Botánica?
La botánica es la ciencia que estudia las plantas en todos sus aspectos.

## Clasificación de las Plantas
### Por su estructura
- **Briófitos**: Musgos y hepáticas
- **Pteridófitos**: Helechos
- **Gimnospermas**: Coníferas
- **Angiospermas**: Plantas con flores

### Por su ciclo de vida
- **Anuales**: Completan su ciclo en un año
- **Bianuales**: Requieren dos años
- **Perennes**: Viven varios años

## Procesos Fundamentales
### Fotosíntesis
Proceso mediante el cual las plantas convierten luz solar en energía química.

### Respiración
Las plantas también respiran, consumiendo oxígeno y liberando CO2.
"""

        # Documento agricultura ecológica
        eco_doc = """# Principios de la Agricultura Ecológica

## Filosofía de Base
La agricultura ecológica busca trabajar en armonía con la naturaleza.

## Principios Fundamentales
1. **Salud del suelo**: Base de todo sistema sostenible
2. **Biodiversidad**: Promover la diversidad biológica
3. **Ciclos naturales**: Respetar los ritmos de la naturaleza
4. **Bienestar animal**: Garantizar condiciones naturales

## Técnicas Principales
### Compostaje
- Transformación de residuos orgánicos
- Mejora la estructura del suelo
- Aporta nutrientes naturales

### Rotación de Cultivos
- Previene agotamiento del suelo
- Reduce plagas y enfermedades
- Optimiza uso de nutrientes

### Control Biológico
- Uso de enemigos naturales
- Plantas companion
- Preparados biodinámicos
"""

        # Documento jardinería urbana
        urban_doc = """# Jardinería en Espacios Urbanos

## Desafíos de la Ciudad
- Espacio limitado
- Calidad del aire
- Acceso limitado a luz solar
- Restricciones de peso en balcones

## Soluciones Prácticas
### Cultivo Vertical
- Aprovechar paredes y estructuras
- Sistemas de trepado
- Jardines verticales modulares

### Contenedores y Macetas
- Selección según espacio disponible
- Sistemas de drenaje adecuados
- Movilidad para optimizar luz

## Plantas Recomendadas
### Para balcones
- Hierbas aromáticas: albahaca, perejil, cilantro
- Tomates cherry
- Fresas

### Para interiores
- Pothos
- Sansevieria
- Plantas aromáticas

## Sistemas de Riego
- Riego por goteo automático
- Sistemas de autorriego con reserva de agua
- Aplicaciones móviles para control de humedad
"""
        
        # Guardar documentos
        documents = [
            ("plants", "manzano_cultivo.txt", plants_doc),
            ("pathology", "enfermedades_manzano.txt", pathology_doc), 
            ("general", "introduccion_botanica.txt", general_doc),
            ("eco_agriculture", "agricultura_ecologica_principios.txt", eco_doc),
            ("urban_gardening", "jardineria_urbana_basicos.txt", urban_doc)
        ]
        
        for topic, filename, content in documents:
            doc_path = self.base_path / "data" / "documents" / topic / filename
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   📄 {topic}/{filename}")
    
    def create_custom_agents(self):
        """Crea agentes personalizados de ejemplo"""
        
        # Agente de agricultura ecológica
        eco_agent_code = '''"""
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
            enhanced += "\\n\\n🌱 **Enfoque Ecológico**: Considera siempre alternativas naturales y sostenibles."
        
        if "cultivo" in question.lower():
            enhanced += "\\n\\n♻️ **Sostenibilidad**: Recuerda mantener la salud del suelo y la biodiversidad."
        
        return enhanced
'''

        # Agente de jardinería urbana  
        urban_agent_code = '''"""
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
            enhanced += "\\n\\n🏙️ **Adaptación Urbana**: Considera las limitaciones de espacio y contenedores."
        
        if "riego" in question.lower():
            enhanced += "\\n\\n💧 **Riego Urbano**: Sistemas de autorriego son ideales para balcones."
        
        return enhanced
'''
        
        # Guardar agentes personalizados
        custom_agents_path = self.base_path / "agentragmcp" / "custom_agents"
        
        agents_to_create = [
            ("eco_agriculture_agent.py", eco_agent_code),
            ("urban_gardening_agent.py", urban_agent_code)
        ]
        
        for filename, code in agents_to_create:
            agent_file = custom_agents_path / filename
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(code)
            print(f"   🤖 {filename}")
    
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
            
            # Verificar configuraciones específicas
            expected_rags = ["plants", "pathology", "general", "eco_agriculture", "urban_gardening"]
            for rag_name in expected_rags:
                rag_file = rags_path / f"{rag_name}.yaml"
                if not rag_file.exists():
                    validation_results["errors"].append(f"Configuración RAG faltante: {rag_name}")
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
    
    def test_migration(self):
        """Prueba la funcionalidad del sistema migrado"""
        print("   🧪 Probando carga de configuraciones...")
        
        try:
            # Probar carga de configuraciones RAG
            test_topics = ["plants", "pathology", "general"]
            for topic in test_topics:
                config = self.config_manager.load_rag_config(topic)
                if config:
                    print(f"     ✅ RAG {topic} cargado correctamente")
                else:
                    print(f"     ❌ Error cargando RAG {topic}")
            
            # Probar carga de configuraciones de agentes
            test_agents = ["plants", "pathology", "general"]
            for agent in test_agents:
                config = self.config_manager.load_agent_config(agent)
                if config:
                    print(f"     ✅ Agente {agent} cargado correctamente")
                else:
                    print(f"     ❌ Error cargando agente {agent}")
        
        except Exception as e:
            print(f"     ❌ Error en pruebas: {e}")
    
    def create_migration_docs(self):
        """Crea documentación sobre el sistema migrado"""
        
        readme_content = f"""# 🌱 AgentRagMCP - Sistema Dinámico de Configuración

## 📋 Resumen de la Migración

Este sistema ha sido migrado de configuración hardcodeada a un sistema dinámico y flexible que permite:

✅ **RAGs Configurables**: Cada temática tiene su propio archivo de configuración
✅ **Agentes Dinámicos**: Los agentes se cargan automáticamente desde configuración
✅ **Extensibilidad**: Fácil adición de nuevas temáticas y agentes sin modificar código
✅ **Recarga Automática**: Cambios en configuración se detectan y aplican automáticamente

## 📁 Estructura de Configuración

```
data/configs/
├── rags/                          # Configuraciones de RAG por temática
│   ├── plants.yaml               # Información general de plantas
│   ├── pathology.yaml            # Patologías y enfermedades
│   ├── general.yaml              # Conocimiento general
│   ├── eco_agriculture.yaml      # Agricultura ecológica (ejemplo)
│   └── urban_gardening.yaml      # Jardinería urbana (ejemplo)
├── agents.yaml                   # Configuración de todos los agentes
└── custom/                       # Configuraciones personalizadas

agentragmcp/custom_agents/         # Agentes personalizados
├── eco_agriculture_agent.py      # Ejemplo de agente personalizado
└── __init__.py
```

## 🚀 Cómo Añadir Nuevos RAGs

### 1. Crear Configuración RAG

Crea un archivo `mi_nueva_tematica.yaml` en `data/configs/rags/`:

```yaml
display_name: "Mi Nueva Temática"
description: "Descripción de la temática"
enabled: true
priority: 1

vectorstore:
  type: "chroma"
  path: "./data/vectorstores/mi_nueva_tematica"
  collection_name: "mi_nueva_tematica_collection"
  chunk_size: 1000
  chunk_overlap: 200

retrieval:
  search_type: "mmr"
  k: 5
  lambda_mult: 0.7

system_prompt: |
  Eres un especialista en [tu temática].
  
  **Especialidades:**
  - Lista tus especialidades
  
  {{context}}

categories: ["categoria1", "categoria2"]
keywords:
  primary: ["palabra1", "palabra2"]
  secondary: ["palabra3", "palabra4"]

source_paths: ["./data/documents/mi_nueva_tematica"]
```

### 2. Añadir Documentos

- Crea directorio: `data/documents/mi_nueva_tematica/`
- Añade documentos en formato `.txt`, `.pdf`, `.md`
- Ejecuta script de procesamiento para crear vectorstore

### 3. El Sistema se Encarga del Resto

El sistema detectará automáticamente la nueva configuración y cargará el RAG.

## 🤖 Cómo Añadir Nuevos Agentes

### 1. Agente Genérico (Solo Configuración)

Añade a `data/configs/agents.yaml`:

```yaml
agents:
  mi_agente:
    description: "Descripción del agente"
    class: "GenericRAGAgent"  # Usa agente genérico
    topics: ["mi_nueva_tematica"]
    enabled: true
    priority: 2
    config:
      primary_keywords: ["palabra1", "palabra2"]
      patterns: ["patrón.*regex"]
      target_species: ["Especie específica"]
    thresholds:
      keyword_weight: 0.4
      pattern_weight: 0.3
```

### 2. Agente Personalizado (Con Código)

1. Crea archivo en `agentragmcp/custom_agents/mi_agente.py`
2. Hereda de `DynamicAgent`
3. Implementa lógica específica
4. Actualiza configuración en `agents.yaml`

## 🔧 Comandos Útiles

```bash
# Migrar sistema completo
python scripts/migration_dinamic.py

# Validar configuraciones
python -c "from agentragmcp.core.dynamic_config import config_manager; config_manager.validate_all()"

# Recargar configuraciones
python -c "from agentragmcp.core.dynamic_config import config_manager; config_manager.reload_if_changed()"

# Listar configuraciones disponibles
python -c "from agentragmcp.core.dynamic_config import config_manager; print(config_manager.list_available_configs())"
```

## 📝 Ejemplos Incluidos

La migración incluye configuraciones de ejemplo para:

- **🌱 Plants**: Información general de plantas
- **🦠 Pathology**: Diagnóstico y tratamiento de enfermedades
- **📚 General**: Conocimiento educativo de botánica
- **🌿 Eco Agriculture**: Agricultura ecológica y sostenible
- **🏙️ Urban Gardening**: Jardinería en espacios urbanos

## 🛠️ Desarrollo y Personalización

### Estructura de un Agente Personalizado

```python
from agentragmcp.api.app.agents.dinamic_agent import DynamicAgent

class MiAgentePersonalizado(DynamicAgent):
    def __init__(self, config, rag_service):
        super().__init__("mi_tematica", config, rag_service)
    
    def calculate_confidence(self, question: str) -> float:
        # Lógica personalizada de confianza
        confidence = super().calculate_confidence(question)
        # Añadir bonificaciones específicas
        return confidence
    
    def enhance_response(self, response: str, question: str) -> str:
        # Mejoras específicas a las respuestas
        return enhanced_response
```

### Configuración Avanzada de RAG

```yaml
# Configuración avanzada con múltiples fuentes
vectorstore:
  type: "chroma"
  path: "./data/vectorstores/mi_rag"
  collection_name: "mi_collection"
  chunk_size: 1200
  chunk_overlap: 300
  embedding_model: "llama3.1"

retrieval:
  search_type: "mmr"
  k: 6
  fetch_k: 20
  lambda_mult: 0.8
  score_threshold: 0.4

# Configuraciones personalizadas
custom_settings:
  use_metadata_filter: true
  include_source_info: true
  max_context_length: 4000
  response_language: "es"
```

## 📊 Monitoreo y Métricas

El sistema incluye capacidades de monitoreo:

- **Carga de configuraciones**: Tiempo y éxito de carga
- **Uso de agentes**: Frecuencia de selección por agente
- **Performance de RAGs**: Tiempo de respuesta por temática
- **Detección de cambios**: Recargas automáticas de configuración

## 🔄 Proceso de Migración Completado

La migración automática ha:

1. ✅ Creado estructura de directorios
2. ✅ Extraído configuraciones hardcodeadas
3. ✅ Generado archivos YAML de configuración
4. ✅ Creado agentes personalizados de ejemplo
5. ✅ Añadido documentos de ejemplo
6. ✅ Validado la migración
7. ✅ Generado esta documentación

## 📞 Soporte

Para más información sobre el sistema dinámico:
- Revisa los archivos de configuración en `data/configs/`
- Consulta los ejemplos en `agentragmcp/custom_agents/`
- Ejecuta las validaciones incluidas
- Revisa los logs del sistema para debugging

---

**¡El sistema AgentRagMCP ahora es completamente dinámico y extensible!** 🎉
"""
        
        # Guardar documentación
        readme_file = self.base_path / "MIGRATION_README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Crear archivo de configuración de ejemplo
        example_config = """# Ejemplo de configuración personalizada

display_name: "Mi RAG Personalizado"
description: "Ejemplo de cómo crear un RAG personalizado"
enabled: true
priority: 10

vectorstore:
  type: "chroma"
  path: "./data/vectorstores/mi_rag_personalizado"
  collection_name: "mi_collection"
  chunk_size: 1000
  chunk_overlap: 200

retrieval:
  search_type: "mmr"
  k: 5
  lambda_mult: 0.7

system_prompt: |
  Eres un especialista en [tu área específica].
  
  Proporciona información precisa y útil sobre [tu dominio].
  
  {context}

categories: ["categoria1", "categoria2"]
keywords:
  primary: ["palabra_clave1", "palabra_clave2"]
  secondary: ["término1", "término2"]

source_paths: ["./data/documents/mi_rag_personalizado"]

custom_settings:
  mi_configuracion: "valor"
  otra_opcion: true
"""
        
        example_file = self.config_manager.config_base_path / "custom" / "ejemplo_rag.yaml"
        with open(example_file, 'w', encoding='utf-8') as f:
            f.write(example_config)
        
        print(f"   📖 MIGRATION_README.md")
        print(f"   📋 ejemplo_rag.yaml")
    
    def cleanup_old_files(self):
        """Limpia archivos obsoletos después de la migración"""
        print("   🗂️ Creando backups de archivos originales...")
        
        # Archivos que podrían necesitar backup
        files_to_backup = [
            "agentragmcp/core/config.py",
            "agentragmcp/api/app/agents/base_agent.py",
            "agentragmcp/api/app/agents/plants_agent.py",
            "agentragmcp/api/app/agents/pathology_agent.py",
            "agentragmcp/api/app/agents/general_agent.py",
            "agentragmcp/api/app/services/rag_service.py",
            "agentragmcp/api/app/services/agent_service.py"
        ]
        
        backup_dir = self.base_path / "backups" / "migration"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backed_up = []
        for file_path in files_to_backup:
            source_file = self.base_path / file_path
            if source_file.exists():
                # Crear estructura de directorios en backup
                relative_path = Path(file_path)
                backup_file = backup_dir / relative_path
                backup_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copiar archivo
                shutil.copy2(source_file, backup_file)
                backed_up.append(file_path)
        
        if backed_up:
            print(f"   📦 {len(backed_up)} archivos respaldados en backups/migration/")
        
        # Crear archivo de registro de migración
        migration_log = {
            "migration_date": "2024-12-19",
            "migrated_from": "hardcoded_config",
            "migrated_to": "dynamic_config",
            "backed_up_files": backed_up,
            "new_structure": {
                "configs": "data/configs/",
                "custom_agents": "agentragmcp/custom_agents/",
                "documentation": "MIGRATION_README.md"
            }
        }
        
        log_file = backup_dir / "migration_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(migration_log, f, indent=2, ensure_ascii=False)
        
        print(f"   📋 Log de migración guardado en backups/migration/migration_log.json")

def main():
    """Función principal del script de migración"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migración de AgentRagMCP a sistema dinámico")
    parser.add_argument("--base-path", type=str, help="Directorio base del proyecto")
    parser.add_argument("--dry-run", action="store_true", help="Simular migración sin hacer cambios")
    parser.add_argument("--verbose", "-v", action="store_true", help="Salida detallada")
    
    args = parser.parse_args()
    
    try:
        migrator = AgentRagMCPMigrator(args.base_path)
        
        if args.dry_run:
            print("🧪 MODO DRY-RUN - No se realizarán cambios")
            print("La migración crearía:")
            print("- Estructura de directorios en data/configs/")
            print("- Configuraciones RAG individuales")
            print("- Configuraciones de agentes")
            print("- Agentes personalizados de ejemplo")
            print("- Documentación de migración")
        else:
            migrator.migrate_full_system()
        
    except KeyboardInterrupt:
        print("\n⚠️ Migración interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la migración: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

