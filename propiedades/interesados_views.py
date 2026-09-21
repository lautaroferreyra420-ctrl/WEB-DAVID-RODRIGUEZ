import json
import time

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import ConfiguracionSitio, Interesado, Propiedad, Visitante, TEXTO_CONSENTIMIENTO
from .seguimiento import (
    guardar_alerta, guardar_favorito, interesado_actual, limpiar_filtros, normalizar_email,
    obtener_o_crear_interesado, poner_cookie_visitante, solo_digitos, visitante_actual,
)

MAX_REGISTROS_POR_HORA = 8
CLAVE_REGISTROS = 'dr_registros_ts'
ORIGENES = {
    'favorito': Interesado.ORIGEN_FAVORITO,
    'alerta': Interesado.ORIGEN_ALERTA,
    'popup': Interesado.ORIGEN_POPUP,
}


def _json(request):
    try:
        datos = json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return {}
    return datos if isinstance(datos, dict) else {}


def _propiedad(datos):
    try:
        pk = int(datos.get('propiedad_id') or 0)
    except (TypeError, ValueError):
        return None
    return Propiedad.objects.filter(pk=pk, esta_disponible=True).first() if pk else None


@require_POST
def registrar(request):
    """
    Una persona deja su email o WhatsApp con su permiso para: guardar una propiedad,
    recibir alertas de una búsqueda o recibir novedades.
    """
    datos = _json(request)
    if datos.get('website'):  # honeypot: un humano nunca lo completa
        return JsonResponse({'ok': True})

    if datos.get('acepta') is not True:
        return JsonResponse({'error': 'Para continuar tenés que aceptar recibir novedades.'}, status=400)

    email = normalizar_email(datos.get('email'))
    telefono = str(datos.get('telefono', '')).strip()[:30]
    nombre = str(datos.get('nombre', '')).strip()[:100]
    if not email and not telefono:
        return JsonResponse({'error': 'Dejanos tu email o tu WhatsApp.'}, status=400)
    if email:
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'error': 'Revisá el email: no parece válido.'}, status=400)
    if telefono and len(solo_digitos(telefono)) < 8:
        return JsonResponse({'error': 'Revisá el teléfono: tiene que tener al menos 8 números.'}, status=400)

    tipo = datos.get('tipo') if datos.get('tipo') in ORIGENES else 'popup'
    propiedad = _propiedad(datos)
    filtros = limpiar_filtros(datos.get('filtros'))
    if tipo == 'favorito' and not propiedad:
        return JsonResponse({'error': 'No encontré esa propiedad.'}, status=400)
    if tipo in ('alerta', 'popup') and not filtros:
        return JsonResponse({'error': 'No pude armar la búsqueda para avisarte.'}, status=400)

    ahora = time.time()
    recientes = [t for t in request.session.get(CLAVE_REGISTROS, []) if ahora - t < 3600]
    if len(recientes) >= MAX_REGISTROS_POR_HORA:
        return JsonResponse({'error': 'Ya recibimos varios pedidos tuyos. Probá de nuevo en un rato.'}, status=429)
    request.session[CLAVE_REGISTROS] = recientes + [ahora]

    visitante = visitante_actual(request)
    interesado = obtener_o_crear_interesado(
        email, telefono, nombre, ORIGENES[tipo], actual=visitante.interesado if visitante else None,
    )
    # Prueba del consentimiento: cuándo, desde qué IP y qué texto vio
    interesado.acepta_novedades = True
    interesado.fecha_consentimiento = timezone.now()
    interesado.consentimiento_ip = request.META.get('REMOTE_ADDR') or None
    interesado.consentimiento_texto = TEXTO_CONSENTIMIENTO
    interesado.baja = False
    interesado.fecha_baja = None
    interesado.save()

    # Se une este navegador a la persona: así queda todo lo que ya había mirado
    visitante = visitante or Visitante.objects.create()
    if visitante.interesado_id != interesado.pk:
        visitante.interesado = interesado
        visitante.save(update_fields=['interesado'])

    if tipo == 'favorito':
        guardar_favorito(interesado, propiedad)
        mensaje = 'Listo, guardamos la propiedad. Te avisamos si hay novedades.'
    else:
        guardar_alerta(interesado, filtros)
        mensaje = 'Listo, te vamos a avisar cuando entren propiedades como estas.'

    respuesta = JsonResponse({'ok': True, 'mensaje': mensaje, 'tipo': tipo})
    poner_cookie_visitante(respuesta, visitante)  # cookie necesaria para reconocerlo en el servicio que pidió
    return respuesta


@require_POST
def alternar_favorito(request, pk):
    """Guarda o quita una propiedad para quien ya dejó su contacto."""
    interesado = interesado_actual(request)
    if not interesado:
        return JsonResponse({'necesita_datos': True}, status=401)
    propiedad = get_object_or_404(Propiedad, pk=pk, esta_disponible=True)
    favorito = interesado.favoritos.filter(propiedad=propiedad).first()
    if favorito:
        favorito.delete()
        return JsonResponse({'ok': True, 'guardado': False})
    guardar_favorito(interesado, propiedad)
    return JsonResponse({'ok': True, 'guardado': True})


@csrf_exempt  # los mails permiten darse de baja con un solo clic (POST desde el cliente de correo)
def baja(request, token):
    interesado = get_object_or_404(Interesado, token_baja=token)
    if request.method == 'POST':
        interesado.baja = True
        interesado.fecha_baja = timezone.now()
        interesado.save(update_fields=['baja', 'fecha_baja'])
        interesado.alertas.update(activa=False)
    return render(request, 'propiedades/baja.html', {'interesado': interesado, 'listo': interesado.baja})


def privacidad(request):
    config = ConfiguracionSitio.obtener()
    return render(request, 'propiedades/privacidad.html', {
        'config': config,
        'email_privacidad': config.email_privacidad or 'info@davidrodriguezprop.com',
        'texto_consentimiento': TEXTO_CONSENTIMIENTO,
    })
