from django import forms

from .models import Field


class UserDefinedFieldForm(forms.ModelForm):

    class Meta:
        model = Field
        fields = ['field_name', 'field_description', 'field_type', 'field_default_value',
                  'value_is_locked', 'global_for_part_types' ]
        labels = {
            'value_is_locked': 'Lock this field value for all Items',
            'global_for_part_types': 'Global field for all Parts of this Type',
        }
