"""
Script simplificado para procesar documentos y crear vectorstores
Soluciona los problemas de dimensionalidad y configuración
"""

import sys
import os
from pathlib import Path
from typing import List

# Añadir directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def process_topic(topic: str) -> bool:
    """
    Procesa documentos de una temática específica y crea el vectorstore
    """
    print(f"\n🔄 PROCESANDO TEMA: {topic.upper()}")
    print("-" * 30)
    
    try:
        # Imports necesarios
        from langchain_community.document_loaders import DirectoryLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings
        from agentragmcp.core.config import get_settings
        
        settings = get_settings()
        
        # Configurar paths
        documents_dir = root_dir / "data" / "documents" / topic
        vectorstore_dir = root_dir / "data" / "vectorstores" / topic
        
        # Verificar que existen documentos
        if not documents_dir.exists():
            print(f"❌ Directorio de documentos no existe: {documents_dir}")
            return False
        
        # Buscar archivos de texto
        txt_files = list(documents_dir.glob("*.txt"))
        if not txt_files:
            print(f"❌ No se encontraron archivos .txt en {documents_dir}")
            return False
        
        print(f"📄 Encontrados {len(txt_files)} archivos:")
        for file in txt_files:
            print(f"   - {file.name}")
        
        # Cargar documentos
        print("📂 Cargando documentos...")
        loader = DirectoryLoader(
            str(documents_dir),
            glob="*.txt",
            show_progress=True
        )
        documents = loader.load()
        
        if not documents:
            print("❌ No se pudieron cargar documentos")
            return False
        
        print(f"✅ Cargados {len(documents)} documentos")
        
        # Dividir en chunks
        print("✂️ Dividiendo documentos en chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"✅ Creados {len(chunks)} chunks")
        
        # Crear embeddings con modelo consistente
        print("🧠 Inicializando embeddings...")
        embeddings = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL,
            base_url=settings.LLM_BASE_URL
        )
        
        # Probar embeddings
        test_embedding = embeddings.embed_query("test")
        embedding_dimension = len(test_embedding)
        print(f"📏 Dimensión de embeddings: {embedding_dimension}")
        
        # Limpiar vectorstore existente si hay problemas de dimensionalidad
        if vectorstore_dir.exists():
            print("🗑️ Eliminando vectorstore existente...")
            import shutil
            shutil.rmtree(vectorstore_dir)
        
        # Crear directorio
        vectorstore_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear vectorstore
        print("🏗️ Creando vectorstore...")
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(vectorstore_dir)
        )
        
        print(f"✅ Vectorstore creado en: {vectorstore_dir}")
        
        # Validar vectorstore
        print("🔍 Validando vectorstore...")
        test_results = vectorstore.similarity_search("test", k=1)
        if test_results:
            print(f"✅ Vectorstore validado - {len(test_results)} resultados de prueba")
            return True
        else:
            print("⚠️ Vectorstore creado pero sin resultados de prueba")
            return True
            
    except Exception as e:
        print(f"❌ Error procesando {topic}: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_ollama_connection():
    """
    Verifica que Ollama esté disponible
    """
    print("🔌 VERIFICANDO CONEXIÓN CON OLLAMA...")
    
    try:
        from agentragmcp.core.config import get_settings
        from langchain_ollama import OllamaEmbeddings
        
        settings = get_settings()
        
        # Intentar conectar
        embeddings = OllamaEmbeddings(
            model=settings.EMBEDDING_MODEL,
            base_url=settings.LLM_BASE_URL
        )
        
        # Probar embedding simple
        test_embedding = embeddings.embed_query("hello")
        
        print(f"✅ Ollama conectado en {settings.LLM_BASE_URL}")
        print(f"✅ Modelo {settings.EMBEDDING_MODEL} disponible")
        print(f"📏 Dimensión de embeddings: {len(test_embedding)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error conectando con Ollama: {e}")
        print("\n💡 SOLUCIONES:")
        print("1. Verificar que Ollama esté ejecutándose: ollama serve")
        print("2. Verificar modelo: ollama pull llama3.1")
        print("3. Verificar URL en .env: LLM_BASE_URL=http://localhost:11434")
        return False

def main():
    """
    Función principal
    """
    print("📚 PROCESADOR SIMPLIFICADO DE DOCUMENTOS")
    print("=" * 45)
    
    # Verificar argumentos
    topics_to_process = []
    
    if len(sys.argv) > 1:
        if "--all" in sys.argv:
            topics_to_process = ["plants", "pathology", "general"]
        else:
            # Procesar topics específicos
            for arg in sys.argv[1:]:
                if arg.startswith("--topic="):
                    topic = arg.split("=")[1]
                    topics_to_process.append(topic)
                elif arg in ["plants", "pathology", "general"]:
                    topics_to_process.append(arg)
    
    if not topics_to_process:
        print("❓ USO:")
        print("  python scripts/process_documents_simple.py --all")
        print("  python scripts/process_documents_simple.py plants pathology")
        print("  python scripts/process_documents_simple.py --topic=plants")
        return False
    
    print(f"🎯 Procesando temas: {', '.join(topics_to_process)}")
    
    # Verificar Ollama
    if not check_ollama_connection():
        return False
    
    # Procesar cada tema
    success_count = 0
    for topic in topics_to_process:
        if process_topic(topic):
            success_count += 1
        else:
            print(f"❌ Error procesando {topic}")
    
    # Resumen
    print("\n📊 RESUMEN DEL PROCESAMIENTO")
    print("=" * 30)
    print(f"✅ Temas procesados exitosamente: {success_count}/{len(topics_to_process)}")
    
    if success_count > 0:
        print(f"\n🎉 ¡Procesamiento completado!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Verificar sistema: python scripts/verify_system.py")
        print("2. Ejecutar aplicación: python -m agentragmcp.api.app.main")
    else:
        print(f"\n❌ No se procesó ningún tema correctamente")
        print("Revisa los errores anteriores")
    
    return success_count == len(topics_to_process)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)