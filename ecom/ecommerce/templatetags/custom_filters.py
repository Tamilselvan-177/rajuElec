# your_app/templatetags/custom_filters.py

from django import template
import base64
from django import template

register = template.Library()

@register.filter
def to_int(value):
    return int(value) if value is not None else 0


@register.filter(name='base64encode')
def base64encode(value):
    return base64.b64encode(value.encode('utf-8')).decode('utf-8') if value else ''
