import io
import os

from PIL import Image
from django.core.files.base import ContentFile

ANCHO_MAXIMO = 1600
CALIDAD_JPEG = 82


def optimizar_imagen(imagefield, max_width=ANCHO_MAXIMO, quality=CALIDAD_JPEG):
    """Redimensiona (si hace falta) y comprime una imagen antes de guardarla en el storage."""
    if not imagefield:
        return

    img = Image.open(imagefield)
    es_png_con_transparencia = img.format == 'PNG' and img.mode in ('RGBA', 'LA')
    formato_salida = 'PNG' if es_png_con_transparencia else 'JPEG'

    if formato_salida == 'JPEG' and img.mode != 'RGB':
        img = img.convert('RGB')

    if img.width > max_width:
        nueva_altura = int(img.height * (max_width / float(img.width)))
        img = img.resize((max_width, nueva_altura), Image.LANCZOS)

    buffer = io.BytesIO()
    if formato_salida == 'JPEG':
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
    else:
        img.save(buffer, format='PNG', optimize=True)

    # FieldFile.save() vuelve a aplicar `upload_to` sobre el nombre que le pasemos,
    # así que hay que pasar solo el nombre de archivo (sin la carpeta) para no duplicarla.
    nombre_archivo = os.path.basename(imagefield.name)
    imagefield.save(nombre_archivo, ContentFile(buffer.getvalue()), save=False)
