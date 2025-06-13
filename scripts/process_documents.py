#!/usr/bin/env python3
"""
Script para procesar documentos y crear vectorstores para AgentRagMCP
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
import shutil

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Imports de LangChain
from langchain_community.document_loaders import (
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    Docx2txtLoader,
    UnstructuredHTMLLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain.schema import Document

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import setup_logging

class DocumentProcessor:
    """Procesador de documentos para crear vectorstores"""
    
    def __init__(self, base_path: str = None):
        self.settings = get_settings()
        self.logger = setup_logging()
        
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path.cwd()
        
        self.documents_path = self.base_path / "data" / "documents"
        self.vectorstores_path = Path(self.settings.VECTORSTORE_BASE_PATH)
        
        # Configuración de embeddings
        self.embeddings = OllamaEmbeddings(
            model=self.settings.EMBEDDING_MODEL,
            base_url=self.settings.LLM_BASE_URL
        )
        
        # Configuración de text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
    def setup_directories(self):
        """Crea la estructura de directorios necesaria"""
        directories = [
            self.documents_path / "plants",
            self.documents_path / "pathology", 
            self.documents_path / "general",
            self.vectorstores_path / "plants",
            self.vectorstores_path / "pathology",
            self.vectorstores_path / "general"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Directorio creado/verificado: {directory}")
    
    def get_loader_for_file(self, file_path: Path):
        """Obtiene el loader apropiado según la extensión del archivo"""
        extension = file_path.suffix.lower()
        
        loaders = {
            '.pdf': PyPDFLoader,
            '.txt': TextLoader,
            '.md': UnstructuredMarkdownLoader,
            '.docx': Docx2txtLoader,
            '.html': UnstructuredHTMLLoader,
            '.htm': UnstructuredHTMLLoader
        }
        
        if extension in loaders:
            return loaders[extension](str(file_path))
        else:
            self.logger.warning(f"Extensión no soportada: {extension}")
            return None
    
    def load_documents_from_directory(self, directory: Path, topic: str) -> List[Document]:
        """Carga documentos desde un directorio específico"""
        self.logger.info(f"Cargando documentos desde: {directory}")
        
        documents = []
        supported_extensions = ['.pdf', '.txt', '.md', '.docx', '.html', '.htm']
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    loader = self.get_loader_for_file(file_path)
                    if loader:
                        file_docs = loader.load()
                        
                        # Añadir metadatos
                        for doc in file_docs:
                            doc.metadata.update({
                                'source': str(file_path.relative_to(directory)),
                                'topic': topic,
                                'file_type': file_path.suffix,
                                'full_path': str(file_path)
                            })
                        
                        documents.extend(file_docs)
                        self.logger.info(f"Cargado: {file_path.name} ({len(file_docs)} docs)")
                        
                except Exception as e:
                    self.logger.error(f"Error cargando {file_path}: {e}")
        
        self.logger.info(f"Total documentos cargados para {topic}: {len(documents)}")
        return documents
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Procesa y divide documentos en chunks"""
        self.logger.info(f"Procesando {len(documents)} documentos...")
        
        # Filtrar documentos vacíos
        valid_docs = [doc for doc in documents if doc.page_content.strip()]
        
        if len(valid_docs) != len(documents):
            self.logger.warning(f"Filtrados {len(documents) - len(valid_docs)} documentos vacíos")
        
        # Dividir en chunks
        chunks = self.text_splitter.split_documents(valid_docs)
        
        self.logger.info(f"Documentos divididos en {len(chunks)} chunks")
        return chunks
    
    def create_vectorstore(self, documents: List[Document], topic: str, force_recreate: bool = False) -> Chroma:
        """Crea o actualiza un vectorstore para una temática específica"""
        vectorstore_path = self.vectorstores_path / topic
        
        # Verificar si ya existe
        if vectorstore_path.exists() and force_recreate:
            self.logger.info(f"Eliminando vectorstore existente: {vectorstore_path}")
            shutil.rmtree(vectorstore_path)
        
        try:
            if documents:
                self.logger.info(f"Creando vectorstore para {topic} con {len(documents)} documentos...")
                
                vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=str(vectorstore_path),
                    collection_name=f"{topic}_collection"
                )
                
                self.logger.info(f"Vectorstore creado exitosamente: {vectorstore_path}")
                return vectorstore
            else:
                self.logger.warning(f"No hay documentos para crear vectorstore de {topic}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creando vectorstore para {topic}: {e}")
            raise
    
    def validate_vectorstore(self, topic: str) -> bool:
        """Valida que un vectorstore funcione correctamente"""
        try:
            vectorstore_path = self.vectorstores_path / topic
            
            if not vectorstore_path.exists():
                self.logger.error(f"Vectorstore no existe: {vectorstore_path}")
                return False
            
            # Cargar y probar el vectorstore
            vectorstore = Chroma(
                persist_directory=str(vectorstore_path),
                embedding_function=self.embeddings,
                collection_name=f"{topic}_collection"
            )
            
            # Hacer una consulta de prueba
            results = vectorstore.similarity_search("test query", k=1)
            
            self.logger.info(f"Vectorstore {topic} validado: {len(results)} resultados")
            return True
            
        except Exception as e:
            self.logger.error(f"Error validando vectorstore {topic}: {e}")
            return False
    
    def process_topic(self, topic: str, force_recreate: bool = False) -> bool:
        """Procesa todos los documentos de una temática específica"""
        self.logger.info(f"{'='*50}")
        self.logger.info(f"PROCESANDO TEMÁTICA: {topic.upper()}")
        self.logger.info(f"{'='*50}")
        
        topic_path = self.documents_path / topic
        
        if not topic_path.exists():
            self.logger.warning(f"Directorio no existe: {topic_path}")
            return False
        
        # Verificar si hay documentos
        files = list(topic_path.rglob("*"))
        document_files = [f for f in files if f.is_file() and f.suffix.lower() in ['.pdf', '.txt', '.md', '.docx', '.html']]
        
        if not document_files:
            self.logger.warning(f"No se encontraron documentos en: {topic_path}")
            return False
        
        self.logger.info(f"Encontrados {len(document_files)} archivos para procesar")
        
        try:
            # 1. Cargar documentos
            documents = self.load_documents_from_directory(topic_path, topic)
            
            if not documents:
                self.logger.warning(f"No se pudieron cargar documentos para {topic}")
                return False
            
            # 2. Procesar documentos
            chunks = self.process_documents(documents)
            
            if not chunks:
                self.logger.warning(f"No se generaron chunks para {topic}")
                return False
            
            # 3. Crear vectorstore
            vectorstore = self.create_vectorstore(chunks, topic, force_recreate)
            
            if not vectorstore:
                return False
            
            # 4. Validar
            is_valid = self.validate_vectorstore(topic)
            
            if is_valid:
                self.logger.info(f"✅ Temática {topic} procesada exitosamente")
            else:
                self.logger.error(f"❌ Error validando temática {topic}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Error procesando temática {topic}: {e}")
            return False
    
    def create_sample_documents(self):
        """Crea documentos de ejemplo para testing"""
        self.logger.info("Creando documentos de ejemplo...")
        
        sample_docs = {
            "plants": {
                "cultivo_manzano.txt": """
El manzano (Malus domestica) es uno de los frutales más cultivados del mundo.

CARACTERÍSTICAS:
- Árbol de porte medio que puede alcanzar 8-10 metros de altura
- Flores blancas o rosadas que aparecen en primavera
- Frutos comestibles de diversas variedades

CUIDADOS:
- Riego regular pero sin encharcamiento
- Poda de formación en invierno
- Fertilización en primavera con compost

CULTIVO:
- Plantación: otoño o inicio de primavera
- Exposición: sol o semisombra
- Suelo: bien drenado, pH 6.0-7.0

VARIEDADES RECOMENDADAS:
- Golden Delicious: resistente y productiva
- Granny Smith: ideal para climas templados
- Fuji: excelente sabor y conservación
                """,
                
                "cuidados_tomate.txt": """
El tomate (Solanum lycopersicum) es una hortaliza fundamental en la huerta.

SIEMBRA:
- Época: final del invierno en semillero protegido
- Trasplante: cuando no haya riesgo de heladas
- Marco de plantación: 40x60 cm

CUIDADOS:
- Riego: constante y uniforme, evitar mojar las hojas
- Tutorado: indispensable para variedades indeterminadas
- Poda: eliminar chupones y hojas inferiores

NUTRICIÓN:
- Compost bien maduro antes de la plantación
- Fertilización rica en potasio durante la fructificación
- Evitar exceso de nitrógeno

COSECHA:
- Los frutos se recolectan cuando empiezan a cambiar de color
- Conservación: lugar fresco y ventilado
                """
            },
            
            "pathology": {
                "mildiu_vid.txt": """
El mildiu de la vid (Plasmopara viticola) es una de las enfermedades más graves de la viticultura.

SÍNTOMAS:
- Manchas amarillentas en el haz de las hojas
- Pelusilla blanquecina en el envés
- Necrosis y defoliación en casos severos
- Afectación de racimos jóvenes

CONDICIONES FAVORABLES:
- Humedad relativa alta (>95%)
- Temperaturas entre 20-25°C
- Precipitaciones frecuentes
- Rocío matutino prolongado

CONTROL PREVENTIVO:
- Poda que favorezca la ventilación
- Eliminación de restos vegetales
- Tratamientos preventivos con cobre

CONTROL QUÍMICO:
- Fungicidas sistémicos (fosfonatos)
- Fungicidas de contacto (cobre, mancozeb)
- Alternar materias activas para evitar resistencias

MOMENTO DE APLICACIÓN:
- Preventivo antes de lluvias
- Estadios críticos: brotación, floración, envero
                """,
                
                "oidio_cucurbitaceas.txt": """
El oídio en cucurbitáceas es causado principalmente por Sphaerotheca fuliginea.

IDENTIFICACIÓN:
- Manchas blancas pulverulentas en hojas
- Afecta haz y envés de las hojas
- Deformación y amarilleo foliar
- Puede afectar frutos jóvenes

FACTORES PREDISPONENTES:
- Humedad ambiental alta
- Temperaturas moderadas (20-25°C)
- Falta de ventilación
- Exceso de nitrógeno

MEDIDAS CULTURALES:
- Marcos de plantación amplios
- Eliminación de malas hierbas
- Riego por goteo (evitar mojar follaje)
- Fertilización equilibrada

CONTROL BIOLÓGICO:
- Bacillus subtilis
- Trichoderma harzianum
- Aceites esenciales (tomillo, canela)

CONTROL QUÍMICO:
- Azufre en polvo o mojable
- Fungicidas sistémicos (triazoles)
- Bicarbonato potásico
                """
            },
            
            "general": {
                "fotosintesis.txt": """
La fotosíntesis es el proceso fundamental por el cual las plantas convierten la energía lumínica en energía química.

DEFINICIÓN:
La fotosíntesis es el proceso mediante el cual las plantas utilizan la luz solar, el dióxido de carbono y el agua para producir glucosa y oxígeno.

ECUACIÓN GENERAL:
6CO₂ + 6H₂O + energía lumínica → C₆H₁₂O₆ + 6O₂

FASES DEL PROCESO:

1. FASE LUMINOSA (Tilacoides):
- Captura de luz por las clorofilas
- Fotólisis del agua
- Síntesis de ATP y NADPH
- Liberación de oxígeno

2. FASE OSCURA (Estroma):
- Ciclo de Calvin-Benson
- Fijación del CO₂
- Síntesis de glucosa
- Regeneración de RuBP

IMPORTANCIA:
- Producción de oxígeno atmosférico
- Base de las cadenas alimentarias
- Fijación de carbono atmosférico
- Fuente de energía para la biosfera

FACTORES LIMITANTES:
- Intensidad lumínica
- Concentración de CO₂
- Temperatura
- Disponibilidad de agua
                """,
                
                "clasificacion_plantas.txt": """
La clasificación de las plantas se basa en características morfológicas, anatómicas y evolutivas.

GRANDES GRUPOS:

1. BRIÓFITOS (Musgos y hepáticas):
- Sin tejidos vasculares
- Dependientes del agua para reproducción
- Gametófito dominante

2. PTERIDÓFITOS (Helechos):
- Con tejidos vasculares
- Sin semillas
- Esporófito dominante
- Reproducción por esporas

3. GIMNOSPERMAS:
- Semillas desnudas
- Hojas aciculares o escamosas
- Flores unisexuales
- Ejemplos: pinos, abetos, cipreses

4. ANGIOSPERMAS:
- Semillas protegidas en frutos
- Flores con pétalos y sépalos
- Mayor diversidad vegetal

SUBDIVISIÓN DE ANGIOSPERMAS:

MONOCOTILEDÓNEAS:
- Un cotiledón en la semilla
- Hojas con nerviación paralela
- Flores trímeras
- Ejemplos: gramíneas, orquídeas

DICOTILEDÓNEAS:
- Dos cotiledones en la semilla
- Hojas con nerviación reticulada
- Flores tetrámeras o pentámeras
- Ejemplos: rosales, leguminosas
                """
            }
        }
        
        for topic, files in sample_docs.items():
            topic_dir = self.documents_path / topic
            topic_dir.mkdir(parents=True, exist_ok=True)
            
            for filename, content in files.items():
                file_path = topic_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content.strip())
                
                self.logger.info(f"Creado documento de ejemplo: {file_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de los vectorstores"""
        stats = {}
        
        for topic in self.settings.RAG_TOPICS:
            topic_stats = {
                "documents_path": str(self.documents_path / topic),
                "vectorstore_path": str(self.vectorstores_path / topic),
                "has_documents": False,
                "has_vectorstore": False,
                "document_count": 0,
                "vectorstore_size": 0
            }
            
            # Estadísticas de documentos
            topic_path = self.documents_path / topic
            if topic_path.exists():
                files = list(topic_path.rglob("*"))
                document_files = [f for f in files if f.is_file()]
                topic_stats["has_documents"] = len(document_files) > 0
                topic_stats["document_count"] = len(document_files)
            
            # Estadísticas de vectorstore
            vectorstore_path = self.vectorstores_path / topic
            if vectorstore_path.exists():
                topic_stats["has_vectorstore"] = True
                try:
                    vectorstore = Chroma(
                        persist_directory=str(vectorstore_path),
                        embedding_function=self.embeddings,
                        collection_name=f"{topic}_collection"
                    )
                    # Obtener número de documentos en el vectorstore
                    collection = vectorstore._collection
                    topic_stats["vectorstore_size"] = collection.count()
                except Exception as e:
                    self.logger.warning(f"Error obteniendo estadísticas de {topic}: {e}")
            
            stats[topic] = topic_stats
        
        return stats

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Procesador de documentos para AgentRagMCP")
    parser.add_argument("--topic", choices=["plants", "pathology", "general", "all"],
                       default="all", help="Temática a procesar")
    parser.add_argument("--force", action="store_true",
                       help="Forzar recreación de vectorstores existentes")
    parser.add_argument("--create-samples", action="store_true",
                       help="Crear documentos de ejemplo")
    parser.add_argument("--stats", action="store_true",
                       help="Mostrar estadísticas solamente")
    parser.add_argument("--base-path", help="Directorio base del proyecto")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Modo verbose")
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Crear procesador
    processor = DocumentProcessor(args.base_path)
    
    try:
        # Crear directorios
        processor.setup_directories()
        
        # Crear documentos de ejemplo si se solicita
        if args.create_samples:
            processor.create_sample_documents()
            print("✅ Documentos de ejemplo creados")
        
        # Mostrar estadísticas
        if args.stats:
            stats = processor.get_statistics()
            print("\n📊 ESTADÍSTICAS DE DATOS:")
            print("=" * 50)
            
            for topic, data in stats.items():
                print(f"\n🏷️  {topic.upper()}:")
                print(f"   📁 Documentos: {data['document_count']} archivos")
                print(f"   🗃️  Vectorstore: {'✅' if data['has_vectorstore'] else '❌'} ({data['vectorstore_size']} chunks)")
                print(f"   📍 Ruta docs: {data['documents_path']}")
                print(f"   📍 Ruta vector: {data['vectorstore_path']}")
            
            return
        
        # Procesar temáticas
        if args.topic == "all":
            topics = processor.settings.RAG_TOPICS
        else:
            topics = [args.topic]
        
        success_count = 0
        for topic in topics:
            if processor.process_topic(topic, args.force):
                success_count += 1
        
        # Resumen final
        print(f"\n{'='*50}")
        print("📋 RESUMEN DE PROCESAMIENTO")
        print(f"{'='*50}")
        print(f"✅ Temáticas procesadas exitosamente: {success_count}/{len(topics)}")
        
        if success_count == len(topics):
            print("🎉 ¡Todos los vectorstores creados correctamente!")
        elif success_count > 0:
            print("⚠️  Algunos vectorstores no se pudieron crear")
        else:
            print("❌ No se pudo crear ningún vectorstore")
        
        # Mostrar estadísticas finales
        stats = processor.get_statistics()
        print(f"\n📊 ESTADÍSTICAS FINALES:")
        for topic, data in stats.items():
            status = "✅" if data['has_vectorstore'] else "❌"
            print(f"   {status} {topic}: {data['vectorstore_size']} chunks")
        
    except KeyboardInterrupt:
        print("\n⏹️  Procesamiento interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()