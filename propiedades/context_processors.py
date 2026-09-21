from django.conf import settings


def whatsapp(request):
    return {'whatsapp_number': settings.WHATSAPP_NUMBER}


def seguimiento(request):
    """Le dice a las plantillas si este visitante ya dejó su contacto y qué propiedades guardó."""
    from .models import TEXTO_CONSENTIMIENTO
    from .seguimiento import COOKIE_VISITANTE, interesado_actual

    from .seo import datos_inmobiliaria, json_ld
    from .views import zonas_disponibles

    contexto = {
        'dr_es_interesado': False, 'dr_favoritos_ids': [], 'dr_texto_consentimiento': TEXTO_CONSENTIMIENTO,
        'ld_inmobiliaria': json_ld(datos_inmobiliaria(request)),
        'zonas_pie': zonas_disponibles()[:8],
    }
    if COOKIE_VISITANTE not in request.COOKIES:
        return contexto
    interesado = interesado_actual(request)
    if interesado:
        contexto['dr_es_interesado'] = True
        contexto['dr_favoritos_ids'] = list(interesado.favoritos.values_list('propiedad_id', flat=True))
    return contexto
