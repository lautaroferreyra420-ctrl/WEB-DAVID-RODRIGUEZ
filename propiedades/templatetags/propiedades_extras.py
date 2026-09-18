import re

from django import template

register = template.Library()

_YOUTUBE_RE = re.compile(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([\w-]{11})')
_VIMEO_RE = re.compile(r'vimeo\.com/(\d+)')


@register.filter
def split(value, separator=","):
    """Divide un string por el separador dado. Ej: {{ "a,b,c"|split:"," }}"""
    if not value:
        return []
    return value.split(separator)


@register.filter
def strip(value):
    """Quita espacios en blanco al principio y al final del string."""
    if not value:
        return value
    return value.strip()


@register.filter
def embed_url(value):
    """Convierte un link de YouTube o Vimeo en su URL embebible para <iframe>."""
    if not value:
        return ''
    yt_match = _YOUTUBE_RE.search(value)
    if yt_match:
        return f'https://www.youtube.com/embed/{yt_match.group(1)}'
    vimeo_match = _VIMEO_RE.search(value)
    if vimeo_match:
        return f'https://player.vimeo.com/video/{vimeo_match.group(1)}'
    return value
