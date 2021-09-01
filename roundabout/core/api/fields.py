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

# Fields for outputting Constant Values in serializers.
from __future__ import absolute_import, print_function, unicode_literals

from rest_framework import serializers


class ConstantField(serializers.Field):
    """Return a Constant in the serializer.
    Usage:
        my_field = ConstantField(value='My Value')
    Now, in your serializer.data, the value of 'my_field' will be 'My Value'.
    """

    def __init__(self, value, *args, **kwargs):
        """Set the value to be returned."""
        self._value = value
        kwargs["read_only"] = True

        super(ConstantField, self).__init__(*args, **kwargs)

    def get_attribute(self, obj):  # pylint: disable=W0613
        """Return the value set by the initializer."""
        return self._value

    def to_representation(self, value):
        """Output the constant value."""
        return value
