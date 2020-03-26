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

from django.utils.html import format_html
from django.urls import reverse
import django_tables2 as tables
from django.db.models import Count
from roundabout.inventory.models import Inventory
from roundabout.locations.models import Location
from roundabout.parts.models import Part, PartType, Revision
from roundabout.userdefinedfields.models import FieldValue
from roundabout.admintools.models import Printer
from roundabout.assemblies.models import AssemblyPart,Assembly
from roundabout.builds.models import Build, BuildAction
from roundabout.userdefinedfields.models import Field

UDF_FIELDS = list(Field.objects.all().order_by('id'))

def thing(qs, udf_id, name=None):
    print('LAMBDA', udf_id, name)
    f = qs.filter(field__id=udf_id, is_current=True)
    #print('LAMBDA', udf_id , f, name)
    return f

class UDF_Column(tables.ManyToManyColumn):
    def __init__(self,udf,*args,**kwargs):

        super().__init__(accessor='fieldvalues', verbose_name=udf.field_name,
                         filter=lambda qs: thing(qs,udf.id,name='UDF_Column:'+udf.field_name))#qs.filter(field__field_name=udf.field_name, is_current=True))

    #def render(self, value):
    #    print(type(value),value)
    #    return value

class SearchTable(tables.Table):
    class Meta:
        template_name = "django_tables2/bootstrap4.html"

class InventoryTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Inventory
        fields = ["serial_number", 'part', ]#'location', "created_at", "updated_at" ] #+ udf_field_names

    #TODO with filterview auto select filtere'd columns: https://stackoverflow.com/questions/52686382/dynamic-columns-with-singletablemixin-and-filterview-in-django

    '''def __init__(self, data, extra_columns=[], *args, **kwargs):

        extra_columns.extend(self.udf_cols())
        #extra_columns.extend(reversed(self.udf_cols()))

        super().__init__(data, extra_columns=extra_columns, *args, **kwargs)
        self.extra_columns = extra_columns
    '''

    @staticmethod
    def udf_cols():

        udf_fields = Field.objects.all().order_by('id')

        msisdn_col = tables.ManyToManyColumn(verbose_name='MSISDN (hard)', accessor='fieldvalues',
                                          filter=lambda qs:  thing(qs,2))
        sim_col = tables.ManyToManyColumn(verbose_name='Sim (hard)', accessor='fieldvalues',
                                        filter=lambda qs:  thing(qs,3))
        manuf_col = tables.ManyToManyColumn(verbose_name='Manuf (hard)', accessor='fieldvalues',
                                          filter=lambda qs:  thing(qs,4))
        model_col = tables.ManyToManyColumn(verbose_name='Model (hard)', accessor='fieldvalues',
                                         filter=lambda qs:  thing(qs,5))
        imei_col = tables.ManyToManyColumn(verbose_name='IMEI (hard)', accessor='fieldvalues',
                                        filter=lambda qs:  thing(qs,1))

        extra_cols = [('UDF1_imei_h',imei_col),('UDF3_sim_h',sim_col)]

        print('LOOP FIELDS:')
        for udf in udf_fields[2:5]:
            col_filter = lambda qs:  thing(qs,udf.id,name='Loop:'+udf.field_name)
            print('    id=',udf.id,udf.field_name,id(col_filter))
            col_name = 'UDF{}_{}'.format(udf.id,udf.field_name.lower().replace(' ','_'))
            col_kwargs = dict(verbose_name=udf.field_name+' (soft {})'.format(udf.id),
                              accessor='fieldvalues',
                              filter=col_filter)
            col_obj = tables.ManyToManyColumn(**col_kwargs)
            # UNCOMMENT TO SHOW THAT EVEN IF NOT USED, FINAL LOOP FILTER IS USED
            #if udf.field_name=='Model':
            #    col_obj = tables.Column(empty_values=())
            extra_cols.append( (col_name,col_obj) )

        extra_cols.append(('UDF5_model_h',model_col))
        extra_cols.append(('UDF4_manuf_h',manuf_col))
        extra_cols.append(('UDF2_msisdn_h',msisdn_col))
        filters = [id(col[1].filter) for col in extra_cols]
        print('All Filters Different?',len(filters) == len(set(filters)),filters)
        return extra_cols

    def render_serial_number(self, value, record):
        item_url = reverse("inventory:inventory_detail", args=[record.pk])
        html_string = '<a href={}>{}</a>'.format(item_url, value)
        return format_html(html_string)
    def value_serial_number(self,record):
        return record.serial_number

    def render_part(self,record):
        item_url = reverse("parts:parts_detail", args=[record.part.pk])
        name = record.part.friendly_name_display()
        html_string = '{} <a href={}>➤</a>'.format(name, item_url)
        return format_html(html_string)
    def value_part(self,record):
        return record.part.name

for udf in UDF_FIELDS:
    print('{} {} {:>14}'.format(udf.id, udf.field_name.lower().replace(' ','_'), udf.field_name))
    InventoryTable.base_columns[udf.field_name] = UDF_Column(udf)
'''            tables.ManyToManyColumn(verbose_name=udf.field_name,
                                    accessor='fieldvalues',
                                    filter=lambda qs: qs.filter(field__id=udf.id))
    # Part Number,Serial Number,Location,Notes,
    # Manufacturer Serial Number,WHOI Property  Number,OOI Property Number,Model,Firmware Version,Manufacturer,Current Status,Latest Calibration Date,Incoming Inspection History,QCT History,Pre-Deployment History,Post-Deployment History,RMA/Shipping History,DO Number,Date Received,Deployment History
'''
#print(InventoryTable.__dict__)

class PartTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Part
        fields = ("part_number", 'name', 'part_type__name','inventory_count')

    part_type__name = tables.Column(verbose_name='Type')
    inventory_count = tables.Column(empty_values=())

    def render_part_number(self, value, record):
        item_url = reverse("parts:parts_detail", args=[record.pk])
        html_string = '<a href={}>{}</a>'.format(item_url, value)
        return format_html(html_string)

    def render_name(self,record):
        return record.friendly_name_display()

    def render_inventory_count(self,record):
        return record.get_part_inventory_count()
    def order_inventory_count(self, queryset, is_ascending):
        queryset = queryset.annotate(count=Count('inventory'))\
                           .order_by(("" if is_ascending else "-")+'count')
        return queryset, True


class BuildTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Build
        fields = ('build','name','build_number','location',"created_at","updated_at",'is_deployed','time_at_sea')

    build=tables.Column(empty_values=(),attrs={"th": {"style": "white-space:nowrap;"}})

    def render_build(self, record):
        item_url = reverse("builds:builds_detail", args=[record.pk])
        html_string = '<a href={}>{}-{}</a>'.format(item_url, record.assembly.assembly_number, record.build_number.replace('Build ',''))
        return format_html(html_string)


class AssemblyTable(SearchTable):
    class Meta(SearchTable.Meta):
        model = Assembly
        fields = ("assembly_number", 'name', 'assembly_type')

    def render_assembly_number(self, value, record):
        item_url = reverse("assemblies:assembly_detail", args=[record.pk])
        html_string = '<a href={}>{}</a>'.format(item_url, value)
        return format_html(html_string)

