from django.shortcuts import render, get_object_or_404
from .models import Propiedad
from .forms import ContactoForm
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.

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
    if precio_min:
        # Filtramos propiedades con precio mayor o igual a...
        propiedades = propiedades.filter(precio__gte=precio_min)
    if precio_max:
        # Filtramos propiedades con precio menor o igual a...
        propiedades = propiedades.filter(precio__lte=precio_max)
    if metros_min:
        # Filtramos propiedades con metros cuadrados mayor o igual a...
        propiedades = propiedades.filter(metros_cuadrados__gte=metros_min)
    
    
    # --- SEO: Construcción de un título dinámico ---
    # (Esta lógica ya estaba bien, la dejamos como está)
    titulo_partes = []
    if tipo_propiedad:
        titulo_partes.append(tipo_propiedad + 's') # Ej: "Casas"
    else:
        titulo_partes.append('Propiedades') # Genérico si no hay tipo
        
    if estado:
        titulo_partes.append(f"en {estado}") # Ej: "en Venta"
        
    if ubicacion:
        titulo_partes.append(f"en {ubicacion}") # Ej: "en Palermo"
        
    # Unimos todo para formar el título. Si no hay filtros, será "Propiedades Disponibles"
    titulo_seo = ' '.join(titulo_partes) if titulo_partes else 'Propiedades Disponibles'
    
    # 3. Creamos el "contexto", que es un diccionario para pasarle datos a la plantilla.
    context = {
        'propiedades': propiedades, # Ahora pasamos la lista ya filtrada
        'Propiedad': Propiedad, # Pasamos la clase del modelo a la plantilla
        'titulo_seo': titulo_seo, # Pasamos nuestro nuevo título SEO a la plantilla
    }
    # 4. Renderizamos (dibujamos) la plantilla HTML con los datos del contexto.
    return render(request, 'propiedades/lista_propiedades.html', context)


def detalle_propiedad(request, pk):
    """
    Esta vista obtiene UNA propiedad específica por su ID (pk)
    y la envía a la plantilla para mostrar todos sus detalles.
    """
    # 1. Obtenemos la propiedad que corresponde a la ID (pk). Si no la encuentra, da un error 404.
    propiedad = get_object_or_404(Propiedad, pk=pk)

    # 2. Creamos el contexto para pasar la propiedad a la plantilla.
    context = {
        'propiedad': propiedad
    }

    # 3. Renderizamos la plantilla de detalle.
    return render(request, 'propiedades/detalle_propiedad.html', context)


def pagina_contacto(request):
    """
    Esta vista simplemente renderiza la página estática de contacto.
    Para el SEO, es bueno tener una página dedicada con información de contacto clara.
    """
    mensaje_enviado = False

    if request.method == 'POST':
        # Si el método es POST, procesamos el formulario
        form = ContactoForm(request.POST)
        if form.is_valid():
            # Si el formulario es válido, enviamos el correo
            cd = form.cleaned_data
            asunto = f"Nuevo mensaje de contacto de {cd['nombre']}"
            cuerpo_mensaje = (
                f"Nombre: {cd['nombre']}\n"
                f"Email: {cd['email']}\n"
                f"Teléfono: {cd.get('telefono', 'No proporcionado')}\n\n"
                f"Mensaje:\n{cd['mensaje']}"
            )
            
            send_mail(asunto, cuerpo_mensaje, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER])
            
            mensaje_enviado = True
            form = ContactoForm() # Limpiamos el formulario después de enviar
    else:
        # Si el método es GET, mostramos un formulario vacío
        form = ContactoForm()

    context = {'form': form, 'mensaje_enviado': mensaje_enviado}
    return render(request, 'propiedades/contacto.html', context)