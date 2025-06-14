"""
Gestor de configuración dinámico para AgentRagMCP
Permite configuraciones personalizadas por RAG y carga dinámica
"""
import os
import yaml
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

@dataclass
class VectorStoreConfig:
    """Configuración de vectorstore"""
    type: str = "chroma"  # chroma, faiss, pinecone, etc.
    path: str = ""
    collection_name: str = ""
    
    # Parámetros específicos de creación
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", ". ", " "])
    
    # Configuración de embeddings
    embedding_model: str = "llama3.1"
    embedding_base_url: str = "http://localhost:11434"
    normalize_embeddings: bool = True

@dataclass 
class RetrievalConfig:
    """Configuración de recuperación de documentos"""
    search_type: str = "mmr"  # mmr, similarity, similarity_score_threshold
    k: int = 5
    fetch_k: int = 20  # Para MMR
    lambda_mult: float = 0.7  # Para MMR
    score_threshold: float = 0.5  # Para similarity_score_threshold
    max_k: int = 20
    
    # Configuración de reranking
    reranking_enabled: bool = False
    reranking_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranking_top_k: int = 3

@dataclass
class AgentConfig:
    """Configuración de agente especializado"""
    name: str
    description: str
    class_name: str  # Nombre de la clase del agente
    module_path: str = ""  # Path del módulo si es personalizado
    
    # Temáticas que maneja
    topics: List[str] = field(default_factory=list)
    
    # Configuración de confianza
    max_confidence: float = 1.0
    min_confidence: float = 0.1
    base_confidence: float = 0.2  # Para agentes fallback
    
    # Palabras clave y patrones
    primary_keywords: List[str] = field(default_factory=list)
    secondary_keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    
    # Especies específicas (para agentes botánicos)
    target_species: List[str] = field(default_factory=list)
    common_names: List[str] = field(default_factory=list)
    
    # Configuración de pesos para cálculo de confianza
    keyword_weight: float = 0.3
    species_weight: float = 0.5
    pattern_weight: float = 0.2
    context_bonus: float = 0.2
    
    # Configuración específica adicional
    custom_config: Dict[str, Any] = field(default_factory=dict)
    
    # Estado
    enabled: bool = True
    priority: int = 1  # 1 = alta, 2 = media, 3 = baja
    fallback_enabled: bool = False

@dataclass
class RAGTopicConfig:
    """Configuración completa de una temática RAG"""
    name: str
    display_name: str
    description: str
    enabled: bool = True
    priority: int = 1
    
    # Configuraciones
    vectorstore: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    retrieval: RetrievalConfig = field(default_factory=RetrievalConfig)
    
    # Prompt personalizado
    system_prompt: str = ""
    context_template: str = "{context}"
    
    # Categorías y metadatos
    categories: List[str] = field(default_factory=list)
    keywords: Dict[str, List[str]] = field(default_factory=dict)
    
    # Configuración específica
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Configuración de documentos fuente
    source_paths: List[str] = field(default_factory=list)
    supported_formats: List[str] = field(default_factory=lambda: [".txt", ".pdf", ".md", ".json"])
    
    # Métricas y cache
    track_metrics: bool = True
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600

class ConfigManager:
    """Gestor principal de configuraciones dinámicas"""
    
    def __init__(self, config_base_path: str = "./data/configs"):
        self.config_base_path = Path(config_base_path)
        self.config_base_path.mkdir(parents=True, exist_ok=True)
        
        # Almacenamiento de configuraciones cargadas
        self.rag_configs: Dict[str, RAGTopicConfig] = {}
        self.agent_configs: Dict[str, AgentConfig] = {}
        self.global_config: Dict[str, Any] = {}
        
        # Cache de archivos modificados
        self._file_timestamps: Dict[str, float] = {}
        
        logger.info(f"ConfigManager inicializado en: {self.config_base_path}")
    
    def discover_rag_configs(self) -> List[str]:
        """Descubre automáticamente archivos de configuración RAG"""
        rag_configs_path = self.config_base_path / "rags"
        rag_configs_path.mkdir(exist_ok=True)
        
        config_files = []
        for ext in [".yaml", ".yml", ".json"]:
            config_files.extend(rag_configs_path.glob(f"*{ext}"))
        
        logger.info(f"Encontrados {len(config_files)} archivos de configuración RAG")
        return [f.stem for f in config_files]
    
    def load_rag_config(self, topic_name: str) -> Optional[RAGTopicConfig]:
        """Carga configuración de un RAG específico"""
        config_path = None
        
        # Buscar archivo de configuración
        for ext in [".yaml", ".yml", ".json"]:
            potential_path = self.config_base_path / "rags" / f"{topic_name}{ext}"
            if potential_path.exists():
                config_path = potential_path
                break
        
        if not config_path:
            logger.warning(f"No se encontró configuración para RAG: {topic_name}")
            return None
        
        try:
            # Cargar datos según el formato
            if config_path.suffix in [".yaml", ".yml"]:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:  # JSON
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Crear configuración
            config = self._create_rag_config_from_dict(topic_name, data)
            self.rag_configs[topic_name] = config
            
            # Actualizar timestamp
            self._file_timestamps[str(config_path)] = config_path.stat().st_mtime
            
            logger.info(f"Configuración RAG cargada: {topic_name}")
            return config
            
        except Exception as e:
            logger.error(f"Error cargando configuración RAG {topic_name}: {e}")
            return None
    
    def _create_rag_config_from_dict(self, name: str, data: Dict) -> RAGTopicConfig:
        """Crea configuración RAG desde diccionario"""
        
        # Configuración de vectorstore
        vectorstore_data = data.get("vectorstore", {})
        vectorstore = VectorStoreConfig(
            type=vectorstore_data.get("type", "chroma"),
            path=vectorstore_data.get("path", f"./data/vectorstores/{name}"),
            collection_name=vectorstore_data.get("collection_name", f"{name}_collection"),
            chunk_size=vectorstore_data.get("chunk_size", 1000),
            chunk_overlap=vectorstore_data.get("chunk_overlap", 200),
            embedding_model=vectorstore_data.get("embedding_model", "llama3.1"),
            embedding_base_url=vectorstore_data.get("embedding_base_url", "http://localhost:11434")
        )
        
        # Configuración de retrieval
        retrieval_data = data.get("retrieval", {})
        retrieval = RetrievalConfig(
            search_type=retrieval_data.get("search_type", "mmr"),
            k=retrieval_data.get("k", 5),
            fetch_k=retrieval_data.get("fetch_k", 20),
            lambda_mult=retrieval_data.get("lambda_mult", 0.7),
            score_threshold=retrieval_data.get("score_threshold", 0.5)
        )
        
        # Crear configuración completa
        config = RAGTopicConfig(
            name=name,
            display_name=data.get("display_name", name.title()),
            description=data.get("description", f"RAG para temática {name}"),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 1),
            vectorstore=vectorstore,
            retrieval=retrieval,
            system_prompt=data.get("system_prompt", ""),
            categories=data.get("categories", []),
            keywords=data.get("keywords", {}),
            source_paths=data.get("source_paths", [f"./data/documents/{name}"]),
            custom_settings=data.get("custom_settings", {})
        )
        
        return config
    
    def load_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Carga configuración de un agente específico"""
        agents_file = self.config_base_path / "agents.yaml"
        
        if not agents_file.exists():
            logger.warning(f"Archivo de configuración de agentes no encontrado: {agents_file}")
            return None
        
        try:
            with open(agents_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            agents_data = data.get("agents", {})
            if agent_name not in agents_data:
                logger.warning(f"Agente {agent_name} no encontrado en configuración")
                return None
            
            agent_data = agents_data[agent_name]
            
            # Crear configuración de agente
            config = AgentConfig(
                name=agent_name,
                description=agent_data.get("description", ""),
                class_name=agent_data.get("class", f"{agent_name.title()}Agent"),
                topics=agent_data.get("topics", []),
                enabled=agent_data.get("enabled", True),
                priority=agent_data.get("priority", 1),
                max_confidence=agent_data.get("config", {}).get("max_confidence", 1.0),
                min_confidence=agent_data.get("config", {}).get("min_confidence", 0.1),
                primary_keywords=agent_data.get("config", {}).get("primary_keywords", []),
                patterns=agent_data.get("config", {}).get("patterns", []),
                target_species=agent_data.get("config", {}).get("target_species", []),
                keyword_weight=agent_data.get("thresholds", {}).get("keyword_weight", 0.3),
                species_weight=agent_data.get("thresholds", {}).get("species_weight", 0.5),
                pattern_weight=agent_data.get("thresholds", {}).get("pattern_weight", 0.2),
                custom_config=agent_data.get("config", {})
            )
            
            self.agent_configs[agent_name] = config
            logger.info(f"Configuración de agente cargada: {agent_name}")
            return config
            
        except Exception as e:
            logger.error(f"Error cargando configuración de agente {agent_name}: {e}")
            return None
    
    def create_sample_configs(self):
        """Crea configuraciones de ejemplo"""
        self._create_sample_rag_configs()
        self._create_sample_agent_config()
        logger.info("Configuraciones de ejemplo creadas")
    
    def _create_sample_rag_configs(self):
        """Crea configuraciones RAG de ejemplo"""
        rags_path = self.config_base_path / "rags"
        rags_path.mkdir(exist_ok=True)
        
        # Configuración para plantas
        plants_config = {
            "display_name": "Plantas y Botánica General",
            "description": "Información general sobre plantas, cultivo y cuidados",
            "enabled": True,
            "priority": 1,
            "vectorstore": {
                "type": "chroma",
                "path": "./data/vectorstores/plants",
                "collection_name": "plants_collection",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "embedding_model": "llama3.1"
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
- Características de especies específicas
- Técnicas de jardinería y horticultura

**Instrucciones de respuesta:**
- Proporciona información práctica y científicamente fundamentada
- Incluye consejos de cuidado cuando sea relevante
- Responde en español de España, de forma clara y educativa

{context}""",
            "categories": ["botánica_general", "cultivo_plantas", "cuidados_plantas"],
            "keywords": {
                "primary": ["planta", "cultivo", "botánica", "jardín"],
                "secondary": ["cuidado", "riego", "fertilización", "poda"]
            },
            "source_paths": ["./data/documents/plants"],
            "custom_settings": {
                "species_focus": ["Malus domestica", "Solanum lycopersicum"],
                "difficulty_level": "beginner_to_advanced"
            }
        }
        
        # Configuración para patologías
        pathology_config = {
            "display_name": "Patologías y Enfermedades de Plantas",
            "description": "Diagnóstico, tratamiento y prevención de enfermedades",
            "enabled": True,
            "priority": 1,
            "vectorstore": {
                "type": "chroma",
                "path": "./data/vectorstores/pathology",
                "collection_name": "pathology_collection",
                "chunk_size": 800,
                "chunk_overlap": 150
            },
            "retrieval": {
                "search_type": "similarity_score_threshold",
                "k": 7,
                "score_threshold": 0.4
            },
            "system_prompt": """Eres un especialista en fitopatología y sanidad vegetal.

**Especialidades principales:**
- Diagnóstico de enfermedades de plantas
- Identificación de plagas y patógenos
- Tratamientos fitosanitarios
- Estrategias de prevención

**IMPORTANTE:** Siempre incluye advertencias de seguridad para productos químicos.

{context}""",
            "categories": ["diagnóstico_enfermedades", "tratamientos", "prevención"],
            "keywords": {
                "primary": ["enfermedad", "plaga", "síntomas", "tratamiento"],
                "secondary": ["hongo", "bacteria", "virus", "prevención"]
            },
            "source_paths": ["./data/documents/pathology"],
            "custom_settings": {
                "safety_warnings": True,
                "treatment_focus": "integrated_pest_management"
            }
        }
        
        # Guardar configuraciones
        with open(rags_path / "plants.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(plants_config, f, default_flow_style=False, allow_unicode=True)
        
        with open(rags_path / "pathology.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(pathology_config, f, default_flow_style=False, allow_unicode=True)
        
        # Configuración para un RAG personalizado de ejemplo
        custom_config = {
            "display_name": "Agricultura Ecológica",
            "description": "Técnicas de agricultura sostenible y ecológica",
            "enabled": True,
            "priority": 2,
            "vectorstore": {
                "type": "chroma",
                "path": "./data/vectorstores/eco_agriculture",
                "chunk_size": 1200,
                "chunk_overlap": 300
            },
            "retrieval": {
                "search_type": "mmr",
                "k": 6,
                "lambda_mult": 0.8
            },
            "system_prompt": """Eres un especialista en agricultura ecológica y sostenible.

Enfócate en técnicas respetuosas con el medio ambiente, biodiversidad y sostenibilidad.

{context}""",
            "categories": ["agricultura_ecológica", "sostenibilidad", "biodiversidad"],
            "source_paths": ["./data/documents/eco_agriculture"],
            "custom_settings": {
                "certification_standards": ["EU_Organic", "USDA_Organic"],
                "focus_areas": ["soil_health", "biodiversity", "water_conservation"]
            }
        }
        
        with open(rags_path / "eco_agriculture.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(custom_config, f, default_flow_style=False, allow_unicode=True)
    
    def _create_sample_agent_config(self):
        """Crea configuración de agentes de ejemplo"""
        agents_config = {
            "agents": {
                "plants": {
                    "description": "Especialista en información general de plantas",
                    "class": "PlantsAgent",
                    "topics": ["plants"],
                    "enabled": True,
                    "priority": 1,
                    "config": {
                        "max_confidence": 1.0,
                        "min_confidence": 0.1,
                        "primary_keywords": [
                            "planta", "plantas", "árbol", "cultivo", "jardín", "botánica"
                        ],
                        "patterns": [
                            "cómo.*cultivar", "cuándo.*plantar", "cuidados.*de"
                        ],
                        "target_species": [
                            "Malus domestica", "Solanum lycopersicum", "Vitis vinifera"
                        ]
                    },
                    "thresholds": {
                        "keyword_weight": 0.3,
                        "species_weight": 0.5,
                        "pattern_weight": 0.2
                    }
                },
                "pathology": {
                    "description": "Especialista en patologías y enfermedades",
                    "class": "PathologyAgent", 
                    "topics": ["pathology"],
                    "enabled": True,
                    "priority": 2,
                    "config": {
                        "max_confidence": 1.0,
                        "min_confidence": 0.1,
                        "primary_keywords": [
                            "enfermedad", "plaga", "hongo", "tratamiento", "síntomas"
                        ],
                        "patterns": [
                            "qué.*enfermedad", "cómo.*tratar", "síntomas.*de"
                        ],
                        "target_species": [
                            "Malus domestica", "Vitis vinifera", "Solanum lycopersicum"
                        ]
                    },
                    "thresholds": {
                        "keyword_weight": 0.5,
                        "symptom_weight": 0.3,
                        "pattern_weight": 0.4
                    }
                },
                "eco_agriculture": {
                    "description": "Especialista en agricultura ecológica",
                    "class": "EcoAgricultureAgent",
                    "topics": ["eco_agriculture"],
                    "enabled": True,
                    "priority": 2,
                    "config": {
                        "max_confidence": 0.9,
                        "min_confidence": 0.1,
                        "primary_keywords": [
                            "ecológico", "sostenible", "orgánico", "biodiversidad", "compost"
                        ],
                        "patterns": [
                            "agricultura.*ecológica", "técnicas.*sostenibles", "sin.*químicos"
                        ]
                    },
                    "thresholds": {
                        "keyword_weight": 0.4,
                        "sustainability_weight": 0.4,
                        "pattern_weight": 0.2
                    }
                }
            },
            "selector": {
                "selection_method": "hybrid",
                "confidence_threshold": 0.3,
                "llm_enabled": True
            }
        }
        
        agents_file = self.config_base_path / "agents.yaml"
        with open(agents_file, 'w', encoding='utf-8') as f:
            yaml.dump(agents_config, f, default_flow_style=False, allow_unicode=True)
    
    def get_all_rag_configs(self) -> Dict[str, RAGTopicConfig]:
        """Obtiene todas las configuraciones RAG disponibles"""
        if not self.rag_configs:
            # Carga automática si no hay configuraciones
            topic_names = self.discover_rag_configs()
            for topic in topic_names:
                self.load_rag_config(topic)
        
        return self.rag_configs
    
    def get_enabled_topics(self) -> List[str]:
        """Obtiene lista de temáticas habilitadas"""
        all_configs = self.get_all_rag_configs()
        return [name for name, config in all_configs.items() if config.enabled]
    
    def reload_if_changed(self) -> List[str]:
        """Recarga configuraciones si han cambiado los archivos"""
        reloaded = []
        
        # Verificar archivos RAG
        rags_path = self.config_base_path / "rags"
        if rags_path.exists():
            for config_file in rags_path.glob("*.yaml"):
                current_mtime = config_file.stat().st_mtime
                stored_mtime = self._file_timestamps.get(str(config_file), 0)
                
                if current_mtime > stored_mtime:
                    topic_name = config_file.stem
                    if self.load_rag_config(topic_name):
                        reloaded.append(f"rag:{topic_name}")
        
        # Verificar archivo de agentes
        agents_file = self.config_base_path / "agents.yaml"
        if agents_file.exists():
            current_mtime = agents_file.stat().st_mtime
            stored_mtime = self._file_timestamps.get(str(agents_file), 0)
            
            if current_mtime > stored_mtime:
                # Recargar todos los agentes
                self.agent_configs.clear()
                reloaded.append("agents:all")
                self._file_timestamps[str(agents_file)] = current_mtime
        
        if reloaded:
            logger.info(f"Configuraciones recargadas: {reloaded}")
        
        return reloaded
    
    def validate_config(self, topic_name: str) -> Dict[str, Any]:
        """Valida configuración de un RAG"""
        config = self.rag_configs.get(topic_name)
        if not config:
            return {"valid": False, "errors": ["Configuración no encontrada"]}
        
        errors = []
        warnings = []
        
        # Validar paths
        vectorstore_path = Path(config.vectorstore.path)
        if not vectorstore_path.exists():
            warnings.append(f"Vectorstore path no existe: {vectorstore_path}")
        
        for source_path in config.source_paths:
            if not Path(source_path).exists():
                warnings.append(f"Source path no existe: {source_path}")
        
        # Validar configuración de retrieval
        if config.retrieval.k > config.retrieval.max_k:
            errors.append(f"k ({config.retrieval.k}) mayor que max_k ({config.retrieval.max_k})")
        
        if not 0 <= config.retrieval.score_threshold <= 1:
            errors.append(f"score_threshold debe estar entre 0 y 1")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

# Instancia global del gestor de configuración
config_manager = ConfigManager()