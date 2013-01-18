from django import template
from django.utils.encoding import force_unicode

register = template.Library()

@register.filter
def in_group(user, group):
    return bool(user.is_superuser or user.groups.filter(name__iexact=group))

@register.filter
def has_perm(user, perm):
    return bool(user.is_superuser or user.has_perm(perm))