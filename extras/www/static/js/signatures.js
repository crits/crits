function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    var res = div.innerHTML;
    div.remove();
    return res;
}

function append_inline_comment(data) {
    var line_el = $('tr.file_line[data-position="' + (Number(data.line) + 1) + '"]');
    if (line_el.length < 1) {
        var line_el = $('table.line_table tr.inline_comment:last');
        if (line_el.length < 1) {
            var line_el = $('tr.file_line[data-position="' + data.line + '"]');
        }
        line_el.after(data.html);
    } else {
        line_el.before(data.html);
    }
}

function diffUsingJS(from_text, to_text, from_header, to_header, output_div) {
    var base = difflib.stringAsLines(from_text);
    var newtxt = difflib.stringAsLines(to_text);
    var sm = new difflib.SequenceMatcher(base, newtxt);
    var opcodes = sm.get_opcodes();
    $(output_div).empty()
        .append(diffview.buildView({
            baseTextLines:base,
            newTextLines:newtxt,
            opcodes:opcodes,
            baseTextName:from_header,
            newTextName:to_header,
            viewType:0}));
}

function upload_new_signature_version_dialog(e) {
    var dialog = $(this);
    var form = dialog.find("form");
    var widget = dialog.dialog("activatedBy");
    var copy_rels = '<tr><th><label for="id_copy_relationships">Copy relationships:</label></th><td><input id="id_copy_relationships" name="copy_relationships" type="checkbox"></td></tr>';

    if (!form.find("#id_copy_relationships").length) {
        form.find("#id_data").closest('tr').after(copy_rels);
    };

    if (!form.attr("_dialog_once")) {
        copy_button = {'Copy Data From Current Version': function() {
            //title
            form.find("#id_title").val($('#signature_title').attr('data-title'));
            //data_type
            form.find("#id_data_type").val($('#signature_type').text());
            //description
            form.find("#id_description").val($('#object_description').text());
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

function upload_new_signature_version_dialog_submit(e) {
    var dialog = $(this).closest(".ui-dialog").find(".ui-dialog-content");
    var form = $(this).find("form");
    form.attr('action', $('#upload-new-signature-version').attr('data-action'));
    var data = form.serialize();
    $.ajax({
        type: "POST",
        url: form.attr('action'),
        data: data,
        datatype: 'json',
        success: function(data) {
            $('#form-upload-new-signature-version-results').html(data.message).show();
        }
    });
}

$(document).ready(function() {

    $(document).on('click', '#highlight_comment', function(e) {
        $(this).editable(function(value, settings) {
            var line = $(this).closest('tr').find('td:nth-child(2)').text();
            return function(value, settings, elem) {
                var data = {
                    comment: value,
                    line: line,
                };
                $.ajax({
                    type: "POST",
                    async: false,
                    url: update_signature_highlight_comment,
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
        $(this).trigger('click');
    });

    $(document).on('click', '#highlight_date', function(e) {
        $(this).editable(function(value, settings) {
            var line = $(this).closest('tr').find('td:nth-child(2)').text();
            return function(value, settings, elem) {
                var data = {
                    date: value,
                    line: line,
                };
                $.ajax({
                    type: "POST",
                    async: false,
                    url: update_signature_highlight_date,
                    data: data,
                });
                return value;
            }(value, settings, this);
            },
            {
                event: 'highlight_date',
                type: 'datetimepicker',
                width: "225px",
                data: '',
                style: "display: inline",
                tooltip: "",
                cancel: "Cancel",
                submit: "Ok",
        });
        $(this).trigger('highlight_date');
    });

    $('#signature_type').editable(function(value, settings) {
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
                        her.attr('title', data.message);
                        value = revert;
                    } else {
                        her.removeClass('ui-icon-alert');
                        her.addClass('ui-icon');
                        her.addClass('ui-icon-circle-check');
                        her.attr('title', "Success!");
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
                      url: get_signature_type_dropdown,
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

    $( "#delete_signature" ).click( function() {
                    $( "#delete-signature-form" ).dialog( "open" );
    });
    $( "#delete-signature-form" ).dialog({
                    autoOpen: false,
                    modal: true,
                    width: "auto",
                    height: "auto",
                    buttons: {
                                    "Delete Signature": function() {
                                                    $("#form-delete-signature").submit();
                                    },
                                    "Cancel": function() {
                                                    $( this ).dialog( "close" );
                                    },
                    },
                    close: function() {
                                    // allFields.val( "" ).removeClass( "ui-state-error" );
                    },
    });

    $('tr.file_line').on('mouseover', function(e) {
        var dts = $('#add_inline_comment').detach();
        var me = $(this);
        dts.css({
            display: 'inline-block',
            float: 'right',
        }).attr('data-position', me.attr('data-position'));
        me.children('td:last').append(dts);
    });

    $('table.line_table').on('mouseout', function(e) {
        $('#add_inline_comment').hide();
    });

    $('#add_inline_comment').on('click', function(e) {
        var line_num = $(this).closest('tr').attr('data-position');
        var act = $(this).attr('action');
        if (act.lastIndexOf('/') != -1) {
            act = act.substring(0, act.lastIndexOf('/'));
        }
        act = act + "/?line=" + line_num;
        $(this).attr('action', act);
    });

    $('#versions_button').on('click', function(e) {
        $.ajax({
            type: 'POST',
            url: get_signature_versions,
            success: function(data) {
                $('#signature_versions').find('option').remove();
                $("div[id^=version_]").remove();
                $.each(data, function(i, d) {
                    $('#signature_versions').append('<option value=' +  d.version + '>' + d.version + ' - ' + d.title + '</option>');
                    $('#versions_container').append('<div id="version_' + d.version + '" style="display: none;" data-link="' + d.link + '"><pre>' + escapeHtml(d.data) + '</pre></div>');
                });
                $('#signature_versions')
                .html($("option", $('#signature_versions')).sort(function(a, b) {
                    var arel = parseInt($(a).attr('value'), 10) || 0;
                    var brel = parseInt($(b).attr('value'), 10)|| 0;
                    return arel == brel ? 0 : arel < brel ? -1 : 1
                }));
                $('#signature_diff_selector').html($('#signature_versions').html());
                $('#signature_versions').trigger('change');
            }
        });
    });

    $('#signature_versions').on('change', function(e) {
        $("div#versions_container").find('div').hide();
        $('div#version_' + this.value).show();
        var link = '<a href="' + $('div#version_' + this.value).attr('data-link') + '">View Details</a>';
        $('span#signature_version_info').html(link);
    });

    $('#signature_versions_diff').on('submit', function(e) {
        e.preventDefault();
        var versions = $('#signature_diff_selector').val();
        var first = $('div#version_' + versions[0]).children('pre').text();
        var first_title = $("#signature_diff_selector option[value='" + versions[0] + "']").text()
        var second = $('div#version_' + versions[1]).children('pre').text();
        var second_title = $("#signature_diff_selector option[value='" + versions[1] + "']").text()
        diffUsingJS(first, second, first_title, second_title, $('#diff_results'));
        $("div#versions_container").find('div').hide();
        $('#diff_results')
        .css('width', '100%')
        .show();
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

    var highlighted_lines = [];
    $('div#highlights_section table tbody tr').each(function() {
        highlighted_lines.push([$(this).find('td:nth-child(2)').text(),
                                $(this).find('td:nth-child(4)').text()]);
    });
    $.each(highlighted_lines, function(i,v) {
        highlight_line(v);
    });

    var localDialogs = {
        "upload-new-signature-version": {title: "Upload New Version",
            open: upload_new_signature_version_dialog,
            new: { submit: upload_new_signature_version_dialog_submit },
        },
    };

    $.each(localDialogs, function(id,opt) { stdDialog(id, opt) });
    details_copy_id('Signature');
    toggle_favorite('Signature');
});
