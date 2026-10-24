from django import template

register = template.Library()


@register.filter
def stars(rating):
    """Turn 3.6 into ['full', 'full', 'full', 'half', 'empty'] for star icons."""
    rating = float(rating or 0)
    result = []
    for i in range(1, 6):
        if rating >= i:
            result.append('full')
        elif rating >= i - 0.5:
            result.append('half')
        else:
            result.append('empty')
    return result


@register.simple_tag(takes_context=True)
def url_with(context, **kwargs):
    """Current query string with some values replaced, e.g. {% url_with page=2 %} keeps the filters."""
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        if value in (None, ''):
            query.pop(key, None)
        else:
            query[key] = value
    return f'?{query.urlencode()}' if query else '?'


@register.filter
def get_item(mapping, key):
    """Dictionary lookup with a variable key: {{ counts|get_item:status }}."""
    return mapping.get(key) if hasattr(mapping, 'get') else None


@register.filter
def money(value):
    """Format a price as Rs. 1,250 (no decimals when the value is whole)."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    text = f'{value:,.0f}' if value == int(value) else f'{value:,.2f}'
    return f'Rs. {text}'
