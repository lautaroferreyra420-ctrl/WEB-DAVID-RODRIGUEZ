from django.contrib import admin
from django.utils.html import format_html

from .models import Propiedad, FotoPropiedad, ConsultaPropiedad


class FotoPropiedadInline(admin.TabularInline):
    model = FotoPropiedad
    extra = 3
    fields = ('imagen', 'orden', 'vista_previa')
    readonly_fields = ('vista_previa',)

    def vista_previa(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;">', obj.imagen.url)
        return "—"
    vista_previa.short_description = "Vista previa"


@admin.register(Propiedad)
class PropiedadAdmin(admin.ModelAdmin):
    list_display = ('vista_previa', 'direccion', 'tipo_propiedad', 'estado', 'precio', 'esta_disponible', 'destacado', 'fecha_publicacion')
    list_display_links = ('vista_previa', 'direccion')
    list_filter = ('tipo_propiedad', 'estado', 'esta_disponible', 'destacado')
    search_fields = ('direccion', 'descripcion')
    list_editable = ('esta_disponible', 'destacado')
    ordering = ('-fecha_publicacion',)
    prepopulated_fields = {'slug': ('direccion',)}
    inlines = [FotoPropiedadInline]

    def vista_previa(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:45px; border-radius:4px;">', obj.imagen.url)
        return "—"
    vista_previa.short_description = "Foto"


@admin.register(ConsultaPropiedad)
class ConsultaPropiedadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'propiedad', 'fecha', 'atendida')
    list_filter = ('atendida', 'fecha')
    list_editable = ('atendida',)
    search_fields = ('nombre', 'email', 'mensaje', 'propiedad__direccion')
    ordering = ('-fecha',)
    readonly_fields = ('propiedad', 'nombre', 'email', 'mensaje', 'fecha')
