"""Datos estructurados (schema.org / JSON-LD) para que Google entienda la inmobiliaria y cada propiedad."""
import json

from django.templatetags.static import static
from django.utils.safestring import mark_safe

TELEFONO = "+54 11 2200-2755"
EMAIL = "info@davidrodriguezprop.com"
INSTAGRAM = "https://www.instagram.com/davidrodriguezprop"


def json_ld(datos):
    """JSON listo para ir dentro de <script type="application/ld+json"> (escapa lo que podría cerrar el script)."""
    texto = json.dumps(datos, ensure_ascii=False)
    return mark_safe(texto.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026'))


def datos_inmobiliaria(request):
    """La inmobiliaria como negocio local: aparece en el panel de Google con teléfono, dirección y horarios."""
    raiz = f"{request.scheme}://{request.get_host()}"
    return {
        "@context": "https://schema.org",
        "@type": "RealEstateAgent",
        "name": "David Rodríguez Propiedades",
        "url": raiz + "/",
        "logo": raiz + static("img/logo.png"),
        "image": raiz + static("img/logo.png"),
        "telephone": TELEFONO,
        "email": EMAIL,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "Leandro N. Alem 1041",
            "addressLocality": "Morón",
            "addressRegion": "Buenos Aires",
            "addressCountry": "AR",
        },
        "areaServed": "Zona oeste, Buenos Aires",
        "sameAs": [INSTAGRAM],
    }


def datos_propiedad(request, propiedad):
    """La propiedad como aviso inmobiliario: precio, ubicación, características y fotos."""
    raiz = f"{request.scheme}://{request.get_host()}"
    fotos = []
    if propiedad.imagen:
        fotos.append(raiz + propiedad.imagen.url)
    fotos += [raiz + f.imagen.url for f in propiedad.fotos.all()]

    tipo_schema = {'Casa': 'House', 'Depto': 'Apartment', 'Local': 'Place', 'Terreno': 'Landform'}.get(propiedad.tipo_propiedad, 'Place')
    lugar = {
        "@type": tipo_schema,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": propiedad.direccion,
            "addressLocality": propiedad.zona or "Buenos Aires",
            "addressRegion": "Buenos Aires",
            "addressCountry": "AR",
        },
    }
    if propiedad.tipo_propiedad in ('Casa', 'Depto'):
        lugar["numberOfBedrooms"] = propiedad.dormitorios
        lugar["numberOfBathroomsTotal"] = propiedad.banos
    if propiedad.ambientes:
        lugar["numberOfRooms"] = propiedad.ambientes
    if propiedad.metros_cuadrados:
        lugar["floorSize"] = {"@type": "QuantitativeValue", "value": propiedad.metros_cuadrados, "unitCode": "MTK"}
    if propiedad.latitud is not None and propiedad.longitud is not None:
        lugar["geo"] = {"@type": "GeoCoordinates", "latitude": float(propiedad.latitud), "longitude": float(propiedad.longitud)}

    disponibilidad = "https://schema.org/SoldOut" if propiedad.vendido else "https://schema.org/InStock"
    datos = {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "name": f"{propiedad.get_tipo_propiedad_display()} en {propiedad.get_estado_display()}: {propiedad.direccion}",
        "url": request.build_absolute_uri(propiedad.get_absolute_url()),
        "description": propiedad.descripcion[:300],
        "about": lugar,
    }
    if fotos:
        datos["image"] = fotos
    if propiedad.precio:
        datos["offers"] = {
            "@type": "Offer",
            "price": str(int(propiedad.precio)),
            "priceCurrency": propiedad.moneda,
            "availability": disponibilidad,
        }
    return datos
