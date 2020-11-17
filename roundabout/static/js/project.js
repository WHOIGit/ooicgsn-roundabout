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

/* Project specific Javascript goes here. */

$(document).ready(function() {
    /* Auto focus to the Serial Number search box on page load */
    $('#search-serial-number').focus();

    /* Make the Documentation Inline Formset Jquery work */
    $('.form-group').removeClass('row');

});

/* Use History API to load AJAX data on Back button click */
window.onpopstate = function (event) {
  if (event.state) {
      $.ajax({
          url: event.state.backURL,
          success: function (data) {
            $("#detail-view").html(data);
            $(navTree).jstree(true).deselect_all();
            $(navTree).jstree(true).select_node(event.state.navTreeNodeID);
          }
      });
  } else {
      // Not an AJAX generated event, clear the HTML in #detail-view
      $("#detail-view").html('');
  }
};

/* AJAX navtree functions - Global */

var openNodes = [];
var navTree = $('#jstree-navtree');
var navtreePrefix = navTree.attr('data-node-type');
var navURL = navTree.attr('data-navtree-url');

$(document).ready(function() {

    // AJAX functions for Nav Tree
    $(navTree).jstree({
      'core' : {
        'data' : {
          'url' : navURL,
          'data' : function (node) {
            return { 'id' : node.id };
          }
        }
      }
    });

    var nodeID = navtreePrefix + '_' + $('.card-header').attr('data-object-id');
    console.log(nodeID);
    $(navTree).on('ready.jstree', function (event, data) {
        /* Need to check if the loading item is on a Build or Assembly Revision template,
           if so need to open the parent tree first */
        /* buildID variable is set by Django in ajax_inventory_detail or ajax_build_detail template */
        /* assemblyID variable is set by Django in ajax_assembly_detail or ajax_assemblypart_detail template */
        if (typeof buildID !== 'undefined') {
            console.log(buildID);
            data.instance._open_to(buildID);
            data.instance.open_node(buildID);
            $(navTree).on("open_node.jstree", function (event, data) {
                data.instance._open_to(nodeID);
                data.instance.select_node(nodeID);
            });
        } else if (typeof assemblyID !== 'undefined') {
            console.log(assemblyID);
            if (typeof assemblyRevisionID !== 'undefined') {
              data.instance._open_to(assemblyRevisionID);
              data.instance.open_node(assemblyRevisionID);
            } else{
              data.instance._open_to(assemblyID);
              data.instance.open_node(assemblyID);
            }
            $(navTree).on("open_node.jstree", function (event, data) {
                data.instance._open_to(nodeID);
                data.instance.select_node(nodeID);
            });
        } else {
            data.instance._open_to(nodeID);
            data.instance.select_node(nodeID);
        }
    });

    $(navTree).on('click','a',function(){

        var nodeType = $(this).attr("data-node-type");
        console.log(nodeType);
        if (!nodeType) {
            nodeType = navtreePrefix;
        }

        var url = $(this).attr("data-detail-url");
        console.log(url);
        var nodeID = nodeType + '_' + $(this).attr("data-node-id");
        var itemID = $(this).attr("data-node-id");
        // Get the li ID for the jsTree node
        var navTreeNodeID = $(this).parent().attr("id");

        $.ajax({
            url: url,
            data: {
              'navTreeNodeID': navTreeNodeID
            },
            success: function (data) {
              $("#detail-view").html(data);

              /* Use History API to change browser Back button behavior, create bookmarkable URLs */
              if (nodeType == 'assemblyparts') {
                  var bookmarkURL = '/assemblies/assemblypart/' + itemID;
              } else if (nodeType == 'assemblytype') {
                  var bookmarkURL = '/assemblies/assemblytype/' + itemID;
              } else if (nodeType == 'assemblyrevisions') {
                  var bookmarkURL = '/assemblies/assemblyrevision/' + itemID;
              } else if (nodeType == 'part_type') {
                  var bookmarkURL = '/parts/part_type/' + itemID;
              } else if (nodeType == 'cruises_by_year') {
                  var bookmarkURL = '/cruises/cruises-by-year/' + itemID;
              } else {
                 var bookmarkURL = '/' + nodeType + '/' + itemID
              }

              var backURL = url
              var state = {
                  navTreeNodeID: navTreeNodeID,
                  itemID: itemID,
                  nodeType: nodeType,
                  backURL: backURL,
                  bookmarkURL: bookmarkURL,
              };
              history.pushState(state, '', bookmarkURL);
              console.log(history.state);
            }
        });
    });

});

/* AJAX template functions - Global */

$(document).ready(function() {

    // AJAX functions for Add Button
    $('#content-block').on('click','.parts-add-btn a', function(){
        var url = $(this).attr("data-create-url");

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
    $('#content-block').on('click','input.cancel-btn', function(){
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
    $('#content-block').on('click','.ajax-detail-link a', function(event){
        event.preventDefault();
        var nodeType = $(this).attr("data-node-type");
        console.log(nodeType);
        if (!nodeType) {
            nodeType = navtreePrefix;
        }

        var url = $(this).attr("data-detail-url");
        var nodeID = nodeType + '_' + $(this).attr("data-node-id");
        var itemID = $(this).attr("data-node-id");
        var previousNodeID = nodeType + '_' + $('.card-header').attr('data-object-id');

        $.ajax({
            url: url,
            beforeSend: function() {
               $(navTree).jstree(true).deselect_node(previousNodeID);
            },
            success: function (data) {
              $("#detail-view").html(data);
              $(navTree).jstree(true).select_node(nodeID);

              /* Use History API to change browser Back button behavior, create bookmarkable URLs */
              if (nodeType == 'assemblyparts') {
                  var bookmarkURL = '/assemblies/assemblypart/' + itemID;
              } else if (nodeType == 'assemblytype') {
                  var bookmarkURL = '/assemblies/assemblytype/' + itemID;
              } else if (nodeType == 'assemblyrevisions') {
                  var bookmarkURL = '/assemblies/assemblyrevision/' + itemID;
              } else if (nodeType == 'part_type') {
                  var bookmarkURL = '/parts/part_type/' + itemID;
              } else {
                 var bookmarkURL = '/' + nodeType + '/' + itemID
              }

              var backURL = url
              var state = {
                  itemID: itemID,
                  nodeType: nodeType,
                  backURL: backURL,
                  bookmarkURL: bookmarkURL,
              };

              history.pushState(state, '', bookmarkURL);
              console.log(history.state);
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
              $(navTree).jstree(true).settings.core.data.url = navURL;
              $(navTree).on('refresh.jstree', function (event, data) {
                  data.instance.deselect_all();
                  data.instance._open_to(nodeID);
                  data.instance.select_node(nodeID);
              });
              $(navTree).jstree(true).refresh();

            }
        });
    });

    // Open tabs links with URL hash
    $(function () {
        var hash = window.location.hash;
        hash && $('ul.nav a[href="' + hash + '"]').tab('show');
    });

    // AJAX function for Filter by Part type
    $('#content-block').on('change','.filter-checkbox', function(event){
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
            success: function (data) {
                $(navTree).jstree(true).settings.core.data = data;
                $(navTree).jstree(true).open_all();
                $(navTree).jstree(true).refresh();

            }
        });
    });

    $('#content-block').on('click','#filter-part-type-clear', function(event){
        event.preventDefault();
        $( ".filter-checkbox" ).prop( "checked", false );
        $.ajax({
            url: navURL,
            success: function (data) {
                $(navTree).jstree(true).settings.core.data = data;
                $(navTree).jstree(true).refresh();

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

function handleBeforeSend(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
        // Show spinner container
        $("#spinner-loader").show();
        // Clear error messages
        clear_form_field_errors();
}

function handleFormSuccess(data, textStatus, jqXHR){
    console.log(data)
    console.log(textStatus)
    console.log(data.detail_path)

    if (data.hasOwnProperty('object_type')) {
        var objectTypePrefix = data.object_type;
    } else {
        var objectTypePrefix = navtreePrefix;
    }

    $.ajax({
        url: data.detail_path,
        success: function (data) {
          $("#detail-view").html(data);
        }
    });

    var nodeID = objectTypePrefix + '_' + data.object_id ;
    console.log(nodeID)
    $(navTree).jstree(true).settings.core.data.url = navURL;
    $(navTree).jstree(true).refresh();
    $(navTree).on('refresh.jstree', function (event, data) {
        data.instance.deselect_all();
        data.instance._open_to(nodeID);
        data.instance.select_node(nodeID);
    });
}

function handleDeleteFormSuccess(data, textStatus, jqXHR){
    $("#detail-view").html('');

    if (data.hasOwnProperty('object_type')) {
        var objectTypePrefix = data.object_type;
    } else {
        var objectTypePrefix = navtreePrefix;
    }

    if (data.hasOwnProperty('parent_type')) {
        var parentTypePrefix = data.parent_type;
    } else {
        var parentTypePrefix = navtreePrefix;
    }

    var nodeID = parentTypePrefix + '_' + data.parent_id;

    $(navTree).jstree(true).settings.core.data.url = navURL;
    $(navTree).jstree(true).refresh();
    $(navTree).on('refresh.jstree', function (event, data) {
      data.instance._open_to(nodeID);
    });
}

function handleCopyFormSuccess(data, textStatus, jqXHR){
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

function handleFormError(data, textStatus, errorThrown){
    console.log(data)
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

function handleFormComplete() {
    // Hide spinner container
    $("#spinner-loader").hide();
}

// Append a formset row's field error messages below the respective field
function apply_form_field_error_array(index, value, error) {
    let inputField = $("input[id$=" + index + '-' + value + "]");
    let selectField = $("select[id$=" + index + '-' + value + "]");
    let textArea = $("textarea[id$=" + index + '-' + value + "]");
    let allRow = $("#__all__")
    let fieldType = '';
    if (inputField.length) {
        fieldType = inputField;
    } else if (selectField.length) {
        fieldType = selectField;
    } else if (textArea.length) {
        fieldType = textArea;
    } else if (allRow.length) {
        fieldType = allRow;
    }
    let error_msg = $("<div style = 'width: " + fieldType.width() + "px; padding: 1rem 1rem' id = error-" + index + '-' + value + " />")
        .addClass("ajax-error alert-danger")
        .text(error[0]);
    error_msg.insertAfter(fieldType);
}

// AJAX functions to display Django error messages
function apply_form_field_error(fieldname, error) {
    var input = $("#id_" + fieldname),
        container = $("#div_id_" + fieldname),
        error_msg = $("<div />").addClass("ajax-error alert alert-danger").text(error[0]);

    container.addClass("error");
    error_msg.insertAfter(input);
}

function clear_form_field_errors(form) {
    $("#content-block .ajax-error").remove();
    $("#content-block .error").removeClass("error");
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
            beforeSend: handleBeforeSend,
            success: handleFormSuccess,
            error: handleFormError,
            complete:handleFormComplete,
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
            beforeSend: handleBeforeSend,
            success: handleDeleteFormSuccess,
            error: handleFormError,
            complete:handleFormComplete,
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
            beforeSend: handleBeforeSend,
            success: handleCopyFormSuccess,
            error: handleFormError,
            complete:handleFormComplete,
        })
    })

    function handleFormSuccess(data, textStatus, jqXHR){
        console.log(data)
        console.log(textStatus)
        console.log(data.detail_path)

        if (data.hasOwnProperty('object_type')) {
            var objectTypePrefix = data.object_type;
        } else {
            var objectTypePrefix = navtreePrefix;
        }

        $.ajax({
            url: data.detail_path,
            success: function (data) {
              $("#detail-view").html(data);
            }
        });

        var nodeID = objectTypePrefix + '_' + data.object_id ;
        console.log(nodeID)
        $(navTree).jstree(true).settings.core.data.url = navURL;
        $(navTree).jstree(true).refresh();
        $(navTree).on('refresh.jstree', function (event, data) {
            data.instance.deselect_all();
            data.instance._open_to(nodeID);
            data.instance.select_node(nodeID);
        });
    }

    function handleDeleteFormSuccess(data, textStatus, jqXHR){
        console.log(data)
        console.log(textStatus)
        console.log(jqXHR)
        console.log(data.parent_id);
        console.log(data.object_type);
        console.log(navtreePrefix);
        $("#detail-view").html('');

        if (data.hasOwnProperty('object_type')) {
            var objectTypePrefix = data.object_type;
        } else {
            var objectTypePrefix = navtreePrefix;
        }

        if (data.hasOwnProperty('parent_type')) {
            var parentTypePrefix = data.parent_type;
        } else {
            var parentTypePrefix = navtreePrefix;
        }

        var nodeID = parentTypePrefix + '_' + data.parent_id;

        $(navTree).jstree(true).settings.core.data.url = navURL;
        $(navTree).jstree(true).refresh();
        $(navTree).on('refresh.jstree', function (event, data) {
          data.instance._open_to(nodeID);
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

    function handleFormError(data, textStatus, errorThrown){
        console.log(data)
        console.log(textStatus)
        console.log(errorThrown)
        var errors = $.parseJSON(data.responseText);
        console.log(errors)
        $('[id^=error-]').each(function() {
            $(this).remove();
        });
        if (Array.isArray(errors)) {
            errors.map((error, rowNum) => {
                $.each(error, function(columnName, value) {
                    apply_form_field_error_array(rowNum, columnName, value);
                });
            });
        } else {
            $.each(errors, function(index, value) {
                if (index === "__all__") {
                    django_message(value[0], "error");
                } else {
                    apply_form_field_error(index, value);
                }
            });
        }
    }
})

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
