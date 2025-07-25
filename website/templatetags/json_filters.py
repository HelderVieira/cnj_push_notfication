from django import template

register = template.Library()

@register.filter(name='is_list')
def is_list(value):
    return isinstance(value, list)

@register.filter(name='is_dict')
def is_dict(value):
    return isinstance(value, dict)

@register.simple_tag
def load_json_filters():
    """Dummy tag to ensure the template loads the library."""
    return ""
