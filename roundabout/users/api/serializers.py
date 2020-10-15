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
from rest_flex_fields import FlexFieldsModelSerializer

from ..models import *

API_VERSION = 'api_v1'

class UserSerializer(FlexFieldsModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name = API_VERSION + ':users-detail',
        lookup_field = 'pk',
    )
    actions = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':actions-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )
    fieldvalues = serializers.HyperlinkedRelatedField(
        view_name = API_VERSION + ':user-defined-fields/field-values-detail',
        many = True,
        read_only = True,
        lookup_field = 'pk',
    )


    class Meta:
        model = User
        fields = [
            'id',
            'url',
            'username',
            'name',
            'email',
            'last_login',
            'is_infield',
            'actions',
            'fieldvalues',
        ]

        expandable_fields = {
            #'parts': ('roundabout.parts.api.serializers.PartSerializer', {'many': True}),
            'actions': ('roundabout.inventory.api.serializers.ActionSerializer', {'many': True}),
            'fieldvalues': ('roundabout.userdefinedfields.api.serializers.FieldValueSerializer', {'many': True}),
        }
