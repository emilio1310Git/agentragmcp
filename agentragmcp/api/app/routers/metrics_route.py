from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from prometheus_client import Gauge
from senfast.api.app.db import database

# router = APIRouter(prefix="/metrics", tags=["Metrics"])

router = APIRouter(prefix="/metrics", tags=["Metrics"])

# Métricas adicionales
db_up = Gauge("senfast_db_up", "Database up status (1=UP, 0=DOWN)")
db_pool_size = Gauge("senfast_db_pool_size", "Current pool size")

@router.get("/", summary="Exporta métricas Prometheus")
def metrics():
    pool = database.get_connection_pool()
    try:
        with database.get_db_connection() as conn:
            db_up.set(1)
    except Exception:
        db_up.set(0)
    db_pool_size.set(1 if pool else 0)
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/debug_metrics", include_in_schema=False)
async def debug_metrics():
    """Endpoint para depurar métricas."""
   
    # Crear una métrica de prueba garantizada
    test_metric = Gauge('senfast_debug_metric', 'Debug metric')
    test_metric.set(42)  # Establecer un valor fijo
    
    # Intentar generar las métricas
    try:
        metrics_data = generate_latest(REGISTRY)
        return {
            "metrics_available": True,
            "metrics_count": len(metrics_data.splitlines()) if metrics_data else 0,
            "metrics_sample": metrics_data[:500].decode('utf-8') if metrics_data else "No metrics",
            "registry_collectors": str(list(REGISTRY._collector_to_names.keys()))
        }
    except Exception as e:
        return {
            "metrics_available": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    