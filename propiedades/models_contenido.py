"""Contenido que carga el equipo desde el admin: solicitudes de tasación, testimonios y equipo."""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .models import Propiedad
from .utils import optimizar_imagen

__all__ = ['SolicitudTasacion', 'Testimonio', 'MiembroEquipo']


class _ConFotoOptimizada(models.Model):
    """Base: la foto se redimensiona y comprime al guardar (igual que las fotos de las propiedades)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.foto:
            anterior = None
            if self.pk:
                anterior = type(self).objects.filter(pk=self.pk).values_list('foto', flat=True).first()
            if anterior != self.foto.name:
                optimizar_imagen(self.foto, max_width=800)
        super().save(*args, **kwargs)


class SolicitudTasacion(models.Model):
    OPCIONES_OBJETIVO = [
        ('vender', 'Quiero venderla'),
        ('alquilar', 'Quiero alquilarla'),
        ('saber', 'Solo quiero saber su precio'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    email = models.EmailField(verbose_name="Email")
    telefono = models.CharField(max_length=30, verbose_name="Teléfono / WhatsApp")
    direccion = models.CharField(max_length=200, verbose_name="Dirección de la propiedad")
    tipo_propiedad = models.CharField(max_length=50, choices=Propiedad.OPCIONES_TIPO, default='Casa', verbose_name="Tipo")
    objetivo = models.CharField(max_length=20, choices=OPCIONES_OBJETIVO, default='saber', verbose_name="Qué quiere hacer")
    metros_cubiertos = models.PositiveIntegerField(null=True, blank=True, verbose_name="M² cubiertos")
    dormitorios = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Dormitorios")
    mensaje = models.TextField(blank=True, verbose_name="Comentarios")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    atendida = models.BooleanField(default=False, verbose_name="Atendida")

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Solicitud de tasación"
        verbose_name_plural = "Solicitudes de tasación"

    def __str__(self):
        return f"{self.nombre} - {self.direccion}"


class Testimonio(_ConFotoOptimizada):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del cliente")
    zona = models.CharField(max_length=100, blank=True, verbose_name="Barrio o localidad", help_text="Ej: Castelar. Es opcional.")
    texto = models.TextField(verbose_name="Testimonio", help_text="Lo que dijo el cliente, con sus palabras y con su permiso.")
    estrellas = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Estrellas (1 a 5)",
    )
    foto = models.ImageField(upload_to='testimonios/', blank=True, null=True, verbose_name="Foto (opcional)")
    activo = models.BooleanField(default=True, verbose_name="Mostrar en la web")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden", help_text="Los números más chicos aparecen primero.")

    class Meta:
        ordering = ['orden', '-id']
        verbose_name = "Testimonio"
        verbose_name_plural = "Testimonios"

    def __str__(self):
        return f"{self.nombre} ({self.estrellas}★)"


class MiembroEquipo(_ConFotoOptimizada):
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    cargo = models.CharField(max_length=100, verbose_name="Cargo", help_text="Ej: Corredor inmobiliario, Martillero público.")
    foto = models.ImageField(upload_to='equipo/', blank=True, null=True, verbose_name="Foto")
    whatsapp = models.CharField(max_length=30, blank=True, verbose_name="WhatsApp (opcional)", help_text="Con código de país, sin + ni espacios. Ej: 5491133405963")
    activo = models.BooleanField(default=True, verbose_name="Mostrar en la web")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden", help_text="Los números más chicos aparecen primero.")

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = "Miembro del equipo"
        verbose_name_plural = "Equipo"

    def __str__(self):
        return self.nombre
