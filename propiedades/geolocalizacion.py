"""
Ubica una propiedad en el mapa a partir de su dirección, con el servicio gratuito Nominatim (OpenStreetMap).
Solo se acepta un resultado a nivel calle: un pin en un lugar equivocado engaña al visitante, y es mejor
dejar la propiedad sin pin (se puede cargar a mano en el admin) que mostrarla mal ubicada.
"""
import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal

logger = logging.getLogger(__name__)

NOMINATIM = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "DavidRodriguezPropiedades/1.0 (info@davidrodriguezprop.com)"
PAUSA_ENTRE_PEDIDOS = 1.1   # la política de uso de Nominatim pide como máximo 1 pedido por segundo


def _consultas(direccion):
    """
    Variantes de la búsqueda, de la más exacta a la más simple. Ej: 'Zapiola al 2000, Castelar Norte' ->
    'Zapiola 2000, Castelar Norte, Buenos Aires, Argentina' y luego 'Zapiola 2000, Castelar, Buenos Aires, Argentina'.
    """
    limpia = re.sub(r'\s+al\s+(\d+)', r' \1', direccion, flags=re.I)
    variantes = [f"{limpia}, Buenos Aires, Argentina"]
    if ',' in limpia:
        calle, zona = limpia.rsplit(',', 1)
        zona_simple = re.sub(r'\s+(norte|sur|este|oeste|chico|centro)$', '', zona.strip(), flags=re.I)
        if zona_simple != zona.strip():
            variantes.append(f"{calle}, {zona_simple}, Buenos Aires, Argentina")
    return variantes


def _buscar(consulta):
    parametros = urllib.parse.urlencode({
        'q': consulta, 'format': 'jsonv2', 'addressdetails': 1, 'limit': 1, 'countrycodes': 'ar',
    })
    pedido = urllib.request.Request(f"{NOMINATIM}?{parametros}", headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(pedido, timeout=8) as respuesta:
            resultados = json.loads(respuesta.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        logger.warning("No se pudo consultar Nominatim para %r", consulta)
        return None
    if not resultados or 'road' not in resultados[0].get('address', {}):
        return None   # solo barrio o localidad: no alcanza para ubicar la propiedad
    return Decimal(resultados[0]['lat']).quantize(Decimal('0.000001')), Decimal(resultados[0]['lon']).quantize(Decimal('0.000001'))


def geolocalizar(direccion):
    """Devuelve (latitud, longitud) como Decimal, o None si no se encontró una calle."""
    for indice, consulta in enumerate(_consultas(direccion)):
        if indice:
            time.sleep(PAUSA_ENTRE_PEDIDOS)
        resultado = _buscar(consulta)
        if resultado:
            return resultado
    return None


def ubicar_propiedades(propiedades):
    """Intenta ubicar cada propiedad (que todavía no tenga coordenadas). Devuelve (ubicadas, no_encontradas)."""
    ubicadas, fallidas = [], []
    for propiedad in propiedades:
        if propiedad.latitud is not None and propiedad.longitud is not None:
            continue
        resultado = geolocalizar(propiedad.direccion)
        if resultado:
            propiedad.latitud, propiedad.longitud = resultado
            propiedad.save(update_fields=['latitud', 'longitud'])
            ubicadas.append(propiedad)
        else:
            fallidas.append(propiedad)
        time.sleep(PAUSA_ENTRE_PEDIDOS)
    return ubicadas, fallidas
