import logging

import anthropic
from django.conf import settings

logger = logging.getLogger(__name__)

MODEL = "claude-opus-5"

SYSTEM_PROMPT = """Sos un copywriter inmobiliario experto en español rioplatense (Argentina).
Tu trabajo es escribir descripciones de propiedades breves, cálidas y seductoras que
enganchen al visitante y le den ganas de consultar por la propiedad.

Reglas estrictas:
- Escribí en español, tono cercano y profesional, nunca exagerado ni "vendedor de humo".
- Entre 3 y 5 oraciones (unas 60 a 90 palabras). Nada de listas ni títulos.
- Usá ÚNICAMENTE los datos que te den. Nunca inventes amenities, ubicación, estado o
  características que no te hayan pasado explícitamente.
- Si te pasan un borrador o notas del dueño, tomalas como base y elevá la redacción,
  sin agregar datos que no estén ahí.
- No repitas el precio salvo que aporte a la narrativa (ej. "una oportunidad a un precio...").
- Terminá con una frase que invite a imaginarse viviendo ahí o a dar el siguiente paso,
  sin sonar a cliché publicitario.
- Devolvé SOLO el texto de la descripción, sin comillas ni explicaciones adicionales."""


class GeneracionDescripcionError(Exception):
    """Error al generar la descripción con IA (clave faltante, API caída, etc.)."""


def generar_descripcion(datos: dict) -> str:
    """
    Genera una descripcion de propiedad corta y seductora a partir de datos estructurados.

    `datos` espera claves: direccion, tipo_propiedad, estado, precio, dormitorios,
    banos, metros_cuadrados, amenidades, notas (borrador opcional del usuario).
    """
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise GeneracionDescripcionError(
            "No hay una ANTHROPIC_API_KEY configurada en el servidor."
        )

    hechos = []
    if datos.get('direccion'):
        hechos.append(f"Dirección: {datos['direccion']}")
    if datos.get('tipo_propiedad'):
        hechos.append(f"Tipo de propiedad: {datos['tipo_propiedad']}")
    if datos.get('estado'):
        hechos.append(f"Operación: {datos['estado']}")
    if datos.get('precio'):
        hechos.append(f"Precio: {datos['precio']} USD")
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

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": mensaje_usuario}],
        )
    except anthropic.APIStatusError as exc:
        logger.exception("Error de la API de Anthropic al generar descripción")
        raise GeneracionDescripcionError(f"La IA no pudo responder ({exc.status_code}).") from exc
    except anthropic.APIConnectionError as exc:
        logger.exception("Error de conexión con la API de Anthropic")
        raise GeneracionDescripcionError("No se pudo conectar con el servicio de IA.") from exc

    texto = "".join(block.text for block in response.content if block.type == "text").strip()
    if not texto:
        raise GeneracionDescripcionError("La IA no devolvió texto.")
    return texto
