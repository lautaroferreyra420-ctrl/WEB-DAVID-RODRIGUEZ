from django import template

register = template.Library()


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
