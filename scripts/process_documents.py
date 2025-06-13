#!/usr/bin/env python3
"""
Script para procesar documentos y crear vectorstores para AgentRagMCP
"""

import os
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

# Añadir el directorio raíz al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from agentragmcp.core.config import get_settings
from agentragmcp.core.monitoring import logger

class DocumentProcessor:
    """Procesador de documentos para crear vectorstores"""
    
    def __init__(self):
        self.settings = get_settings()
        self.embeddings = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Inicializa el modelo de embeddings"""
        try:
            self.embeddings = OllamaEmbeddings(
                model=self.settings.EMBEDDING_MODEL,
                base_url=self.settings.LLM_BASE_URL
            )
            logger.info(f"Embeddings inicializados: {self.settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Error inicializando embeddings: {e}")
            raise
    
    def setup_directories(self):
        """Crea los directorios necesarios"""
        directories = [
            "data/documents/plants",
            "data/documents/pathology", 
            "data/documents/general",
            "data/vectorstores/plants",
            "data/vectorstores/pathology",
            "data/vectorstores/general"
        ]
        
        for directory in directories:
            abs_path = os.path.abspath(directory)
            os.makedirs(abs_path, exist_ok=True)
            logger.info(f"Directorio creado/verificado: {abs_path}")
    
    def create_sample_documents(self):
        """Crea documentos de ejemplo para testing"""
        logger.info("Creando documentos de ejemplo...")
        
        # Documentos de plantas
        plants_docs = {
            "cultivo_manzano.txt": """# Cultivo del Manzano (Malus domestica)

## Características Generales
El manzano es un árbol frutal de la familia Rosaceae, originario de Asia Central. Es uno de los frutales más cultivados en el mundo debido a su adaptabilidad y la calidad de sus frutos.

## Requerimientos Climáticos
- Temperatura: Requiere entre 600-1200 horas frío (temperaturas por debajo de 7°C)
- Precipitación: 600-800 mm anuales bien distribuidos
- Altitud: Se desarrolla bien entre 0-2000 metros sobre el nivel del mar
- Exposición: Prefiere lugares soleados con buena ventilación

## Suelo
- pH óptimo: 6.0-7.0 (ligeramente ácido a neutro)
- Drenaje: Excelente, no tolera encharcamientos
- Textura: Franco-arcillosos o franco-arenosos
- Profundidad: Mínimo 80 cm para un buen desarrollo radicular

## Plantación
- Época: Finales de invierno o inicio de primavera
- Marco de plantación: 4x4 metros en cultivo tradicional, 2x1 en intensivo
- Preparación del hoyo: 60x60x60 cm
- Abonado de fondo: Estiércol maduro + fósforo

## Cuidados
- Riego: Regular pero sin encharcamiento
- Poda: Formación en los primeros años, luego poda de fructificación
- Fertilización: NPK equilibrado según análisis de suelo
- Tratamientos: Preventivos contra plagas y enfermedades

## Cosecha
- Tiempo: 3-5 años desde la plantación
- Época: Agosto-octubre según variedad
- Indicadores: Color, facilidad de desprendimiento, sabor""",
            
            "cuidados_tomate.txt": """# Cuidados del Tomate (Solanum lycopersicum)

## Introducción
El tomate es una de las hortalizas más cultivadas en el mundo. Requiere cuidados específicos para obtener una producción óptima y frutos de calidad.

## Preparación del Suelo
- pH ideal: 6.0-6.8
- Materia orgánica: Incorporar compost o estiércol maduro
- Drenaje: Fundamental para evitar enfermedades radiculares
- Profundidad de laboreo: 25-30 cm

## Siembra y Trasplante
- Semillero: Febrero-marzo en zona templada
- Trasplante: Cuando las plantas tengan 15-20 cm
- Marco de plantación: 40x80 cm
- Profundidad: Enterrar hasta las primeras hojas verdaderas

## Riego
- Frecuencia: Regular y constante
- Cantidad: 2-3 litros por planta y riego
- Método: Por goteo o surcos, evitar mojar hojas
- Mulching: Recomendado para conservar humedad

## Entutorado
- Sistemas: Caña, espalderas o mallas
- Altura: Mínimo 1.5 metros
- Atado: Con rafia o clips especiales
- Momento: Desde el trasplante

## Poda
- Destallado: Eliminar brotes axilares semanalmente
- Deshojado: Quitar hojas inferiores progresivamente
- Despunte: Cortar el ápice cuando alcance la altura deseada

## Fertilización
- Base: Fósforo y potasio antes del trasplante
- Cobertera: Nitrógeno fraccionado durante el cultivo
- Microelementos: Especial atención a calcio y magnesio

## Problemas Comunes
- Podredumbre apical: Falta de calcio
- Agrietado: Riego irregular
- Plagas: Mosca blanca, trips, ácaros
- Enfermedades: Mildiu, alternaria, fusarium"""
        }
        
        # Documentos de patología
        pathology_docs = {
            "mildiu_vid.txt": """# Mildiu de la Vid (Plasmopara viticola)

## Descripción
El mildiu es una de las enfermedades más destructivas de la vid, causada por el oomiceto Plasmopara viticola. Afecta principalmente hojas, racimos y brotes jóvenes.

## Síntomas
### En Hojas
- Manchas amarillentas traslúcidas (manchas de aceite)
- En el envés: pelusilla blanca característica
- Necrosis y defoliación en casos graves

### En Racimos
- Granos pardos y arrugados
- Podredumbre seca en uvas jóvenes
- Pérdida total del racimo en ataques severos

### En Brotes
- Lesiones necróticas
- Deformaciones y acortamiento de entrenudos

## Condiciones Favorables
- Temperatura: 20-25°C óptima
- Humedad: Superior al 95%
- Agua libre: Necesaria para la germinación
- Lluvias frecuentes en primavera-verano

## Ciclo de la Enfermedad
1. **Invernación**: Oosporas en hojas caídas
2. **Infección primaria**: Abril-mayo con lluvias
3. **Infecciones secundarias**: Mayo-agosto
4. **Formación de oosporas**: Agosto-septiembre

## Tratamientos Preventivos
- Cobre: Tratamientos de invierno
- Fungicidas sistémicos: Metalaxil, fosetil-Al
- Fungicidas de contacto: Mancozeb, propineb
- Calendarios de tratamiento según riesgo

## Medidas Culturales
- Poda adecuada para ventilación
- Eliminación de restos vegetales
- Drenaje correcto del suelo
- Variedades resistentes

## Umbrales de Tratamiento
- Modelo Mills: Suma de grados día después de lluvia
- Regla de los 3-10: 3 días consecutivos con T>10°C tras 10mm lluvia
- Monitoreo de esporas en aire""",
            
            "oidio_cucurbitaceas.txt": """# Oídio en Cucurbitáceas (Podosphaera xanthii)

## Agente Causal
Podosphaera xanthii (anteriormente Sphaerotheca fuliginea) es el principal causante del oídio en cucurbitáceas como melón, sandía, calabacín y pepino.

## Síntomas Característicos
### En Hojas
- Manchas blancas pulverulentas circulares
- Crecimiento del micelio en haz y envés
- Amarilleamiento y necrosis progresiva
- Defoliación prematura en casos severos

### En Tallos y Pecíolos
- Lesiones blanquecinas alargadas
- Debilitamiento estructural
- Posible rotura por viento

### En Frutos
- Manchas superficiales blancas
- Alteración de la calidad
- Maduración irregular

## Condiciones Predisponentes
- Temperatura: 20-30°C (óptimo 26°C)
- Humedad relativa: 50-90%
- Ambiente seco favorece conidiogénesis
- Cultivo protegido propicia desarrollo

## Ciclo Biológico
1. **Supervivencia**: Micelio en plantas hospederas
2. **Diseminación**: Conidios por viento
3. **Infección**: Penetración directa por epidermis
4. **Colonización**: Desarrollo superficial del micelio
5. **Reproducción**: Formación de conidios cada 3-7 días

## Estrategias de Control
### Control Químico
- Azufre: Fungicida tradicional eficaz
- IBE (Inhibidores de la biosíntesis del ergosterol)
- QoI (Inhibidores del complejo III)
- Rotación de materias activas

### Control Biológico
- Bacillus subtilis
- Ampelomyces quisqualis
- Trichoderma harzianum
- Aplicaciones preventivas

### Medidas Culturales
- Eliminación de restos infectados
- Ventilación adecuada en invernadero
- Evitar exceso de nitrógeno
- Variedades resistentes

## Resistencias
- Múltiples razas del patógeno
- Genes de resistencia: Pm-1, Pm-3, Pm-5
- Necesidad de variedades multigénicas
- Monitoreo constante de nuevas razas"""
        }
        
        # Documentos generales
        general_docs = {
            "fotosintesis.txt": """# La Fotosíntesis: Proceso Fundamental de la Vida

## Definición
La fotosíntesis es el proceso biológico mediante el cual las plantas, algas y algunas bacterias convierten la energía solar, el dióxido de carbono y el agua en glucosa y oxígeno, utilizando la clorofila como pigmento principal.

## Ecuación General
6CO₂ + 6H₂O + energía solar → C₆H₁₂O₆ + 6O₂

## Fases de la Fotosíntesis

### Fase Luminosa (Reacciones de Hill)
**Localización**: Tilacoides de los cloroplastos
**Procesos**:
- Captación de luz por fotosistemas I y II
- Fotólisis del agua (H₂O → 2H⁺ + ½O₂ + 2e⁻)
- Transporte de electrones
- Síntesis de ATP y NADPH
- Liberación de oxígeno

### Fase Oscura (Ciclo de Calvin-Benson)
**Localización**: Estroma de los cloroplastos
**Procesos**:
- Fijación de CO₂ por la RuBisCO
- Formación de compuestos de 3 carbonos
- Regeneración de la ribulosa 1,5-bifosfato
- Síntesis de glucosa

## Factores que Afectan la Fotosíntesis

### Factores Internos
- Concentración de clorofila
- Edad de las hojas
- Estado nutricional de la planta
- Estructura del aparato fotosintético

### Factores Externos
- **Intensidad lumínica**: Factor limitante principal
- **Temperatura**: Óptimo entre 20-30°C
- **Concentración de CO₂**: Actual ~400 ppm
- **Disponibilidad de agua**: Necesaria para reacciones

## Importancia Biológica
- Producción de oxígeno atmosférico
- Base de todas las cadenas alimentarias
- Almacenamiento de energía en compuestos orgánicos
- Regulación del CO₂ atmosférico
- Formación de biomasa vegetal

## Tipos de Fotosíntesis

### Plantas C3
- 85% de las plantas
- Fijación directa de CO₂
- Eficiente en climas templados
- Ejemplos: trigo, arroz, soja

### Plantas C4
- Adaptadas a climas cálidos
- Concentración de CO₂
- Mayor eficiencia en temperatura alta
- Ejemplos: maíz, caña de azúcar

### Plantas CAM
- Metabolismo Ácido de las Crasuláceas
- Apertura estomática nocturna
- Adaptación a ambientes áridos
- Ejemplos: cactus, piña, agave""",
            
            "clasificacion_plantas.txt": """# Clasificación Botánica de las Plantas

## Sistema de Clasificación Taxonómica

### Jerarquía Taxonómica
1. **Reino**: Plantae
2. **División/Filo**: Ejemplo - Magnoliophyta
3. **Clase**: Ejemplo - Magnoliopsida
4. **Orden**: Ejemplo - Rosales
5. **Familia**: Ejemplo - Rosaceae
6. **Género**: Ejemplo - Malus
7. **Especie**: Ejemplo - domestica

### Nomenclatura Binomial
Creada por Carl Linnaeus, utiliza dos nombres latinos:
- **Género** (mayúscula inicial)
- **Epíteto específico** (minúscula)
- Ejemplo: *Malus domestica* (manzano)

## Grandes Grupos de Plantas

### Briófitas (Musgos y Hepáticas)
- Sin tejidos vasculares verdaderos
- Pequeño tamaño
- Dependientes del agua para reproducción
- Gametofito dominante

### Pteridófitas (Helechos)
- Primeras plantas vasculares
- Sin semillas
- Reproducción por esporas
- Esporofito dominante

### Gimnospermas
- Plantas con semillas desnudas
- Hojas en forma de aguja o escama
- Adaptadas a climas fríos
- Ejemplos: pinos, abetos, cipreses

### Angiospermas
- Plantas con flores y frutos
- Semillas protegidas
- Mayor diversidad vegetal
- Divididas en monocotiledóneas y dicotiledóneas

## Clasificación por Características Morfológicas

### Según el Tallo
- **Árboles**: Tallo leñoso >5m
- **Arbustos**: Tallo leñoso <5m, ramificado desde la base
- **Hierbas**: Tallo no leñoso

### Según las Hojas
- **Perennes**: Mantienen hojas todo el año
- **Caducas**: Pierden hojas en época desfavorable
- **Forma**: Linear, ovalada, palmeada, etc.

### Según el Hábitat
- **Terrestres**: Crecen en tierra firme
- **Acuáticas**: Viven en medios acuáticos
- **Epífitas**: Crecen sobre otras plantas
- **Parásitas**: Dependen de otros organismos

## Familias Importantes

### Rosaceae (Rosáceas)
- Flores con 5 pétalos
- Frutos variados (drupa, pomo, aquenio)
- Ejemplos: rosa, manzano, almendro, fresa

### Fabaceae (Leguminosas)
- Fruto en legumbre
- Fijación de nitrógeno
- Ejemplos: judía, guisante, alfalfa

### Solanaceae (Solanáceas)
- Flores pentámeras
- Fruto en baya o cápsula
- Ejemplos: tomate, patata, pimiento

### Asteraceae (Compuestas)
- Inflorescencia en capítulo
- Familia más numerosa
- Ejemplos: margarita, girasol, lechuga

## Criterios de Clasificación Moderna

### Morfológicos
- Estructura de flores, frutos, hojas
- Anatomía interna
- Desarrollo embriológico

### Moleculares
- Secuenciación de ADN
- Análisis filogenético
- Proteínas y enzimas

### Ecológicos
- Adaptaciones al medio
- Relaciones evolutivas
- Distribución geográfica"""
        }
        
        # Crear archivos con codificación UTF-8
        base_path = Path("data/documents")
        
        for category, docs in [("plants", plants_docs), ("pathology", pathology_docs), ("general", general_docs)]:
            category_path = base_path / category
            for filename, content in docs.items():
                file_path = category_path / filename
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Creado documento de ejemplo: {file_path}")
                except Exception as e:
                    logger.error(f"Error creando {file_path}: {e}")
    
    def load_documents_from_directory(self, directory: str, topic: str) -> List:
        """Carga documentos desde un directorio con manejo robusto de errores"""
        logger.info(f"Cargando documentos desde: {directory}")
        
        if not os.path.exists(directory):
            logger.warning(f"Directorio no existe: {directory}")
            return []
        
        documents = []
        
        # Buscar archivos manualmente para mejor control de errores
        for file_path in Path(directory).glob("*.txt"):
            try:
                # Intentar diferentes codificaciones
                content = None
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                
                if content is None:
                    logger.error(f"No se pudo decodificar {file_path}")
                    continue
                
                # Crear documento manualmente
                from langchain_core.documents import Document
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(file_path),
                        "topic": topic,
                        "filename": file_path.name
                    }
                )
                documents.append(doc)
                logger.info(f"Cargado: {file_path.name} (1 docs)")
                
            except Exception as e:
                logger.error(f"Error cargando {file_path}: {e}")
                continue
        
        logger.info(f"Total documentos cargados para {topic}: {len(documents)}")
        return documents
    
    def process_documents(self, documents: List, chunk_size: int = 1000, chunk_overlap: int = 200) -> List:
        """Procesa y divide documentos en chunks"""
        if not documents:
            return []
        
        logger.info(f"Procesando {len(documents)} documentos...")
        
        # Configurar text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        # Dividir documentos
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Documentos divididos en {len(chunks)} chunks")
        
        return chunks
    
    def create_vectorstore(self, documents: List, topic: str) -> bool:
        """Crea el vectorstore para una temática"""
        if not documents:
            logger.warning(f"No hay documentos para crear vectorstore de {topic}")
            return False
        
        logger.info(f"Creando vectorstore para {topic} con {len(documents)} documentos...")
        
        try:
            vectorstore_path = self.settings.get_vectorstore_path(topic)
            
            # Crear vectorstore
            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=vectorstore_path
            )
            
            logger.info(f"Vectorstore creado exitosamente: {vectorstore_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creando vectorstore para {topic}: {e}")
            return False
    
    def validate_vectorstore(self, topic: str) -> bool:
        """Valida que el vectorstore se creó correctamente"""
        try:
            vectorstore_path = self.settings.get_vectorstore_path(topic)
            
            # Cargar vectorstore
            vectorstore = Chroma(
                persist_directory=vectorstore_path,
                embedding_function=self.embeddings
            )
            
            # Hacer una consulta de prueba
            results = vectorstore.similarity_search("test", k=1)
            logger.info(f"Vectorstore {topic} validado: {len(results)} resultados")
            return True
            
        except Exception as e:
            logger.error(f"Error validando vectorstore {topic}: {e}")
            return False
    
    def process_topic(self, topic: str) -> bool:
        """Procesa una temática completa"""
        logger.info("=" * 50)
        logger.info(f"PROCESANDO TEMÁTICA: {topic.upper()}")
        logger.info("=" * 50)
        
        # Directorio de documentos
        docs_directory = os.path.join("data", "documents", topic)
        
        # Verificar si hay archivos
        if not os.path.exists(docs_directory):
            logger.warning(f"Directorio no existe: {docs_directory}")
            return False
        
        files = list(Path(docs_directory).glob("*.txt"))
        if not files:
            logger.warning(f"No se encontraron archivos .txt en {docs_directory}")
            return False
        
        logger.info(f"Encontrados {len(files)} archivos para procesar")
        
        # Cargar documentos
        documents = self.load_documents_from_directory(docs_directory, topic)
        
        if not documents:
            logger.warning(f"No se pudieron cargar documentos para {topic}")
            return False
        
        # Procesar documentos
        chunks = self.process_documents(documents)
        
        # Crear vectorstore
        success = self.create_vectorstore(chunks, topic)
        
        if success:
            # Validar vectorstore
            if self.validate_vectorstore(topic):
                logger.info(f"✅ Temática {topic} procesada exitosamente")
                return True
        
        logger.error(f"❌ Error procesando temática {topic}")
        return False
    
    def get_vectorstore_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas de los vectorstores"""
        stats = {}
        
        for topic in self.settings.RAG_TOPICS:
            try:
                vectorstore_path = self.settings.get_vectorstore_path(topic)
                if os.path.exists(vectorstore_path):
                    vectorstore = Chroma(
                        persist_directory=vectorstore_path,
                        embedding_function=self.embeddings
                    )
                    # Contar documentos con una búsqueda amplia
                    results = vectorstore.similarity_search("", k=1000)
                    stats[topic] = len(results)
                else:
                    stats[topic] = 0
            except Exception as e:
                logger.error(f"Error obteniendo stats de {topic}: {e}")
                stats[topic] = 0
        
        return stats

def main():
    parser = argparse.ArgumentParser(description="Procesador de documentos para AgentRagMCP")
    parser.add_argument("--create-samples", action="store_true", 
                       help="Crear documentos de ejemplo")
    parser.add_argument("--topics", nargs="+", 
                       help="Temáticas específicas a procesar")
    parser.add_argument("--chunk-size", type=int, default=1000,
                       help="Tamaño de los chunks")
    parser.add_argument("--chunk-overlap", type=int, default=200,
                       help="Solapamiento entre chunks")
    
    args = parser.parse_args()
    
    # Inicializar procesador
    processor = DocumentProcessor()
    
    # Configurar directorios
    processor.setup_directories()
    
    # Crear documentos de ejemplo si se solicita
    if args.create_samples:
        processor.create_sample_documents()
        print("✅ Documentos de ejemplo creados")
    
    # Determinar temáticas a procesar
    topics_to_process = args.topics if args.topics else processor.settings.RAG_TOPICS
    
    # Procesar cada temática
    successful_topics = 0
    total_topics = len(topics_to_process)
    
    for topic in topics_to_process:
        if processor.process_topic(topic):
            successful_topics += 1
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PROCESAMIENTO")
    print("=" * 50)
    
    if successful_topics == total_topics:
        print(f"✅ Todas las temáticas procesadas exitosamente: {successful_topics}/{total_topics}")
    else:
        print(f"⚠️  Algunas temáticas no se pudieron crear")
        print(f"✅ Temáticas procesadas exitosamente: {successful_topics}/{total_topics}")
    
    # Estadísticas finales
    stats = processor.get_vectorstore_stats()
    print(f"\n📊 ESTADÍSTICAS FINALES:")
    for topic, count in stats.items():
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {topic}: {count} chunks")

if __name__ == "__main__":
    main()