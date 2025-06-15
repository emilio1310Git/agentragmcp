#!/usr/bin/env python3
"""
Script de inicialización para AgentRagMCP
Prepara el entorno, verifica dependencias y configura los servicios
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import setup_logging

def setup_directories(base_path: Path) -> bool:
    """
    Crea la estructura de directorios necesaria.
    
    Args:
        base_path: Directorio base del proyecto
        
    Returns:
        bool: True si se crearon correctamente
    """
    directories = [
        "data/vectorstores/plants",
        "data/vectorstores/pathology", 
        "data/vectorstores/general",
        "data/configs",
        "logs/agentragmcp",
        "static",
        "tests/data"
    ]
    
    success = True
    for directory in directories:
        dir_path = base_path / directory
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Directorio creado/verificado: {dir_path}")
        except Exception as e:
            print(f"✗ Error creando directorio {dir_path}: {e}")
            success = False
    
    return success

def check_dependencies() -> Dict[str, bool]:
    """
    Verifica que las dependencias principales estén instaladas.
    
    Returns:
        Dict con el estado de cada dependencia
    """
    dependencies = {
        "fastapi": False,
        "langchain": False,
        "langchain_chroma": False,
        "langchain_ollama": False,
        "pydantic": False,
        "uvicorn": False,
        "httpx": False,
        "pyyaml": False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
            print(f"✓ {dep} - Instalado")
        except ImportError:
            print(f"✗ {dep} - No encontrado")
            dependencies[dep] = False
    
    return dependencies

def verify_ollama_connection(base_url: str = "http://localhost:11434") -> bool:
    """
    Verifica la conexión con Ollama.
    
    Args:
        base_url: URL base de Ollama
        
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        import httpx
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"✓ Ollama conectado - {len(models)} modelos disponibles")
                
                # Mostrar modelos disponibles
                for model in models[:3]:  # Mostrar solo los primeros 3
                    print(f"  - {model.get('name', 'Unknown')}")
                
                return True
            else:
                print(f"✗ Ollama responde con código: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"✗ Error conectando con Ollama: {e}")
        return False

def check_vectorstores(settings) -> Dict[str, bool]:
    """
    Verifica el estado de los vectorstores.
    
    Args:
        settings: Configuración de la aplicación
        
    Returns:
        Dict con el estado de cada vectorstore
    """
    vectorstores = {}
    
    for topic in settings.RAG_TOPICS:
        path = Path(settings.get_vectorstore_path(topic))
        exists = path.exists() and any(path.iterdir()) if path.exists() else False
        vectorstores[topic] = exists
        
        status = "✓ Existe" if exists else "✗ No encontrado"
        print(f"{status} Vectorstore '{topic}': {path}")
    
    return vectorstores

def create_sample_env_file(base_path: Path) -> bool:
    """
    Crea un archivo .env de ejemplo si no existe.
    
    Args:
        base_path: Directorio base del proyecto
        
    Returns:
        bool: True si se creó correctamente
    """
    env_file = base_path / ".env"
    
    if env_file.exists():
        print(f"✓ Archivo .env ya existe: {env_file}")
        return True
    
    env_example = base_path / ".env.example"
    if not env_example.exists():
        print(f"✗ Archivo .env.example no encontrado")
        return False
    
    try:
        # Copiar .env.example a .env
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            content = src.read()
            dst.write(content)
        
        print(f"✓ Archivo .env creado desde .env.example")
        print(f"  → Revisa y ajusta la configuración en: {env_file}")
        return True
        
    except Exception as e:
        print(f"✗ Error creando archivo .env: {e}")
        return False

def verify_configuration() -> Dict[str, Any]:
    """
    Verifica la configuración actual.
    
    Returns:
        Dict con información de configuración
    """
    try:
        settings = get_settings()
        
        config_status = {
            "app_name": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
            "llm_model": settings.LLM_MODEL,
            "llm_url": settings.LLM_BASE_URL,
            "topics": settings.RAG_TOPICS,
            "mcp_enabled": settings.MCP_ENABLED,
            "valid": True
        }
        
        print("✓ Configuración cargada correctamente:")
        print(f"  - Aplicación: {settings.APP_NAME} v{settings.APP_VERSION}")
        print(f"  - Entorno: {settings.ENVIRONMENT}")
        print(f"  - LLM: {settings.LLM_MODEL} @ {settings.LLM_BASE_URL}")
        print(f"  - Temáticas RAG: {', '.join(settings.RAG_TOPICS)}")
        print(f"  - MCP habilitado: {settings.MCP_ENABLED}")
        
        return config_status
        
    except Exception as e:
        print(f"✗ Error en configuración: {e}")
        return {"valid": False, "error": str(e)}

def run_health_checks() -> bool:
    """
    Ejecuta checks de salud básicos.
    
    Returns:
        bool: True si todos los checks pasan
    """
    print("\n=== HEALTH CHECKS ===")
    
    all_checks_passed = True
    
    # Check 1: Configuración
    config_status = verify_configuration()
    if not config_status.get("valid", False):
        all_checks_passed = False
    
    # Check 2: Conexión Ollama
    settings = get_settings()
    ollama_ok = verify_ollama_connection(settings.LLM_BASE_URL)
    if not ollama_ok:
        all_checks_passed = False
    
    # Check 3: Vectorstores
    vectorstores = check_vectorstores(settings)
    if not any(vectorstores.values()):
        print("⚠️  Ningún vectorstore encontrado - necesitarás cargar datos")
        # No marca como fallo porque es normal en primera instalación
    
    return all_checks_passed

def check_dynamic_system():
    """Verifica que el sistema dinámico esté configurado"""
    config_path = Path("data/configs")
    if not config_path.exists():
        print("⚠️  Sistema dinámico no configurado. Ejecutar migración.")
        return False
    return True

def create_sample_data_info(base_path: Path) -> bool:
    """
    Crea información sobre cómo agregar datos de ejemplo.
    
    Args:
        base_path: Directorio base del proyecto
        
    Returns:
        bool: True si se creó correctamente
    """
    data_dir = base_path / "data"
    data_dir.mkdir(exist_ok=True)
    
    readme_content = """# Datos para AgentRagMCP

## Estructura de Vectorstores

Los vectorstores deben colocarse en:
- `vectorstores/plants/` - Información general de plantas
- `vectorstores/pathology/` - Patologías y enfermedades  
- `vectorstores/general/` - Conocimiento general

## Formato de Datos

Los datos pueden estar en formato:
- PDF
- Texto plano (.txt)
- Markdown (.md)
- JSON estructurado

## Creación de Vectorstores

Para crear vectorstores desde documentos:

```python
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Cargar documentos
loader = DirectoryLoader("./docs/plants", glob="**/*.txt")
documents = loader.load()

# Dividir en chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)

# Crear embeddings
embeddings = OllamaEmbeddings(model="hdnh2006/salamandra-7b-instruct:latest")

# Crear vectorstore
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./data/vectorstores/plants"
)
```

## Fuentes de Datos Recomendadas

- Manuales de agricultura y horticultura
- Guías de identificación de plantas
- Documentación científica sobre patologías
- Enciclopedias botánicas
- Artículos de divulgación científica
"""
    
    try:
        readme_file = data_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✓ Información sobre datos creada: {readme_file}")
        return True
        
    except Exception as e:
        print(f"✗ Error creando información de datos: {e}")
        return False

def main():
    """Función principal del script de inicialización."""
    parser = argparse.ArgumentParser(description="Inicialización de AgentRagMCP")
    parser.add_argument("--skip-deps", action="store_true", 
                       help="Saltar verificación de dependencias")
    parser.add_argument("--skip-ollama", action="store_true",
                       help="Saltar verificación de Ollama")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Modo verbose")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    print("🚀 Inicializando AgentRagMCP...\n")
    
    # Obtener directorio base
    base_path = Path(__file__).parent.parent
    print(f"Directorio base: {base_path}\n")
    
    # Paso 1: Crear estructura de directorios
    print("=== CREANDO ESTRUCTURA DE DIRECTORIOS ===")
    if not setup_directories(base_path):
        print("❌ Error creando directorios")
        sys.exit(1)
    
    # Paso 2: Verificar dependencias
    if not args.skip_deps:
        print("\n=== VERIFICANDO DEPENDENCIAS ===")
        deps = check_dependencies()
        missing_deps = [dep for dep, installed in deps.items() if not installed]
        
        if missing_deps:
            print(f"\n❌ Dependencias faltantes: {', '.join(missing_deps)}")
            print("Instálalas con: pip install -r config/requirements.txt")
            sys.exit(1)
    
    # Paso 3: Crear archivo .env
    print("\n=== CONFIGURANDO ARCHIVO .ENV ===")
    if not create_sample_env_file(base_path):
        print("⚠️  No se pudo crear archivo .env")
    
    # Paso 4: Verificar configuración
    print("\n=== VERIFICANDO CONFIGURACIÓN ===")
    if not verify_configuration():
        print("❌ Error en configuración")
        sys.exit(1)
    
    # Paso 5: Health checks
    if run_health_checks():
        print("\n✅ Todos los health checks pasaron")
    else:
        print("\n⚠️  Algunos health checks fallaron")
    
    # Paso 6: Crear información sobre datos
    print("\n=== CREANDO INFORMACIÓN DE DATOS ===")
    create_sample_data_info(base_path)
    
    print("\n🎉 Inicialización completada!")
    print("\n📋 Próximos pasos:")
    print("1. Ajusta la configuración en .env si es necesario")
    print("2. Asegúrate de que Ollama esté corriendo con el modelo llama3.1")
    print("3. Agrega documentos a los directorios de vectorstores")
    print("4. Ejecuta la aplicación con: python -m agentragmcp.api.app.main")
    print("\n📖 Documentación completa en: README.md")

if __name__ == "__main__":
    main()