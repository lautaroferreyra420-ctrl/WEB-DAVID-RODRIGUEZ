"""
Seguimiento de visitantes y alta de interesados, siempre con consentimiento:
- El recorrido (qué propiedades mira cada navegador) solo se guarda si la persona aceptó las cookies.
- Los datos de contacto solo se guardan si la persona los deja ella misma.
"""
import re
import uuid

from django.db.models import F
from django.utils import timezone

from .models import (
    AlertaBusqueda, Favorito, Interesado, Propiedad, Visitante, VisitaPropiedad,
)

COOKIE_VISITANTE = 'dr_vid'
COOKIE_CONSENTIMIENTO = 'dr_consent'
UN_ANIO = 60 * 60 * 24 * 365

FILTROS_PERMITIDOS = (
    'estado', 'tipo_propiedad', 'ubicacion_texto',
    'precio_min', 'precio_max', 'metros_cuadrados_min', 'ambientes_min',
)
_BOTS = re.compile(r'bot|crawl|spider|slurp|preview|monitor|facebookexternalhit|curl|wget|python-requests', re.I)


def es_bot(request):
    return bool(_BOTS.search(request.META.get('HTTP_USER_AGENT', '')))


def acepto_cookies(request):
    return request.COOKIES.get(COOKIE_CONSENTIMIENTO) == 'all'


def visitante_actual(request):
    """El Visitante de este navegador (por su cookie), o None."""
    crudo = request.COOKIES.get(COOKIE_VISITANTE)
    if not crudo:
        return None
    try:
        token = uuid.UUID(crudo)
    except ValueError:
        return None
    return Visitante.objects.filter(token=token).select_related('interesado').first()


def poner_cookie_visitante(response, visitante):
    response.set_cookie(
        COOKIE_VISITANTE, str(visitante.token), max_age=UN_ANIO, httponly=True, samesite='Lax',
    )


def interesado_actual(request):
    visitante = visitante_actual(request)
    return visitante.interesado if visitante else None


def registrar_visita(request, response, propiedad):
    """Suma una visita a `propiedad` para este navegador. No hace nada sin consentimiento de cookies."""
    if not acepto_cookies(request) or es_bot(request) or request.user.is_staff:
        return
    visitante = visitante_actual(request) or Visitante.objects.create()
    ahora = timezone.now()
    visita, creada = VisitaPropiedad.objects.get_or_create(visitante=visitante, propiedad=propiedad)
    if not creada:
        VisitaPropiedad.objects.filter(pk=visita.pk).update(veces=F('veces') + 1, ultima=ahora)
    Visitante.objects.filter(pk=visitante.pk).update(ultima_visita=ahora)
    if visitante.interesado_id:
        Interesado.objects.filter(pk=visitante.interesado_id).update(ultima_actividad=ahora)
    poner_cookie_visitante(response, visitante)


# ---------------------------------------------------------------- interesados

def normalizar_email(valor):
    return (valor or '').strip().lower()


def solo_digitos(valor):
    return re.sub(r'\D', '', valor or '')


def obtener_o_crear_interesado(email='', telefono='', nombre='', origen=Interesado.ORIGEN_POPUP, actual=None):
    """
    Busca por email (o teléfono si no hay email); si no existe lo crea. No pisa datos que ya tenía.
    `actual` es la persona a la que ya está asociado este navegador: si no hay otro email en juego, se reutiliza.
    """
    email = normalizar_email(email)
    interesado = None
    if email:
        interesado = Interesado.objects.filter(email=email).first()
    if not interesado and actual and (not email or not actual.email):
        interesado = actual
    if not interesado and telefono and not email:
        digitos = solo_digitos(telefono)
        interesado = next(
            (i for i in Interesado.objects.filter(email='').exclude(telefono='') if solo_digitos(i.telefono) == digitos),
            None,
        )
    if interesado:
        cambios = []
        if nombre and not interesado.nombre:
            interesado.nombre = nombre[:100]; cambios.append('nombre')
        if telefono and not interesado.telefono:
            interesado.telefono = telefono[:30]; cambios.append('telefono')
        if email and not interesado.email:
            interesado.email = email; cambios.append('email')
        interesado.ultima_actividad = timezone.now(); cambios.append('ultima_actividad')
        interesado.save(update_fields=cambios)
        return interesado
    return Interesado.objects.create(
        email=email, telefono=(telefono or '')[:30], nombre=(nombre or '')[:100], origen=origen,
    )


def registrar_consulta_como_interesado(request, nombre, email, telefono='', origen=Interesado.ORIGEN_CONSULTA):
    """
    Una consulta por el formulario también crea un Interesado, para tener todo en un solo lugar.
    NO cuenta como permiso para mandarle novedades: eso solo se marca con el consentimiento explícito.
    """
    visitante = visitante_actual(request)
    interesado = obtener_o_crear_interesado(
        email, telefono, nombre, origen, actual=visitante.interesado if visitante else None,
    )
    if visitante and visitante.interesado_id != interesado.pk:
        Visitante.objects.filter(pk=visitante.pk).update(interesado=interesado)
    return interesado


# ---------------------------------------------------------------- alertas

def limpiar_filtros(crudos):
    """Se queda solo con los filtros conocidos y valores cortos (viene de la web, no es de fiar)."""
    if not isinstance(crudos, dict):
        return {}
    limpios = {}
    for clave in FILTROS_PERMITIDOS:
        valor = str(crudos.get(clave, '')).strip()[:60]
        if valor:
            limpios[clave] = valor
    return limpios


def describir_filtros(filtros):
    """Texto legible de una búsqueda guardada. Ej: 'Casa en Venta · Castelar · hasta USD 300000'."""
    tipos = dict(Propiedad.OPCIONES_TIPO)
    partes = []
    if filtros.get('tipo_propiedad'):
        partes.append(tipos.get(filtros['tipo_propiedad'], filtros['tipo_propiedad']))
    else:
        partes.append('Propiedades')
    if filtros.get('estado'):
        partes[0] += f" en {filtros['estado']}"
    if filtros.get('ubicacion_texto'):
        partes.append(filtros['ubicacion_texto'])
    moneda = '$' if filtros.get('estado') == 'Alquiler' else 'USD'
    if filtros.get('precio_min') and filtros.get('precio_max'):
        partes.append(f"{moneda} {filtros['precio_min']} a {filtros['precio_max']}")
    elif filtros.get('precio_max'):
        partes.append(f"hasta {moneda} {filtros['precio_max']}")
    elif filtros.get('precio_min'):
        partes.append(f"desde {moneda} {filtros['precio_min']}")
    if filtros.get('ambientes_min'):
        partes.append(f"{filtros['ambientes_min']}+ ambientes")
    if filtros.get('metros_cuadrados_min'):
        partes.append(f"{filtros['metros_cuadrados_min']}+ m²")
    return ' · '.join(partes)[:250]


def guardar_alerta(interesado, filtros):
    """Crea la alerta si esa persona no tiene ya una igual."""
    if not filtros:
        return None
    alerta, _ = AlertaBusqueda.objects.get_or_create(
        interesado=interesado, filtros=filtros,
        defaults={'descripcion': describir_filtros(filtros)},
    )
    return alerta


def guardar_favorito(interesado, propiedad):
    favorito, _ = Favorito.objects.get_or_create(interesado=interesado, propiedad=propiedad)
    return favorito
