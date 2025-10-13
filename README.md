# Proyecto Inmobiliario - David Rodriguez

Este es un sitio web para la gestión y visualización de propiedades inmobiliarias, desarrollado con Python y Django.

---

## Tecnologías Utilizadas
* Python
* Django
* HTML / CSS

---

## Estructura del Proyecto

Aquí se explica el propósito de las carpetas y archivos más importantes.

* `manage.py`: El script principal de Django para ejecutar comandos.
* `config/`: La carpeta del proyecto principal. Contiene la configuración global (`settings.py`) y las rutas principales (`urls.py`).
* `propiedades/`: Nuestra aplicación de Django. Contiene toda la lógica del negocio inmobiliario (modelos, vistas, etc.).
* `static/`: Contiene los archivos estáticos como CSS, JavaScript e imágenes.
* `.venv/`: La carpeta del entorno virtual (no se sube a GitHub).
* `requirements.txt`: La lista de "ingredientes" (librerías de Python) para que el proyecto funcione.

---

## Diario de Desarrollo (Paso a Paso)

* **10/10/2025:**
    * Se clonó el repositorio y se configuró el entorno de desarrollo local.
    * Se creó el modelo `Propiedad` en `propiedades/models.py` para definir la estructura de datos.
    * Se crearon las vistas `lista_propiedades` y `detalle_propiedad` en `propiedades/views.py`.
    * Se configuraron las URLs de la aplicación en `propiedades/urls.py`.

*(...aquí iremos añadiendo los nuevos pasos que demos...)*