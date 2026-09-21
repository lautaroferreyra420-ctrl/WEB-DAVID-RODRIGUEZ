from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Propiedad


class PaginasEstaticasSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return ['inicio', 'nosotros', 'tasacion', 'mapa', 'contacto']

    def location(self, item):
        return reverse(item)


class PropiedadSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return Propiedad.objects.filter(esta_disponible=True)

    def location(self, obj):
        return obj.get_absolute_url()


class ZonaSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        from .views import zonas_disponibles
        return [slug for slug, _nombre, _cantidad in zonas_disponibles()]

    def location(self, slug):
        return reverse('zona', args=[slug])
