#!/usr/bin/env python3
"""
Script para poblar los vectorstores de AgentRagMCP
"""

import os
import logging
from pathlib import Path
from typing import List, Dict
import yaml

from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader, 
    PyPDFLoader,
    CSVLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStorePopulator:
    """Poblador de vectorstores para AgentRagMCP"""
    
    def __init__(self, base_path: str = "./data", embedding_model: str = "hdnh2006/salamandra-7b-instruct:latest"):
        self.base_path = Path(base_path)
        self.vectorstore_path = self.base_path / "vectorstores"
        self.documents_path = self.base_path / "documents"
        self.embedding_model = embedding_model
        
        # Crear directorios si no existen
        self.vectorstore_path.mkdir(parents=True, exist_ok=True)
        self.documents_path.mkdir(parents=True, exist_ok=True)
        
        # Configuración de embeddings
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url="http://localhost:11434"
        )
        
        # Configuración de text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
    
    def get_topics_config(self) -> Dict[str, Dict]:
        """Obtiene configuración de temáticas"""
        return {
            "eco_agriculture": {
                "display_name": "Agricultura Ecológica",
                "description": "Conocimiento sobre agricultura sostenible y ecológica",
                "keywords": ["agricultura", "ecológico", "sostenible", "orgánico", "permacultura"],
                "sample_docs": [
                    "La agricultura ecológica es un sistema de producción que evita el uso de pesticidas sintéticos.",
                    "Los principios de la permacultura incluyen cuidar la tierra, cuidar las personas y compartir equitativamente.",
                    "El compostaje es fundamental en la agricultura ecológica para mantener la fertilidad del suelo."
                ]
            },
            "general": {
                "display_name": "General",
                "description": "Conocimiento general sobre plantas y jardinería",
                "keywords": ["plantas", "jardinería", "cuidados", "general"],
                "sample_docs": [
                    "Las plantas necesitan luz, agua y nutrientes para crecer adecuadamente.",
                    "El riego debe adaptarse a las necesidades específicas de cada especie.",
                    "La poda es importante para mantener la forma y salud de las plantas."
                ]
            },
            "pathology": {
                "display_name": "Patología Vegetal",
                "description": "Enfermedades y problemas de las plantas",
                "keywords": ["enfermedades", "plagas", "patología", "hongos", "virus"],
                "sample_docs": [
                    "El oídio es un hongo que aparece como polvo blanco en las hojas.",
                    "Los pulgones son insectos que chupan la savia de las plantas.",
                    "La clorosis férrica causa amarillamiento de hojas por falta de hierro."
                ]
            },
            "plants": {
                "display_name": "Plantas",
                "description": "Información específica sobre especies de plantas",
                "keywords": ["especies", "taxonomía", "características", "cultivo"],
                "sample_docs": [
                    "El tomate (Solanum lycopersicum) es una planta de la familia Solanaceae.",
                    "Las rosas requieren suelo bien drenado y exposición solar directa.",
                    "Los cactus son plantas suculentas adaptadas a climas áridos."
                ]
            },
            "urban_gardening": {
                "display_name": "Jardinería Urbana",
                "description": "Jardinería en espacios urbanos y pequeños",
                "keywords": ["urbano", "macetas", "balcón", "interior", "espacios pequeños"],
                "sample_docs": [
                    "La jardinería vertical permite aprovechar espacios pequeños en balcones.",
                    "Las plantas de interior mejoran la calidad del aire en las viviendas.",
                    "Los huertos urbanos pueden producir alimentos frescos en la ciudad."
                ]
            }
        }
    
    def create_sample_documents(self, topic: str, config: Dict):
        """Crea documentos de ejemplo para una temática"""
        topic_dir = self.documents_path / topic
        topic_dir.mkdir(exist_ok=True)
        
        # Crear archivo de texto con contenido de ejemplo
        sample_file = topic_dir / f"{topic}_knowledge.txt"
        
        content = f"""# {config['display_name']}

{config['description']}

## Contenido de Ejemplo

"""
        
        for i, doc in enumerate(config['sample_docs'], 1):
            content += f"{i}. {doc}\n\n"
        
        content += f"""
## Palabras Clave
{', '.join(config['keywords'])}

## Información Adicional
Este es contenido de ejemplo para la temática {config['display_name']}.
Para un funcionamiento completo, añade documentos reales en el directorio:
{topic_dir}

Formatos soportados: .txt, .pdf, .csv, .md
"""
        
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Documento de ejemplo creado: {sample_file}")
    
    def load_documents_for_topic(self, topic: str) -> List:
        """Carga documentos para una temática específica"""
        topic_dir = self.documents_path / topic
        
        if not topic_dir.exists():
            logger.warning(f"Directorio no encontrado: {topic_dir}")
            return []
        
        documents = []
        
        # Cargar archivos de texto
        for txt_file in topic_dir.glob("*.txt"):
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Cargado: {txt_file}")
            except Exception as e:
                logger.error(f"Error cargando {txt_file}: {e}")
        
        # Cargar archivos PDF
        for pdf_file in topic_dir.glob("*.pdf"):
            try:
                loader = PyPDFLoader(str(pdf_file))
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Cargado: {pdf_file}")
            except Exception as e:
                logger.error(f"Error cargando {pdf_file}: {e}")
        
        # Cargar archivos CSV
        for csv_file in topic_dir.glob("*.csv"):
            try:
                loader = CSVLoader(str(csv_file))
                docs = loader.load()
                documents.extend(docs)
                logger.info(f"Cargado: {csv_file}")
            except Exception as e:
                logger.error(f"Error cargando {csv_file}: {e}")
        
        return documents
    
    def populate_topic_vectorstore(self, topic: str) -> bool:
        """Puebla el vectorstore de una temática específica"""
        logger.info(f"Poblando vectorstore para: {topic}")
        
        try:
            # Cargar documentos
            documents = self.load_documents_for_topic(topic)
            
            if not documents:
                logger.warning(f"No se encontraron documentos para {topic}")
                return False
            
            # Dividir documentos en chunks
            text_chunks = self.text_splitter.split_documents(documents)
            logger.info(f"Generados {len(text_chunks)} chunks para {topic}")
            
            # Crear vectorstore
            vectorstore_dir = self.vectorstore_path / topic
            vectorstore_dir.mkdir(exist_ok=True)
            
            vectorstore = Chroma.from_documents(
                documents=text_chunks,
                embedding=self.embeddings,
                persist_directory=str(vectorstore_dir),
                collection_name=f"{topic}_collection"
            )
            
            # Persistir
            vectorstore.persist()
            
            # Verificar
            test_results = vectorstore.similarity_search("test", k=1)
            if test_results:
                logger.info(f"✅ Vectorstore poblado exitosamente: {topic}")
                return True
            else:
                logger.warning(f"⚠️ Vectorstore puede estar vacío: {topic}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error poblando vectorstore {topic}: {e}")
            return False
    
    def populate_all_vectorstores(self, create_samples: bool = True):
        """Puebla todos los vectorstores"""
        logger.info("🚀 Iniciando población de vectorstores...")
        
        topics_config = self.get_topics_config()
        results = {}
        
        for topic, config in topics_config.items():
            logger.info(f"\n--- Procesando {topic} ---")
            
            # Crear documentos de ejemplo si se solicita
            if create_samples:
                self.create_sample_documents(topic, config)
            
            # Poblar vectorstore
            success = self.populate_topic_vectorstore(topic)
            results[topic] = success
        
        # Resumen
        logger.info("\n=== RESUMEN ===")
        successful = sum(results.values())
        total = len(results)
        
        for topic, success in results.items():
            status = "✅" if success else "❌"
            logger.info(f"{status} {topic}")
        
        logger.info(f"\nVectorstores poblados: {successful}/{total}")
        
        if successful == total:
            logger.info("🎉 ¡Todos los vectorstores poblados exitosamente!")
        else:
            logger.warning("⚠️ Algunos vectorstores no se pudieron poblar")
        
        return results

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Poblar vectorstores de AgentRagMCP")
    parser.add_argument("--no-samples", action="store_true", 
                       help="No crear documentos de ejemplo")
    parser.add_argument("--topic", type=str, 
                       help="Poblar solo una temática específica")
    parser.add_argument("--base-path", type=str, default="./data",
                       help="Ruta base de datos")
    
    args = parser.parse_args()
    
    populator = VectorStorePopulator(base_path=args.base_path)
    
    if args.topic:
        # Poblar solo una temática
        config = populator.get_topics_config().get(args.topic)
        if not config:
            logger.error(f"Temática no encontrada: {args.topic}")
            return
        
        if not args.no_samples:
            populator.create_sample_documents(args.topic, config)
        
        success = populator.populate_topic_vectorstore(args.topic)
        if success:
            logger.info(f"✅ {args.topic} poblado exitosamente")
        else:
            logger.error(f"❌ Error poblando {args.topic}")
    else:
        # Poblar todos
        populator.populate_all_vectorstores(create_samples=not args.no_samples)

if __name__ == "__main__":
    main()