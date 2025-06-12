#!/bin/sh

# Aplicar migraciones antes de arrancar el servidor
echo "Aplicando migraciones..."
python manage.py migrate --noinput

# Ejecutar el comando original (Gunicorn)
exec "$@"