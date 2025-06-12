#!/bin/sh

# Fuerza el módulo de settings correcto y muestra debug
export DJANGO_SETTINGS_MODULE="eventhub.settings"
echo "=== CONFIGURACIÓN CONFIRMADA ==="
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "================================"

# Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# Solo colectar estáticos en producción
if [ "$DJANGO_ENV" = "production" ] || [ "$ENVIRONMENT" = "production" ]; then
    echo "Colectando archivos estáticos..."
    python manage.py collectstatic --noinput
fi

# Ejecutar comando principal
exec "$@"