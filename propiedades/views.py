# propiedades/views.py 
from django.shortcuts import render, get_object_or_404 # << MODIFICADO: Agregamos get_object_or_404
from django.db.models import Q # Importamos Q para búsquedas más complejas (ej. OR)
from .models import Propiedad # Tu modelo ya tiene los campos actualizados

# -----------------------------------------------------------------
# FUNCIÓN PRINCIPAL: LISTA Y BUSCADOR (FILTRADO)
# -----------------------------------------------------------------
def lista_propiedades(request):
    # 1. Base de la consulta: Obtener todas las propiedades
    propiedades = Propiedad.objects.all()
    
    # 2. Obtener los parámetros de búsqueda (los valores de los filtros HTML)
    filtros = request.GET 

    # --- LÓGICA DE FILTRADO ---
    
    # FILTRO 1: TRANSACCIÓN (Estado: Venta/Alquiler)
    estado_seleccionado = filtros.get('estado') # El nombre debe coincidir con el campo HTML
    if estado_seleccionado:
        propiedades = propiedades.filter(estado=estado_seleccionado)

    # FILTRO 2: TIPO DE PROPIEDAD (Múltiples Checkboxes)
    # Usamos getlist para capturar múltiples opciones si es un filtro de checkboxes
    tipos_seleccionados = filtros.getlist('tipo_propiedad') 
    if tipos_seleccionados:
        propiedades = propiedades.filter(tipo_propiedad__in=tipos_seleccionados)

    # FILTRO 3: RANGO DE PRECIO (Características Numéricas)
    try:
        precio_min = filtros.get('precio_min')
        precio_max = filtros.get('precio_max')
        
        if precio_min:
            # __gte: Mayor o igual que (Greater Than or Equal)
            propiedades = propiedades.filter(precio__gte=int(precio_min))
            
        if precio_max:
            # __lte: Menor o igual que (Less Than or Equal)
            propiedades = propiedades.filter(precio__lte=int(precio_max))
            
    except ValueError:
        # Manejo de error si el usuario ingresa texto en lugar de números en los rangos
        pass 

    # FILTRO 4: METROS CUADRADOS MÍNIMOS
    try:
        m2_min = filtros.get('metros_cuadrados_min')
        if m2_min:
            propiedades = propiedades.filter(metros_cuadrados__gte=int(m2_min))
    except ValueError:
        pass
        
    # FILTRO 5: BÚSQUEDA POR TEXTO (Ubicación / Dirección)
    busqueda_texto = filtros.get('ubicacion_texto') # Nombre del campo de texto principal
    if busqueda_texto:
        # Usamos Q para buscar el texto en diferentes campos
        propiedades = propiedades.filter(
            Q(direccion__icontains=busqueda_texto) | 
            Q(descripcion__icontains=busqueda_texto) # Buscamos en dirección O descripción
        )
        
    # --- FIN DE LÓGICA DE FILTRADO ---

    # 3. Ordenar y preparar el contexto
    # Aplicamos el ordenamiento DESPUÉS del filtrado
    propiedades = propiedades.order_by('-fecha_publicacion')
    
    contexto = {
        'propiedades': propiedades,
        'titulo': 'Resultados de Búsqueda'
    }
    
    # 4. Renderiza la plantilla HTML
    # La misma plantilla ahora mostrará la lista filtrada
    return render(request, 'propiedades/lista_propiedades.html', contexto)

# -----------------------------------------------------------------
# FUNCIÓN DE DETALLE DE LA PROPIEDAD (NUEVA FUNCIÓN REQUERIDA)
# -----------------------------------------------------------------
def detalle_propiedad(request, pk):
    # Obtiene la propiedad por su clave primaria (pk) o muestra un error 404
    propiedad = get_object_or_404(Propiedad, pk=pk)
    
    contexto = {
        'propiedad': propiedad,
        'titulo': propiedad.direccion # Usamos la dirección como título de la página
    }
    
    # Renderiza la plantilla HTML que vamos a diseñar ahora
    return render(request, 'propiedades/detalle_propiedad.html', contexto)