# propiedades/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 1. URL PRINCIPAL (Ahora maneja la lista Y la búsqueda/filtros)
    path('', views.lista_propiedades, name='inicio'),
    
    # 2. URL DE DETALLE (con slug para SEO: /5/casa-en-palermo/)
    path('<int:pk>/<slug:slug>/', views.detalle_propiedad, name='detalle_propiedad'),
    # Compatibilidad con enlaces viejos sin slug (redirige a la URL con slug)
    path('<int:pk>/', views.detalle_propiedad, name='detalle_propiedad_sin_slug'),

    # 3. URL PARA LA PÁGINA DE CONTACTO (NUEVO)
    path('contacto/', views.pagina_contacto, name='contacto'),
]