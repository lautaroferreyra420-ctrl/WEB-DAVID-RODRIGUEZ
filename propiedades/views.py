import json
import json
import logging

from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.conf import settings
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect

from .models import Propiedad, ConfiguracionSitio
from .forms import ContactoForm, ConsultaPropiedadForm
from .seguimiento import (
    FILTROS_PERMITIDOS, describir_filtros, limpiar_filtros,
    registrar_consulta_como_interesado, registrar_visita,
)

logger = logging.getLogger(__name__)

PROPIEDADES_POR_PAGINA = 12


def _enviar_email_seguro(asunto, cuerpo, destinatario, responder_a=None):
    """
    Envía un email sin romper la vista si el servidor de correo no está configurado o falla.
    `responder_a` es el email del cliente: así "Responder" en la casilla le contesta a él.
    """
    if not settings.EMAIL_HOST_USER:
        logger.warning("Email no enviado (EMAIL_HOST_USER no configurado): %s", asunto)
        return
    try:
        EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario],
            reply_to=[responder_a] if responder_a else None,
        ).send(fail_silently=False)
    except Exception:
        logger.exception("Fallo al enviar email: %s", asunto)


def lista_propiedades(request):
    """
    Esta vista obtiene todas las propiedades disponibles de la base de datos
    y las envía a la plantilla para mostrarlas en una lista.
    """
    # Obtenemos los filtros de la URL (request.GET)
    estado = request.GET.get('estado', '')
    tipo_propiedad = request.GET.get('tipo_propiedad', '')
    ubicacion = request.GET.get('ubicacion_texto', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    metros_min = request.GET.get('metros_cuadrados_min', '')
    ambientes_min = request.GET.get('ambientes_min', '')

    # 1. Empezamos con todas las propiedades disponibles. Esta es nuestra base.
    propiedades = Propiedad.objects.filter(esta_disponible=True)

    # 2. Aplicamos los filtros uno por uno. Esto es clave para el SEO y la funcionalidad.
    if estado:
        # Filtramos por 'Venta', 'Alquiler', etc.
        propiedades = propiedades.filter(estado=estado)
    if tipo_propiedad:
        # Filtramos por 'Casa', 'Depto', etc.
        propiedades = propiedades.filter(tipo_propiedad=tipo_propiedad)
    if ubicacion:
        # Usamos 'icontains' para buscar texto dentro de la dirección (ignora mayúsculas/minúsculas).
        # Esto es perfecto para búsquedas de barrios o ciudades.
        propiedades = propiedades.filter(direccion__icontains=ubicacion)
    if precio_min or precio_max:
        # El rango de precio se interpreta en pesos para Alquiler y en dólares para el resto:
        # así no se comparan montos de monedas distintas.
        if estado:
            propiedades = propiedades.filter(moneda='ARS' if estado == 'Alquiler' else 'USD')
    if precio_min:
        # Filtramos propiedades con precio mayor o igual a...
        propiedades = propiedades.filter(precio__gte=precio_min)
    if precio_max:
        # Filtramos propiedades con precio menor o igual a...
        propiedades = propiedades.filter(precio__lte=precio_max)
    if metros_min:
        # Filtramos propiedades con metros cuadrados mayor o igual a...
        propiedades = propiedades.filter(metros_cuadrados__gte=metros_min)
    if ambientes_min:
        # Filtramos propiedades con ambientes mayor o igual a... (el filtro que se muestra en Alquiler)
        propiedades = propiedades.filter(ambientes__gte=ambientes_min)

    # --- SEO: Construcción de un título dinámico ---
    titulo_partes = []
    if tipo_propiedad:
        titulo_partes.append(tipo_propiedad + 's')  # Ej: "Casas"
    else:
        titulo_partes.append('Propiedades')  # Genérico si no hay tipo

    if estado:
        titulo_partes.append(f"en {estado}")  # Ej: "en Venta"

    if ubicacion:
        titulo_partes.append(f"en {ubicacion}")  # Ej: "en Palermo"

    # Unimos todo para formar el título. Si no hay filtros, será "Propiedades Disponibles"
    titulo_seo = ' '.join(titulo_partes) if titulo_partes else 'Propiedades Disponibles'

    # 3. Paginamos los resultados para no traer cientos de propiedades de una sola vez.
    total_propiedades = propiedades.count()
    paginator = Paginator(propiedades, PROPIEDADES_POR_PAGINA)
    numero_pagina = request.GET.get('page')
    pagina = paginator.get_page(numero_pagina)

    # Armamos la querystring de los filtros actuales para que la paginación no los pierda
    filtros_querystring = request.GET.copy()
    filtros_querystring.pop('page', None)

    # La búsqueda que se está viendo, para ofrecer "avisame cuando entre algo así".
    # Solo tiene sentido si la persona filtró algo (además de la operación) o si no hubo resultados.
    filtros_alerta = limpiar_filtros(request.GET.dict())
    hay_filtros_propios = any(clave != 'estado' for clave in filtros_alerta)

    # La búsqueda que se está viendo, para ofrecer "avisame cuando entre algo así".
    # Solo tiene sentido si la persona filtró algo (además de la operación) o si no hubo resultados.
    filtros_alerta = limpiar_filtros(request.GET.dict())
    hay_filtros_propios = any(clave != 'estado' for clave in filtros_alerta)

    # 4. Creamos el "contexto", que es un diccionario para pasarle datos a la plantilla.
    context = {
        'propiedades': pagina,  # La página actual de resultados
        'total_propiedades': total_propiedades,
        'Propiedad': Propiedad,  # Pasamos la clase del modelo a la plantilla
        'titulo_seo': titulo_seo,  # Pasamos nuestro nuevo título SEO a la plantilla
        'filtros_querystring': filtros_querystring.urlencode(),
        'estadisticas_sitio': ConfiguracionSitio.obtener().estadisticas(),
        'mostrar_alerta': bool(filtros_alerta) and (hay_filtros_propios or total_propiedades == 0),
        'filtros_alerta_json': json.dumps(filtros_alerta),
        'descripcion_alerta': describir_filtros(filtros_alerta),
    }
    # 5. Renderizamos (dibujamos) la plantilla HTML con los datos del contexto.
    return render(request, 'propiedades/lista_propiedades.html', context)


def detalle_propiedad(request, pk, slug=None):
    """
    Esta vista obtiene UNA propiedad específica por su ID (pk), la envía a la
    plantilla para mostrar todos sus detalles y procesa la consulta del interesado.
    """
    propiedad = get_object_or_404(Propiedad, pk=pk)
    if not propiedad.esta_disponible and not request.user.is_staff:
        raise Http404  # los borradores solo los ve el equipo

    # Si el slug de la URL no coincide (o falta), redirigimos a la URL canónica.
    if slug != propiedad.slug:
        return redirect(propiedad.get_absolute_url(), permanent=True)

    mensaje_enviado = False

    if request.method == 'POST':
        form = ConsultaPropiedadForm(request.POST)
        if form.is_valid():
            if not form.es_spam():
                consulta = form.save(commit=False)
                consulta.propiedad = propiedad
                consulta.save()
                registrar_consulta_como_interesado(request, consulta.nombre, consulta.email)

                _enviar_email_seguro(
                    asunto=f"Consulta por propiedad: {propiedad.direccion}",
                    cuerpo=(
                        f"Nombre: {consulta.nombre}\n"
                        f"Email: {consulta.email}\n\n"
                        f"Propiedad: {propiedad.direccion} ({propiedad.get_absolute_url()})\n\n"
                        f"Mensaje:\n{consulta.mensaje}"
                    ),
                    destinatario=settings.EMAIL_DESTINO_CONSULTAS,
                    responder_a=consulta.email,
                )
            # Mostramos éxito igual si era spam, para no delatarle al bot que lo detectamos.
            mensaje_enviado = True
            form = ConsultaPropiedadForm()
    else:
        form = ConsultaPropiedadForm()

    context = {
        'propiedad': propiedad,
        'form': form,
        'mensaje_enviado': mensaje_enviado,
    }

    # 3. Renderizamos la plantilla de detalle.
    respuesta = render(request, 'propiedades/detalle_propiedad.html', context)
    if request.method == 'GET':
        registrar_visita(request, respuesta, propiedad)  # solo si el visitante aceptó las cookies
    return respuesta


def pagina_contacto(request):
    """
    Esta vista simplemente renderiza la página estática de contacto.
    Para el SEO, es bueno tener una página dedicada con información de contacto clara.
    """
    mensaje_enviado = False

    if request.method == 'POST':
        # Si el método es POST, procesamos el formulario
        form = ContactoForm(request.POST)
        if form.is_valid() and not form.es_spam():
            # Si el formulario es válido, enviamos el correo
            cd = form.cleaned_data
            registrar_consulta_como_interesado(
                request, cd['nombre'], cd['email'], cd.get('telefono', ''), origen='contacto',
            )
            asunto = f"Nuevo mensaje de contacto de {cd['nombre']}"
            cuerpo_mensaje = (
                f"Nombre: {cd['nombre']}\n"
                f"Email: {cd['email']}\n"
                f"Teléfono: {cd.get('telefono', 'No proporcionado')}\n\n"
                f"Mensaje:\n{cd['mensaje']}"
            )

            _enviar_email_seguro(asunto, cuerpo_mensaje, settings.EMAIL_DESTINO_CONSULTAS, responder_a=cd['email'])

            mensaje_enviado = True
            form = ContactoForm()  # Limpiamos el formulario después de enviar
    else:
        # Si el método es GET, mostramos un formulario vacío
        form = ContactoForm()

    context = {'form': form, 'mensaje_enviado': mensaje_enviado}
    return render(request, 'propiedades/contacto.html', context)


def pagina_nosotros(request):
    """Pagina institucional: quienes somos, vision, mision y servicios."""
    return render(request, 'propiedades/nosotros.html', {
        'estadisticas_sitio': ConfiguracionSitio.obtener().estadisticas(),
    })
