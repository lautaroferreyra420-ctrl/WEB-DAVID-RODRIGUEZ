"""
Interesados: personas que dejaron su contacto con permiso (guardando una propiedad,
pidiendo alertas, consultando) y el recorrido anónimo de los visitantes que aceptaron cookies.
"""
import re
import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone

from .models import Propiedad

__all__ = ['Interesado', 'Visitante', 'VisitaPropiedad', 'Favorito', 'AlertaBusqueda', 'TEXTO_CONSENTIMIENTO']

# Texto exacto que ve la persona al dar su contacto. Se guarda una copia junto con cada consentimiento.
TEXTO_CONSENTIMIENTO = (
    "Acepto recibir novedades y alertas de David Rodríguez Propiedades por email o WhatsApp. "
    "Puedo darme de baja cuando quiera."
)


class Interesado(models.Model):
    ORIGEN_FAVORITO = 'favorito'
    ORIGEN_ALERTA = 'alerta'
    ORIGEN_POPUP = 'popup'
    ORIGEN_CONSULTA = 'consulta'
    ORIGEN_CONTACTO = 'contacto'
    OPCIONES_ORIGEN = [
        (ORIGEN_FAVORITO, 'Guardó una propiedad'),
        (ORIGEN_ALERTA, 'Pidió alertas de búsqueda'),
        (ORIGEN_POPUP, 'Ventana de novedades'),
        (ORIGEN_CONSULTA, 'Consulta por una propiedad'),
        (ORIGEN_CONTACTO, 'Formulario de contacto'),
    ]
    OPCIONES_ESTADO = [
        ('nuevo', 'Nuevo'),
        ('contactado', 'Contactado'),
        ('cerrado', 'Cerrado'),
    ]

    nombre = models.CharField(max_length=100, blank=True, verbose_name="Nombre")
    email = models.EmailField(blank=True, verbose_name="Email")
    telefono = models.CharField(max_length=30, blank=True, verbose_name="Teléfono / WhatsApp")
    origen = models.CharField(max_length=20, choices=OPCIONES_ORIGEN, default=ORIGEN_POPUP, verbose_name="Cómo llegó")
    estado = models.CharField(max_length=20, choices=OPCIONES_ESTADO, default='nuevo', verbose_name="Estado")
    notas = models.TextField(blank=True, verbose_name="Notas internas")

    # Consentimiento para mandarle novedades (prueba de que dio su permiso)
    acepta_novedades = models.BooleanField(default=False, verbose_name="Aceptó recibir novedades")
    fecha_consentimiento = models.DateTimeField(null=True, blank=True, verbose_name="Fecha del consentimiento")
    consentimiento_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP del consentimiento")
    consentimiento_texto = models.TextField(blank=True, verbose_name="Texto aceptado")

    baja = models.BooleanField(default=False, verbose_name="Se dio de baja")
    fecha_baja = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de baja")
    token_baja = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    creado = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de alta")
    ultima_actividad = models.DateTimeField(default=timezone.now, verbose_name="Última actividad")

    class Meta:
        ordering = ['-ultima_actividad']
        verbose_name = "Interesado"
        verbose_name_plural = "Interesados"
        constraints = [
            models.UniqueConstraint(fields=['email'], condition=~Q(email=''), name='interesado_email_unico'),
        ]

    def __str__(self):
        return self.nombre or self.email or self.telefono or f"Interesado #{self.pk}"

    def puede_recibir_novedades(self):
        return self.acepta_novedades and not self.baja

    def telefono_whatsapp(self):
        """Mejor esfuerzo para pasar un teléfono argentino al formato de wa.me (549 + área + número)."""
        digitos = re.sub(r'\D', '', self.telefono or '')
        if digitos.startswith('00'):
            digitos = digitos[2:]
        if digitos.startswith('54'):
            resto = digitos[2:]
            digitos = '54' + (resto if resto.startswith('9') else '9' + resto)
        else:
            digitos = digitos.lstrip('0')
            if digitos.startswith('1115') and len(digitos) == 12:  # 11 15 XXXX-XXXX
                digitos = '11' + digitos[4:]
            digitos = '549' + digitos
        return digitos if 11 <= len(digitos) <= 15 else ''

    def visitas(self):
        """Visitas a propiedades de todos los dispositivos de esta persona (usa prefetch si está disponible)."""
        return [v for visitante in self.visitantes.all() for v in visitante.visitas.all()]

    def temperatura(self):
        """
        caliente: miró la misma propiedad 3+ veces, 4+ vistas en total o ya consultó.
        tibio: miró 2+ propiedades o guardó algo / pidió una alerta.
        frío: el resto.
        """
        visitas = self.visitas()
        total = sum(v.veces for v in visitas)
        maximo = max((v.veces for v in visitas), default=0)
        if maximo >= 3 or total >= 4 or self.origen in (self.ORIGEN_CONSULTA, self.ORIGEN_CONTACTO):
            return 'caliente'
        if total >= 2 or self.favoritos.all() or self.alertas.all():
            return 'tibio'
        return 'frio'


class Visitante(models.Model):
    """Un navegador anónimo que aceptó las cookies. Solo se une a un Interesado si esa persona deja su contacto."""
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    interesado = models.ForeignKey(
        Interesado, null=True, blank=True, on_delete=models.SET_NULL, related_name='visitantes',
    )
    creado = models.DateTimeField(auto_now_add=True)
    ultima_visita = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Visitante"
        verbose_name_plural = "Visitantes"

    def __str__(self):
        return f"Visitante {str(self.token)[:8]}"


class VisitaPropiedad(models.Model):
    visitante = models.ForeignKey(Visitante, on_delete=models.CASCADE, related_name='visitas')
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='visitas')
    veces = models.PositiveIntegerField(default=1)
    primera = models.DateTimeField(default=timezone.now)
    ultima = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Visita a propiedad"
        verbose_name_plural = "Visitas a propiedades"
        constraints = [
            models.UniqueConstraint(fields=['visitante', 'propiedad'], name='visita_unica_por_propiedad'),
        ]


class Favorito(models.Model):
    interesado = models.ForeignKey(Interesado, on_delete=models.CASCADE, related_name='favoritos')
    propiedad = models.ForeignKey(Propiedad, on_delete=models.CASCADE, related_name='favoritos')
    creado = models.DateTimeField(auto_now_add=True, verbose_name="Guardada el")

    class Meta:
        verbose_name = "Propiedad guardada"
        verbose_name_plural = "Propiedades guardadas"
        constraints = [
            models.UniqueConstraint(fields=['interesado', 'propiedad'], name='favorito_unico'),
        ]

    def __str__(self):
        return f"{self.interesado} guardó {self.propiedad.direccion}"


class AlertaBusqueda(models.Model):
    interesado = models.ForeignKey(Interesado, on_delete=models.CASCADE, related_name='alertas')
    filtros = models.JSONField(default=dict, verbose_name="Filtros")
    descripcion = models.CharField(max_length=250, verbose_name="Búsqueda")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    creado = models.DateTimeField(auto_now_add=True, verbose_name="Creada el")
    ultimo_envio = models.DateTimeField(null=True, blank=True, verbose_name="Último aviso enviado")

    class Meta:
        verbose_name = "Alerta de búsqueda"
        verbose_name_plural = "Alertas de búsqueda"

    def __str__(self):
        return self.descripcion
