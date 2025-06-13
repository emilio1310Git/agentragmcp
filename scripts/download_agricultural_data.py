#!/usr/bin/env python3
"""
Script para descargar datos agrícolas y botánicos de fuentes públicas
"""
import os
import sys
import requests
import argparse
from pathlib import Path
from typing import List, Dict, Any
import time
from urllib.parse import urljoin, urlparse
import logging

# Añadir el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from agentragmcp.core.monitoring import setup_logging

class AgriculturalDataDownloader:
    """Descargador de datos agrícolas desde fuentes públicas"""
    
    def __init__(self, base_path: str = None):
        self.logger = setup_logging()
        
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path.cwd()
        
        self.documents_path = self.base_path / "data" / "documents"
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; AgentRagMCP-DataCollector/1.0)'
        }
    
    def setup_directories(self):
        """Crea directorios necesarios"""
        for topic in ["plants", "pathology", "general"]:
            topic_path = self.documents_path / topic
            topic_path.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url: str, filepath: Path, max_size_mb: int = 50) -> bool:
        """Descarga un archivo desde una URL"""
        try:
            self.logger.info(f"Descargando: {url}")
            
            response = requests.get(url, headers=self.headers, stream=True, timeout=30)
            response.raise_for_status()
            
            # Verificar tamaño
            content_length = response.headers.get('content-length')
            if content_length:
                size_mb = int(content_length) / (1024 * 1024)
                if size_mb > max_size_mb:
                    self.logger.warning(f"Archivo demasiado grande ({size_mb:.1f}MB): {url}")
                    return False
            
            # Descargar archivo
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"Descargado: {filepath}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error descargando {url}: {e}")
            return False
    
    def download_fao_resources(self) -> List[str]:
        """Descarga recursos de la FAO (Organización para la Alimentación y la Agricultura)"""
        self.logger.info("Descargando recursos de la FAO...")
        
        fao_resources = [
            {
                "url": "https://www.fao.org/3/i3325e/i3325e.pdf",
                "name": "fao_good_agricultural_practices.pdf",
                "topic": "plants",
                "description": "Buenas prácticas agrícolas"
            },
            {
                "url": "https://www.fao.org/3/i7749e/i7749e.pdf", 
                "name": "fao_integrated_pest_management.pdf",
                "topic": "pathology",
                "description": "Manejo integrado de plagas"
            },
            {
                "url": "https://www.fao.org/3/ca6640en/ca6640en.pdf",
                "name": "fao_plant_health_guidelines.pdf",
                "topic": "pathology", 
                "description": "Directrices de sanidad vegetal"
            }
        ]
        
        downloaded = []
        for resource in fao_resources:
            filepath = self.documents_path / resource["topic"] / resource["name"]
            
            if self.download_file(resource["url"], filepath):
                downloaded.append(resource["name"])
                # Pequeña pausa entre descargas
                time.sleep(2)
        
        return downloaded
    
    def download_university_resources(self) -> List[str]:
        """Descarga recursos de universidades (ejemplos públicos)"""
        self.logger.info("Descargando recursos universitarios...")
        
        # Ejemplos de recursos universitarios públicos
        university_resources = [
            {
                "url": "https://extension.umn.edu/sites/extension.umn.edu/files/garden-insects-and-disease.pdf",
                "name": "university_garden_diseases.pdf", 
                "topic": "pathology",
                "description": "Enfermedades de jardín"
            },
            {
                "url": "https://extension.oregonstate.edu/sites/default/files/documents/ec1304.pdf",
                "name": "oregon_plant_care.pdf",
                "topic": "plants",
                "description": "Cuidado de plantas"
            }
        ]
        
        downloaded = []
        for resource in university_resources:
            filepath = self.documents_path / resource["topic"] / resource["name"]
            
            if self.download_file(resource["url"], filepath):
                downloaded.append(resource["name"])
                time.sleep(2)
        
        return downloaded
    
    def create_botanical_texts(self) -> List[str]:
        """Crea textos botánicos básicos desde fuentes públicas"""
        self.logger.info("Creando textos botánicos básicos...")
        
        botanical_texts = {
            "photosynthesis_basics.txt": """
FOTOSÍNTESIS: PROCESO FUNDAMENTAL DE LAS PLANTAS

La fotosíntesis es el proceso biológico más importante de la Tierra, mediante el cual las plantas convierten la energía lumínica en energía química.

DEFINICIÓN:
La fotosíntesis es el proceso por el cual las plantas utilizan la luz solar, dióxido de carbono (CO₂) y agua (H₂O) para producir glucosa (C₆H₁₂O₆) y oxígeno (O₂).

ECUACIÓN GENERAL:
6CO₂ + 6H₂O + energía lumínica → C₆H₁₂O₆ + 6O₂

UBICACIÓN:
- Principalmente en las hojas
- En estructuras llamadas cloroplastos
- Contienen clorofila (pigmento verde)

FASES DEL PROCESO:

1. REACCIONES LUMINOSAS (Fase Clara):
- Ocurren en los tilacoides
- Captura de energía lumínica
- Fotólisis del agua (H₂O → H⁺ + e⁻ + ½O₂)
- Síntesis de ATP y NADPH
- Liberación de oxígeno

2. CICLO DE CALVIN (Fase Oscura):
- Ocurre en el estroma del cloroplasto
- No requiere luz directa
- Fijación del CO₂ atmosférico
- Síntesis de glucosa
- Utiliza ATP y NADPH de la fase luminosa

FACTORES QUE AFECTAN LA FOTOSÍNTESIS:
- Intensidad lumínica
- Concentración de CO₂
- Temperatura
- Disponibilidad de agua
- Concentración de clorofila

IMPORTANCIA BIOLÓGICA:
- Producción del oxígeno atmosférico
- Base de todas las cadenas alimentarias
- Regulación del CO₂ atmosférico
- Fuente primaria de energía en los ecosistemas

TIPOS DE FOTOSÍNTESIS:
- C3: La mayoría de plantas (trigo, arroz, soja)
- C4: Plantas adaptadas a climas cálidos (maíz, caña de azúcar)
- CAM: Plantas suculentas (cactus, piña)

La fotosíntesis es esencial para la vida en la Tierra, ya que proporciona el oxígeno que respiramos y la energía que sustenta prácticamente todos los ecosistemas.
            """,
            
            "plant_classification.txt": """
CLASIFICACIÓN DE LAS PLANTAS

La taxonomía vegetal organiza las plantas según sus características evolutivas y morfológicas.

REINO PLANTAE:
Las plantas son organismos eucariotas, autótrofos y principalmente terrestres.

PRINCIPALES DIVISIONES:

1. BRYOPHYTA (Briófitos):
- Musgos, hepáticas y antoceros
- Sin tejidos vasculares verdaderos
- Dependientes del agua para reproducción
- Gametófito dominante
- Tamaño pequeño (pocos centímetros)

Ejemplos: Musgo común (Bryum), Hepática (Marchantia)

2. PTERIDOPHYTA (Pteridófitos):
- Helechos y plantas afines
- Con tejidos vasculares (xilema y floema)
- Sin semillas
- Esporófito dominante
- Reproducción por esporas

Ejemplos: Helecho común (Pteridium), Cola de caballo (Equisetum)

3. GYMNOSPERMAE (Gimnospermas):
- Plantas con semillas desnudas
- Sin frutos verdaderos
- Generalmente hojas aciculares
- Flores unisexuales simples (conos)
- Adaptadas a climas fríos

Ejemplos: Pino (Pinus), Abeto (Abies), Ciprés (Cupressus)

4. ANGIOSPERMAE (Angiospermas):
- Plantas con flores verdaderas
- Semillas protegidas en frutos
- Mayor diversidad vegetal
- Adaptadas a múltiples ambientes

SUBDIVISIONES DE ANGIOSPERMAS:

A. MONOCOTILEDÓNEAS:
- Un solo cotiledón en la semilla
- Hojas con nervación paralela
- Flores con partes en múltiplos de 3
- Sistema radicular fasciculado
- Crecimiento primario únicamente

Familias importantes:
- Poaceae (gramíneas): trigo, arroz, maíz
- Liliaceae (lirios): cebolla, ajo, tulipán
- Orchidaceae (orquídeas): vainilla, orquídeas

B. DICOTILEDÓNEAS:
- Dos cotiledones en la semilla
- Hojas con nervación reticulada
- Flores con partes en múltiplos de 4 o 5
- Sistema radicular pivotante
- Crecimiento secundario (formación de madera)

Familias importantes:
- Rosaceae (rosáceas): rosa, manzano, cerezo
- Fabaceae (leguminosas): judía, guisante, alfalfa
- Solanaceae (solanáceas): tomate, patata, pimiento

NOMENCLATURA BINOMIAL:
Sistema creado por Linneo:
- Género + especie
- Ejemplo: Solanum lycopersicum (tomate)
- Nombres en latín o latinizados
- Sistema universal para científicos

CRITERIOS DE CLASIFICACIÓN:
- Morfología (forma y estructura)
- Anatomía (tejidos internos)
- Fisiología (procesos biológicos)
- Genética (ADN y evolución)
- Reproducción (tipo de flores, frutos)

Esta clasificación ayuda a entender las relaciones evolutivas entre plantas y predecir características compartidas.
            """,
            
            "plant_diseases_intro.txt": """
INTRODUCCIÓN A LAS ENFERMEDADES DE PLANTAS

Las enfermedades vegetales son alteraciones en el funcionamiento normal de las plantas causadas por patógenos o factores ambientales.

TIPOS DE PATÓGENOS:

1. HONGOS (Enfermedades Fúngicas):
- Causan el 80% de las enfermedades vegetales
- Estructuras: micelio, esporas, cuerpos fructíferos
- Transmisión: aire, agua, suelo, insectos
- Condiciones favorables: humedad alta, temperaturas moderadas

Ejemplos comunes:
- Mildiu (Plasmopara viticola): en vid
- Oídio (Erysiphe graminis): en cereales
- Roya (Puccinia graminis): en trigo
- Alternaria (Alternaria solani): en tomate

2. BACTERIAS (Enfermedades Bacterianas):
- Organismos unicelulares
- Penetran por heridas o aberturas naturales
- Transmisión: agua, insectos, herramientas
- Síntomas: marchitez, manchas acuosas, tumores

Ejemplos:
- Erwinia amylovora: fuego bacteriano en rosáceas
- Xanthomonas: mancha bacteriana en tomate
- Agrobacterium: tumores en muchas plantas

3. VIRUS (Enfermedades Virales):
- Parásitos obligados intracelulares
- Transmisión: insectos vectores, injertos, semillas
- Síntomas: mosaicos, deformaciones, enanismo
- Difíciles de controlar

Ejemplos:
- Virus del mosaico del tabaco (TMV)
- Virus del mosaico del pepino (CMV)
- Virus de la tristeza de los cítricos

4. NEMATODOS:
- Gusanos microscópicos del suelo
- Atacan raíces principalmente
- Síntomas: agallas, necrosis radicular, enanismo
- Transmisión: suelo infestado

Ejemplos:
- Meloidogyne (nematodo agallador)
- Heterodera (nematodo del quiste)

SÍNTOMAS PRINCIPALES:

FOLIARES:
- Manchas: circulares, angulares, irregulares
- Mosaicos: alternancias de color verde
- Amarilleo: clorosis generalizada o localizada
- Necrosis: muerte de tejidos (marrón/negro)
- Deformaciones: rizado, abollado

RADICULARES:
- Pudriciones: tejidos blandos y oscuros
- Agallas: hinchazones anormales
- Necrosis: raíces muertas

VASCULARES:
- Marchitez: pérdida de turgencia
- Decoloraciones: cambios en vasos conductores

FACTORES PREDISPONENTES:
- Estrés hídrico (exceso o deficiencia)
- Temperaturas extremas
- Nutrición desequilibrada
- Heridas y daños mecánicos
- Densidad excesiva de plantación
- Falta de ventilación

TRIÁNGULO DE LA ENFERMEDAD:
Para que ocurra una enfermedad se necesitan:
1. Huésped susceptible
2. Patógeno virulento  
3. Ambiente favorable

ESTRATEGIAS DE CONTROL:

PREVENTIVO:
- Variedades resistentes
- Rotación de cultivos
- Saneamiento (eliminación de restos)
- Desinfección de herramientas
- Manejo del riego

CULTURAL:
- Espaciamiento adecuado
- Fertilización equilibrada
- Poda sanitaria
- Control de malas hierbas

BIOLÓGICO:
- Microorganismos antagonistas
- Extractos vegetales
- Feromonas y trampas

QUÍMICO:
- Fungicidas, bactericidas
- Aplicación preventiva y curativa
- Rotación de materias activas
- Respeto a dosis y plazo de seguridad

El manejo integrado combina múltiples estrategias para un control efectivo y sostenible.
            """
        }
        
        created_files = []
        for filename, content in botanical_texts.items():
            if filename.endswith('intro.txt'):
                topic = "pathology"
            elif filename.endswith('classification.txt') or filename.endswith('basics.txt'):
                topic = "general"
            else:
                topic = "general"
            
            filepath = self.documents_path / topic / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content.strip())
            
            created_files.append(filename)
            self.logger.info(f"Creado: {filepath}")
        
        return created_files
    
    def download_all_resources(self) -> Dict[str, List[str]]:
        """Descarga todos los recursos disponibles"""
        self.logger.info("Iniciando descarga de recursos...")
        
        self.setup_directories()
        
        results = {
            "fao_resources": [],
            "university_resources": [],
            "botanical_texts": [],
            "errors": []
        }
        
        try:
            # Descargar recursos FAO
            results["fao_resources"] = self.download_fao_resources()
            
            # Descargar recursos universitarios
            results["university_resources"] = self.download_university_resources()
            
            # Crear textos botánicos
            results["botanical_texts"] = self.create_botanical_texts()
            
        except Exception as e:
            self.logger.error(f"Error durante la descarga: {e}")
            results["errors"].append(str(e))
        
        return results
    
    def get_download_urls(self) -> Dict[str, List[Dict[str, str]]]:
        """Devuelve lista de URLs recomendadas para descarga manual"""
        return {
            "plants": [
                {
                    "name": "Manual de Agricultura Orgánica",
                    "url": "https://www.fao.org/3/i7749e/i7749e.pdf",
                    "description": "Prácticas agrícolas sostenibles"
                },
                {
                    "name": "Guía de Horticultura",
                    "url": "https://extension.umn.edu/growing-guides",
                    "description": "Cultivo de hortalizas"
                }
            ],
            "pathology": [
                {
                    "name": "Manejo Integrado de Plagas",
                    "url": "https://www.fao.org/integrated-pest-management",
                    "description": "Control de plagas y enfermedades"
                },
                {
                    "name": "Atlas de Enfermedades Vegetales", 
                    "url": "https://www.apsnet.org/edcenter/resources/",
                    "description": "Identificación de patógenos"
                }
            ],
            "general": [
                {
                    "name": "Botánica General",
                    "url": "https://www.botanicalgarden.org/education",
                    "description": "Conceptos básicos de botánica"
                },
                {
                    "name": "Fisiología Vegetal",
                    "url": "https://plantphys.net/",
                    "description": "Procesos biológicos de plantas"
                }
            ]
        }

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Descargador de datos agrícolas")
    parser.add_argument("--download", action="store_true",
                       help="Descargar recursos automáticamente")
    parser.add_argument("--create-texts", action="store_true", 
                       help="Crear textos botánicos básicos")
    parser.add_argument("--list-urls", action="store_true",
                       help="Mostrar URLs recomendadas")
    parser.add_argument("--base-path", help="Directorio base del proyecto")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Modo verbose")
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Crear descargador
    downloader = AgriculturalDataDownloader(args.base_path)
    
    try:
        if args.list_urls:
            # Mostrar URLs recomendadas
            urls = downloader.get_download_urls()
            print("\n📋 URLs RECOMENDADAS PARA DESCARGA MANUAL:")
            print("=" * 50)
            
            for topic, resources in urls.items():
                print(f"\n🏷️  {topic.upper()}:")
                for resource in resources:
                    print(f"   📄 {resource['name']}")
                    print(f"      🔗 {resource['url']}")
                    print(f"      📝 {resource['description']}\n")
        
        elif args.create_texts:
            # Crear solo textos básicos
            created = downloader.create_botanical_texts()
            print(f"\n✅ Creados {len(created)} textos botánicos:")
            for filename in created:
                print(f"   • {filename}")
        
        elif args.download:
            # Descarga completa
            print("🚀 Iniciando descarga de recursos...")
            results = downloader.download_all_resources()
            
            print(f"\n📊 RESUMEN DE DESCARGA:")
            print("=" * 30)
            print(f"📄 Recursos FAO: {len(results['fao_resources'])}")
            print(f"🎓 Recursos universitarios: {len(results['university_resources'])}")
            print(f"📚 Textos creados: {len(results['botanical_texts'])}")
            
            if results['errors']:
                print(f"❌ Errores: {len(results['errors'])}")
                for error in results['errors']:
                    print(f"   • {error}")
        
        else:
            # Mostrar ayuda
            parser.print_help()
            print(f"\n💡 EJEMPLOS DE USO:")
            print(f"   python {sys.argv[0]} --create-texts")
            print(f"   python {sys.argv[0]} --download --verbose")
            print(f"   python {sys.argv[0]} --list-urls")
    
    except KeyboardInterrupt:
        print("\n⏹️  Descarga interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()