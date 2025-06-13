#!/usr/bin/env python3
"""
Script para testear la configuración corregida
"""

import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def test_configuration():
    """Prueba la carga de configuración"""
    print("🧪 TESTEANDO CONFIGURACIÓN CORREGIDA")
    print("=" * 50)
    
    try:
        # Importar y cargar configuración
        from agentragmcp.core.config import get_settings
        
        print("✅ Importación exitosa")
        
        # Intentar crear la configuración
        settings = get_settings()
        
        print("✅ Configuración cargada exitosamente")
        print()
        
        # Mostrar valores clave
        print("📋 VALORES DE CONFIGURACIÓN:")
        print(f"   APP_NAME: {settings.APP_NAME}")
        print(f"   ENVIRONMENT: {settings.ENVIRONMENT}")
        print(f"   API_HOST: {settings.API_HOST}")
        print(f"   API_PORT: {settings.API_PORT}")
        print()
        
        print("📋 LISTAS PARSEADAS:")
        print(f"   RAG_TOPICS: {settings.RAG_TOPICS}")
        print(f"   CORS_ORIGINS: {settings.CORS_ORIGINS}")
        print(f"   SPECIFIC_SPECIES: {len(settings.SPECIFIC_SPECIES)} especies")
        print(f"   PATHOLOGY_SPECIES: {len(settings.PATHOLOGY_SPECIES)} especies")
        print()
        
        print("📋 PROPIEDADES CALCULADAS:")
        print(f"   available_topics: {settings.available_topics}")
        print(f"   is_production: {settings.is_production}")
        print()
        
        print("📋 PATHS DE VECTORSTORES:")
        for topic in settings.available_topics:
            path = settings.get_vectorstore_path(topic)
            print(f"   {topic}: {path}")
        
        print()
        print("🎉 ¡CONFIGURACIÓN FUNCIONANDO CORRECTAMENTE!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print(f"🔍 Tipo: {type(e).__name__}")
        
        # Mostrar traceback completo para debugging
        import traceback
        print("\n📜 TRACEBACK COMPLETO:")
        traceback.print_exc()
        
        return False

def check_env_file():
    """Verifica el archivo .env"""
    print("\n🔍 VERIFICANDO ARCHIVO .env")
    print("=" * 50)
    
    env_path = root_dir / ".env"
    
    if not env_path.exists():
        print("❌ Archivo .env no encontrado")
        return False
    
    print(f"✅ Archivo .env encontrado: {env_path}")
    
    # Leer y mostrar líneas problemáticas
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📏 Total líneas: {len(lines)}")
    
    # Buscar variables problemáticas
    problematic_vars = ['RAG_TOPICS', 'CORS_ORIGINS', 'SPECIFIC_SPECIES', 'MCP_SERVERS']
    
    for var in problematic_vars:
        for i, line in enumerate(lines, 1):
            if line.strip().startswith(f"{var}="):
                value = line.strip().split('=', 1)[1] if '=' in line else ''
                print(f"   Línea {i}: {var} = '{value}'")
    
    return True

if __name__ == "__main__":
    print(f"📍 Directorio de trabajo: {root_dir}")
    
    check_env_file()
    test_configuration()