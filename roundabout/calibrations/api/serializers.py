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

from rest_framework import serializers
from dynamic_rest.serializers import DynamicModelSerializer
from dynamic_rest.fields import DynamicRelationField

from ..models import CalibrationEvent, CoefficientValueSet, CoefficientName, CoefficientNameEvent, CoefficientValue
from roundabout.inventory.api.serializers import InventorySerializer
from roundabout.parts.api.serializers import PartSerializer

class CalibrationEventSerializer(DynamicModelSerializer):
    inventory = DynamicRelationField('InventorySerializer', read_only=True)
    coefficient_value_sets = DynamicRelationField('CoefficientValueSetSerializer', read_only=True, many=True, embed=True)

    class Meta:
        model = CalibrationEvent
        fields = [
            'id',
            'created_at',
            'updated_at',
            'calibration_date',
            'user_draft',
            'user_approver',
            'inventory',
            'deployment',
            'approved',
            'detail',
            'coefficient_value_sets'
        ]


class CoefficientNameEventSerializer(DynamicModelSerializer):
    part = DynamicRelationField('PartSerializer', read_only=True)
    coefficient_names = DynamicRelationField('CoefficientNameSerializer', read_only=True, many=True, embed=True)

    class Meta:
        model = CoefficientNameEvent
        fields = [
            'id',
            'created_at',
            'updated_at',
            'user_draft',
            'user_approver',
            'part',
            'approved',
            'detail',
            'coefficient_names'
        ]


class CoefficientNameSerializer(DynamicModelSerializer):

    class Meta:
        model = CoefficientName
        fields = [
            'id',
            'calibration_name',
            'value_set_type',
            'sigfig_override',
            'created_at',
            'part',
            'coeff_name_event',
        ]


class CoefficientValueSetSerializer(DynamicModelSerializer):
    calibration_event = DynamicRelationField('CalibrationEventSerializer', read_only=True)
    coefficient_name = DynamicRelationField('CoefficientNameSerializer', read_only=True, embed=True)
    coefficient_values = DynamicRelationField('CoefficientValueSerializer', read_only=True, embed=True, many=True)

    class Meta:
        model = CoefficientValueSet
        fields = [
            'id',
            'value_set',
            'notes',
            'created_at',
            'coefficient_name',
            'calibration_event',
            'coefficient_values',
        ]


class CoefficientValueSerializer(DynamicModelSerializer):

    class Meta:
        model = CoefficientValue
        fields = [
            'id',
            'value',
            'original_value',
            'notation_format',
            'sigfig',
            'row',
            'created_at',
            'coeff_value_set',
        ]
