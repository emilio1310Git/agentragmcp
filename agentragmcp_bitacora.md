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
  
  {{context}}

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

1. **Crear el código del agente** en `agentragmcp/custom_agents/mi_agente.py`:

```python
from agentragmcp.api.app.services.dynamic_agent_system import ConfigurableAgent

class MiAgentePersonalizado(ConfigurableAgent):
    def can_handle(self, question: str, context=None) -> float:
        # Tu lógica personalizada
        base_confidence = super().can_handle(question, context)
        # Añadir lógica específica...
        return base_confidence
    
    def process(self, question: str, session_id: str, **kwargs):
        # Tu procesamiento personalizado
        return self.rag_service.query(...)
```

2. **Añadir configuración** en `agents.yaml`:

```yaml
mi_agente:
  class: "MiAgentePersonalizado"
  module_path: "./agentragmcp/custom_agents/mi_agente.py"
  # resto de configuración...
```

## 🔄 Recarga Automática

El sistema verifica automáticamente cada 30 segundos si hay cambios en:
- Archivos de configuración RAG (`.yaml`)
- Archivo de configuración de agentes (`agents.yaml`)

Los cambios se aplican automáticamente sin reiniciar el servidor.

## 📊 Monitoreo y Métricas