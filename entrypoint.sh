#!/bin/sh

# Verificar configuración
echo "Usando DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"

# Aplicar migraciones
echo "Aplicando migraciones..."
python manage.py migrate --noinput


if [ "$DJANGO_ENV" = "production" ] || [ "$DJANGO_SETTINGS_MODULE" = "eventhub.settings" ]; then
    echo "Colectando archivos estáticos..."
    python manage.py collectstatic --noinput
fi

# Ejecutar el comando principal
exec "$@"