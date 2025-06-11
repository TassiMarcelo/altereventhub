# ==========================================================
# Dockerfile para EventHub - Django/Python
# Buenas practicas: 
# - Imagen de python slim para reducir tamaño
# - Build en 2 etapas, para reducir tamaño (la 2da etapa tiene lo necesario para correr)
# - Seguridad: usuario no-root
# ==========================================================

# ETAPA 1
# ==========================================================
# Uso esta version de python porque corre en una version de linux modificada para ser mas ligera
FROM python:3.12-slim as builder

# Nombre de la carpeta raiz, donde vamos a estar posicionados
WORKDIR /app

# Variables de entorno (configurables en build)
# No generamos los archivos bytecode de python para ahorrar espacio 
ENV PYTHONDONTWRITEBYTECODE 1
# Consola sin buffer para mayor velocidad de salida
ENV PYTHONUNBUFFERED 1

# Instalar python y sus dependencias
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Copiar requirements a nuestro entorno de trabajo de docker
COPY requirements.txt .

# Actualizar pip y finalmente instalar las dependencias de python
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt


# ETAPA 2
# ==========================================================
FROM python:3.12-slim

WORKDIR /app

# Crear un grupo y un usuario eventhub, (no root) para aumentar la seguridad del servidor
RUN groupadd -r eventhub && useradd -r -g eventhub eventhub && \
    chown eventhub:eventhub /app

# Copiar virtualenv desde builder (ya tiene las dependencias preinstaladas)
COPY --from=builder /opt/venv /opt/venv

# Copiar proyecto (excluyendo lo del .dockerignore)
COPY --chown=eventhub:eventhub . .

# Variables de entorno
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV DJANGO_SETTINGS_MODULE="eventhub.settings"

# Dar permisos de ejecucion al entorno
RUN chmod -R a+xr /opt/venv

# Puerto expuesto (configurable en runtime)
EXPOSE 8000

# Cambiar a usuario no-root
USER eventhub

# Debug
RUN echo $PATH



# Comando de ejecución (sobrescribible en runtime)
# Nota: Para desarrollo, montar volumen y usar "python manage.py runserver 0.0.0.0:8000"
# Para produccion, se utiliza gunicorn (intermediario entre python y las peticiones http mas eficiente)
COPY --chown=eventhub:eventhub entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/opt/venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "eventhub.wsgi:application"]