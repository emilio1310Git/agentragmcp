from typing import Callable
from fastapi import FastAPI, Request, Response
import time
import psutil
import threading
from prometheus_client import multiprocess, CollectorRegistry, Counter, Histogram, Gauge, Summary
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from prometheus_client.exposition import _bake_output
from starlette.responses import Response as StarletteResponse
from starlette.routing import Route
from senfast.core.config import get_settings
from senfast.core.monitoring import logger
# settings = get_settings()

STARTUP_TIME = Gauge('senfast_startup_timestamp', 'Timestamp when the application started')
STARTUP_TIME.set_to_current_time()  # Esto garantiza que al menos tengamos una métrica

# Definir métricas de Prometheus
REQUEST_COUNT = Counter(
    'senfast_request_total', 
    'Total de peticiones HTTP',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'senfast_request_duration_seconds', 
    'Latencia de las peticiones HTTP en segundos',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1, 2.5, 5, 7.5, 10]
)

IN_PROGRESS = Gauge(
    'senfast_requests_in_progress',
    'Número de peticiones actualmente en proceso',
    ['method', 'endpoint']
)

EXCEPTIONS = Counter(
    'senfast_exceptions_total',
    'Total de excepciones lanzadas',
    ['exception_type']
)

DB_POOL_CONNECTIONS = Gauge(
    'senfast_db_pool_connections',
    'Conexiones en el pool de base de datos',
    ['state']  # 'active', 'idle', 'total'
)

DB_QUERY_LATENCY = Histogram(
    'senfast_db_query_duration_seconds',
    'Latencia de las consultas a la base de datos en segundos',
    ['query_type'],  # 'select', 'insert', 'update', 'delete'
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5]
)

SYSTEM_MEMORY = Gauge(
    'senfast_system_memory_bytes',
    'Uso de memoria del sistema',
    ['type']  # 'total', 'available', 'used'
)

SYSTEM_CPU = Gauge(
    'senfast_system_cpu_percent',
    'Porcentaje de uso de CPU',
    []
)

SYSTEM_DISK = Gauge(
    'senfast_system_disk_usage_bytes',
    'Uso de disco',
    ['mountpoint', 'type']  # 'total', 'used', 'free'
)

# Middleware para recopilar métricas de las peticiones
async def metrics_middleware(request: Request, call_next: Callable) -> Response:
    method = request.method
    endpoint = request.url.path
    
    # Incrementar contador de peticiones en proceso
    IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()
    
    # Medir tiempo de respuesta
    start_time = time.time()
    
    try:
        response = await call_next(request)
        status_code = response.status_code
        
    except Exception as e:
        # Capturar excepciones y registrarlas
        EXCEPTIONS.labels(exception_type=type(e).__name__).inc()
        raise
    finally:
        # Decrementar contador de peticiones en proceso
        IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()
    
    # Registrar métricas de la petición
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(time.time() - start_time)
    
    return response

# Función para recopilar métricas del sistema
def collect_system_metrics():
    # Métricas de memoria
    memory = psutil.virtual_memory()
    SYSTEM_MEMORY.labels(type='total').set(memory.total)
    SYSTEM_MEMORY.labels(type='available').set(memory.available)
    SYSTEM_MEMORY.labels(type='used').set(memory.used)
    
    # Métricas de CPU
    SYSTEM_CPU.set(psutil.cpu_percent(interval=1))
    
    # Métricas de disco
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            SYSTEM_DISK.labels(mountpoint=partition.mountpoint, type='total').set(usage.total)
            SYSTEM_DISK.labels(mountpoint=partition.mountpoint, type='used').set(usage.used)
            SYSTEM_DISK.labels(mountpoint=partition.mountpoint, type='free').set(usage.free)
        except (PermissionError, FileNotFoundError):
            # Algunos puntos de montaje pueden no ser accesibles
            pass

# Decorador para medir tiempo de consultas a la base de datos
def measure_db_query(query_type):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                DB_QUERY_LATENCY.labels(query_type=query_type).observe(time.time() - start_time)
        return wrapper
    return decorator

# Registrar métricas de pool de conexiones
def update_db_pool_metrics(pool):
    if hasattr(pool, '_used') and hasattr(pool, '_pool'):
        active = len(pool._used)
        idle = len(pool._pool)
        DB_POOL_CONNECTIONS.labels(state='active').set(active)
        DB_POOL_CONNECTIONS.labels(state='idle').set(idle)
        DB_POOL_CONNECTIONS.labels(state='total').set(active + idle)

# Endpoint para exponer métricas
async def metrics_endpoint(request):
    """Endpoint para exponer métricas de Prometheus."""
    # Actualizar métricas del sistema antes de exportarlas
    collect_system_metrics()
    # Generar las métricas usando REGISTRY directamente
    metrics_data = generate_latest(REGISTRY)    
    # # Crear un registro y recolectar métricas de múltiples procesos
    # registry = CollectorRegistry()
    # multiprocess.MultiProcessCollector(registry)
    
    # # Generar las métricas
    # metrics_data = generate_latest(registry)
    
    # Devolver la respuesta con el tipo de contenido correcto
    return StarletteResponse(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )

def setup_metrics(app: FastAPI):
    """Configura métricas de Prometheus para la aplicación."""
    # Añadir middleware para recopilar métricas
    settings = get_settings()
    if not settings.PROMETHEUS_ENABLED:
        logger.info("Prometheus metrics disabled")
        return
    app.middleware("http")(metrics_middleware)
    
    # Añadir endpoint para exponer métricas
    # app.add_route("/api/metrics", metrics_endpoint) # ya está en routes.py
    
    # Iniciar hilo para recopilar métricas del sistema cada 30 segundos
    if settings.ENVIRONMENT == "production":
        def metrics_collector():
            while True:
                collect_system_metrics()
                time.sleep(30)
        
        collector_thread = threading.Thread(target=metrics_collector, daemon=True)
        collector_thread.start()