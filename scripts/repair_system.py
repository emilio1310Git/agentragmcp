import sys
import time
from pathlib import Path

def main():
    """Script principal de reparación del sistema"""
    
    print("🔧 SISTEMA DE REPARACIÓN AGENTRAGMCP")
    print("=" * 50)
    
    # 1. Crear documentos de ejemplo
    print("\n1️⃣ CREANDO DOCUMENTOS DE EJEMPLO...")
    if create_sample_documents():
        print("✅ Documentos de ejemplo creados")
    else:
        print("⚠️ Algunos documentos ya existían")
    
    # 2. Corregir vectorstores
    print("\n2️⃣ VERIFICANDO VECTORSTORES...")
    fix_vectorstores()
    
    # 3. Recrear configuraciones
    print("\n3️⃣ RECREANDO CONFIGURACIONES...")
    try:
        from agentragmcp.core.dynamic_config import config_manager
        if config_manager.create_sample_configs():
            print("✅ Configuraciones creadas")
        else:
            print("❌ Error creando configuraciones")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 4. Procesar documentos
    print("\n4️⃣ PROCESANDO DOCUMENTOS...")
    print("Ejecuta ahora: python scripts/process_documents.py --all")
    
    # 5. Verificar sistema
    print("\n5️⃣ PARA VERIFICAR EL SISTEMA:")
    print("Ejecuta: python scripts/verify_system.py")
    
    print("\n🎉 REPARACIÓN COMPLETADA")
    print("Ahora puedes ejecutar el sistema con: python -m agentragmcp.api.app.main")

if __name__ == "__main__":
    main()