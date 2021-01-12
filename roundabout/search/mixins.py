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

from django.http import StreamingHttpResponse
from django_tables2.export import TableExport
from django_tables2.export.views import ExportMixin
from tablib import Dataset

class TableExportStream(TableExport):

    def table_to_dataset(self, table, exclude_columns, dataset_kwargs=None):
        """A generator that returns a tablib dataset for each row of the table."""
        table_rows = table.as_values(exclude_columns=exclude_columns)
        headers = next(table_rows)
        data = Dataset(headers=headers)
        yield getattr(data, self.format)

        for row in table_rows:
            # Return subset of the data (one row)
            # This is a simple implementation to fix the tablib library which is missing returning the data as generator
            data = Dataset()
            data.append(row)
            yield getattr(data, self.format)

    def response(self, filename=None):
        """
        Builds and returns a `StreamingHttpResponse` containing the exported data

        Arguments:
            filename (str): if not `None`, the filename is attached to the
                `Content-Disposition` header of the response.
        """
        response = StreamingHttpResponse(self.dataset, content_type=self.content_type())
        if filename is not None:
            response["Content-Disposition"] = 'attachment; filename="{}"'.format(filename)

        return response


class ExportStreamMixin(ExportMixin):
    export_class = TableExportStream

# https://github.com/django-import-export/django-import-export/issues/206#issuecomment-567935233
# https://docs.djangoproject.com/en/2.2/ref/request-response/#django.http.StreamingHttpResponse
# https://stackoverflow.com/a/49820427
