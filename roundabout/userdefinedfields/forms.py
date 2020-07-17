"""
# Copyright (C) 2019-2020 Woods Hole Oceanographic Institution
#
# This file is part of the Roundabout Database project ("RDB" or 
# "ooicgsn-roundabout").
#
# ooicgsn-roundabout is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# ooicgsn-roundabout is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ooicgsn-roundabout in the COPYING.md file at the project root.
# If not, see <http://www.gnu.org/licenses/>.
"""
import json
from django import forms
from django.contrib.postgres.forms.jsonb import JSONField
from django.core.exceptions import ValidationError

from .models import Field

# Custom field class to format/validate JSON data in textarea with line breaks/delimiters
class CustomJSONTextAreaField(forms.CharField):

    def __init__(self, *args, **kwargs):
        super(CustomJSONTextAreaField, self).__init__(*args, **kwargs)

    def clean(self, value):
        super(CustomJSONTextAreaField, self).clean(value)
        try:
            if value:
                # Split value into list by line breaks
                value_options_list = value.splitlines()
                # Set each option by splitting on the | delimiter
                options = []
                for option in value_options_list:
                    option_list = option.split('|')
                    value = option_list[0]
                    try:
                        label = option_list[1]
                    except:
                        label = None
                    options.append({'value': value, 'label': label})

                value = {'options': options}
                # check if this is valid JSON
                value_check = json.dumps(value)
            return value
        except:
            raise ValidationError('Invalid format. Please use "value|label", one option per line')


class UserDefinedFieldForm(forms.ModelForm):
    choice_field_options = CustomJSONTextAreaField(required=False,
                                                   widget=forms.Textarea(attrs={'cols': 80, 'rows': 8}),
                                                   label='Dropdown Field options',
                                                   help_text='One option per line, use "Value|Label" format if you have separate values and labels \
                                                              (ex: MA|Massachusetts).',)
    class Meta:
        model = Field
        fields = ['field_name', 'field_description', 'field_type', 'choice_field_options',
                  'field_default_value', 'global_for_part_types' ]
        labels = {
            'global_for_part_types': 'Global field for all Parts of this Type',
        }

        widgets = {
            'global_for_part_types': forms.CheckboxSelectMultiple(),
        }

    class Media:
        js = ('js/form-userdefinedfields.js',)

    def __init__(self, *args, **kwargs):
        super(UserDefinedFieldForm, self).__init__(*args, **kwargs)
        # Need to reformat JSON field to text area field with line breaks/delimiters
        if self.instance.pk:
            if self.instance.choice_field_options:
                options_dict = self.instance.choice_field_options
                field_value = ''
                for option in options_dict['options']:
                    line_value = option['value']
                    if option['label']:
                        line_value = line_value + '|' + option['label']
                    line_value = line_value + '\n'
                    field_value = field_value + line_value
                self.initial['choice_field_options'] = field_value
