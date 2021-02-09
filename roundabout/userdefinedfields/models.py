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
from dateutil import parser

from django.db import models
from django.utils import timezone

# Create your models here.

class Field(models.Model):
    FIELD_TYPES = (
        ('CharField', 'Text Field'),
        ('IntegerField', 'Integer Field'),
        ('DecimalField', 'Decimal Field'),
        ('BooleanField', 'Boolean Field'),
        ('DateField', 'Date Field'),
        ('ChoiceField', 'Dropdown Field'),
    )
    field_name = models.CharField(max_length=255, unique=True, db_index=True)
    field_description = models.CharField(max_length=255, null=False, blank=True)
    field_type = models.CharField(max_length=100, choices=FIELD_TYPES)
    field_default_value = models.CharField(max_length=255, null=False, blank=True)
    choice_field_options = models.JSONField(null=True, blank=True)
    global_for_part_types = models.ManyToManyField('parts.PartType', blank=True, related_name='custom_fields')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('field_name',)

    def __str__(self):
        return self.field_name


class FieldValue(models.Model):
    field_value = models.TextField(null=False, blank=True)
    field = models.ForeignKey(Field, related_name='fieldvalues',
                          on_delete=models.CASCADE, null=False, blank=False)
    inventory = models.ForeignKey('inventory.Inventory', related_name='fieldvalues',
                          on_delete=models.CASCADE, null=True)
    part = models.ForeignKey('parts.Part', related_name='fieldvalues',
                          on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('users.User', related_name='fieldvalues',
                             on_delete=models.SET_NULL, null=True, blank=False)
    is_current = models.BooleanField(default=False)
    is_default_value = models.BooleanField(default=False)

    class Meta:
        ordering = ('field', 'created_at')
        get_latest_by = 'created_at'

    def __str__(self):
        return self.field_value

    @property
    def get_field_value(self):
        #Check if UDF field is a DateField, if so format date for display
        if self.field.field_type == 'DateField':
            try:
                field_value = parser.parse(self.field_value)
                field_value = field_value.strftime("%m-%d-%Y %H:%M:%S")
                return field_value
            except:
                pass

        # Check if field is ChoiceField, set the value to the label if available
        if self.field.field_type == 'ChoiceField':
            try:
                options_list= self.field.choice_field_options['options']

                for option in options_list:
                    if option['value'] == self.field_value and option['label']:
                        print(option['label'])
                        return option['label']
            except:
                pass

        return self.field_value
