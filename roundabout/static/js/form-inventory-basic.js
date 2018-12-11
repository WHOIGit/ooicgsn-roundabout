$(document).ready(function() {
    // AJAX functions for Inventory form
    if ( $("#id_deployment option").length == 1 ) {
        $("#div_id_deployment").hide();
    }  else {
        $("#div_id_deployment").show();
    }

    if ( $("#id_mooring_part option").length == 1 ) {
        $("#div_id_mooring_part").hide();
    }  else {
        $("#div_id_mooring_part").show();
    }

    if ( $("#id_parent option").length == 1 ) {
        $("#div_id_parent").hide();
    }  else {
        $("#div_id_parent").show();
    }

    if ( ! $('#div_id_whoi_number input').val() ) {
        $("#div_id_whoi_number").hide();
    }

    if ( ! $('#div_id_ooi_property_number input').val() ) {
        $("#div_id_ooi_property_number").hide();
    }

    $("#hint_id_serial_number").click(function () {
        $("#id_serial_number").removeAttr("readonly");
    });

    $("#inventory-filter-form-part-number").on("submit", function(){
      var url = $(this).attr("data-url");
      var url_serialnumber = $(this).attr("data-serialnumber-url");
      var url_equipment = $(this).attr("data-equipment-url");
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
      $.ajax({
          url: url_equipment,
          data: {
            'part_number': partNumber
          },
          success: function (data) {
            console.log(data.is_equipment);
            if (data.is_equipment) {
                $("#div_id_whoi_number").show();
                $("#div_id_ooi_property_number").show();
            } else {
                $("#div_id_whoi_number").hide();
                $("#div_id_ooi_property_number").hide();
            }
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

    $("#id_part").change(function () {
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
            url: url_equipment,
            data: {
              'part': partID
            },
            success: function (data) {
              console.log(data.is_equipment);
              if (data.is_equipment) {
                  $("#div_id_whoi_number").show();
                  $("#div_id_ooi_property_number").show();
              } else {
                  $("#div_id_whoi_number").hide();
                  $("#div_id_ooi_property_number").hide();
              }
            }
        });

    });

});
