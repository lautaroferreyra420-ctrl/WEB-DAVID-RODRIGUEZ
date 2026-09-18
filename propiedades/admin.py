from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from .ai import generar_descripcion, GeneracionDescripcionError
from .models import Propiedad, FotoPropiedad, ConsultaPropiedad, ConfiguracionIA, ConfiguracionSitio


class ModeloSingletonAdminMixin:
    """Panel único: no se puede agregar ni borrar, se salta directo a la edición."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        self.model.obtener()
        opts = self.model._meta
        return redirect(reverse(f'admin:{opts.app_label}_{opts.model_name}_change', args=[1]))


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

    class Media:
        css = {'all': ('css/admin_generar_descripcion.css',)}
        js = ('js/admin_generar_descripcion.js',)

    def vista_previa(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:45px; border-radius:4px;">', obj.imagen.url)
        return "—"
    vista_previa.short_description = "Foto"

    def get_urls(self):
        urls = [
            path(
                'generar-descripcion-ia/',
                self.admin_site.admin_view(self.generar_descripcion_ia_view),
                name='propiedades_propiedad_generar_descripcion_ia',
            ),
        ]
        return urls + super().get_urls()

    def generar_descripcion_ia_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido.'}, status=405)

        datos = {campo: request.POST.get(campo, '').strip() for campo in (
            'direccion', 'tipo_propiedad', 'estado', 'precio',
            'dormitorios', 'banos', 'metros_cuadrados', 'amenidades', 'notas',
        )}

        try:
            descripcion = generar_descripcion(datos)
        except GeneracionDescripcionError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        return JsonResponse({'descripcion': descripcion})


@admin.register(ConsultaPropiedad)
class ConsultaPropiedadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'propiedad', 'fecha', 'atendida')
    list_filter = ('atendida', 'fecha')
    list_editable = ('atendida',)
    search_fields = ('nombre', 'email', 'mensaje', 'propiedad__direccion')
    ordering = ('-fecha',)
    readonly_fields = ('propiedad', 'nombre', 'email', 'mensaje', 'fecha')


@admin.register(ConfiguracionIA)
class ConfiguracionIAAdmin(ModeloSingletonAdminMixin, admin.ModelAdmin):
    fields = ('instrucciones_estilo', 'actualizado')
    readonly_fields = ('actualizado',)


@admin.register(ConfiguracionSitio)
class ConfiguracionSitioAdmin(ModeloSingletonAdminMixin, admin.ModelAdmin):
    fieldsets = (
        ('Estadística 1', {'fields': ('estadistica_1_numero', 'estadistica_1_etiqueta')}),
        ('Estadística 2', {'fields': ('estadistica_2_numero', 'estadistica_2_etiqueta')}),
        ('Estadística 3', {'fields': ('estadistica_3_numero', 'estadistica_3_etiqueta')}),
    )
