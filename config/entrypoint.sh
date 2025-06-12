#!/bin/bash
set -e

# Funciones de utilidad
log() {
  echo "$(date +'%Y-%m-%d %H:%M:%S') - $1"
}

# Manejo de señales mejorado
log "INFO: Iniciando aplicación en entorno $ENVIRONMENT"
trap 'log "INFO: Finalizando aplicación"; exit 0' SIGTERM SIGINT

# Verificar rutas
echo "Rutas disponibles:"
ip route

# Verificar hosts
echo "Contenido de /etc/hosts:"
cat /etc/hosts

# Verificar resolución DNS
echo "Servidores DNS:"
cat /etc/resolv.conf

# Verificación de variables de entorno críticas
if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_NAME" ]; then
  log "ERROR: Variables de entorno de base de datos no configuradas"
  exit 1
fi

log "INFO: Variables de conexión a DB:"
log "  DB_HOST: $DB_HOST"
log "  DB_PORT: $DB_PORT"
log "  DB_NAME: $DB_NAME"

# Verificar conectividad básica
log "Verificando conectividad de red..."
if ping -c 1 -W 2 $DB_HOST >/dev/null 2>&1; then
  log "Ping a $DB_HOST exitoso"
else
  log "ERROR: No se puede hacer ping a $DB_HOST"
fi

# Verificar resolución de nombres
log "Resolviendo nombre de host..."
if nslookup $DB_HOST >/dev/null 2>&1; then
  log "Resolución de nombres exitosa para $DB_HOST"
else
  log "Advertencia: No se pudo resolver $DB_HOST"
fi

# Intentar conexión directa
log "Intentando conexión directa con PostgreSQL..."
timeout 5 bash -c "echo > /dev/tcp/$DB_HOST/$DB_PORT" && log "Conexión TCP exitosa" || log "Conexión TCP fallida"

# Esperar a que los servicios dependientes estén disponibles con timeout
wait_for_oracle() {
  local host=$1
  local port=$2
  local timeout=${3:-120}
  local start_time=$(date +%s)
  local end_time=$((start_time + timeout))

  log "Esperando a Oracle en $host:$port (timeout: ${timeout}s)..."
  while ! (echo > /dev/tcp/$host/$port) >/dev/null 2>&1; do
    current_time=$(date +%s)
    if [ $current_time -ge $end_time ]; then
      log "ERROR: Timeout esperando a Oracle en $host:$port"
      return 1
    fi
    log "Esperando a Oracle..."
    sleep 2
  done
  log "Oracle está disponible en $host:$port"
  return 0
}

# Esperar a la base de datos con timeout
if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
  if ! wait_for_oracle "$DB_HOST" "$DB_PORT" 120; then
    log "ERROR: No se pudo conectar a Oracle"
    exit 1
  fi
fi

# Ejecutar migraciones con manejo de errores
# if [ "$RUN_MIGRATIONS" = "true" ]; then
#   log "Ejecutando migraciones de base de datos..."
#   if ! python -m senfast.core.db.migrations; then
#     log "ERROR: Las migraciones de la base de datos fallaron"
#     exit 1
#   fi
# fi

# Configuración de workers optimizados según el entorno
calculate_workers() {
  local cores=$(nproc)
  local memory=$(free -m | awk '/^Mem:/{print $2}')
  
  # Calcula workers basado en CPU y memoria (2*CPU+1, pero no más de memoria/100MB)
  local cpu_workers=$((cores * 2 + 1))
  local mem_workers=$((memory / 100))
  
  # Usa el menor de los dos valores
  if [ $cpu_workers -lt $mem_workers ]; then
    echo $cpu_workers
  else
    echo $mem_workers
  fi
}

# Calcular workers si no están especificados
if [ -z "$MAX_WORKERS" ]; then
  MAX_WORKERS=$(calculate_workers)
  log "Calculado número óptimo de workers: $MAX_WORKERS"
fi

# Iniciar la aplicación con configuración optimizada
if [ "$ENVIRONMENT" = "production" ]; then
  log "Iniciando en modo producción con $MAX_WORKERS workers"
  # Configurar opciones de Gunicorn para métricas y rendimiento
  PROMETHEUS_MULTIPROC_DIR=${PROMETHEUS_MULTIPROC_DIR:-/tmp}
  export PROMETHEUS_MULTIPROC_DIR
  
  # Limpiar y crear directorio para métricas en modo multiproceso
  rm -rf "$PROMETHEUS_MULTIPROC_DIR"/*
  mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
  # Deshabilitar temporalmente statsd
  STATSD_ENABLED="false"
  
  if [ "$STATSD_ENABLED" = "true" ]; then
    STATSD_OPTIONS="--statsd-host=${STATSD_HOST:-localhost:9125} --statsd-prefix=${STATSD_PREFIX:-senfast}"
  else
    STATSD_OPTIONS=""
  fi

  exec gunicorn \
    --workers $MAX_WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${API_PORT:-8000} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info} \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --graceful-timeout 30 \
    --worker-tmp-dir /dev/shm \
    $STATSD_OPTIONS \
    senfast.api.app.main:app
else
  log "Iniciando en modo desarrollo"
  # Asegurar permiso de escritura en logs
  mkdir -p /app/logs
  chmod 777 /app/logs  
  exec uvicorn \
    senfast.api.app.main:app \
    --host 0.0.0.0 \
    --port ${API_PORT:-8000} \
    --reload \
    --log-level ${LOG_LEVEL:-debug}
fi