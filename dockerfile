# ==========================================================
# Dockerfile para EventHub - Django/Python
# ==========================================================

# ETAPA 1 - Builder
FROM python:3.12-slim as builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install -r requirements.txt

# ETAPA 2 - Runtime
FROM python:3.12-slim

WORKDIR /app

RUN groupadd -r eventhub && useradd -r -g eventhub eventhub && \
    chown eventhub:eventhub /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=eventhub:eventhub . .

ARG DJANGO_SECRET_KEY
ENV DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE="eventhub.settings" \
    SETTINGS_MODULE="eventhub.settings"

RUN chmod -R a+xr /opt/venv

EXPOSE 8000

USER eventhub

COPY --chown=eventhub:eventhub entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/opt/venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "eventhub.wsgi:application"]
