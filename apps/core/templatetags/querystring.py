from django import template

register = template.Library()


@register.simple_tag
def querystring(params, **kwargs):
    if params is None:
        return ""
    query = params.copy()
    for key, value in kwargs.items():
        if value is None or value == "":
            query.pop(key, None)
        else:
            query[key] = value
    return query.urlencode()
