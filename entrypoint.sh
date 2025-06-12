#!/bin/sh
set -e  # Detiene el script al primer error

# =============================================
# 1. CONFIGURACIÓN INICIAL Y VERIFICACIONES
# =============================================

# Fuerza el módulo de settings correcto
export DJANGO_SETTINGS_MODULE="eventhub.settings"

# Debug: Mostrar variables importantes
echo "=== CONFIGURACIÓN INICIAL ==="
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "DJANGO_SECRET_KEY: $(if [ -z "$DJANGO_SECRET_KEY" ]; then echo "NO CONFIGURADA"; else echo "CONFIGURADA"; fi)"
echo "============================="

# =============================================
# 2. VERIFICACIÓN DE VARIABLES CRÍTICAS
# =============================================

# Lista de variables requeridas
REQUIRED_VARS="DJANGO_SECRET_KEY"

for var in $REQUIRED_VARS; do
  if [ -z "${!var}" ]; then
    echo "ERROR: La variable $var no está configurada"
    echo "Por favor, configúrala como variable de entorno"
    exit 1
  fi
done

# =============================================
# 3. OPERACIONES DE BASE DE DATOS
# =============================================

echo "Aplicando migraciones..."
python manage.py migrate --noinput

# =============================================
# 4. ARCHIVOS ESTÁTICOS (SOLO PRODUCCIÓN)
# =============================================

if [ "$DJANGO_ENV" = "production" ] || [ "$ENVIRONMENT" = "production" ]; then
    echo "Colectando archivos estáticos..."
    python manage.py collectstatic --noinput
fi

# =============================================
# 5. EJECUCIÓN DEL COMANDO PRINCIPAL
# =============================================

echo "Iniciando la aplicación..."
exec "$@"