#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de configuración
"""
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def check_env_file():
    """Verifica el archivo .env"""
    env_path = root_dir / ".env"
    
    print("🔍 DIAGNÓSTICO DE CONFIGURACIÓN")
    print("=" * 40)
    
    print(f"📍 Directorio actual: {os.getcwd()}")
    print(f"📁 Directorio raíz: {root_dir}")
    print(f"📄 Archivo .env: {env_path}")
    print(f"📄 Existe .env: {'✅' if env_path.exists() else '❌'}")
    
    if env_path.exists():
        print(f"📏 Tamaño .env: {env_path.stat().st_size} bytes")
        
        # Leer contenido del .env
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📝 Líneas en .env: {len(content.splitlines())}")
            
            # Buscar CORS_ORIGINS específicamente
            lines = content.splitlines()
            cors_line = None
            for i, line in enumerate(lines):
                if line.startswith('CORS_ORIGINS'):
                    cors_line = (i + 1, line)
                    break
            
            if cors_line:
                print(f"🎯 CORS_ORIGINS encontrado en línea {cors_line[0]}: {cors_line[1]}")
            else:
                print("⚠️  CORS_ORIGINS no encontrado en .env")
            
            # Mostrar variables que pueden causar problemas
            problematic_vars = ['CORS_ORIGINS', 'RAG_TOPICS', 'SPECIFIC_SPECIES', 'MCP_SERVERS']
            print(f"\n🔍 VARIABLES PROBLEMÁTICAS:")
            for var in problematic_vars:
                for line in lines:
                    if line.startswith(f'{var}='):
                        print(f"   {var}: {line.split('=', 1)[1]}")
                        break
                else:
                    print(f"   {var}: (no definida)")
        
        except Exception as e:
            print(f"❌ Error leyendo .env: {e}")
    
    else:
        print("❌ Archivo .env no existe")

def test_config_loading():
    """Prueba cargar la configuración"""
    print(f"\n🧪 PRUEBA DE CARGA DE CONFIGURACIÓN")
    print("=" * 40)
    
    try:
        # Intentar importar
        from agentragmcp.core.config import get_settings
        print("✅ Importación exitosa")
        
        # Intentar crear configuración
        settings = get_settings()
        print("✅ Configuración creada")
        
        # Mostrar valores importantes
        print(f"📱 APP_NAME: {settings.APP_NAME}")
        print(f"🌐 CORS_ORIGINS: {settings.CORS_ORIGINS}")
        print(f"📚 RAG_TOPICS: {settings.RAG_TOPICS}")
        print(f"🤖 LLM_MODEL: {settings.LLM_MODEL}")
        print(f"🔗 LLM_BASE_URL: {settings.LLM_BASE_URL}")
        
        print("✅ Configuración cargada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando configuración: {e}")
        print(f"🔍 Tipo de error: {type(e).__name__}")
        
        # Mostrar traceback completo
        import traceback
        traceback.print_exc()
        return False

def create_minimal_env():
    """Crea un archivo .env mínimo"""
    env_path = root_dir / ".env"
    
    minimal_config = """# Configuración mínima para AgentRagMCP
APP_NAME=AgentRagMCP
APP_VERSION=1.0.0
ENVIRONMENT=development
DEBUG=true

# API
API_HOST=localhost
API_PORT=8000

# CORS - formato JSON válido
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]

# LLM
LLM_MODEL=hdnh2006/salamandra-7b-instruct:latest
LLM_BASE_URL=http://localhost:11434
EMBEDDING_MODEL=hdnh2006/salamandra-7b-instruct:latest

# RAG - lista separada por comas
RAG_TOPICS=plants,pathology,general
VECTORSTORE_BASE_PATH=./data/vectorstores

# Agentes
DEFAULT_AGENT=general

# MCP
MCP_ENABLED=false
MCP_SERVERS=

# Especies - listas separadas por comas
SPECIFIC_SPECIES=Malus domestica,Vitis vinifera,Solanum lycopersicum
PATHOLOGY_SPECIES=Malus domestica,Vitis vinifera
"""
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(minimal_config.strip())
        
        print(f"✅ Archivo .env mínimo creado en: {env_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando .env mínimo: {e}")
        return False

def main():
    """Función principal de diagnóstico"""
    check_env_file()
    
    success = test_config_loading()
    
    if not success:
        print(f"\n🔧 INTENTANDO CREAR CONFIGURACIÓN MÍNIMA...")
        if create_minimal_env():
            print(f"\n🔄 PROBANDO NUEVAMENTE...")
            test_config_loading()
    
    print(f"\n💡 PRÓXIMOS PASOS:")
    print(f"1. Asegúrate de que el archivo .env esté en: {root_dir}")
    print(f"2. Verifica que CORS_ORIGINS tenga formato JSON válido")
    print(f"3. Ejecuta: python scripts/process_documents.py --create-samples")

if __name__ == "__main__":
    main()