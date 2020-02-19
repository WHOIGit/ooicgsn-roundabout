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
    // AJAX functions for Inventory form
    if ( $("#id_deployment option").length == 1 ) {
        $("#div_id_deployment").hide();
    }  else {
        $("#div_id_deployment").show();
    }

    if ( $("#id_assembly_part option").length == 1 ) {
        $("#div_id_assembly_part").hide();
    }  else {
        $("#div_id_assembly_part").show();
    }

    if ( $("#id_parent option").length == 1 ) {
        $("#div_id_parent").hide();
    }  else {
        $("#div_id_parent").show();
    }

    $("#hint_id_serial_number").click(function () {
        $("#id_serial_number").removeAttr("readonly");
    });

    $("#inventory-filter-form-part-number").on("submit", function(){
      var url = $(this).attr("data-url");
      var url_serialnumber = $(this).attr("data-serialnumber-url");
      var partNumber = $("#part_number_search").val();
      $.ajax({
          url: url,
          data: {
            "part_number": partNumber
          },
          success: function (data) {
            $("#id_part").html(data);
          }
      });
      $.ajax({
          url: url_serialnumber,
          data: {
            "part_number": partNumber
          },
          success: function (data) {
            $("#div_id_serial_number div").html(data);
          }
      });

      return false;
    })

    $("#id_part_type").change(function () {
        var url = $("#inventory-filter-form").attr("data-url");
        var partType = $(this).val();
        $.ajax({
            url: url,
            data: {
              'part_type': partType
            },
            success: function (data) {
              $("#id_part").html(data);
            }
        });
    });

    $("#id_location").change(function () {
        var url_deployments = $("#inventory-action-form").attr("data-deployments-url");
        var url_parents = $("#inventory-action-form").attr("data-parents-url");
        var locationID = $(this).val();
        if ( $( "#id_part" ).length ) {
            var partID = $("#id_part").val();
        }  else {
            var partID;
        }

        console.log(partID);
        //$("#id_mooring_part").html('<option value="">---------</option>');
        //$("#div_id_mooring_part").hide();

        $.ajax({
            url: url_deployments,
            data: {
              'location': locationID
            },
            success: function (data) {
              $("#id_deployment").html(data);
              if ( $("#id_deployment option").length == 1 ) {
                  $("#div_id_deployment").hide();
              }  else {
                  $("#div_id_deployment").show();
              }
            }
        });

        $.ajax({
            url: url_parents,
            data: {
              'location': locationID,
              'part': partID,
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

    $("#id_deployment").change(function () {
        var url_mooring_parts = $("#inventory-action-form").attr("data-mooring-parts-url");
        var deploymentID = $(this).val();
        if ( $( "#id_part" ).length ) {
            var partID = $("#id_part").val();
        }  else {
            var partID;
        }
        console.log(partID);

        $.ajax({
            url: url_mooring_parts,
            data: {
              'deployment': deploymentID
            },
            success: function (data) {
              $("#id_mooring_part").html(data);
              if ( $("#id_mooring_part option").length == 1 ) {
                  $("#div_id_mooring_part").hide();
              }  else {
                  $("#div_id_mooring_part").show();
              }

            }
        });

    });

    $("#id_part").change(function () {
        var url_deployments = $("#inventory-action-form").attr("data-deployments-url");
        var url_parents = $("#inventory-action-form").attr("data-parents-url");
        var url_equipment = $("#inventory-action-form").attr("data-equipment-url");
        var url_serialnumber = $("#inventory-action-form").attr("data-serialnumber-url");
        var partID = $(this).val();

        if ( $( "#id_location" ).length ) {
            var locationID = $("#id_location").val();
        }  else {
            var locationID;
        }

        $.ajax({
            url: url_serialnumber,
            data: {
              "part_id": partID
            },
            success: function (data) {
              $("#div_id_serial_number div").html(data);
            }
        });

        $.ajax({
            url: url_deployments,
            data: {
              'location': locationID
            },
            success: function (data) {
              $("#id_mooring_part").html(data);
            }
        });

        $.ajax({
            url: url_parents,
            data: {
              'location': locationID,
              'part': partID
            },
            success: function (data) {
              $("#id_parent").html(data);
            }
        });

    });

});
