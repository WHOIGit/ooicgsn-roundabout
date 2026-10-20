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

    // Repopulate the Part Revision dropdown for the currently selected Part
    function loadPartRevisions() {
        var url = $("#assembly-part-form").attr("data-part-revisions-url");
        if (!url) { return; }
        var partID = $("#id_part").val();
        $.ajax({
            url: url,
            data: {
              'part_id': partID
            },
            success: function (data) {
              $("#id_revision").html(data);
            }
        });
    }

    // AJAX functions for form
    $("#inventory-filter-form-part-number").on("submit", function(){
      var url = $(this).attr("data-url");
      var partNumber = $("#part_number_search").val();
      $.ajax({
          url: url,
          data: {
            "part_number": partNumber
          },
          success: function (data) {
            $("#id_part").html(data);
            loadPartRevisions();
          }
      });
      return false;
    })

    $("#id_part_type").change(function () {
        var url = $("#parttype-filter-form").attr("data-url");
        var partType = $(this).val();
        $.ajax({
            url: url,
            data: {
              'part_type': partType
            },
            success: function (data) {
              $("#id_part").html(data);
              loadPartRevisions();
            }
        });

    });

    // When the Part choice changes, refresh the available Revisions
    $(document).on("change", "#id_part", loadPartRevisions);

    $("#id_assembly").change(function () {
        var url_assembly_parts = $("#assembly-part-form").attr("data-assembly-parts-url");
        var assemblyID = $(this).val();
        console.log(assemblyID);

        $.ajax({
            url: url_assembly_parts,
            data: {
              'assembly': assemblyID
            },
            success: function (data) {
              $("#id_parent").html(data);
              if ( $("#id_parent option").length == 1 ) {
                  $("#div_id_parent").hide();
              }  else {
                  $("#div_id_parent").show();
              }

            }
        });

    });


});
