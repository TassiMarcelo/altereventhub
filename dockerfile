# ==========================================================
# Dockerfile para EventHub - Django/Python (Versión Corregida)
# ==========================================================

# ETAPA 1 - Builder
FROM python:3.12-slim as builder

WORKDIR /app

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias de compilación
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias Python
COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ETAPA 2 - Runtime
FROM python:3.12-slim

WORKDIR /app

# Configurar usuario no-root
RUN groupadd -r eventhub && useradd -r -g eventhub eventhub && \
    chown eventhub:eventhub /app

# Copiar virtualenv
COPY --from=builder /opt/venv /opt/venv

# Copiar aplicación (excluyendo lo especificado en .dockerignore)
COPY --chown=eventhub:eventhub . .

# SOBRESCRIBIR CUALQUIER CONFIGURACIÓN PREVIA DE SETTINGS
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE="eventhub.settings" \
    SETTINGS_MODULE="eventhub.settings"

# Permisos
RUN chmod -R a+xr /opt/venv

# Puerto
EXPOSE 8000

# Usuario no-root
USER eventhub

# Entrypoint (asegurar permisos)
COPY --chown=eventhub:eventhub entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/opt/venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "eventhub.wsgi:application"]