import os
import shutil
from pathlib import Path
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger

def fix_vectorstores():
    """
    Soluciona problemas de dimensionalidad en vectorstores existentes
    """
    print("🔧 SOLUCIONANDO PROBLEMAS DE VECTORSTORES...")
    
    settings = get_settings()
    vectorstore_base = Path(settings.VECTORSTORE_BASE_PATH)
    
    # Obtener embedding model actual
    current_embedding_model = settings.EMBEDDING_MODEL
    print(f"Modelo de embeddings actual: {current_embedding_model}")
    
    # Crear embeddings con modelo actual
    embeddings = OllamaEmbeddings(
        model=current_embedding_model,
        base_url=settings.LLM_BASE_URL
    )
    
    # Obtener dimensión del modelo actual
    test_embedding = embeddings.embed_query("test")
    current_dimension = len(test_embedding)
    print(f"Dimensión actual del modelo: {current_dimension}")
    
    # Verificar cada vectorstore
    topics = ['plants', 'pathology', 'general', 'eco_agriculture', 'urban_gardening']
    
    for topic in topics:
        vectorstore_path = vectorstore_base / topic
        
        if not vectorstore_path.exists():
            print(f"⚠️ Vectorstore {topic} no existe: {vectorstore_path}")
            continue
            
        print(f"\n🔍 Verificando vectorstore: {topic}")
        
        try:
            # Intentar cargar vectorstore existente
            vectorstore = Chroma(
                persist_directory=str(vectorstore_path),
                embedding_function=embeddings
            )
            
            # Probar una consulta simple
            results = vectorstore.similarity_search("test", k=1)
            print(f"✅ Vectorstore {topic} es compatible")
            
        except Exception as e:
            error_msg = str(e)
            if "dimension" in error_msg.lower():
                print(f"❌ Error de dimensionalidad en {topic}: {error_msg}")
                fix_vectorstore_dimensions(topic, vectorstore_path, embeddings)
            else:
                print(f"⚠️ Error desconocido en {topic}: {e}")

def fix_vectorstore_dimensions(topic: str, vectorstore_path: Path, embeddings):
    """
    Corrige problemas de dimensionalidad eliminando y recreando el vectorstore
    """
    print(f"🔄 Corrigiendo dimensionalidad para {topic}...")
    
    # Hacer backup si es importante
    backup_path = vectorstore_path.parent / f"{topic}_backup_{int(time.time())}"
    try:
        shutil.move(str(vectorstore_path), str(backup_path))
        print(f"📁 Backup creado en: {backup_path}")
    except Exception as e:
        print(f"⚠️ No se pudo crear backup: {e}")
    
    # Crear directorio vacío
    vectorstore_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🗑️ Vectorstore {topic} eliminado. Necesitas recrearlo con:")
    print(f"   python scripts/process_documents.py --topic {topic}")