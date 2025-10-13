# propiedades/models.py

from django.db import models
from django.utils import timezone 

class Propiedad(models.Model):
    # --- MODIFICACIONES DE CHOICES PARA FILTROS MÁS LIMPIOS ---
    
    # OPCIONES DE TRANSACCIÓN (Usamos valores cortos y limpios para la lógica de búsqueda)
    OPCIONES_ESTADO = [
        ('Venta', 'En Venta'),
        ('Alquiler', 'En Alquiler'),
        ('Permuta', 'Permuta'),
    ]

    # OPCIONES DE TIPO DE PROPIEDAD (Usamos valores limpios para la lógica de búsqueda)
    OPCIONES_TIPO = [
        ('Casa', 'Casa'),
        ('Depto', 'Departamento'), # MODIFICADO: Usamos 'Depto' para valor de BD pero 'Departamento' para etiqueta
        ('Local', 'Local Comercial'),
        ('Terreno', 'Terreno'), # AÑADIDO: Incluimos 'Terreno' como tipo de propiedad común
    ]
    
    # --- CAMPOS DE INFORMACIÓN ---
    direccion = models.CharField(max_length=200, verbose_name="Dirección")
    descripcion = models.TextField(verbose_name="Descripción detallada")
    
    # Campos Numéricos y Financieros
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio (USD)")
    dormitorios = models.IntegerField(default=1, verbose_name="Dormitorios")
    metros_cuadrados = models.IntegerField(default=0, verbose_name="M² Construidos")
    banos = models.IntegerField(default=1, verbose_name="Baños")
    
    # --- CAMPOS DE ESTADO Y FILTRO ---
    tipo_propiedad = models.CharField(max_length=50, choices=OPCIONES_TIPO, default='Casa', verbose_name="Tipo")
    estado = models.CharField(max_length=50, choices=OPCIONES_ESTADO, default='Venta', verbose_name="Estado") # MODIFICADO: Usamos las nuevas OPCIONES_ESTADO
    esta_disponible = models.BooleanField(default=True, verbose_name="Disponible")

    # --- CAMPO AÑADIDO PARA LA BÚSQUEDA AVANZADA (AMENIDADES) ---
    # Usaremos un campo de texto simple para las amenidades por ahora.
    # En un proyecto real se usaría un campo ManyToMany.
    amenidades = models.TextField(default='', blank=True, verbose_name="Amenidades (separadas por coma)")
    
    # --- CAMPO AÑADIDO PARA UI (DESTACADO) ---
    destacado = models.BooleanField(default=False, verbose_name="Propiedad Destacada (Rojo en UI)")
    
    # Campos de Tiempo
    fecha_publicacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Publicación")

    class Meta:
        verbose_name_plural = "Propiedades" 

    def __str__(self):
        return f"{self.direccion} - ${self.precio}"