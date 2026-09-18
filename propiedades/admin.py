from django.contrib import admin
from .models import Propiedad


@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ('direccion', 'tipo_propiedad', 'estado', 'precio', 'esta_disponible', 'destacado', 'fecha_publicacion')
    list_filter = ('tipo_propiedad', 'estado', 'esta_disponible', 'destacado')
    search_fields = ('direccion', 'descripcion')
    list_editable = ('esta_disponible', 'destacado')
    ordering = ('-fecha_publicacion',)
