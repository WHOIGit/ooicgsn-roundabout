/* Project specific Javascript goes here. */

/* Auto focus to the Serial Number search box on page load */
$(document).ready(function() {
    $('#search-serial-number').focus();
});

/* Make the Documentation Inline Formset Jquery work */
$('.form-group').removeClass('row');

/* AJAX navtree functions - Global */

var openNodes = [];
var navTree = $('#jstree-navtree');
var navtreePrefix = navTree.attr('data-node-type');
var navURL = navTree.attr('data-navtree-url');

$(document).ready(function() {

    // AJAX functions for Nav Tree
    $.ajax({
        url: navURL,
        success: function (data) {

            $(navTree).html(data);
            $(navTree).jstree();
            $(navTree).on('open_node.jstree', function (event, data) {
                console.log("node =" + data.node.id);
                openNodes.push(data.node.id);
                console.log(openNodes);
            });
            $(navTree).on('close_node.jstree', function (event, data) {
                console.log("node =" + data.node.id);
                var index = openNodes.indexOf(data.node.id);
                if (index > -1) {
                  openNodes.splice(index, 1);
                }
                console.log(openNodes);
            });
            var nodeID = navtreePrefix + '_' + $('.card-header').attr('data-object-id');
            console.log(nodeID);
            $(navTree).jstree(true).select_node(nodeID);


        }
    });

    $(navTree).on('click','a',function(){
        var url = $(this).attr("data-detail-url");
        // Get the li ID for the jsTree node
        var navTreeNodeID = $(this).parent().attr("id");

        $.ajax({
            url: url,
            data: {
              'navTreeNodeID': navTreeNodeID
            },
            success: function (data) {
              $("#detail-view").html(data);
            }
        });
    });

});

/* AJAX form functions - Global */

// Enable Django CSRF-ready AJAX Calls
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
        clear_form_field_errors( $('#content-block form.ajax-form') );
    }
});

// AJAX functions to display Django error messages
function apply_form_field_error(fieldname, error) {
    var input = $("#id_" + fieldname),
        container = $("#div_id_" + fieldname),
        error_msg = $("<div />").addClass("ajax-error alert alert-danger").text(error[0]);

    container.addClass("error");
    error_msg.insertAfter(input);
}

function clear_form_field_errors(form) {
    $("#content-block .ajax-error", $(form)).remove();
    $("#content-block .error", $(form)).removeClass("error");
}

// AJAX form submit

$(document).ready(function(){

    $('#content-block').on('submit', 'form.ajax-form', function (event) {
        event.preventDefault()
        var formData = $(this).serialize()
        var thisURL = $('.ajax-form').attr('data-url') || window.location.href

        $.ajax({
            method: "POST",
            url: thisURL,
            data: formData,
            success: handleFormSuccess,
            error: handleFormError,
        })
    })

    $('#content-block').on('submit', 'form.delete-form', function (event) {
        event.preventDefault()
        var formData = $(this).serialize()
        var thisURL = $(this).attr('data-url') || window.location.href
        $.ajax({
            method: "POST",
            url: thisURL,
            data: formData,
            success: handleDeleteFormSuccess,
            error: handleFormError,
        })
    })

    $('#content-block').on('submit', 'form.copy-form', function (event) {
        event.preventDefault()
        var formData = $(this).serialize()
        var thisURL = $(this).attr('data-url') || window.location.href
        $.ajax({
            method: "POST",
            url: thisURL,
            data: formData,
            success: handleCopyFormSuccess,
            error: handleFormError,
        })
    })

    $('#content-block').on('submit', 'form.deployment-form', function (event) {
        event.preventDefault()
        var formData = $(this).serialize()
        var thisURL = $(this).attr('data-url') || window.location.href
        $.ajax({
            method: "POST",
            url: thisURL,
            data: formData,
            success: handleDeploymentFormSuccess,
            error: handleFormError,
        })
    })

    function handleFormSuccess(data, textStatus, jqXHR){
        console.log(data)
        console.log(textStatus)
        console.log(jqXHR)
        $.ajax({
            url: '/' + navtreePrefix + '/ajax/detail/' + data.object_id + '/',
            success: function (data) {
              $("#detail-view").html(data);
            }
        });
        console.log(data.object_id);
        console.log(navtreePrefix);
        var nodeID = navtreePrefix + '_' + data.object_id ;
        $.ajax({
            url: navURL,
            success: function (data) {
                $(navTree).jstree(true).destroy();
                $(navTree).html(data);
                $(navTree).jstree();
                $(navTree).jstree(true).select_node(nodeID);
                $.each(openNodes, function(key, value) {
                    $(navTree).jstree(true).open_node(value);
                });
                console.log(openNodes);
                $(navTree).on('open_node.jstree', function (event, data) {
                    console.log("node =" + data.node.id);
                    openNodes.push(data.node.id);
                    console.log(openNodes);
                });
                $(navTree).on('close_node.jstree', function (event, data) {
                    console.log("node =" + data.node.id);
                    var index = openNodes.indexOf(data.node.id);
                    if (index > -1) {
                      openNodes.splice(index, 1);
                    }
                    console.log(openNodes);
                });
            }
        });
    }

    function handleDeleteFormSuccess(data, textStatus, jqXHR){
        console.log(data)
        console.log(textStatus)
        console.log(jqXHR)
        console.log(data.parent_id);
        console.log(data.object_model);
        console.log(navtreePrefix);
        $("#detail-view").html('');
        if (navtreePrefix == 'deployments') {
            var parentPrefix = 'locations';
        } else if (navtreePrefix == 'parts') {

            if (data.object_model == 'revision') {
                var parentPrefix = 'parts';
            } else {
                var parentPrefix = 'part_type';
            }

        } else {
            var parentPrefix = navtreePrefix;
        }
        var nodeID = parentPrefix + '_' + data.parent_id;

        $.ajax({
            url: '/' + navtreePrefix + '/ajax/load-navtree/',
            success: function (data) {
                $(navTree).jstree(true).destroy();
                $(navTree).html(data);
                $(navTree).jstree();
                $(navTree).jstree(true).select_node(nodeID);
                $(navTree).jstree(true).open_node(nodeID);
                console.log(nodeID);
            }
        });
    }

    function handleCopyFormSuccess(data, textStatus, jqXHR){
        console.log(data)
        console.log(textStatus)
        console.log(jqXHR)
        $.ajax({
            url: '/' + navtreePrefix + '/ajax/detail/location/' + data.object_id + '/',
            success: function (data) {
              $("#detail-view").html(data);
            }
        });
        var nodeID = 'locations_' + data.object_id ;
        //$("#jstree_inventory").jstree(true).refresh_node(parentID);

        $.ajax({
            url: '/' + navtreePrefix + '/ajax/load-navtree/',
            success: function (data) {
                $(navTree).jstree(true).destroy();
                $(navTree).html(data);
                $(navTree).jstree();
                $(navTree).jstree(true).select_node(nodeID);
                console.log(nodeID);
            }
        });
    }

    function handleDeploymentFormSuccess(data, textStatus, jqXHR){
        console.log(data)
        console.log(textStatus)
        console.log(jqXHR)
        $.ajax({
            url: '/deployments/ajax/detail/' + data.object_id + '/',
            success: function (data) {
              $("#detail-view").html(data);
            }
        });
        console.log(data.object_id);
        console.log(navtreePrefix);
        var nodeID = 'deployment' + '_' + data.object_id ;
        $.ajax({
            url: navURL,
            success: function (data) {
                $(navTree).jstree(true).destroy();
                $(navTree).html(data);
                $(navTree).jstree();
                $(navTree).jstree(true).select_node(nodeID);
                $.each(openNodes, function(key, value) {
                    $(navTree).jstree(true).open_node(value);
                });
                console.log(openNodes);
                $(navTree).on('open_node.jstree', function (event, data) {
                    console.log("node =" + data.node.id);
                    openNodes.push(data.node.id);
                    console.log(openNodes);
                });
                $(navTree).on('close_node.jstree', function (event, data) {
                    console.log("node =" + data.node.id);
                    var index = openNodes.indexOf(data.node.id);
                    if (index > -1) {
                      openNodes.splice(index, 1);
                    }
                    console.log(openNodes);
                });
            }
        });
    }

    function handleFormError(data, textStatus, errorThrown){
        console.log(data)
        console.log(textStatus)
        console.log(errorThrown)
        var errors = $.parseJSON(data.responseText);
        console.log(errors)
        $.each(errors, function(index, value) {
            if (index === "__all__") {
                django_message(value[0], "error");
            } else {
                apply_form_field_error(index, value);
            }
        });
    }
})

/* AJAX template functions - Global */

$(document).ready(function() {

    // AJAX functions for Add Button
    $('#content-block').on('click','.parts-add-btn a', function(){
        var url = $(this).attr("data-create-url");
        console.log(url);

        $.ajax({
            url: url,
            success: function (data) {
              $("#detail-view").html(data);
            }
        });
    });

    // AJAX functions for Update/Delete Buttons
    $('#content-block').on('click','.ajax-btn a', function(){
        var url = $(this).attr("data-update-url");
        console.log(url);

        $.ajax({
            url: url,
            success: function (data) {
              $("#detail-view").html(data);
            }
        });
    });

    // AJAX call for Cancel Button to go back to object detail
    $('#content-block').on('click','input.cancel-btn',function(){
        var url = $(this).attr("data-detail-url");
        var nodeID = $(this).attr("data-node-id");
        console.log(url);
        $.ajax({
            url: url,
            success: function (data) {
              $("#detail-view").html(data);
            }
        });
    });

    // AJAX functions for Detail template
    $('#content-block').on('click','.ajax-detail-link a',function(){
        var url = $(this).attr("data-detail-url");
        var nodeID = navtreePrefix + '_' + $(this).attr("data-node-id");
        var previousNodeID = navtreePrefix + '_' + $('.card-header').attr('data-object-id');
        console.log(previousNodeID);
        $.ajax({
            url: url,
            beforeSend: function() {
               $(navTree).jstree(true).deselect_node(previousNodeID);
            },
            success: function (data) {
              $("#detail-view").html(data);
              console.log(nodeID);
              $(navTree).jstree(true).select_node(nodeID);
            }
        });
    });

    // AJAX functions for Add Subassembly/Assign Destination template
    $('#content-block').on('click','.ajax-add-subassembly-link a',function(){
        var url = $(this).attr("data-detail-url");
        var nodeID = navtreePrefix + '_' + $(this).attr("data-node-id");
        $.ajax({
            url: url,
            success: function (data) {
              $("#detail-view").html(data);
              $.ajax({
                  url: '/' + navtreePrefix + '/ajax/load-navtree/',
                  success: function (data) {
                      $(navTree).jstree(true).destroy();
                      $(navTree).html(data);
                      $(navTree).jstree();
                      $(navTree).jstree(true).select_node(nodeID);
                      $(navTree).jstree(true).open_node(nodeID);
                      $.each(openNodes, function(key, value) {
                          $(navTree).jstree(true).open_node(value);
                      });
                      console.log(openNodes);
                      $(navTree).on('open_node.jstree', function (event, data) {
                          console.log("node =" + data.node.id);
                          openNodes.push(data.node.id);
                          console.log(openNodes);
                      });
                      $(navTree).on('close_node.jstree', function (event, data) {
                          console.log("node =" + data.node.id);
                          var index = openNodes.indexOf(data.node.id);
                          if (index > -1) {
                            openNodes.splice(index, 1);
                          }
                          console.log(openNodes);
                      });
                  }
              });

            }
        });
    });

    // Open tabs links with URL hash
    $(function () {
        var hash = window.location.hash;
        hash && $('ul.nav a[href="' + hash + '"]').tab('show');
    });

    // AJAX function for Filter by Part type
    $('#content-block').on('change','.filter-checkbox',function(event){
        event.preventDefault();
        var filterList = $("#filter-part-type input:checkbox:checked").map(function(){
          return $(this).val();
        }).get();
        console.log(filterList);
        var navFilterURL = $('#filter-part-type').attr("data-navtree-filter-url");
        $.ajax({
            url: navFilterURL,
            data: {
              'part_types[]': filterList
            },
            beforeSend: function() {
                $(navTree).html('<img src="/static/images/loading-icon.gif" class="loading-icon"/>');
            },
            success: function (data) {
                $(navTree).jstree(true).destroy();
                $(navTree).html(data);
                $(navTree).jstree();
                $.each(openNodes, function(key, value) {
                    $(navTree).jstree(true).open_node(value);
                });
                $(navTree).on('open_node.jstree', function (event, data) {

                    console.log("node =" + data.node.id);
                    openNodes.push(data.node.id);
                    console.log(openNodes);
                });
                $(navTree).on('close_node.jstree', function (event, data) {
                    console.log("node =" + data.node.id);
                    var index = openNodes.indexOf(data.node.id);
                    if (index > -1) {
                      openNodes.splice(index, 1);
                    }
                    console.log(openNodes);
                });


            }
        });
    });

    $('#content-block').on('click','#filter-part-type-clear',function(){
        $( ".filter-checkbox" ).prop( "checked", false );
        $.ajax({
            url: navURL,
            beforeSend: function() {
                $(navTree).html('<img src="/static/images/loading-icon.gif" class="loading-icon"/>');
            },
            success: function (data) {
                $(navTree).jstree(true).destroy();
                $(navTree).html(data);
                $(navTree).jstree();
                $.each(openNodes, function(key, value) {
                    $(navTree).jstree(true).open_node(value);
                });
                $(navTree).on('open_node.jstree', function (event, data) {

                    console.log("node =" + data.node.id);
                    openNodes.push(data.node.id);
                    console.log(openNodes);
                });
                $(navTree).on('close_node.jstree', function (event, data) {
                    console.log("node =" + data.node.id);
                    var index = openNodes.indexOf(data.node.id);
                    if (index > -1) {
                      openNodes.splice(index, 1);
                    }
                    console.log(openNodes);
                });


            }
        });
    });


});

/* Function to print specific page DIV */
function printDiv(eleId){
    var PW = window.open('', '_blank', 'Print Bar Code');
    var styleSheet = document.getElementById(eleId).getAttribute('class');
    //IF YOU HAVE DIV STYLE IN CSS, REMOVE BELOW COMMENT AND ADD CSS ADDRESS
    //PW.document.write('<link rel="stylesheet" type="text/css" href="/static/css/' + styleSheet + '.css"/>');

    PW.document.write(document.getElementById(eleId).innerHTML);
    PW.document.close();
    PW.focus();
    PW.print();
    //PW.close();
}

/* Function to get URL paramaters */
var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};
