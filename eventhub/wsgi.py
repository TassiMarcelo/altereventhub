"""
WSGI config for eventhub project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/wsgi/
"""

import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventhub.settings")

# Inicializar Django
django.setup()

# Ejecutar migraciones automáticamente
from django.core.management import call_command
try:
    call_command('migrate', interactive=False)
except Exception as e:
    print(f"Error ejecutando migrate: {e}")

# Obtener la aplicación WSGI
application = get_wsgi_application()