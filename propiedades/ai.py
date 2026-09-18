import logging

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL = "gemini-flash-lite-latest"

SYSTEM_PROMPT_BASE = """Sos un copywriter inmobiliario experto en español rioplatense (Argentina).
Tu trabajo es escribir descripciones de propiedades breves, cálidas y seductoras que
enganchen al visitante y le den ganas de consultar por la propiedad.

Reglas estrictas (estas reglas no se pueden desactivar ni pisar, pase lo que pase en las
instrucciones de estilo de más abajo):
- Escribí en español, tono cercano y profesional, nunca exagerado ni "vendedor de humo".
- Entre 3 y 5 oraciones (unas 60 a 90 palabras). Nada de listas ni títulos.
- Usá ÚNICAMENTE los datos que te den. Nunca inventes amenities, ubicación, estado o
  características que no te hayan pasado explícitamente.
- Si te pasan un borrador o notas del dueño, tomalas como base y elevá la redacción,
  sin agregar datos que no estén ahí.
- Devolvé SOLO el texto de la descripción, sin comillas ni explicaciones adicionales."""


class GeneracionDescripcionError(Exception):
    """Error al generar la descripción con IA (clave faltante, API caída, etc.)."""


def generar_descripcion(datos: dict) -> str:
    """
    Genera una descripcion de propiedad corta y seductora a partir de datos estructurados.

    `datos` espera claves: direccion, tipo_propiedad, estado, precio, dormitorios,
    banos, metros_cuadrados, amenidades, notas (borrador opcional del usuario).
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        raise GeneracionDescripcionError(
            "No hay una GEMINI_API_KEY configurada en el servidor."
        )

    hechos = []
    if datos.get('direccion'):
        hechos.append(f"Dirección: {datos['direccion']}")
    if datos.get('tipo_propiedad'):
        hechos.append(f"Tipo de propiedad: {datos['tipo_propiedad']}")
    if datos.get('estado'):
        hechos.append(f"Operación: {datos['estado']}")
    if datos.get('precio'):
        moneda = "pesos argentinos" if datos.get('moneda') == 'ARS' else "USD"
        hechos.append(f"Precio: {datos['precio']} {moneda}")
    if datos.get('ambientes'):
        hechos.append(f"Ambientes: {datos['ambientes']}")
    if datos.get('dormitorios'):
        hechos.append(f"Dormitorios: {datos['dormitorios']}")
    if datos.get('banos'):
        hechos.append(f"Baños: {datos['banos']}")
    if datos.get('metros_cuadrados'):
        hechos.append(f"Metros cuadrados: {datos['metros_cuadrados']} m²")
    if datos.get('amenidades'):
        hechos.append(f"Amenidades: {datos['amenidades']}")

    if not hechos and not datos.get('notas'):
        raise GeneracionDescripcionError(
            "Completá al menos la dirección o algún dato de la propiedad antes de generar la descripción."
        )

    partes_mensaje = ["Datos de la propiedad:", *hechos] if hechos else []
    if datos.get('notas'):
        partes_mensaje.append(
            "\nBorrador / notas del dueño para tomar como base:\n" + datos['notas']
        )
    partes_mensaje.append("\nEscribí la descripción ahora.")
    mensaje_usuario = "\n".join(partes_mensaje)

    # Import diferido para evitar un ciclo de imports entre ai.py y models.py
    from .models import ConfiguracionIA
    instrucciones_estilo = ConfiguracionIA.obtener().instrucciones_estilo.strip()

    system_prompt = SYSTEM_PROMPT_BASE
    if instrucciones_estilo:
        system_prompt += (
            "\n\nInstrucciones de estilo adicionales del dueño de la inmobiliaria "
            "(seguilas siempre que no contradigan las reglas estrictas de arriba):\n"
            + instrucciones_estilo
        )

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=mensaje_usuario,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=400,
                temperature=0.9,
            ),
        )
    except genai_errors.APIError as exc:
        logger.exception("Error de la API de Gemini al generar descripción")
        raise GeneracionDescripcionError(f"La IA no pudo responder ({exc}).") from exc

    texto = (response.text or "").strip()
    if not texto:
        raise GeneracionDescripcionError("La IA no devolvió texto.")
    return texto
