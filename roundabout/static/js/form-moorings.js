$(document).ready(function() {

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
            }
        });

    });

    $("#id_location").change(function () {
        var url_mooring_parts = $("#parts-form").attr("data-mooring-parts-url");
        var locationID = $(this).val();
        console.log(locationID);

        $.ajax({
            url: url_mooring_parts,
            data: {
              'location': locationID
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
