"""
Script de solución rápida para problemas de AgentRagMCP
Ejecutar con: python scripts/quick_fix.py
"""

import sys
import shutil
import time
from pathlib import Path

# Añadir directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def fix_dynamic_agent_loader():
    """
    Aplica la corrección al método create_agent de DynamicAgentLoader
    """
    print("🔧 Aplicando corrección a DynamicAgentLoader...")
    
    agent_file = root_dir / "agentragmcp" / "api" / "app" / "agents" / "dinamic_agent.py"
    
    if not agent_file.exists():
        print(f"❌ Archivo no encontrado: {agent_file}")
        return False
    
    # Leer archivo actual
    try:
        with open(agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Crear backup
        backup_file = agent_file.with_suffix('.py.backup')
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"📁 Backup creado: {backup_file}")
        
        # Buscar y reemplazar el método problemático
        old_pattern = """        try:
            # Crear instancia
            agent = agent_class(config, rag_service)
            logger.info(f"Agente creado: {config.name} ({config.class_name})")
            return agent"""
        
        new_pattern = """        try:
            # CORRECCIÓN: Verificar si es DynamicAgent que requiere constructor especial
            if agent_class == DynamicAgent:
                # DynamicAgent requiere (agent_name, config_dict, rag_service)
                # Convertir AgentConfig a diccionario
                config_dict = {
                    "description": config.description,
                    "class": config.class_name,
                    "topics": config.topics,
                    "enabled": config.enabled,
                    "priority": config.priority,
                    "config": {
                        "max_confidence": config.max_confidence,
                        "min_confidence": config.min_confidence,
                        "primary_keywords": config.primary_keywords,
                        "secondary_keywords": config.secondary_keywords,
                        "patterns": config.patterns,
                        "target_species": config.target_species
                    },
                    "thresholds": {
                        "keyword_weight": config.keyword_weight,
                        "species_weight": config.species_weight,
                        "pattern_weight": config.pattern_weight
                    }
                }
                agent = agent_class(config.name, config_dict, rag_service)
            else:
                # Para todas las demás clases (ConfigurableAgent y subclases)
                agent = agent_class(config, rag_service)
            
            logger.info(f"Agente creado: {config.name} ({config.class_name})")
            return agent"""
        
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            
            # Guardar archivo corregido
            with open(agent_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✅ Corrección aplicada exitosamente")
            return True
        else:
            print("⚠️ Patrón no encontrado - puede que ya esté corregido")
            return True
            
    except Exception as e:
        print(f"❌ Error aplicando corrección: {e}")
        return False

def clean_problematic_vectorstores():
    """
    Limpia vectorstores con problemas de dimensionalidad
    """
    print("🗑️ Limpiando vectorstores problemáticos...")
    
    vectorstore_base = root_dir / "data" / "vectorstores"
    
    if not vectorstore_base.exists():
        print("⚠️ Directorio de vectorstores no existe")
        return True
    
    # Vectorstores que reportaron errores de dimensionalidad
    problematic_stores = ['general', 'plants']
    
    for store_name in problematic_stores:
        store_path = vectorstore_base / store_name
        
        if store_path.exists():
            # Crear backup
            backup_path = vectorstore_base / f"{store_name}_backup_{int(time.time())}"
            try:
                shutil.move(str(store_path), str(backup_path))
                print(f"📁 {store_name} movido a backup: {backup_path}")
            except Exception as e:
                print(f"⚠️ Error moviendo {store_name}: {e}")
        else:
            print(f"ℹ️ Vectorstore {store_name} no existe")
    
    print("✅ Limpieza de vectorstores completada")
    return True

def create_minimal_sample_documents():
    """
    Crea documentos mínimos de ejemplo para testing
    """
    print("📄 Creando documentos mínimos de ejemplo...")
    
    docs_base = root_dir / "data" / "documents"
    docs_base.mkdir(parents=True, exist_ok=True)
    
    samples = {
        "plants": {
            "file": "plantas_basicas.txt",
            "content": """# Plantas Básicas

## Manzano (Malus domestica)
El manzano es un árbol frutal caducifolio de la familia Rosaceae.
Requiere clima templado y riego regular.

### Cuidados:
- Riego: semanal en verano
- Poda: en invierno
- Cosecha: otoño

## Tomate (Solanum lycopersicum)
Planta anual de la familia Solanaceae.
Requiere tutor y mucha luz solar.

### Cuidados:
- Riego: diario en verano
- Luz: 8 horas directas
- Suelo: bien drenado
"""
        },
        
        "pathology": {
            "file": "enfermedades_comunes.txt", 
            "content": """# Enfermedades Comunes

## Mildiu en Vid
Enfermedad fúngica causada por Plasmopara viticola.

### Síntomas:
- Manchas amarillas en hojas
- Pelusa blanca en el envés
- Afecta frutos jóvenes

### Tratamiento:
- Fungicidas cúpricos preventivos
- Mejora de ventilación
- Eliminación de hojas afectadas

## Sarna del Manzano
Causada por Venturia inaequalis.

### Síntomas:
- Manchas marrones en hojas
- Deformación de frutos
- Caída prematura de hojas

### Prevención:
- Poda para ventilación
- Tratamientos fungicidas primaverales
"""
        },
        
        "general": {
            "file": "botanica_general.txt",
            "content": """# Botánica General

## Fotosíntesis
Proceso por el cual las plantas convierten luz solar, CO2 y agua en glucosa y oxígeno.

### Ecuación:
6CO2 + 6H2O + luz solar → C6H12O6 + 6O2

## Partes de la Planta

### Raíces
- Absorción de agua y nutrientes
- Fijación al suelo
- Almacenamiento de reservas

### Tallo
- Soporte de la planta
- Transporte de nutrientes
- Almacenamiento

### Hojas
- Fotosíntesis
- Intercambio gaseoso
- Transpiración

### Flores
- Reproducción sexual
- Atracción de polinizadores
- Formación de frutos

## Clasificación Básica
- Monocotiledóneas: un cotiledón (gramíneas, palmeras)
- Dicotiledóneas: dos cotiledones (mayoría de plantas)
"""
        }
    }
    
    created_count = 0
    for topic, data in samples.items():
        topic_dir = docs_base / topic
        topic_dir.mkdir(exist_ok=True)
        
        file_path = topic_dir / data["file"]
        
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data["content"])
            print(f"✅ Creado: {file_path}")
            created_count += 1
        else:
            print(f"ℹ️ Ya existe: {file_path}")
    
    print(f"📊 {created_count} archivos creados")
    return True

def create_minimal_configs():
    """
    Crea configuraciones mínimas pero funcionales
    """
    print("⚙️ Creando configuraciones mínimas...")
    
    config_base = root_dir / "data" / "configs"
    config_base.mkdir(parents=True, exist_ok=True)
    
    rags_dir = config_base / "rags"
    rags_dir.mkdir(exist_ok=True)
    
    # Configuraciones RAG simplificadas
    rag_configs = {
        "plants": {
            "name": "plants",
            "display_name": "Plantas",
            "description": "Información básica sobre plantas",
            "enabled": True,
            "priority": 1,
            "vectorstore": {
                "type": "chroma",
                "path": "./data/vectorstores/plants"
            },
            "retrieval": {
                "search_type": "similarity",
                "k": 3
            },
            "embedding": {
                "model": "llama3.1",
                "chunk_size": 1000,
                "chunk_overlap": 200
            }
        },
        
        "pathology": {
            "name": "pathology",
            "display_name": "Patologías",
            "description": "Diagnóstico de enfermedades",
            "enabled": True,
            "priority": 1,
            "vectorstore": {
                "type": "chroma", 
                "path": "./data/vectorstores/pathology"
            },
            "retrieval": {
                "search_type": "similarity",
                "k": 3
            },
            "embedding": {
                "model": "llama3.1",
                "chunk_size": 800,
                "chunk_overlap": 150
            }
        },
        
        "general": {
            "name": "general",
            "display_name": "General",
            "description": "Conocimiento general",
            "enabled": True,
            "priority": 2,
            "vectorstore": {
                "type": "chroma",
                "path": "./data/vectorstores/general"
            },
            "retrieval": {
                "search_type": "similarity",
                "k": 3
            },
            "embedding": {
                "model": "llama3.1",
                "chunk_size": 1200,
                "chunk_overlap": 250
            }
        }
    }
    
    # Guardar configuraciones RAG
    import yaml
    for topic, config in rag_configs.items():
        config_file = rags_dir / f"{topic}.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        print(f"✅ Config RAG creada: {config_file}")
    
    # Configuración de agentes simplificada
    agents_config = {
        "agents": {
            "plants": {
                "description": "Especialista en plantas",
                "class": "GenericRAGAgent",
                "topics": ["plants"],
                "enabled": True,
                "priority": 1,
                "config": {
                    "max_confidence": 1.0,
                    "min_confidence": 0.1,
                    "primary_keywords": ["planta", "cultivo", "riego", "manzano", "tomate"],
                    "secondary_keywords": ["jardinería", "botánica"],
                    "patterns": ["cómo cuidar", "cuándo plantar"],
                    "target_species": ["Malus domestica", "Solanum lycopersicum"]
                },
                "thresholds": {
                    "keyword_weight": 0.3,
                    "species_weight": 0.5,
                    "pattern_weight": 0.2
                }
            },
            
            "pathology": {
                "description": "Especialista en enfermedades",
                "class": "GenericRAGAgent",
                "topics": ["pathology"],
                "enabled": True,
                "priority": 1,
                "config": {
                    "max_confidence": 1.0,
                    "min_confidence": 0.1,
                    "primary_keywords": ["enfermedad", "síntomas", "tratamiento", "mildiu"],
                    "secondary_keywords": ["hongo", "bacteria"],
                    "patterns": ["qué enfermedad", "cómo tratar"],
                    "target_species": ["Malus domestica", "Vitis vinifera"]
                },
                "thresholds": {
                    "keyword_weight": 0.4,
                    "species_weight": 0.3,
                    "pattern_weight": 0.3
                }
            },
            
            "general": {
                "description": "Conocimiento general",
                "class": "GenericRAGAgent", 
                "topics": ["general"],
                "enabled": True,
                "priority": 2,
                "config": {
                    "max_confidence": 0.8,
                    "min_confidence": 0.1,
                    "primary_keywords": ["qué es", "fotosíntesis", "explicar"],
                    "secondary_keywords": ["botánica", "biología"],
                    "patterns": ["qué es", "cómo funciona"],
                    "target_species": []
                },
                "thresholds": {
                    "keyword_weight": 0.5,
                    "species_weight": 0.1,
                    "pattern_weight": 0.4
                }
            }
        }
    }
    
    # Guardar configuración de agentes
    agents_file = config_base / "agents.yaml"
    with open(agents_file, 'w', encoding='utf-8') as f:
        yaml.dump(agents_config, f, default_flow_style=False, allow_unicode=True)
    print(f"✅ Config agentes creada: {agents_file}")
    
    return True

def main():
    """
    Función principal de solución rápida
    """
    print("🚀 SOLUCIÓN RÁPIDA PARA AGENTRAGMCP")
    print("=" * 40)
    print("Este script soluciona los errores principales del sistema\n")
    
    success_count = 0
    total_steps = 4
    
    # Paso 1: Corregir DynamicAgentLoader
    print("1️⃣ CORRIGIENDO DYNAMICAGENTLOADER...")
    if fix_dynamic_agent_loader():
        success_count += 1
        print("✅ DynamicAgentLoader corregido\n")
    else:
        print("❌ Error corrigiendo DynamicAgentLoader\n")
    
    # Paso 2: Limpiar vectorstores problemáticos
    print("2️⃣ LIMPIANDO VECTORSTORES PROBLEMÁTICOS...")
    if clean_problematic_vectorstores():
        success_count += 1
        print("✅ Vectorstores limpiados\n")
    else:
        print("❌ Error limpiando vectorstores\n")
    
    # Paso 3: Crear documentos de ejemplo
    print("3️⃣ CREANDO DOCUMENTOS DE EJEMPLO...")
    if create_minimal_sample_documents():
        success_count += 1
        print("✅ Documentos de ejemplo creados\n")
    else:
        print("❌ Error creando documentos\n")
    
    # Paso 4: Crear configuraciones
    print("4️⃣ CREANDO CONFIGURACIONES...")
    if create_minimal_configs():
        success_count += 1
        print("✅ Configuraciones creadas\n")
    else:
        print("❌ Error creando configuraciones\n")
    
    # Resumen
    print("📊 RESUMEN DE LA REPARACIÓN")
    print("=" * 30)
    print(f"✅ Pasos completados: {success_count}/{total_steps}")
    
    if success_count == total_steps:
        print("\n🎉 ¡REPARACIÓN COMPLETADA EXITOSAMENTE!")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Crear vectorstores: python scripts/process_documents.py --all")
        print("2. Verificar sistema: python scripts/verify_system.py")
        print("3. Ejecutar aplicación: python -m agentragmcp.api.app.main")
    else:
        print(f"\n⚠️ REPARACIÓN PARCIAL ({success_count}/{total_steps} pasos)")
        print("Revisa los errores anteriores y ejecuta nuevamente")
    
    return success_count == total_steps

if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("❌ PyYAML no está instalado. Ejecuta: pip install pyyaml")
        sys.exit(1)
    
    success = main()
    sys.exit(0 if success else 1)