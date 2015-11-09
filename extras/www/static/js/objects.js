function updateObjectSource(value, settings, elem, update) {
    var guardian = $(elem).closest("tr");
    var guard = $(elem).parent();
        var data = {
            coll: $(guardian).attr('coll'),
            oid: $(guardian).attr('oid'),
            type: $(guardian).attr('type'),
            value: $(guardian).attr('vvalue'),
        };

    data['new_source'] =  $(guard).find("span[name='source_name']").attr('sname');
    data['new_method'] =  $(guard).find("span[name='source_method']").attr('method');
    data['new_reference'] =  $(guard).find("span[name='source_reference']").attr('reference');

        if (update == "name") {
            data['new_source'] =  value;
        } else if (update == "method") {
            data['new_method'] =  value;
    } else {
            data['new_reference'] =  value;
        };
        $.ajax({
            type: "POST",
            async: false,
            url: update_objects_source,
            data: data,
        });
        return value;
}

function getAllObjectTypes(sel) {
    if (typeof(obj_types_url) != "undefined") {
        var return_data = {};
        $.ajax({
            type: "POST",
            url: obj_types_url, //defined in base.html
            async: false,
            datatype: 'json',
            success: function(data) {
                if (data.types) {
                    var sorted = [];
                    if (sel) {
                        sel.empty();
                    }
                    $.each(data.types, function(key, value) {
                        sorted.push(key);
                    });
                    sorted.sort();

                    $.each(sorted, function(index, value) {
                        if (sel) {
                            sel.append('<option value="'+value+'">'+value+'</option>');
                        } else {
                            return_data[value] = value;
                        }
                    });
                }
            }
        });
        if (!sel) {
            return return_data;
        }
    }
}

function add_object_submit(e) {
    // my_id and my_type are set in objects_listing_widget - also added data-id data-type attr, but not used yet
    var elem = $(e.currentTarget);
    var dialog = elem.closest(".ui-dialog");
    var form = dialog.find("form");
    if (elem.attr("id") === "add_object_static") {
    dialog = elem.closest("td");  // Not a dialog, but needed to find message box below
    form = $("#form-add-object-static");
    }
    var csrftoken = readCookie('csrftoken');
    form.append("<input type='hidden' name='csrfmiddlewaretoken' value='" + csrftoken + "'>");

    // log(elem);
    // log(form);

    form.find("#id_oid").val(my_id);
    form.find("#id_otype").val(my_type);
    var target = form.find('option:selected');
    var value_type = target.val();
    if (value_type === "File Upload") {
    form.submit();
    } else {
        e.preventDefault();
        var result = form.serializeArray();
        result.push({ 'name': 'relationship_value', 'value': relationship_value });
        // need to add from subscription the type and id of the document we are adding to
        $.ajax({
            type: "POST",
        url: form.attr('action'),
            data: result,
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    post_add_patchup(form, data);
                } else {
                    form.find('#id_object_type').change();
                }
                if (data.message) {
                    dialog.find(".message")
                        .show()
                        .css('display', 'table')
                        .effect('highlight', {}, 5000)
                        .html(data.message)
                        .delay(3000);
                }
            }
        });
    }
}

function change_object_type_field(e) {
    var elem = $(e.currentTarget);
    var dialog = elem.closest(".ui-dialog");
    if (!dialog,length) {
    dialog = $(e.currentTarget).closest("div"); // At least find a container for -static versions
    }
    var form = dialog.find("form");

    var value_field = $(form).find('#id_value');
    var indicator_field = $(form).find('#id_add_indicator');
    var target = elem.find('option:selected');
    var value_val = target.val();
    var new_value_field;

    if (value_val == "File Upload") {
        new_value_field = $('<input type="file" name="value" id="id_value">');
        indicator_field.attr("disabled", true);
    } else { //assume "string"
        new_value_field = $('<textarea name="value" rows="4" cols="28" id="id_value" />');
        indicator_field.removeAttr("disabled");
    }
    value_field.replaceWith(new_value_field);
}

/*******************************************************************************
 * Name: object_indicator_duplicate_crosscheck
 *
 * Description: Performs client-side crosschecking of objects and
 * indicator relationships to indicate to a user if an object might
 * already have an indicator created already. This is to prevent duplicate
 * indicators from existing and also to reduce the manual cross checking a
 * user would have to manually perform.
 *
 * This method should be called only within the page context where a
 * object_listing_widget is loaded.
 *
 * @params - None
 * @returns - None. Icons are changed in the objects listing table
 *      to indicate any objects that might already have indicators.
 ******************************************************************************/
function object_indicator_duplicate_crosscheck() {
    /* This is client side crosschecking of email fields to see
     * if an indicator has been created. This is not needed
     * right now since there is server-side validation though
     * there might be a time when we would want to do client
     * side processing to alleviate server load.
     */
    var textTypeValueSet = {}

    $('#relationship_listing_table_indicator tbody tr').each(function() {
        // create a map of a map for a multi-key map
        var ind_value = $(this).attr('data-value')
        var ind_type = $(this).attr('data-type')

        if((typeof textTypeValueSet[ind_type] !== 'undefined')) {
            textTypeValueSet[ind_type][ind_value] = true
        } else {
            textTypeValueSet[ind_type] = {}
            textTypeValueSet[ind_type][ind_value] = true
        }
    })

    $('table[name=object_listing_table] tbody tr').each(function() {
        var obj_value = $(this).attr('vvalue')
        var obj_type = $(this).attr('type')

        if(obj_type in textTypeValueSet) {
            if(obj_value in textTypeValueSet[obj_type]) {
                var iconNode = $(this).find('.indicator_from_object')
                var originalTitle = $(iconNode).prop('title')
                $(iconNode).removeClass('ui-icon-plusthick').addClass('ui-icon-circle-plus')
                %(iconNode).prop('title', originalTitle + ": Warning: Indicator might already exist")
            }
        }
    })
}

// This feels like a special case that could be noramlized --BD
function post_add_patchup(elem, data) {
    elem.find('#id_value').val("");
    $('#object_box_container').parent().html(data.html);
    if (data.rel_made) {
        $('#relationship_box_container').parent().html(data.rel_msg);
    }
    //elem.parent().dialog( "close" );
}

function add_object_dialog(e) {
    var dialog = $("#dialog-add-object").closest(".ui-dialog");
    var form = dialog.find("form");

    file_upload_dialog(e);
}

$(document).ready(function() {
    // had an unbind
    $(document).on('click', '.indicator_from_object', function(event) {
        var me = $(this);
        var guardian = me.closest("tr");
        var value = $(guardian).attr('vvalue');
        var source = $(guardian).find("span[name='source_name']").attr('sname');
        var method = $(guardian).find("span[name='source_method']").attr('method');
        var reference = $(guardian).find("span[name='source_reference']").attr('reference');

        // Might be nicer if this was a spinning icon, but working with what we have handy
        me.removeClass('ui-icon-plus');
        me.removeClass('ui-icon-circle-plus');
        me.removeClass('ui-icon-alert');
        me.addClass('ui-icon-clock');

        data = {
            'ind_type': $(this).attr('data-type'),
            'value': value,
            'rel_type': my_type,
            'rel_id': my_id,
            'source': source,
            'method': method,
            'reference': reference,
        };
        $.ajax({
            type: "POST",
            url: indicator_from_object,
            data: data,
            dataType: "json",
            success: function(data) {
                me.removeClass('ui-icon-clock');
                me.removeClass('ui-icon-plus');
                me.removeClass('ui-icon-circle-plus');
                me.removeClass('ui-icon-circle-alert');
                if (data.success) {
                    $('#relationship_box_container').parent().html(data.message);
                    me.addClass('ui-icon-circle-check');
                    me.attr('title', "Success!");
                } else {
                    me.addClass('ui-icon-alert');
                    me.attr('title', data.message);
                }

                qtip_container_setup();
            }
        });
    });

    $(document).on('change', '.object-types', function(e) {
        change_object_type_field(e);
    }).change();

    $(document).on('click', '.objects_dropdown', function(e) {
        $(this).parent().next('td').children('table').toggle();
        if ($(this).parent().next('td').children('table').is(":visible")) {
            $(this).toggleClass('ui-icon-triangle-1-s ui-icon-triangle-1-e');
        } else {
            $(this).toggleClass('ui-icon-triangle-1-e ui-icon-triangle-1-s');
        }
    });

    $(document).on('click', 'a.object_value_search', function(e) {
        var cv = $(this).find('form');
        if (cv.length) {
            return false;
        } else {
            return true;
        }
    });
    $(document).on('click', 'span.edit_object_value', function(e) {
        var obj_edit = $(this).closest("td").find("span[name='object_value']");
        obj_edit.trigger('custom_edit');
    });
    $("span[name='object_value']").editable(function(value, settings) {
        return function(value, settings, elem) {
        var guardian = $(elem).closest("tr");
        var data = {
            coll: $(guardian).attr('coll'),
            oid: $(guardian).attr('oid'),
            type: $(guardian).attr('type'),
            value: $(guardian).attr('vvalue'),
            new_value: value,
        };
        $.ajax({
            type: "POST",
                async: false,
                url: update_objects_value,
                data: data,
                });
        var link_edit = guardian.children("td:first").next().children("div:first").children("a:first");
        var link_url = link_edit.attr('href');
        var link_split = link_url.split('=');
        link_split[link_split.length -1] = data['new_value'];
        var new_url = link_split.join('=');
        link_edit.attr('href', new_url);
        return value;
        }(value, settings, this);
        },
        {
            event: 'custom_edit',
            tooltip: "",
            style: 'inherit',
    });
    $(document).on('click', "span[name='source_name']", function(e) {
        $(this).editable(function(value, settings) {
            return updateObjectSource(value, settings, $(this), "name");
            },
            {
                tooltip: "Edit Name",
                type: 'select',
                data: function() {
                    var dtypes = {};
                    var sorted = [];
                    $.ajax({
                      type: "POST",
                      async: false,
                      url: get_user_source_list,
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
                style: 'display:inline',
                cancel: 'Cancel',
        submit: 'OK',
        });
    });
    $(document).on('click', "span[name='source_method']", function(e) {
        $(this).editable(function(value, settings) {
            return updateObjectSource(value, settings, $(this), "method");
            },
            {
                tooltip: "Edit Method",
                placeholder: "Click to edit",
                style: 'inherit',

        });
    });
    $(document).on('click', "span[name='source_reference']", function(e) {
        $(this).editable(function(value, settings) {
            return updateObjectSource(value, settings, $(this), "reference");
            },
            {
                tooltip: "Edit Reference",
                placeholder: "Click to edit",
                style: 'inherit',
        });
    });

    var localDialogs = {
      "add-object": {title: "Add Object", open: add_object_dialog,
             new: { submit: add_object_submit } },
    };

    $.each(localDialogs, function(id,opt) {
        stdDialog(id,opt);
    });

});
