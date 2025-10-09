# config/urls.py

from django.contrib import admin
from django.urls import path, include 

# Importaciones necesarias para servir archivos estáticos
from django.conf import settings
from django.conf.urls.static import static 

urlpatterns = [
    # La URL para el administrador
    path('admin/', admin.site.urls),
    
    # La URL principal (la home) apunta a la aplicación 'propiedades'
    path('', include('propiedades.urls')), 
]

# Configuración CRÍTICA para servir archivos estáticos (CSS, JS, imágenes) en MODO DESARROLLO (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
