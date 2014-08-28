function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    var res = div.innerHTML;
    div.remove();
    return res;
}

function upload_new_version_dialog(e) {
    var dialog = $(this);
    var form = dialog.find("form");
    var widget = dialog.dialog("activatedBy");
    var copy_rels = '<tr><th><label for="id_copy_relationships">Copy relationships:</label></th><td><input id="id_copy_relationships" name="copy_relationships" type="checkbox"></td></tr>';

    if (!form.find("#id_copy_relationships").length) {
        form.find("#id_data").closest('tr').after(copy_rels);
    };

    if (!form.attr("_dialog_once")) {
        copy_button = {'Copy Data From Current Version': function() {
            //name
            form.find("#id_name").val($('#disassembly_name').attr('data-name'));
            //tool name
            form.find("#id_tool_name").val($('#disassembly_tool_name').text());
            //tool version
            form.find("#id_tool_version").val($('#disassembly_tool_version').text());
            //tool details
            form.find("#id_tool_details").val($('#disassembly_tool_details').text());
            //data_type
            form.find("#id_data_type").val($('#disassembly_type').text());
            //description
            form.find("#id_description").val($('#disassembly_description').text());
            //copy relationships
            form.find("#id_copy_relationships").prop('checked', true);
            //source
            //bucket_list
            var buckets = "";
            $.each($('.tagit-label'), function(id,val) {
                buckets = buckets + $(val).text() + ", ";
            });
            if (buckets.length > 2) {
                buckets = buckets.substring(0, buckets.length - 2);
            }
            form.find("#id_bucket_list").val(buckets);
            //ticket
            var tickets = "";
            $.each($('#ticket_listing td[data-field="ticket_number"]'), function(id, val) {
                tickets = tickets + $(val).text() + ", ";
            });
            if (tickets.length > 2) {
                tickets = tickets.substring(0, tickets.length - 2);
            }
            form.find("#id_ticket").val(tickets);
        }};
        var buttons = dialog.dialog("option", "buttons");
        $.extend(copy_button, buttons);
        dialog.dialog("option", "buttons", copy_button);
    }
    form.attr("_dialog_once", true);
}

function upload_new_version_dialog_submit(e) {
    var dialog = $(this).closest(".ui-dialog").find(".ui-dialog-content");
    var form = $(this).find("form");
    form.attr('action', $('#upload-new-disassembly-version').attr('data-action'));
    var data = form.serialize();
    $.ajax({
        type: "POST",
        url: form.attr('action'),
        data: data,
        datatype: 'json',
        success: function(data) {
            $('#form-upload-new-version-results').html(data.message).show();
        }
    });
}

$(document).ready(function() {
    $('#disassembly_description').editable(function(value, settings) {
        return function(value, settings, elem) {
            var data = {
                description: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_disassembly_description,
                data: data,
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'textarea',
            height: "50px",
            width: "400px",
            tooltip: "",
            cancel: "Cancel",
            submit: "Ok",
            onblur: 'ignore',
    });

    $('#disassembly_tool_details').editable(function(value, settings) {
        return function(value, settings, elem) {
            var data = {
                details: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_disassembly_tool_details,
                data: data,
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'textarea',
            height: "50px",
            width: "400px",
            tooltip: "",
            cancel: "Cancel",
            submit: "Ok",
    });

    $('#disassembly_tool_name').editable(function(value, settings) {
        return function(value, settings, elem) {
            var data = {
                name: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_disassembly_tool_name,
                data: data,
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'textarea',
            height: "50px",
            width: "400px",
            tooltip: "",
            cancel: "Cancel",
            submit: "Ok",
    });

    $('#disassembly_type').editable(function(value, settings) {
        revert = this.revert;
        var her = $(this).closest('tr').find('.object_status_response');
        return function(value, settings, elem) {
            var data = {
                data_type: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: $(elem).attr('action'),
                data: data,
                success: function(data) {
                    if (!data.success) {
                        her.removeClass('ui-icon-circle-check');
                        her.addClass('ui-icon');
                        her.addClass('ui-icon-alert');
                        her.attr('name', data.message);
                        value = revert;
                    } else {
                        her.removeClass('ui-icon-alert');
                        her.addClass('ui-icon');
                        her.addClass('ui-icon-circle-check');
                        her.attr('name', "Success!");
                    }
                }
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'select',
            data: function() {
                    var dtypes = {};
                    var sorted = [];
                    $.ajax({
                      type: "POST",
                      async: false,
                      url: get_disassembly_type_dropdown,
                      data: '',
                      success: function(data) {
                        sorted = data.data;
                        sorted.sort();
                        len = sorted.length
                        for (var i=0; i < len; i++) {
                            dtypes[sorted[i]] = sorted[i];
                        }
                    }
                    });
                    return dtypes;
                },
            style: "display:inline",
            submit: "OK",
    });

    $( "#delete_disassembly" ).click( function() {
                    $( "#delete-disassembly-form" ).dialog( "open" );
    });
    $( "#delete-disassembly-form" ).dialog({
                    autoOpen: false,
                    modal: true,
                    width: "auto",
                    height: "auto",
                    buttons: {
                                    "Delete Disassembly": function() {
                                                    $("#form-delete-disassembly").submit();
                                    },
                                    "Cancel": function() {
                                                    $( this ).dialog( "close" );
                                    },
                    },
                    close: function() {
                                    // allFields.val( "" ).removeClass( "ui-state-error" );
                    },
    });

    $('#versions_button').on('click', function(e) {
        $.ajax({
            type: 'POST',
            url: get_disassembly_versions,
            success: function(data) {
                $('#disassembly_versions').find('option').remove();
                $("div[id^=version_]").remove();
                $.each(data, function(i, d) {
                    $('#disassembly_versions').append('<option value=' +  d.version + '>' + d.version + ' - ' + d.name + '</option>');
                    $('#versions_container').append('<div id="version_' + d.version + '" style="display: none;" data-link="' + d.link + '"><pre>' + escapeHtml(d.data) + '</pre></div>');
                });
                $('#disassembly_versions')
                .html($("option", $('#disassembly_versions')).sort(function(a, b) {
                    var arel = parseInt($(a).attr('value'), 10) || 0;
                    var brel = parseInt($(b).attr('value'), 10)|| 0;
                    return arel == brel ? 0 : arel < brel ? -1 : 1
                }));
                $('#disassembly_versions').trigger('change');
            }
        });
    });

    $('#disassembly_versions').on('change', function(e) {
        $("div#versions_container").find('div').hide();
        $('div#version_' + this.value).show();
        var link = '<a href="' + $('div#version_' + this.value).attr('data-link') + '">View Details</a>';
        $('span#disassembly_version_info').html(link);
    });


    $('#jump_versions').on('change', function(e) {
        var version = this.value;
        window.location.href = details_by_link + "?version=" + version;
    });

    var version = $('#jump_versions').attr('data-version');
    var versions = $('#jump_versions').attr('data-length');
    var data_link = $('#jump_versions').attr('data-link');
    var i;
    for (i = 1; i <= versions; i++) {
        if (i == version) {
            $('#jump_versions').append('<option value=' + i + ' selected="selected">' + i + '</option>');
        } else {
            $('#jump_versions').append('<option value=' + i + '>' + i + '</option>');
        }
    }

    var localDialogs = {
        "upload-new-disassembly-version": {title: "Upload New Version",
            open: upload_new_version_dialog,
            new: { submit: upload_new_version_dialog_submit },
        },
    };

    $.each(localDialogs, function(id,opt) { stdDialog(id, opt) });
    details_copy_id('Disassembly');
    toggle_favorite('Disassembly');
}); //document.ready
