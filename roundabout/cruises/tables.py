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

import django_tables2 as tables2
from roundabout.inventory.models import Action
from roundabout.search.tables import trunc_render

class ActionData_Column(tables2.Column):
    def __init__(self, field_name, trunc_func=None, **kwargs):
        self.field_name = field_name

        if trunc_func is True: self.trunk_func = trunc_render()
        elif isinstance(trunc_func,dict): self.trunk_func = trunc_render(**trunc_func)
        elif callable(trunc_func): self.trunk_func = trunc_func
        else: self.trunk_func = None

        if 'verbose_name' not in kwargs:
            kwargs['verbose_name'] = ' '.join([s.capitalize() for s in field_name.split('_')])
        super().__init__(accessor='data', default='',**kwargs)

    def render(self,value):
        try:
            val = value['updated_values'][self.field_name]['to']
            if self.trunk_func:
                return self.trunk_func(val)
            return val
        except KeyError:
            return ''
    def value(self,value):
        try: return value['updated_values'][self.field_name]['to']
        except KeyError: return ''


class ActionTableBase(tables2.Table):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"
        attrs = {'style':'display: block; overflow-x: auto;','class':'table table-sm table-striped'}
        model = Action
        orderable = False
        fields = ['created_at','action_type','user']
    created_at = tables2.DateTimeColumn(accessor='created_at', verbose_name='Date')
    def render_user(self,value):
        return value.name or value.username


class VesselActionTable(ActionTableBase):
    class Meta(ActionTableBase.Meta):
        pass
    prefix = ActionData_Column('prefix')
    vessel_designation = ActionData_Column('vessel_designation')
    vessel_name = ActionData_Column('vessel_name')
    ICES_code = ActionData_Column('ICES_code', verbose_name='ICES Code')
    operator =ActionData_Column('operator')
    call_sign = ActionData_Column('call_sign')
    MMSI_number = ActionData_Column('MMSI_number', verbose_name='MMSI Number')
    IMO_number = ActionData_Column('IMO_number', verbose_name='IMO Number')
    length = ActionData_Column('length')
    max_speed = ActionData_Column('max_speed')
    max_draft = ActionData_Column('max_draft')
    designation = ActionData_Column('designation')
    active = ActionData_Column('active')
    R2R = ActionData_Column('R2R', verbose_name='R2R')
    notes = ActionData_Column('notes', trunc_func={'length':50})


class CruiseActionTable(ActionTableBase):
    class Meta(ActionTableBase.Meta):
        pass
    CUID = ActionData_Column('CUID', verbose_name='CUID')
    vessel = ActionData_Column('vessel')
    cruise_start_date = ActionData_Column('cruise_start_date')
    cruise_stop_date = ActionData_Column('cruise_stop_date')
    notes = ActionData_Column('notes', trunc_func={'length':50})
    location = ActionData_Column('location')
