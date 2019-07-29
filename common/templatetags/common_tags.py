from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter
def get_model_name(value):
    return value.__class__.__name__


@register.filter(name='has_group')
def has_group(user, group_name):
    group =  Group.objects.get(name=group_name)
    return group in user.groups.all()


# Custom filter to get dictionary values by key
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# filter Time at Sea duration field to show Hours/Minutes
@register.filter
def time_at_sea_display(duration):
    total_seconds = int(duration.total_seconds())
    days = total_seconds // (3600 * 24)
    hours = (total_seconds % (3600 * 24)) // 3600
    minutes = (total_seconds % 3600) // 60

    return '{} days {} hours {} min'.format(days, hours, minutes)    
