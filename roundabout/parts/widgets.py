from django.forms.widgets import SelectMultiple

from django.template import loader
from django.utils.safestring import mark_safe

from .models import Part
from roundabout.locations.models import Location

class PartParentWidget(SelectMultiple):
    template_name = 'parts/part_parent_widget.html'

    def get_context(self, name, value, attrs):
        context = super(PartParentWidget, self).get_context(name, value, attrs)
        context.update({
            'parts_form_options': Part.objects.filter(parent=None).prefetch_related('children')
        })
        return context

    def render(self, name, value, attrs=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)


class PartLocationWidget(SelectMultiple):
    template_name = 'parts/part_location_widget.html'

    def get_context(self, name, value, attrs):
        context = super(PartLocationWidget, self).get_context(name, value, attrs)
        context.update({
            'locations_form_options': Location.objects.filter(tree_id=2).filter(level__gt=0)
        })
        return context

    def render(self, name, value, attrs=None):
        context = self.get_context(name, value, attrs)
        template = loader.get_template(self.template_name).render(context)
        return mark_safe(template)
