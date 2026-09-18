# config/urls.py

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.views.generic import TemplateView

# Importaciones necesarias para servir archivos estáticos
from django.conf import settings
from django.conf.urls.static import static

from propiedades.sitemaps import PropiedadSitemap, PaginasEstaticasSitemap

sitemaps = {
    'propiedades': PropiedadSitemap,
    'paginas': PaginasEstaticasSitemap,
}

urlpatterns = [
    # La URL para el administrador
    path('admin/', admin.site.urls),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    # La URL principal (la home) apunta a la aplicación 'propiedades'
    path('', include('propiedades.urls')),
]

# Configuración CRÍTICA para servir archivos estáticos (CSS, JS, imágenes) en MODO DESARROLLO (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
