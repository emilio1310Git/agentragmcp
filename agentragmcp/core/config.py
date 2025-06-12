
import os
from typing import List, Dict, Optional, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """Configuración principal de AgentRagMCP con variables de entorno."""

    model_config = SettingsConfigDict(
        case_sensitive=True, 
        env_file_encoding="utf-8",
        env_file=".env", 
        extra="allow",
        validate_default=True,
        arbitrary_types_allowed=True
    )
    
    # Configuración básica de la aplicación
    APP_NAME: str = Field("agentragmcp", json_schema_extra={"env": 'APP_NAME'})
    API_PREFIX: str = Field("/api", json_schema_extra={"env": "API_PREFIX"}) 
    APP_VERSION: str = Field(default="2.0.0", json_schema_extra={"env": "APP_VERSION"})
    APP_DESCRIPTION: str = Field(
        default="agentragmcp - Asistente IA especializado en plantas con múltiples RAGs",
        json_schema_extra={"env": "APP_DESCRIPTION"}
    )
    ENVIRONMENT: str = Field(default="development", json_schema_extra={"env": "ENVIRONMENT"})
    DEBUG: bool = Field(default=False, json_schema_extra={"env": "DEBUG"}) 
    LOG_LEVEL: str = Field(default="info", json_schema_extra={"env": "LOG_LEVEL"})

    # Configuración API
    API_HOST: str = Field(default="localhost", json_schema_extra={"env": "API_HOST"})
    API_PORT: int = Field(default=8000, json_schema_extra={"env": "API_PORT"}) 
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"], 
        json_schema_extra={"env": "CORS_ORIGINS"}
    )

    # Configuración LLM y Embeddings
    LLM_MODEL: str = Field(default="llama3.1", json_schema_extra={"env": "LLM_MODEL"})
    LLM_BASE_URL: str = Field(default="http://localhost:11434", json_schema_extra={"env": "LLM_BASE_URL"})
    EMBEDDING_MODEL: str = Field(default="llama3.1", json_schema_extra={"env": "EMBEDDING_MODEL"})
    LLM_TEMPERATURE: float = Field(default=0.7, json_schema_extra={"env": "LLM_TEMPERATURE"})
    
    # Configuración RAG
    VECTORSTORE_TYPE: str = Field(default="chroma", json_schema_extra={"env": "VECTORSTORE_TYPE"})
    VECTORSTORE_BASE_PATH: str = Field(
        default="./data/vectorstores", 
        json_schema_extra={"env": "VECTORSTORE_BASE_PATH"}
    )
    RETRIEVAL_K: int = Field(default=5, json_schema_extra={"env": "RETRIEVAL_K"})
    RETRIEVAL_TYPE: str = Field(default="mmr", json_schema_extra={"env": "RETRIEVAL_TYPE"})
    
    # Configuración de temáticas RAG (desde .env)
    RAG_TOPICS: List[str] = Field(
        default=["plants", "pathology", "general"],
        json_schema_extra={"env": "RAG_TOPICS"}
    )
    
    # Configuración específica por temática
    PLANTS_VECTORSTORE_PATH: str = Field(
        default="./data/vectorstores/plants", 
        json_schema_extra={"env": "PLANTS_VECTORSTORE_PATH"}
    )
    PATHOLOGY_VECTORSTORE_PATH: str = Field(
        default="./data/vectorstores/pathology", 
        json_schema_extra={"env": "PATHOLOGY_VECTORSTORE_PATH"}
    )
    GENERAL_VECTORSTORE_PATH: str = Field(
        default="./data/vectorstores/general", 
        json_schema_extra={"env": "GENERAL_VECTORSTORE_PATH"}
    )
    
    # Configuración de agentes
    AGENT_SELECTION_MODEL: str = Field(
        default="llama3.1", 
        json_schema_extra={"env": "AGENT_SELECTION_MODEL"}
    )
    DEFAULT_AGENT: str = Field(default="general", json_schema_extra={"env": "DEFAULT_AGENT"})
    
    # Configuración MCP
    MCP_ENABLED: bool = Field(default=False, json_schema_extra={"env": "MCP_ENABLED"})
    MCP_SERVERS: Dict[str, str] = Field(
        default={}, 
        json_schema_extra={"env": "MCP_SERVERS"}
    )  # formato: {"server_name": "server_url"}
    
    # Configuración de historial de chat
    CHAT_HISTORY_TYPE: str = Field(default="memory", json_schema_extra={"env": "CHAT_HISTORY_TYPE"})
    CHAT_HISTORY_MAX_MESSAGES: int = Field(default=20, json_schema_extra={"env": "CHAT_HISTORY_MAX_MESSAGES"})
    
    # Configuración de monitoreo
    METRICS_ENABLED: bool = Field(default=True, json_schema_extra={"env": "METRICS_ENABLED"})
    
    # Configuraciones específicas de especies y patologías
    SPECIFIC_SPECIES: List[str] = Field(
        default=[
            "Malus domestica", "Prunus cerasus", "Vitis vinifera", 
            "Citrus aurantium", "Prunus persica", "Fragaria vesca",
            "Solanum lycopersicum", "Psidium guajava", "Syzygium cumini",
            "Citrus limon", "Mangifera indica", "Punica granatum",
            "Prunus armeniaca", "Vaccinium macrocarpon", "Pyrus communis"
        ],
        json_schema_extra={"env": "SPECIFIC_SPECIES"}
    )
    
    PATHOLOGY_SPECIES: List[str] = Field(
        default=[
            "Malus domestica", "Vitis vinifera", "Citrus aurantium", 
            "Solanum lycopersicum"
        ],
        json_schema_extra={"env": "PATHOLOGY_SPECIES"}
    )

    @field_validator("RAG_TOPICS", mode="before")
    @classmethod
    def parse_rag_topics(cls, v):
        """Parsea la lista de temáticas RAG desde string o lista"""
        if isinstance(v, str):
            return [topic.strip() for topic in v.split(",")]
        return v

    @field_validator("SPECIFIC_SPECIES", "PATHOLOGY_SPECIES", mode="before")
    @classmethod
    def parse_species_lists(cls, v):
        """Parsea las listas de especies desde string o lista"""
        if isinstance(v, str):
            return [species.strip() for species in v.split(",")]
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parsea orígenes CORS desde string o lista"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("MCP_SERVERS", mode="before")
    @classmethod
    def parse_mcp_servers(cls, v):
        """Parsea servidores MCP desde string o dict"""
        if isinstance(v, str) and v:
            # Formato esperado: "server1:url1,server2:url2"
            servers = {}
            for pair in v.split(","):
                if ":" in pair:
                    name, url = pair.split(":", 1)
                    servers[name.strip()] = url.strip()
            return servers
        return v or {}

    def get_vectorstore_path(self, topic: str) -> str:
        """Obtiene el path del vectorstore para una temática específica"""
        # Intentar usar path específico configurado
        specific_path_attr = f"{topic.upper()}_VECTORSTORE_PATH"
        if hasattr(self, specific_path_attr):
            return getattr(self, specific_path_attr)
        
        # Fallback al path base
        return os.path.join(self.VECTORSTORE_BASE_PATH, topic)

    @property
    def available_topics(self) -> List[str]:
        """Devuelve las temáticas RAG disponibles"""
        return self.RAG_TOPICS

    @property
    def is_production(self) -> bool:
        """Indica si está en entorno de producción"""
        return self.ENVIRONMENT.lower() == "production"

@lru_cache
def get_settings() -> Settings:
    """Factory function para evitar instanciación temprana"""
    return Settings()