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

import csv
import datetime
import io
from types import SimpleNamespace

from celery import shared_task
from django.core.cache import cache

from roundabout.calibrations.forms import parse_valid_coeff_vals
from roundabout.calibrations.models import CoefficientName, CoefficientValueSet, CalibrationEvent
from roundabout.inventory.models import Inventory, Action
from roundabout.inventory.utils import _create_action_history


@shared_task(bind = True)
def parse_cal_files(self):
    self.update_state(state='PROGRESS', meta = {'key': 'started',})
    user = cache.get('user')
    user_draft = cache.get('user_draft')
    ext_files = cache.get('ext_files')
    csv_files = cache.get('csv_files')
    counter = 0
    for cal_csv in csv_files:
        counter+=1
        self.update_state(state='PROGRESS', meta = {'progress': counter, 'total': len(cal_csv)})
        cal_csv_filename = cal_csv.name[:-4]
        cal_csv.seek(0)
        reader = csv.DictReader(io.StringIO(cal_csv.read().decode('utf-8')))
        headers = reader.fieldnames
        coeff_val_sets = []
        inv_serial = cal_csv.name.split('__')[0]
        cal_date_string = cal_csv.name.split('__')[1][:8]
        inventory_item = Inventory.objects.get(serial_number=inv_serial)
        cal_date_date = datetime.datetime.strptime(cal_date_string, "%Y%m%d").date()
        csv_event = CalibrationEvent.objects.create(
            calibration_date = cal_date_date,
            inventory = inventory_item
        )
        for idx, row in enumerate(reader):
            row_data = row.items()
            for key, value in row_data:
                if key == 'name':
                    calibration_name = value.strip()
                    cal_name_item = CoefficientName.objects.get(
                        calibration_name = calibration_name,
                        coeff_name_event =  inventory_item.part.coefficient_name_events.first()
                    )
                elif key == 'value':
                    valset_keys = {'cal_dec_places': inventory_item.part.cal_dec_places}
                    mock_valset_instance = SimpleNamespace(**valset_keys)
                    raw_valset = str(value)
                    if '[' in raw_valset:
                        raw_valset = raw_valset[1:-1]
                    if 'SheetRef' in raw_valset:
                        ext_finder_filename = "__".join((cal_csv_filename,calibration_name))
                        ref_file = [file for file in ext_files if ext_finder_filename in file.name][0]
                        ref_file.seek(0)
                        reader = io.StringIO(ref_file.read().decode('utf-8'))
                        contents = reader.getvalue()
                        raw_valset = contents
                elif key == 'notes':
                    notes = value.strip()
                    coeff_val_set = CoefficientValueSet(
                        coefficient_name = cal_name_item,
                        value_set = raw_valset,
                        notes = notes
                    )
                    coeff_val_sets.append(coeff_val_set)
        if user_draft.exists():
            draft_users = user_draft
            for user in draft_users:
                csv_event.user_draft.add(user)
        for valset in coeff_val_sets:
            valset.calibration_event = csv_event
            valset.save()
            parse_valid_coeff_vals(valset)
        _create_action_history(csv_event, Action.CALCSVIMPORT, user)
