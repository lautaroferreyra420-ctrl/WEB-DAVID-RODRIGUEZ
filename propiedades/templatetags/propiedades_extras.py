import re

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_YOUTUBE_RE = re.compile(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([\w-]{11})')
_VIMEO_RE = re.compile(r'vimeo\.com/(\d+)')

_SVG_ATTRS = 'class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'

ICONOS_SVG = {
    'cama': f'<svg {_SVG_ATTRS}><path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v6"/></svg>',
    'bano': f'<svg {_SVG_ATTRS}><path d="M9 6 6.5 3.5a1.5 1.5 0 0 0-2.5 1V17a5 5 0 0 0 5 5h6a5 5 0 0 0 5-5v-2"/><line x1="10" y1="5" x2="8" y2="7"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="7" y1="19" x2="7" y2="21"/><line x1="17" y1="19" x2="17" y2="21"/></svg>',
    'ambientes': f'<svg {_SVG_ATTRS}><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 10h8"/><path d="M11 3v18"/><path d="M11 15h10"/></svg>',
    'area': f'<svg {_SVG_ATTRS}><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>',
    'tipo': f'<svg {_SVG_ATTRS}><path d="M12.6 2.6a2 2 0 0 0-1.4-.6H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4Z"/><circle cx="7.5" cy="7.5" r="1" fill="currentColor" stroke="none"/></svg>',
    'ubicacion': f'<svg {_SVG_ATTRS}><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
}


@register.simple_tag
def icono(nombre):
    """Devuelve el SVG inline de un ícono (cama, bano, area, tipo, ubicacion)."""
    return mark_safe(ICONOS_SVG.get(nombre, ''))


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
        return f'https://www.youtube-nocookie.com/embed/{yt_match.group(1)}'
    vimeo_match = _VIMEO_RE.search(value)
    if vimeo_match:
        return f'https://player.vimeo.com/video/{vimeo_match.group(1)}'
    return value


@register.filter
def preview_embed_url(value):
    """
    Como embed_url, pero armado para reproducirse solo, mudo, en loop y sin
    controles: para el preview que se ve al pasar el mouse sobre una card.
    """
    if not value:
        return ''
    yt_match = _YOUTUBE_RE.search(value)
    if yt_match:
        video_id = yt_match.group(1)
        return (
            f'https://www.youtube-nocookie.com/embed/{video_id}'
            f'?autoplay=1&mute=1&loop=1&playlist={video_id}'
            f'&controls=0&modestbranding=1&rel=0&playsinline=1&showinfo=0'
        )
    vimeo_match = _VIMEO_RE.search(value)
    if vimeo_match:
        video_id = vimeo_match.group(1)
        return (
            f'https://player.vimeo.com/video/{video_id}'
            f'?autoplay=1&muted=1&loop=1&background=1'
        )
    return ''
