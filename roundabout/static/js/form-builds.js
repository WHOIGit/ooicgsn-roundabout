$(document).ready(function() {
    // AJAX functions for build_detail form

    $("#hint_id_serial_number").click(function () {
        $("#id_serial_number").removeAttr("readonly");
    });

    $("#id_assembly").change(function () {
        var url_serialnumber = $("#build-form").attr("data-serialnumber-url");
        var assemblyID = $(this).val();
        console.log(assemblyID);

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
