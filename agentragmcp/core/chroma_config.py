"""
Configuración para ChromaDB sin telemetría
"""
import os

# Deshabilitar telemetría de ChromaDB
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_SERVER_HTTP_PORT"] = "8001"  # Puerto alternativo si hay conflictos

def configure_chroma():
    """Configura ChromaDB para evitar problemas de telemetría y SSL"""
    
    # Configuraciones adicionales
    import chromadb
    from chromadb.config import Settings
    
    # Configuración sin telemetría
    settings = Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True
    )
    
    return settings

# Aplicar configuración al importar
configure_chroma()