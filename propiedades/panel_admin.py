"""Datos del panel de inicio del administrador y contador de consultas para el menú lateral."""
from urllib.parse import quote

from django.urls import reverse

from .models import ConsultaPropiedad, Interesado, Propiedad, SolicitudTasacion


def consultas_pendientes(request):
    """Número que aparece junto a «Consultas por propiedad» en el menú (vacío si no hay pendientes)."""
    cantidad = ConsultaPropiedad.objects.filter(atendida=False).count()
    return str(cantidad) if cantidad else ""


def tasaciones_pendientes(request):
    cantidad = SolicitudTasacion.objects.filter(atendida=False).count()
    return str(cantidad) if cantidad else ""


def _lista(nombre_modelo, filtro=''):
    url = reverse(f'admin:propiedades_{nombre_modelo}_changelist')
    return f'{url}?{filtro}' if filtro else url


def dashboard_callback(request, context):
    interesados = list(
        Interesado.objects.prefetch_related('visitantes__visitas__propiedad', 'favoritos', 'alertas')
    )
    calientes = [i for i in interesados if i.temperatura() == 'caliente' and not i.baja][:6]

    for i in calientes:
        numero = i.telefono_whatsapp()
        vistas = sorted(i.visitas(), key=lambda v: v.ultima, reverse=True)
        i.enlace_whatsapp = (
            f"https://wa.me/{numero}?text=" + quote(
                f"Hola{' ' + i.nombre if i.nombre else ''}, te escribimos de David Rodríguez Propiedades."
                + (f" Vimos que te interesó la propiedad en {vistas[0].propiedad.direccion}." if vistas else "")
            )
        ) if numero else ''
        i.resumen_vistas = ', '.join(f"{v.propiedad.direccion} ({v.veces})" for v in vistas[:2])

    context.update({
        'kpis': [
            {
                'titulo': 'Propiedades publicadas', 'icono': 'storefront',
                'valor': Propiedad.objects.filter(esta_disponible=True).count(),
                'url': _lista('propiedad', 'esta_disponible__exact=1'),
            },
            {
                'titulo': 'Borradores sin publicar', 'icono': 'edit_note',
                'valor': Propiedad.objects.filter(esta_disponible=False).count(),
                'url': _lista('propiedad', 'esta_disponible__exact=0'),
            },
            {
                'titulo': 'Consultas sin atender', 'icono': 'mark_email_unread',
                'valor': ConsultaPropiedad.objects.filter(atendida=False).count(),
                'url': _lista('consultapropiedad', 'atendida__exact=0'),
            },
            {
                'titulo': 'Tasaciones pendientes', 'icono': 'request_quote',
                'valor': SolicitudTasacion.objects.filter(atendida=False).count(),
                'url': _lista('solicitudtasacion', 'atendida__exact=0'),
            },
            {
                'titulo': 'Interesados nuevos', 'icono': 'person_add',
                'valor': sum(1 for i in interesados if i.estado == 'nuevo'),
                'url': _lista('interesado', 'estado__exact=nuevo'),
            },
        ],
        'acciones': [
            {'titulo': 'Agregar propiedad', 'icono': 'add_home', 'url': reverse('admin:propiedades_propiedad_add')},
            {'titulo': 'Importar desde un link', 'icono': 'add_link', 'url': reverse('admin:propiedades_propiedad_add') + '#importar-link'},
            {'titulo': 'Ver interesados', 'icono': 'groups', 'url': _lista('interesado')},
            {'titulo': 'Ver la web', 'icono': 'open_in_new', 'url': '/', 'nueva_pestana': True},
        ],
        'ultimas_consultas': ConsultaPropiedad.objects.select_related('propiedad').order_by('-fecha')[:6],
        'interesados_calientes': calientes,
        'url_consultas': _lista('consultapropiedad'),
        'url_interesados': _lista('interesado'),
    })
    return context
