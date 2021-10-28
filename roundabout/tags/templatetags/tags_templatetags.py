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

from django import template
import datetime

from django.utils.html import format_html

from roundabout.inventory.models import Inventory
from roundabout.configs_constants.models import ConfigValue, ConfigName, ConfigDefault
from roundabout.assemblies.models import AssemblyPart

register = template.Library()

@register.filter
def render_tag(tag, inventory_id=None):
    html_snippet = '<span class="badge badge-{} {}" data-toggle="tooltip" title="{}">{}</span>'
    pill_class = 'badge-pill' if tag.pill else ''
    disp_text = tag.tooltip

    try:
        if inventory_id:
            inv = Inventory.objects.get(id=inventory_id)
            print('HERE:',tag.config_name)
            if inv.inventory_configevents.exists and tag.config_name:
                cv = ConfigValue.objects.get(config_name = tag.config_name,
                                             config_event=inv.inventory_configevents.last())
                disp_text = tag.text.format(str(cv))

        elif tag.assembly_part.assemblypart_configdefaultevents.exists and tag.config_name:
            cdv = ConfigDefault.objects.get(config_name = tag.config_name,
                    conf_def_event=tag.assembly_part.assemblypart_configdefaultevents.last())
            disp_text = tag.text.format(str(cdv))
    except: pass

    html_result = format_html(html_snippet, tag.color, pill_class, tag.tooltip, disp_text)
    return html_result

@register.filter
def render_tag_raw(tag):
    html_snippet = '<span class="badge badge-{} {}">{}</span>'
    pill_class = 'badge-pill' if tag.pill else ''
    disp_text = tag.text.format('{'+str(tag.config_name)+'}')
    html_result = format_html(html_snippet, tag.color, pill_class, disp_text)
    return html_result

