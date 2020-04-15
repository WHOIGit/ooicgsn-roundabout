/*
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
*/

$(document).ready(function() {
    // AJAX functions for build_detail form

    $("#hint_id_build_number").click(function () {
        $("#id_build_number").removeAttr("readonly");
    });

    $("#id_assembly").change(function () {
        var url_serialnumber = $("#build-form").attr("data-serialnumber-url");
        var url_assemblyrevision = $("#build-form").attr("data-assemblyrevision-url");
        var assemblyID = $(this).val();
        console.log(assemblyID);

        $.ajax({
            url: url_assemblyrevision,
            data: {
              "assembly_id": assemblyID
            },
            success: function (data) {
              $("#id_assembly_revision").html(data);
            }
        });

        $.ajax({
            url: url_serialnumber,
            data: {
              "assembly_id": assemblyID
            },
            success: function (data) {
              console.log(data.new_serial_number);
              $('#id_build_number').val(data.new_serial_number);
            }
        });

    });

});
