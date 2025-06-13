# AgentRagMCP 🌱🤖

**Asistente IA especializado en plantas con múltiples RAGs y sistema de agentes**

AgentRagMCP es una evolución avanzada del sistema agentragmcp que implementa un enfoque multi-agente con múltiples RAGs (Retrieval-Augmented Generation) especializados. El sistema selecciona automáticamente el agente más apropiado según la consulta del usuario, proporcionando respuestas especializadas y precisas sobre diferentes aspectos del mundo vegetal.

## 🎯 Características Principales

### 🤖 Sistema Multi-Agente

- **Agente de Plantas**: Especializado en información general, cultivo y cuidados
- **Agente de Patologías**: Experto en enfermedades, plagas y tratamientos
- **Agente General**: Conocimiento educativo y divulgativo de botánica
- **Selección Automática**: Algoritmo inteligente que elige el agente más apropiado

### 🧠 RAGs Especializados

- **RAG Plants**: Base de conocimiento sobre especies, cultivo y cuidados
- **RAG Pathology**: Información especializada en patologías vegetales
- **RAG General**: Conocimiento general y educativo sobre botánica

### 🔌 Arquitectura Modular

- **FastAPI**: API REST moderna y eficiente
- **LangChain**: Framework para aplicaciones LLM
- **ChromaDB**: Base de datos vectorial para embeddings
- **Ollama**: Servidor local de modelos LLM
- **Pydantic**: Validación de datos y configuración

### 🛡️ Características Avanzadas

- **MCP Support**: Protocolo de comunicación con modelos (opcional)
- **Health Checks**: Monitoreo automático del sistema
- **Métricas**: Seguimiento de rendimiento y uso
- **Logging Estructurado**: Sistema de logging avanzado
- **Configuración Flexible**: Configuración basada en variables de entorno

## 📋 Requisitos del Sistema

### Software Necesario

- **Python 3.8+**
- **Ollama** con modelo `llama3.1` instalado
- **Git** para clonar el repositorio

### Recursos Recomendados

- **RAM**: 8GB mínimo, 16GB recomendado
- **CPU**: 4 cores mínimo
- **Almacenamiento**: 10GB libres para vectorstores
- **GPU**: Opcional para mejor rendimiento de Ollama

## 🚀 Instalación Rápida

### 1. Clonar y Configurar

```bash
# Clonar repositorio
git clone <tu-repositorio>/agentragmcp.git
cd agentragmcp

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r config/requirements.txt
```

### 2. Configurar Ollama

```bash
# Instalar Ollama (si no está instalado)
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelo
ollama pull llama3.1

# Verificar que está funcionando
ollama list
```

### 3. Inicialización Automática

```bash
# Ejecutar script de inicialización
python scripts/init_agentragmcp.py

# Esto creará:
# - Estructura de directorios
# - Archivo .env desde .env.example  
# - Verificará dependencias
# - Ejecutará health checks
```

### 4. Configurar Variables de Entorno

```bash
# Editar .env con tu configuración
cp .env.example .env
# Ajustar según tu entorno
```

### 5. Ejecutar la Aplicación

```bash
# Desarrollo
python -m agentragmcp.api.app.main

# O con uvicorn directamente
uvicorn agentragmcp.api.app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📁 Estructura del Proyecto

```
📂 agentragmcp/
├── 📂 agentragmcp/
│   ├── 📂 api/
│   │   ├── 📂 app/
│   │   │   ├── 📂 agents/          # Agentes especializados
│   │   │   │   ├── base_agent.py   # Clase base abstracta
│   │   │   │   ├── plants_agent.py # Agente de plantas
│   │   │   │   ├── pathology_agent.py # Agente de patologías
│   │   │   │   └── general_agent.py # Agente general
│   │   │   ├── 📂 models/          # Modelos Pydantic
│   │   │   ├── 📂 routers/         # Endpoints FastAPI
│   │   │   ├── 📂 services/        # Servicios de negocio
│   │   │   └── main.py             # Aplicación principal
│   │   └── 📂 static/              # Archivos estáticos
│   ├── 📂 core/                    # Núcleo del sistema
│   │   ├── config.py               # Configuración
│   │   ├── exceptions.py           # Excepciones personalizadas
│   │   └── monitoring.py           # Logging y métricas
│   └── 📂 data/
│       ├── 📂 configs/             # Configuraciones YAML
│       └── 📂 vectorstores/        # Bases de datos vectoriales
├── 📂 config/                      # Configuración de despliegue
├── 📂 scripts/                     # Scripts de utilidad
├── 📂 tests/                       # Tests automatizados
├── .env.example                    # Configuración de ejemplo
└── README.md                       # Este archivo
```

## 🔧 Configuración Detallada

### Variables de Entorno Principales

```bash
# === APLICACIÓN ===
APP_NAME="AgentRagMCP"
ENVIRONMENT="development"  # development, production
DEBUG=false

# === LLM Y EMBEDDINGS ===
LLM_MODEL="llama3.1"
LLM_BASE_URL="http://localhost:11434"
EMBEDDING_MODEL="llama3.1"

# === RAG Y VECTORSTORES ===
RAG_TOPICS="plants,pathology,general"
VECTORSTORE_BASE_PATH="./data/vectorstores"

# === AGENTES ===
DEFAULT_AGENT="general"
AGENT_SELECTION_MODEL="llama3.1"

# === MCP (OPCIONAL) ===
MCP_ENABLED=false
```

### Configuración de Agentes

Los agentes se configuran en `agentragmcp/data/configs/agents.yaml`:

```yaml
agents:
  plants:
    description: "Especialista en información general de plantas"
    topics: ["plants"]
    priority: 1
    
  pathology:
    description: "Especialista en patologías y enfermedades"
    topics: ["pathology"] 
    priority: 2
```

## 📊 Uso de la API

### Endpoints Principales

#### Chat Principal

```bash
# Consulta con selección automática de agente
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cómo cuidar un manzano?",
    "include_sources": true
  }'
```

#### Consulta Específica por Agente

```bash
# Forzar uso de agente específico
curl -X POST "http://localhost:8000/chat/" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Síntomas de mildiu en vid",
    "agent_type": "pathology"
  }'
```

#### Consulta Directa a RAG

```bash
# Consulta directa sin procesamiento de agentes
curl -X POST "http://localhost:8000/chat/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Fotosíntesis en plantas",
    "topic": "general"
  }'
```

### Respuesta de Ejemplo

```json
{
  "answer": "Para cuidar un manzano correctamente...",
  "session_id": "uuid-session-id",
  "agent_type": "plants",
  "topic": "plants", 
  "confidence": 0.85,
  "sources": [
    {
      "content": "Los manzanos necesitan...",
      "metadata": {"source": "manual_fruticultura.pdf"}
    }
  ],
  "response_time": 1.23
}
```

## 🗃️ Gestión de Datos

### Preparar Vectorstores

1. **Crear directorios de datos**:

```bash
mkdir -p data/documents/{plants,pathology,general}
```

1. **Agregar documentos**:
    - Coloca archivos PDF, TXT o MD en los directorios correspondientes
    - Ejemplos: manuales de cultivo → `plants/`, guías de enfermedades → `pathology/`
2. **Crear vectorstores** (ejemplo para plantas):

```python
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

# Cargar documentos
loader = DirectoryLoader("./data/documents/plants", glob="**/*.pdf")
documents = loader.load()

# Procesar texto
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = text_splitter.split_documents(documents)

# Crear vectorstore
embeddings = OllamaEmbeddings(model="llama3.1")
vectorstore = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory="./data/vectorstores/plants"
)
```

## 🏥 Monitoreo y Health Checks

### Endpoints de Monitoreo

```bash
# Health check básico
curl http://localhost:8000/health/

# Health check detallado  
curl http://localhost:8000/health/detailed

# Estado de agentes específicos
curl http://localhost:8000/health/components/agents
```

### Métricas y Logging

- **Logs**: Almacenados en `logs/agentragmcp/`
- **Métricas**: Tracking automático de rendimiento
- **Health Checks**: Monitoreo continuo de servicios

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests básicos
pytest

# Tests con cobertura
pytest --cov=agentragmcp

# Tests específicos
pytest tests/test_agents.py
```

### Tests de Integración

```bash
# Test completo del sistema
python scripts/test_integration.py

# Test de agentes específicos
python -m pytest tests/test_agents/ -v
```

## 🐳 Despliegue con Docker

### Desarrollo Local

```bash
# Construir imagen
docker build -f config/Dockerfile -t agentragmcp:dev .

# Ejecutar contenedor
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e ENVIRONMENT=development \
  agentragmcp:dev
```

### Producción

```bash
# Usar docker-compose (crear docker-compose.yml)
docker-compose up -d
```

## 🔍 Solución de Problemas

### Problemas Comunes

#### Ollama no conecta

```bash
# Verificar que Ollama esté corriendo
ollama list

# Revisar configuración de URL
echo $LLM_BASE_URL
```

#### Vectorstores vacíos

```bash
# Verificar que existen datos
ls -la data/vectorstores/*/

# Recrear vectorstores si es necesario
python scripts/rebuild_vectorstores.py
```

#### Agentes no responden

```bash
# Verificar health checks
curl http://localhost:8000/health/detailed

# Revisar logs
tail -f logs/agentragmcp/agentragmcp_$(date +%Y%m%d).log
```

### Logs y Debugging

```bash
# Activar modo debug
export DEBUG=true
export LOG_LEVEL=debug

# Verificar configuración
python -c "from agentragmcp.core.config import get_settings; print(get_settings())"
```

## 🤝 Contribución

### Desarrollo

1. **Fork** del repositorio
2. **Crear rama** para feature: `git checkout -b feature/nueva-funcionalidad`
3. **Commits** descriptivos: `git commit -m "feat: agregar nuevo agente"`
4. **Push** y **Pull Request**

### Agregar Nuevos Agentes

1. Crear clase en `agentragmcp/api/app/agents/`
2. Heredar de `BaseAgent`
3. Implementar `can_handle()` y `process()`
4. Registrar en `AgentService`
5. Agregar tests correspondientes

### Agregar Nuevos RAGs

1. Configurar en `data/configs/topics.yaml`
2. Crear vectorstore correspondiente
3. Actualizar configuración de agentes
4. Documentar en README

## 📚 Documentación Adicional

- **[Guía de Agentes](https://claude.ai/chat/docs/agents.md)**: Desarrollo de agentes personalizados
- **[Configuración RAG](https://claude.ai/chat/docs/rag.md)**: Configuración de vectorstores
- **[API Reference](https://claude.ai/chat/docs/api.md)**: Documentación completa de endpoints
- **[Deployment](https://claude.ai/chat/docs/deployment.md)**: Guía de despliegue en producción

## 📄 Licencia

Este proyecto está bajo la licencia **MIT**. Ver `LICENSE` para más detalles.

## 🙏 Reconocimientos

- **LangChain**: Framework para aplicaciones LLM
- **FastAPI**: Framework web moderno para Python
- **Ollama**: Servidor local de modelos LLM
- **ChromaDB**: Base de datos vectorial
- **Comunidad Open Source**: Por las herramientas y librerías utilizadas

------

**🌱 AgentRagMCP - Conocimiento vegetal inteligente y especializado**