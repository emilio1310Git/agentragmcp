FROM python:3.12-slim AS builder

# Establecer variables de entorno
# ENV ENVIRONMENT=production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1
    
# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /venv \
    && /venv/bin/pip install --no-cache-dir --upgrade pip wheel

# Copiar los archivos de requisitos
COPY ./config/requirements.txt /requirements.txt

# Instalar los requisitos
RUN /venv/bin/pip install --no-cache-dir -r /requirements.txt
# Segunda etapa - imagen final más ligera
FROM python:3.12-slim

# Etiquetas
LABEL maintainer="emilio.sanchez@terrassa.cat" \
      version="1.0" \
      description="senfast API Service" \
      org.opencontainers.image.source="https://git.terrassa.cat/gis/senfast"

# Copiar el entorno virtual desde la etapa de construcción
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    API_PORT=8000 \
    LOG_LEVEL=INFO \
    MAX_WORKERS=4



# Instalar runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    tini \
    iputils-ping \
    dnsutils \
    netcat-openbsd \
    iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates \
    && groupadd -r appuser && useradd -r -g appuser appuser \
    && mkdir -p /app/logs /app/data \
    && chown -R appuser:appuser /app

# Instalar Oracle Instant Client
COPY ./config/instantclient-basic-linux.x64-23.8.0.25.04.zip /tmp/ic.zip
RUN apt-get update && apt-get install -y libaio1 unzip && \
    mkdir -p /opt/oracle && \
    unzip -q /tmp/ic.zip -d /opt/oracle && \
    rm /tmp/ic.zip && \
    ls -l /opt/oracle && \
    ln -s /opt/oracle/instantclient_23_8 /opt/oracle/instantclient
ENV LD_LIBRARY_PATH="/opt/oracle/instantclient"
# Crear y cambiar al directorio de la aplicación
WORKDIR /app
COPY . .
# COPY --chown=appuser:appuser . .
COPY config/entrypoint.sh /app/config/entrypoint.sh
RUN chmod +x /app/config/entrypoint.sh && ls -l /app/config/

# Configurar permisos
# RUN chmod +x config/entrypoint.sh
RUN chmod +x /app/config/entrypoint.sh \
    && python -m compileall /app\
    && mkdir -p /app/logs \
    && chmod 777 /app/logs

RUN mkdir -p /app/logs/senfast && \
    chown -R appuser:appuser /app/logs && \
    chmod -R 777 /app/logs
    
# Cambiar al usuario no root para seguridad
USER appuser

# Exponer puerto
EXPOSE 8000

# Usar tini como init system para manejo de señales
ENTRYPOINT ["/usr/bin/tini", "--", "/app/config/entrypoint.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1