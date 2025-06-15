import os
from typing import List, Dict, Optional, Any, Union
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
    
    # CORS - permitir tanto string como lista
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=["http://localhost:3000", "http://localhost:8080"], 
        json_schema_extra={"env": "CORS_ORIGINS"}
    )

    # Configuración LLM y Embeddings
    LLM_MODEL: str = Field(default="llama3.1", json_schema_extra={"env": "LLM_MODEL"})
    LLM_BASE_URL: str = Field(default="http://localhost:11434", json_schema_extra={"env": "LLM_BASE_URL"})
    EMBEDDING_MODEL: str = Field(default="llama3.1", json_schema_extra={"env": "EMBEDDING_MODEL"})
    LLM_TEMPERATURE: float = Field(default=0.7, json_schema_extra={"env": "LLM_TEMPERATURE"})
    
    # Configuración dinámica
    DYNAMIC_CONFIG_ENABLED: bool = Field(
        default=True, 
        json_schema_extra={"env": "DYNAMIC_CONFIG_ENABLED"}
    )
    CONFIG_BASE_PATH: str = Field(
        default="./data/configs",
        json_schema_extra={"env": "CONFIG_BASE_PATH"}
    )
    CONFIG_AUTO_RELOAD: bool = Field(
        default=True,
        json_schema_extra={"env": "CONFIG_AUTO_RELOAD"}
    )    
    
    # Configuración RAG - usar string por defecto y convertir
    VECTORSTORE_TYPE: str = Field(default="chroma", json_schema_extra={"env": "VECTORSTORE_TYPE"})
    VECTORSTORE_BASE_PATH: str = Field(
        default="./data/vectorstores", 
        json_schema_extra={"env": "VECTORSTORE_BASE_PATH"}
    )
    RETRIEVAL_K: int = Field(default=5, json_schema_extra={"env": "RETRIEVAL_K"})
    RETRIEVAL_TYPE: str = Field(default="mmr", json_schema_extra={"env": "RETRIEVAL_TYPE"})
    
    # Configuración de agentes
    AGENT_SELECTION_MODEL: str = Field(
        default="llama3.1", 
        json_schema_extra={"env": "AGENT_SELECTION_MODEL"}
    )
    DEFAULT_AGENT: str = Field(default="general", json_schema_extra={"env": "DEFAULT_AGENT"})
    
    # Configuración MCP
    MCP_ENABLED: bool = Field(default=False, json_schema_extra={"env": "MCP_ENABLED"})
    MCP_SERVERS: Union[str, Dict[str, str]] = Field(
        default="", 
        json_schema_extra={"env": "MCP_SERVERS"}
    )
    
    # Configuración de historial de chat
    CHAT_HISTORY_TYPE: str = Field(default="memory", json_schema_extra={"env": "CHAT_HISTORY_TYPE"})
    CHAT_HISTORY_MAX_MESSAGES: int = Field(default=20, json_schema_extra={"env": "CHAT_HISTORY_MAX_MESSAGES"})
    
    # Configuración de monitoreo
    METRICS_ENABLED: bool = Field(default=True, json_schema_extra={"env": "METRICS_ENABLED"})
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parsea orígenes CORS desde string o lista"""
        if v is None or v == "":
            return ["http://localhost:3000", "http://localhost:8080"]
        if isinstance(v, str):
            # Intentar parsear como JSON primero
            if v.startswith('[') and v.endswith(']'):
                try:
                    import json
                    return json.loads(v)
                except:
                    pass
            # Si no es JSON, dividir por comas
            origins = [origin.strip() for origin in v.split(",") if origin.strip()]
            return origins if origins else ["http://localhost:3000", "http://localhost:8080"]
        if isinstance(v, list):
            return v
        return ["http://localhost:3000", "http://localhost:8080"]

    @field_validator("MCP_SERVERS", mode="before")
    @classmethod
    def parse_mcp_servers(cls, v):
        """Parsea servidores MCP desde string o dict"""
        if v is None or v == "":
            return {}
        if isinstance(v, str):
            if v.strip() == "":
                return {}
            # Formato esperado: "server1:url1,server2:url2"
            servers = {}
            for pair in v.split(","):
                if ":" in pair:
                    name, url = pair.split(":", 1)
                    servers[name.strip()] = url.strip()
            return servers
        if isinstance(v, dict):
            return v
        return {}

    def get_vectorstore_path(self, topic: str) -> str:
        """Obtiene el path del vectorstore para una temática específica"""
        # Intentar usar path específico configurado
        from agentragmcp.core.dynamic_config import config_manager
        config = config_manager.get_rag_config(topic)
        if config:
            return config.vectorstore.path
        return os.path.join(self.VECTORSTORE_BASE_PATH, topic)

    @property
    def available_topics(self) -> List[str]:
        """Devuelve las temáticas RAG disponibles"""
        from agentragmcp.core.dynamic_config import config_manager
        return list(config_manager.get_available_topics())

    @property
    def is_production(self) -> bool:
        """Indica si está en entorno de producción"""
        return self.ENVIRONMENT.lower() == "production"

@lru_cache
def get_settings() -> Settings:
    """Factory function para evitar instanciación temprana"""
    return Settings()