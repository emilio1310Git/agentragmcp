# 🌱 AgentRagMCP - Sistema Dinámico de Configuración

## 📋 Resumen de la Migración

Este sistema ha sido migrado de configuración hardcodeada a un sistema dinámico y flexible que permite:

✅ **RAGs Configurables**: Cada temática tiene su propio archivo de configuración
✅ **Agentes Dinámicos**: Los agentes se cargan automáticamente desde configuración
✅ **Extensibilidad**: Fácil adición de nuevas temáticas y agentes sin modificar código
✅ **Recarga Automática**: Cambios en configuración se detectan y aplican automáticamente

## 📁 Estructura de Configuración

```
data/configs/
├── rags/                          # Configuraciones de RAG por temática
│   ├── plants.yaml               # Información general de plantas
│   ├── pathology.yaml            # Patologías y enfermedades
│   ├── general.yaml              # Conocimiento general
│   ├── eco_agriculture.yaml      # Agricultura ecológica (ejemplo)
│   └── urban_gardening.yaml      # Jardinería urbana (ejemplo)
├── agents.yaml                   # Configuración de todos los agentes
└── custom/                       # Configuraciones personalizadas

agentragmcp/custom_agents/         # Agentes personalizados
├── eco_agriculture_agent.py      # Ejemplo de agente personalizado
└── __init__.py
```

## 🚀 Cómo Añadir Nuevos RAGs

### 1. Crear Configuración RAG

Crea un archivo `mi_nueva_tematica.yaml` en `data/configs/rags/`:

```yaml
display_name: "Mi Nueva Temática"
description: "Descripción de la temática"
enabled: true
priority: 1

vectorstore:
  type: "chroma"
  path: "./data/vectorstores/mi_nueva_tematica"
  collection_name: "mi_nueva_tematica_collection"
  chunk_size: 1000
  chunk_overlap: 200

retrieval:
  search_type: "mmr"
  k: 5
  lambda_mult: 0.7

system_prompt: |
  Eres un especialista en [tu temática].
  
  **Especialidades:**
  - Lista tus especialidades
  
  {context}

categories: ["categoria1", "categoria2"]
keywords:
  primary: ["palabra1", "palabra2"]
  secondary: ["palabra3", "palabra4"]

source_paths: ["./data/documents/mi_nueva_tematica"]
```

### 2. Añadir Documentos

- Crea directorio: `data/documents/mi_nueva_tematica/`
- Añade documentos en formato `.txt`, `.pdf`, `.md`
- Ejecuta script de procesamiento para crear vectorstore

### 3. El Sistema se Encarga del Resto

El sistema detectará automáticamente la nueva configuración y cargará el RAG.

## 🤖 Cómo Añadir Nuevos Agentes

### 1. Agente Genérico (Solo Configuración)

Añade a `data/configs/agents.yaml`:

```yaml
agents:
  mi_agente:
    description: "Descripción del agente"
    class: "GenericRAGAgent"  # Usa agente genérico
    topics: ["mi_nueva_tematica"]
    enabled: true
    priority: 2
    config:
      primary_keywords: ["palabra1", "palabra2"]
      patterns: ["patrón.*regex"]
      target_species: ["Especie específica"]
    thresholds:
      keyword_weight: 0.4
      pattern_weight: 0.3
```

### 2. Agente Personalizado (Con Código)

1. Crea archivo en `agentragmcp/custom_agents/mi_agente.py`
2. Hereda de `DynamicAgent`
3. Implementa lógica específica
4. Actualiza configuración en `agents.yaml`

## 🔧 Comandos Útiles

```bash
# Migrar sistema completo
python scripts/migration_dinamic.py

# Validar configuraciones
python -c "from agentragmcp.core.dynamic_config import config_manager; config_manager.validate_all()"

# Recargar configuraciones
python -c "from agentragmcp.core.dynamic_config import config_manager; config_manager.reload_if_changed()"

# Listar configuraciones disponibles
python -c "from agentragmcp.core.dynamic_config import config_manager; print(config_manager.list_available_configs())"
```

## 📝 Ejemplos Incluidos

La migración incluye configuraciones de ejemplo para:

- **🌱 Plants**: Información general de plantas
- **🦠 Pathology**: Diagnóstico y tratamiento de enfermedades
- **📚 General**: Conocimiento educativo de botánica
- **🌿 Eco Agriculture**: Agricultura ecológica y sostenible
- **🏙️ Urban Gardening**: Jardinería en espacios urbanos

## 🛠️ Desarrollo y Personalización

### Estructura de un Agente Personalizado

```python
from agentragmcp.api.app.agents.dinamic_agent import DynamicAgent

class MiAgentePersonalizado(DynamicAgent):
    def __init__(self, config, rag_service):
        super().__init__("mi_tematica", config, rag_service)
    
    def calculate_confidence(self, question: str) -> float:
        # Lógica personalizada de confianza
        confidence = super().calculate_confidence(question)
        # Añadir bonificaciones específicas
        return confidence
    
    def enhance_response(self, response: str, question: str) -> str:
        # Mejoras específicas a las respuestas
        return enhanced_response
```

### Configuración Avanzada de RAG

```yaml
# Configuración avanzada con múltiples fuentes
vectorstore:
  type: "chroma"
  path: "./data/vectorstores/mi_rag"
  collection_name: "mi_collection"
  chunk_size: 1200
  chunk_overlap: 300
  embedding_model: "llama3.1"

retrieval:
  search_type: "mmr"
  k: 6
  fetch_k: 20
  lambda_mult: 0.8
  score_threshold: 0.4

# Configuraciones personalizadas
custom_settings:
  use_metadata_filter: true
  include_source_info: true
  max_context_length: 4000
  response_language: "es"
```

## 📊 Monitoreo y Métricas

El sistema incluye capacidades de monitoreo:

- **Carga de configuraciones**: Tiempo y éxito de carga
- **Uso de agentes**: Frecuencia de selección por agente
- **Performance de RAGs**: Tiempo de respuesta por temática
- **Detección de cambios**: Recargas automáticas de configuración

## 🔄 Proceso de Migración Completado

La migración automática ha:

1. ✅ Creado estructura de directorios
2. ✅ Extraído configuraciones hardcodeadas
3. ✅ Generado archivos YAML de configuración
4. ✅ Creado agentes personalizados de ejemplo
5. ✅ Añadido documentos de ejemplo
6. ✅ Validado la migración
7. ✅ Generado esta documentación

## 📞 Soporte

Para más información sobre el sistema dinámico:
- Revisa los archivos de configuración en `data/configs/`
- Consulta los ejemplos en `agentragmcp/custom_agents/`
- Ejecuta las validaciones incluidas
- Revisa los logs del sistema para debugging

---

**¡El sistema AgentRagMCP ahora es completamente dinámico y extensible!** 🎉
