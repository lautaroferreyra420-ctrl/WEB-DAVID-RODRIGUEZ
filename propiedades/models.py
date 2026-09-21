# propiedades/models.py

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .utils import optimizar_imagen


class Propiedad(models.Model):
    # --- MODIFICACIONES DE CHOICES PARA FILTROS MÁS LIMPIOS ---
    
    # OPCIONES DE TRANSACCIÓN (Usamos valores cortos y limpios para la lógica de búsqueda)
    OPCIONES_ESTADO = [
        ('Venta', 'En Venta'),
        ('Alquiler', 'En Alquiler'),
        ('Permuta', 'Permuta'),
        ('Emprendimiento', 'Emprendimientos'),
    ]

    # OPCIONES DE TIPO DE PROPIEDAD (Usamos valores limpios para la lógica de búsqueda)
    OPCIONES_TIPO = [
        ('Casa', 'Casa'),
        ('Depto', 'Departamento'), # MODIFICADO: Usamos 'Depto' para valor de BD pero 'Departamento' para etiqueta
        ('Local', 'Local Comercial'),
        ('Terreno', 'Terreno'), # AÑADIDO: Incluimos 'Terreno' como tipo de propiedad común
    ]
    
    OPCIONES_MONEDA = [
        ('USD', 'USD (dólares)'),
        ('ARS', '$ (pesos)'),
    ]

    # --- CAMPOS DE INFORMACIÓN ---
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    slug = models.SlugField(max_length=220, blank=True, verbose_name="URL amigable")
    descripcion = models.TextField(verbose_name="Descripción detallada")
    imagen = models.ImageField(upload_to='propiedades/', blank=True, null=True, verbose_name="Foto principal")
    video_url = models.URLField(
        blank=True, null=True,
        verbose_name="Video (link de YouTube o Vimeo)",
        help_text="Pegá el link del video (recomendado: subirlo a YouTube como 'Oculto' y pegar ese link acá)."
    )
    
    # Campos Numéricos y Financieros
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    moneda = models.CharField(
        max_length=3, choices=OPCIONES_MONEDA, default='USD', verbose_name="Moneda",
        help_text="Los alquileres suelen publicarse en pesos; las ventas, en dólares.",
    )
    dormitorios = models.IntegerField(default=1, verbose_name="Dormitorios")
    ambientes = models.PositiveSmallIntegerField(
        blank=True, null=True, verbose_name="Ambientes",
        help_text="Opcional. Se usa para buscar alquileres por ambientes.",
    )
    metros_cuadrados = models.IntegerField(default=0, verbose_name="M² Construidos")
    banos = models.IntegerField(default=1, verbose_name="Baños")
    
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitud")
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitud")

    link_origen = models.URLField(
        max_length=500, blank=True, verbose_name="Link de origen",
        help_text="Se completa solo cuando la propiedad se importa desde un link. Evita importarla dos veces.",
    )

    # --- CAMPOS DE ESTADO Y FILTRO ---
    tipo_propiedad = models.CharField(max_length=50, choices=OPCIONES_TIPO, default='Casa', verbose_name="Tipo")
    estado = models.CharField(max_length=50, choices=OPCIONES_ESTADO, default='Venta', verbose_name="Estado") # MODIFICADO: Usamos las nuevas OPCIONES_ESTADO
    esta_disponible = models.BooleanField(default=True, verbose_name="Disponible")

    # --- ETIQUETAS QUE SE MUESTRAN EN LA WEB ---
    acepta_permuta = models.BooleanField(default=False, verbose_name="Acepta permuta")
    apto_credito = models.BooleanField(default=False, verbose_name="Apto crédito")
    reservado = models.BooleanField(
        default=False, verbose_name="Reservado",
        help_text="Muestra una banda 'RESERVADA' sobre la foto.",
    )
    vendido = models.BooleanField(
        default=False, verbose_name="Vendido",
        help_text="Muestra una banda 'VENDIDA' sobre la foto. Si querés que deje de aparecer en la web, desmarcá 'Disponible'.",
    )

    # --- CAMPO AÑADIDO PARA LA BÚSQUEDA AVANZADA (AMENIDADES) ---
    # Usaremos un campo de texto simple para las amenidades por ahora.
    # En un proyecto real se usaría un campo ManyToMany.
    amenidades = models.TextField(default='', blank=True, verbose_name="Amenidades (separadas por coma)")
    
    # --- CAMPO AÑADIDO PARA UI (DESTACADO) ---
    destacado = models.BooleanField(default=False, verbose_name="Destacada")
    
    # Campos de Tiempo
    fecha_publicacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Publicación")

    class Meta:
        verbose_name_plural = "Propiedades"

    def __str__(self):
        return f"{self.direccion} - {self.precio_formateado}"

    @property
    def precio_formateado(self):
        """Ej: 'USD 185.000' o '$ 450.000' (punto como separador de miles)."""
        monto = f"{self.precio:,.0f}".replace(",", ".")
        return f"$ {monto}" if self.moneda == 'ARS' else f"USD {monto}"

    @property
    def zona(self):
        """Barrio o localidad: lo que va después de la última coma de la dirección (ej: 'Castelar Norte')."""
        return self.direccion.rsplit(',', 1)[1].strip() if ',' in self.direccion else ''

    @property
    def zona_slug(self):
        return slugify(self.zona)

    def clean(self):
        if self.reservado and self.vendido:
            raise ValidationError("Una propiedad no puede estar a la vez reservada y vendida. Marcá solo una.")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.direccion)[:220]

        if self.imagen:
            imagen_anterior = None
            if self.pk:
                imagen_anterior = Propiedad.objects.filter(pk=self.pk).values_list('imagen', flat=True).first()
            if imagen_anterior != self.imagen.name:
                optimizar_imagen(self.imagen)

        super().save(*args, **kwargs)
        cache.delete('zonas_disponibles')

    def delete(self, *args, **kwargs):
        resultado = super().delete(*args, **kwargs)
        cache.delete('zonas_disponibles')
        return resultado

    def get_absolute_url(self):
        return reverse('detalle_propiedad', args=[self.pk, self.slug])


class FotoPropiedad(models.Model):
    propiedad = models.ForeignKey(Propiedad, related_name='fotos', on_delete=models.CASCADE, verbose_name="Propiedad")
    imagen = models.ImageField(upload_to='propiedades/galeria/', verbose_name="Foto")
    orden = models.PositiveIntegerField(default=0, verbose_name="Orden")

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = "Foto de la galería"
        verbose_name_plural = "Fotos de la galería"

    def save(self, *args, **kwargs):
        if self.imagen:
            imagen_anterior = None
            if self.pk:
                imagen_anterior = FotoPropiedad.objects.filter(pk=self.pk).values_list('imagen', flat=True).first()
            if imagen_anterior != self.imagen.name:
                optimizar_imagen(self.imagen)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Foto de {self.propiedad.direccion}"


class ConsultaPropiedad(models.Model):
    propiedad = models.ForeignKey(Propiedad, related_name='consultas', on_delete=models.CASCADE, verbose_name="Propiedad")
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    email = models.EmailField(verbose_name="Email")
    mensaje = models.TextField(verbose_name="Mensaje")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    atendida = models.BooleanField(default=False, verbose_name="Atendida")

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Consulta por propiedad"
        verbose_name_plural = "Consultas por propiedad"

    def __str__(self):
        return f"{self.nombre} - {self.propiedad.direccion}"


class ModeloSingleton(models.Model):
    """Base para modelos de configuracion de los que solo existe un registro (pk=1)."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ConfiguracionIA(ModeloSingleton):
    """
    Configuracion unica (singleton) con las instrucciones de estilo que se le
    suman al prompt fijo cada vez que se genera una descripcion con IA.
    """
    instrucciones_estilo = models.TextField(
        blank=True,
        default=(
            "No repitas el precio salvo que aporte a la narrativa. "
            "Terminá con una frase que invite a imaginarse viviendo ahí o a dar el siguiente paso, "
            "sin sonar a cliché publicitario."
        ),
        verbose_name="Instrucciones de estilo para la IA",
        help_text=(
            "Ej: 'Somos una inmobiliaria familiar con 20 años en Morón, mencionalo cuando quede natural. "
            "Tono cercano, sin tecnicismos. Evitá la palabra oportunidad.' "
            "Esto se suma a las reglas fijas (nunca inventar datos, longitud corta): no las reemplaza."
        ),
    )
    actualizado = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Configuración de IA"
        verbose_name_plural = "Configuración de IA"

    def __str__(self):
        return "Configuración de IA"


class ConfiguracionSitio(ModeloSingleton):
    """
    Configuracion unica (singleton) con datos generales del sitio: por ahora,
    la barra de estadisticas del inicio (numero + etiqueta, hasta 3). Si los tres
    numeros estan vacios, la barra no se muestra.
    """
    estadistica_1_numero = models.PositiveIntegerField(blank=True, null=True, verbose_name="Estadística 1: número")
    estadistica_1_etiqueta = models.CharField(max_length=60, blank=True, default='', verbose_name="Estadística 1: etiqueta")

    estadistica_2_numero = models.PositiveIntegerField(blank=True, null=True, verbose_name="Estadística 2: número")
    estadistica_2_etiqueta = models.CharField(max_length=60, blank=True, default='', verbose_name="Estadística 2: etiqueta")

    estadistica_3_numero = models.PositiveIntegerField(blank=True, null=True, verbose_name="Estadística 3: número")
    estadistica_3_etiqueta = models.CharField(max_length=60, blank=True, default='', verbose_name="Estadística 3: etiqueta")

    # Datos que aparecen en la Política de privacidad
    razon_social = models.CharField(max_length=150, blank=True, verbose_name="Razón social")
    cuit = models.CharField(max_length=20, blank=True, verbose_name="CUIT")
    domicilio_legal = models.CharField(max_length=200, blank=True, verbose_name="Domicilio legal")
    email_privacidad = models.EmailField(
        blank=True, verbose_name="Email para consultas de privacidad",
        help_text="Donde las personas piden ver, corregir o borrar sus datos. Si lo dejás vacío se usa info@davidrodriguezprop.com.",
    )

    class Meta:
        verbose_name = "Configuración del sitio"
        verbose_name_plural = "Configuración del sitio"

    def __str__(self):
        return "Configuración del sitio"

    def estadisticas(self):
        """Devuelve solo las estadisticas que tienen un numero cargado."""
        candidatas = [
            (self.estadistica_1_numero, self.estadistica_1_etiqueta),
            (self.estadistica_2_numero, self.estadistica_2_etiqueta),
            (self.estadistica_3_numero, self.estadistica_3_etiqueta),
        ]
        return [
            {'numero': numero, 'etiqueta': etiqueta}
            for numero, etiqueta in candidatas
            if numero is not None
        ]


from .models_interesados import *  # noqa: E402,F401,F403
from .models_contenido import *  # noqa: E402,F401,F403
