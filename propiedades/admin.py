import csv
from urllib.parse import quote

from django.contrib import admin, messages
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin, UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .ai import generar_descripcion, GeneracionDescripcionError
from .utils import static_versionado
from .importador import EsListadoError, ImportacionError, importar_propiedad
from .models import (
    Propiedad, FotoPropiedad, ConsultaPropiedad, ConfiguracionIA, ConfiguracionSitio,
    Interesado, Favorito, AlertaBusqueda,
)


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


class FotoPropiedadInline(TabularInline):
    model = FotoPropiedad
    tab = True
    extra = 3
    fields = ('imagen', 'orden', 'vista_previa')
    readonly_fields = ('vista_previa',)

    def vista_previa(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:60px; border-radius:4px;">', obj.imagen.url)
        return "—"
    vista_previa.short_description = "Vista previa"


@admin.register(Propiedad)
class PropiedadAdmin(ModelAdmin):
    list_display = ('vista_previa', 'direccion', 'tipo_propiedad', 'estado', 'precio_lista', 'en_la_web', 'esta_disponible', 'reservado', 'vendido', 'destacado')
    list_display_links = ('vista_previa', 'direccion')
    list_per_page = 25
    compressed_fields = True
    warn_unsaved_form = True
    fieldsets = (
        ("Datos principales", {"classes": ["tab"], "fields": (
            "direccion", "slug", ("tipo_propiedad", "estado"), ("precio", "moneda"),
            ("ambientes", "dormitorios", "banos", "metros_cuadrados"),
        )}),
        ("Descripción", {"classes": ["tab"], "fields": ("descripcion", "amenidades", "video_url")}),
        ("Foto principal", {"classes": ["tab"], "fields": ("imagen",)}),
        ("Estado en la web", {"classes": ["tab"], "fields": (
            "esta_disponible", "destacado", ("acepta_permuta", "apto_credito"), ("reservado", "vendido"),
            "fecha_publicacion", "link_origen",
        )}),
    )
    list_filter = ('tipo_propiedad', 'estado', 'esta_disponible', 'reservado', 'vendido', 'acepta_permuta', 'apto_credito', 'destacado')
    search_fields = ('direccion', 'descripcion')
    list_editable = ('esta_disponible', 'reservado', 'vendido', 'destacado')
    ordering = ('-fecha_publicacion',)
    prepopulated_fields = {'slug': ('direccion',)}
    inlines = [FotoPropiedadInline]

    class Media:
        css = {'all': (
            static_versionado('css/admin_generar_descripcion.css'),
            static_versionado('css/admin_importar_link.css'),
        )}
        js = (
            static_versionado('js/admin_generar_descripcion.js'),
            static_versionado('js/admin_importar_link.js'),
        )

    def vista_previa(self, obj):
        if obj.imagen:
            return format_html('<img src="{}" style="height:45px; border-radius:6px;">', obj.imagen.url)
        return "—"
    vista_previa.short_description = "Foto"

    @display(description="Precio", ordering="precio")
    def precio_lista(self, obj):
        return obj.precio_formateado

    @display(
        description="En la web",
        label={"Publicada": "success", "Reservada": "warning", "Vendida": "danger", "Borrador": "info"},
    )
    def en_la_web(self, obj):
        if not obj.esta_disponible:
            return "Borrador"
        if obj.vendido:
            return "Vendida"
        if obj.reservado:
            return "Reservada"
        return "Publicada"

    def get_urls(self):
        urls = [
            path(
                'generar-descripcion-ia/',
                self.admin_site.admin_view(self.generar_descripcion_ia_view),
                name='propiedades_propiedad_generar_descripcion_ia',
            ),
            path(
                'importar-desde-link/',
                self.admin_site.admin_view(self.importar_desde_link_view),
                name='propiedades_propiedad_importar_desde_link',
            ),
        ]
        return urls + super().get_urls()

    def importar_desde_link_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido.'}, status=405)
        if not self.has_add_permission(request):
            return JsonResponse({'error': 'No tenés permiso para agregar propiedades.'}, status=403)

        # ficha=1: ya se sabe que es la ficha de una propiedad (se está importando un listado de a una).
        # sin_mensajes=1: el resumen lo arma la pantalla, no hace falta un aviso por cada propiedad.
        es_ficha = request.POST.get('ficha') == '1'
        sin_mensajes = request.POST.get('sin_mensajes') == '1'
        try:
            propiedad, avisos = importar_propiedad(
                request.POST.get('link', ''),
                publicar=request.POST.get('publicar') == 'on',
                max_fotos=request.POST.get('max_fotos') or 8,
                detectar_listado=not es_ficha,
            )
        except EsListadoError as listado:
            return JsonResponse({'listado': True, 'fichas': listado.fichas, 'aviso': listado.aviso})
        except ImportacionError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        if sin_mensajes:
            return JsonResponse({
                'ok': True, 'pk': propiedad.pk, 'direccion': propiedad.direccion, 'avisos': avisos,
                'fotos': propiedad.fotos.count() + (1 if propiedad.imagen else 0),
                'publicada': propiedad.esta_disponible,
            })

        estado = "publicada" if propiedad.esta_disponible else "guardada como borrador (no se ve en la web hasta que la marques como Disponible)"
        messages.success(
            request,
            f"Importé «{propiedad.direccion}» con {propiedad.fotos.count() + (1 if propiedad.imagen else 0)} foto(s) y descripción con IA. "
            f"Quedó {estado}. Revisá los datos antes de publicar.",
        )
        for aviso in avisos:
            messages.warning(request, aviso)
        return JsonResponse({'ok': True, 'url': reverse('admin:propiedades_propiedad_change', args=[propiedad.pk])})

    def generar_descripcion_ia_view(self, request):
        if request.method != 'POST':
            return JsonResponse({'error': 'Método no permitido.'}, status=405)

        datos = {campo: request.POST.get(campo, '').strip() for campo in (
            'direccion', 'tipo_propiedad', 'estado', 'precio', 'moneda', 'ambientes',
            'dormitorios', 'banos', 'metros_cuadrados', 'amenidades', 'notas',
        )}

        try:
            descripcion = generar_descripcion(datos)
        except GeneracionDescripcionError as exc:
            return JsonResponse({'error': str(exc)}, status=400)

        return JsonResponse({'descripcion': descripcion})


@admin.register(ConsultaPropiedad)
class ConsultaPropiedadAdmin(ModelAdmin):
    list_display = ('nombre', 'email', 'propiedad', 'fecha', 'atendida')
    list_filter = ('atendida', 'fecha')
    list_editable = ('atendida',)
    search_fields = ('nombre', 'email', 'mensaje', 'propiedad__direccion')
    ordering = ('-fecha',)
    readonly_fields = ('propiedad', 'nombre', 'email', 'mensaje', 'fecha')


@admin.register(ConfiguracionIA)
class ConfiguracionIAAdmin(ModeloSingletonAdminMixin, ModelAdmin):
    fields = ('instrucciones_estilo', 'actualizado')
    readonly_fields = ('actualizado',)


@admin.register(ConfiguracionSitio)
class ConfiguracionSitioAdmin(ModeloSingletonAdminMixin, ModelAdmin):
    fieldsets = (
        ('Estadística 1', {'fields': ('estadistica_1_numero', 'estadistica_1_etiqueta')}),
        ('Estadística 2', {'fields': ('estadistica_2_numero', 'estadistica_2_etiqueta')}),
        ('Estadística 3', {'fields': ('estadistica_3_numero', 'estadistica_3_etiqueta')}),
        ('Datos legales (Política de privacidad)', {
            'description': 'Aparecen en la página /privacidad/. Completalos con los datos reales de la inmobiliaria.',
            'fields': ('razon_social', 'cuit', 'domicilio_legal', 'email_privacidad'),
        }),
    )


# ---------------------------------------------------------------- Interesados

class FavoritoInline(TabularInline):
    model = Favorito
    tab = True
    extra = 0
    fields = ('propiedad', 'creado')
    readonly_fields = ('propiedad', 'creado')
    verbose_name_plural = "Propiedades que guardó"

    def has_add_permission(self, request, obj=None):
        return False


class AlertaBusquedaInline(TabularInline):
    model = AlertaBusqueda
    tab = True
    extra = 0
    fields = ('descripcion', 'activa', 'creado', 'ultimo_envio')
    readonly_fields = ('descripcion', 'creado', 'ultimo_envio')
    verbose_name_plural = "Búsquedas que quiere vigilar"

    def has_add_permission(self, request, obj=None):
        return False


class PropiedadVistaFilter(admin.SimpleListFilter):
    title = "vio la propiedad"
    parameter_name = 'vio'

    def lookups(self, request, model_admin):
        return [(p.pk, p.direccion[:50]) for p in Propiedad.objects.order_by('direccion')[:200]]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(visitantes__visitas__propiedad_id=self.value()).distinct()
        return queryset


class TemperaturaFilter(admin.SimpleListFilter):
    title = "temperatura"
    parameter_name = 'temperatura'

    def lookups(self, request, model_admin):
        return [('caliente', 'Caliente'), ('tibio', 'Tibio'), ('frio', 'Frío')]

    def queryset(self, request, queryset):
        if self.value():
            ids = [i.pk for i in queryset if i.temperatura() == self.value()]
            return queryset.filter(pk__in=ids)
        return queryset


@admin.register(Interesado)
class InteresadoAdmin(ModelAdmin):
    list_display = ('contacto', 'temperatura_visual', 'origen', 'vio', 'guardo', 'busquedas', 'permiso', 'estado', 'ultima_actividad', 'escribirle')
    list_editable = ('estado',)
    list_filter = (TemperaturaFilter, PropiedadVistaFilter, 'estado', 'origen', 'acepta_novedades', 'baja')
    search_fields = ('nombre', 'email', 'telefono')
    date_hierarchy = 'creado'
    inlines = [FavoritoInline, AlertaBusquedaInline]
    actions = ['exportar_csv', 'marcar_contactado']
    compressed_fields = True
    warn_unsaved_form = True
    fieldsets = (
        ('Contacto', {'classes': ['tab'], 'fields': ('nombre', 'email', 'telefono', 'estado', 'notas')}),
        ('Qué miró', {'classes': ['tab'], 'fields': ('historial',)}),
        ('Permiso para escribirle', {'classes': ['tab'], 'fields': (
            'origen', 'acepta_novedades', 'fecha_consentimiento', 'consentimiento_texto', 'consentimiento_ip',
            'baja', 'fecha_baja', 'creado', 'ultima_actividad',
        )}),
    )
    readonly_fields = (
        'historial', 'origen', 'acepta_novedades', 'fecha_consentimiento', 'consentimiento_texto',
        'consentimiento_ip', 'baja', 'fecha_baja', 'creado', 'ultima_actividad',
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('visitantes__visitas__propiedad', 'favoritos', 'alertas')

    @admin.display(description="Contacto", ordering='nombre')
    def contacto(self, obj):
        partes = [p for p in (obj.nombre, obj.email, obj.telefono) if p]
        return format_html('<strong>{}</strong>', partes[0]) if len(partes) == 1 else format_html(
            '<strong>{}</strong><br><span style="color:#777">{}</span>', partes[0], ' · '.join(partes[1:]),
        )

    @display(description="Temperatura", label={"Caliente": "danger", "Tibio": "warning", "Frío": "info"})
    def temperatura_visual(self, obj):
        return {'caliente': 'Caliente', 'tibio': 'Tibio', 'frio': 'Frío'}[obj.temperatura()]

    @admin.display(description="Vio")
    def vio(self, obj):
        visitas = obj.visitas()
        return f"{len(visitas)} prop. ({sum(v.veces for v in visitas)} visitas)" if visitas else "—"

    @admin.display(description="Guardó")
    def guardo(self, obj):
        return len(obj.favoritos.all()) or "—"

    @admin.display(description="Alertas")
    def busquedas(self, obj):
        return len([a for a in obj.alertas.all() if a.activa]) or "—"

    @admin.display(description="Permiso", boolean=True)
    def permiso(self, obj):
        return obj.puede_recibir_novedades()

    @admin.display(description="Escribirle")
    def escribirle(self, obj):
        enlaces = []
        vistas = sorted(obj.visitas(), key=lambda v: v.ultima, reverse=True)
        saludo = f"Hola{' ' + obj.nombre if obj.nombre else ''}, te escribimos de David Rodríguez Propiedades."
        if vistas:
            saludo += f" Vimos que te interesó la propiedad en {vistas[0].propiedad.direccion}. ¿Querés que te pasemos más información?"
        numero = obj.telefono_whatsapp()
        if numero:
            enlaces.append(format_html('<a href="https://wa.me/{}?text={}" target="_blank" rel="noopener">WhatsApp</a>', numero, quote(saludo)))
        if obj.email:
            enlaces.append(format_html('<a href="mailto:{}?subject={}">Mail</a>', obj.email, quote("David Rodríguez Propiedades")))
        return format_html(' · '.join(['{}'] * len(enlaces)), *enlaces) if enlaces else "—"

    @admin.display(description="Propiedades que miró")
    def historial(self, obj):
        visitas = sorted(obj.visitas(), key=lambda v: (v.veces, v.ultima), reverse=True)
        if not visitas:
            return "Todavía no hay recorrido registrado (solo se registra si la persona aceptó las cookies)."
        filas = ''.join(
            format_html(
                '<tr><td><a href="{}">{}</a></td><td style="text-align:center">{}</td><td>{:%d/%m/%Y %H:%M}</td></tr>',
                reverse('admin:propiedades_propiedad_change', args=[v.propiedad_id]),
                v.propiedad.direccion, v.veces, timezone.localtime(v.ultima),
            )
            for v in visitas
        )
        from django.utils.safestring import mark_safe
        return mark_safe(
            '<table class="dr-tabla"><thead><tr><th>Propiedad</th><th>Veces</th><th>Última visita</th></tr></thead><tbody>' + filas + '</tbody></table>'
        )

    @admin.action(description="Exportar los seleccionados a Excel (CSV)")
    def exportar_csv(self, request, queryset):
        respuesta = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        respuesta['Content-Disposition'] = 'attachment; filename="interesados.csv"'
        escritor = csv.writer(respuesta, delimiter=';')
        escritor.writerow(['Nombre', 'Email', 'Teléfono', 'Cómo llegó', 'Temperatura', 'Permiso novedades', 'Baja', 'Propiedades que miró', 'Alta'])
        for i in queryset:
            escritor.writerow([
                i.nombre, i.email, i.telefono, i.get_origen_display(), i.temperatura(),
                'Sí' if i.acepta_novedades else 'No', 'Sí' if i.baja else 'No',
                ' | '.join(f"{v.propiedad.direccion} ({v.veces})" for v in i.visitas()),
                i.creado.strftime('%d/%m/%Y'),
            ])
        return respuesta

    @admin.action(description="Marcar como contactados")
    def marcar_contactado(self, request, queryset):
        cantidad = queryset.update(estado='contactado')
        self.message_user(request, f"{cantidad} interesado(s) marcados como contactados.")


# ---------------------------------------------------------------- Usuarios y grupos (mismo aspecto del panel)

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass
