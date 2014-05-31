from django import template

register = template.Library()

@register.filter
def needs_subtable(value):
    """
    Returns True if `value` is a list.

    This is used to render service_result data items in a subtable.
    """
    return isinstance(value, list)
