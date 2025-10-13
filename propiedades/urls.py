# propiedades/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # 1. URL PRINCIPAL (Ahora maneja la lista Y la búsqueda/filtros)
    path('', views.lista_propiedades, name='inicio'),
    
    # 2. URL DE DETALLE (Nueva URL para ver una propiedad específica)
    # <int:pk> permite que la URL se vea así: /propiedades/5/
    path('<int:pk>/', views.detalle_propiedad, name='detalle_propiedad'),

    # 3. URL PARA LA PÁGINA DE CONTACTO (NUEVO)
    path('contacto/', views.pagina_contacto, name='contacto'),
]