import os
import re

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.utils.safestring import mark_safe

register = template.Library()

_YOUTUBE_RE = re.compile(r'(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/))([\w-]{11})')
_VIMEO_RE = re.compile(r'vimeo\.com/(\d+)')

_SVG_ATTRS = 'class="icono-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'

ICONOS_SVG = {
    'cama': f'<svg {_SVG_ATTRS}><path d="M2 4v16"/><path d="M2 8h18a2 2 0 0 1 2 2v10"/><path d="M2 17h20"/><path d="M6 8v6"/></svg>',
    'bano': f'<svg {_SVG_ATTRS}><path d="M9 6 6.5 3.5a1.5 1.5 0 0 0-2.5 1V17a5 5 0 0 0 5 5h6a5 5 0 0 0 5-5v-2"/><line x1="10" y1="5" x2="8" y2="7"/><line x1="2" y1="12" x2="22" y2="12"/><line x1="7" y1="19" x2="7" y2="21"/><line x1="17" y1="19" x2="17" y2="21"/></svg>',
    'corazon': f'<svg {_SVG_ATTRS}><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
    'campana': f'<svg {_SVG_ATTRS}><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
    'estrella': f'<svg {_SVG_ATTRS}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    'permuta': f'<svg {_SVG_ATTRS}><path d="m16 3 4 4-4 4"/><path d="M20 7H4"/><path d="m8 21-4-4 4-4"/><path d="M4 17h16"/></svg>',
    'credito': f'<svg {_SVG_ATTRS}><path d="M3 22h18"/><path d="M6 18v-7"/><path d="M10 18v-7"/><path d="M14 18v-7"/><path d="M18 18v-7"/><path d="M12 2 3 7h18Z"/></svg>',
    'ambientes': f'<svg {_SVG_ATTRS}><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 10h8"/><path d="M11 3v18"/><path d="M11 15h10"/></svg>',
    'area': f'<svg {_SVG_ATTRS}><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>',
    'tipo': f'<svg {_SVG_ATTRS}><path d="M12.6 2.6a2 2 0 0 0-1.4-.6H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4Z"/><circle cx="7.5" cy="7.5" r="1" fill="currentColor" stroke="none"/></svg>',
    'ubicacion': f'<svg {_SVG_ATTRS}><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>',
}


@register.simple_tag
def static_v(ruta):
    """
    Como {% static %}, pero le suma la fecha de modificación del archivo (?v=...):
    cada vez que cambia el CSS/JS, el navegador lo vuelve a bajar en vez de usar uno viejo.
    """
    url = static(ruta)
    archivo = finders.find(ruta)
    if archivo:
        try:
            url += f"?v={int(os.path.getmtime(archivo))}"
        except OSError:
            pass
    return url


@register.simple_tag
def estrellas(cantidad):
    """Cinco estrellas, con las primeras `cantidad` rellenas (para testimonios)."""
    try:
        cantidad = max(0, min(5, int(cantidad)))
    except (TypeError, ValueError):
        cantidad = 5
    return mark_safe(''.join(
        ICONOS_SVG['estrella'].replace('class="icono-svg"', 'class="icono-svg estrella%s"' % (' llena' if i < cantidad else ''))
        for i in range(5)
    ))


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
