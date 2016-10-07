//
// Collect all the dialog related functions here.
//

// ----------------------------------------
// New Dialog Initializations - Streamlined
// ----------------------------------------


var newDialog = function(id) {
    var d = $('#dialog-' + id);
    if (d.length)  {
    return d;
    } else {
    return $("<div id='dialog-" + id + "'></div>").hide().appendTo("body");
    }
}

var newPersona = function(title, attr, submitAction, isPreventButtons) {
    var newobj = {title: title};

    if(isPreventButtons !== true) {
        newobj['buttons'] = {};
        newobj['buttons'][title] = submitAction;
        newobj['buttons']['Cancel'] = function(e) { $(this).dialog('close'); };
    }

    newobj =  $.extend(newobj, attr);

    return newobj;
}

var stdPersonas = function(title, opt) {
    var submit_title;
    var update_title;
    if (title !== "" && title.indexOf(" ")>0) {
    submit_title =  title;
    update_title = title;  // Not always good, but caller can fix, maybe this is not a split personality kind of dialog
    } else {
    submit_title = "New " + title;
    update_title = "Update " + title;
    }

    // .submit could be stripped as well, but it is harmless for now.
    return {new:    newPersona(submit_title, opt.new, opt.new.submit, opt.is_prevent_buttons),
        update: newPersona(update_title, opt.update, opt.update.submit, opt.is_prevent_buttons)
        };
}

var stdDialog = function(id, options, defaultOptions) {
    // need local opt copy so we can modify defaults
    var opt = $.extend(true, {}, defaultOptions, options);
    var title = opt.title;

    // opt.new and opt.update are a shorthand notation passing the
    // more common submit handlers for the different persona

    // opt.personas.PERSONA.X is the full option path

    // However both of these option objects will be pushed into
    // resulting object, shorthand first, then full path below

    if (opt.new === undefined)
    opt.new = {};
    if (opt.update === undefined)
    opt.update = {};

    // Default actions for Personas
    // On one hand, setting this in each persona means that any extra
    // personas added will need it set but it makes the newPersona
    // logic easier, caller must handle all the other handlers, open,
    // close, etc ?

    if (opt.new.submit === undefined)
        opt.new.submit = opt.submit || addEditSubmit;
    if (opt.update.submit === undefined)
        opt.update.submit = opt.submit || addEditSubmit;
    if (opt.modal === undefined)
        opt.modal = true;

    // Make a copy of opts with the non-dialog options stripped (ones used by stdPersonas)
    var globalopt = $.extend({}, opt);
    delete globalopt.new;
    delete globalopt.update;

    var dialogopt = $.extend(true, {href: get_dialog_url + "?dialog=" + id,
                                    autoOpen: false,
                                    personas: stdPersonas(title, opt)},
                                    globalopt);
    var dialog = newDialog(id).dialog(dialogopt);
    return dialog;
};

function incrementCount(elem, delta, delete_row) {
    //update the item count, if there is one
    if (elem) {
        var count = elem.find('div.count,span.count').first();
        var count_int = parseInt(count.html());

        if (!isNaN(count_int)) {
            count_int += delta;
            // don't let counts go below 0
            if (count_int < 0) {
                count_int = 0;
            }
            count.html(count_int);
            if (count_int === 0 && delete_row) {
                elem.remove();
            }
        }
    }
}

function delete_object_click(e, item_type, del_label, data) {
    var elem = $(e.currentTarget);
    var action = elem.attr('action');

    // We want to follow page redirects to new listing, so craft a form and submit() it
    var fn = (function(e) {
        return function() {
        var form = "<form method='POST' action='" + action + "'>";
        var csrftoken = readCookie('csrftoken');
        form = form + "<input type='hidden' name='csrfmiddlewaretoken' value='" + csrftoken + "'>"
        $.each(data, function(k,v) { form = form + $("input").attr("type","hidden").attr("name",k).val(v).html(); } );
        form = form + "</form>";
        $(form).appendTo("body").submit();
    };
    })(e);

    confirmDelete(del_label, fn);
}

function populate_id(id, type) {
    // Upload a related pcap (Using the related dialog persona)
    $( "#dialog-new-pcap" ).on("dialogopen.add_related_pcap", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        // $(this).find("form").removeAttr("target"); // Get rid of target to refresh page
        // Unlike new-sample below, this does not redirect us nor refresh the
        // Relationships list of the Sample, so delay for a few seconds then reload the
        // page after uploaded.  Added a fileUploadComplete event to work around this.
        $(this).find("form").bind("fileUploadComplete",
                    function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
        }
    });

    // Upload a related Domain (Using the related dialog persona)
    $( "#dialog-new-domain" ).on("dialogopen.add_related_domain", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Upload a related Sample (Using the related dialog persona)
    $( "#dialog-new-sample" ).on("dialogopen.add_related_domain", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("fileUploadComplete",
                    function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
        }
    });
    // Add a related Actor (Using the related dialog persona)
    $( "#dialog-new-actor" ).on("dialogopen.add_related_actor", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related Target (Using the related dialog persona)
    $( "#dialog-new-target" ).on("dialogopen.add_related_target", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related Email (Using the related dialog persona)
    $( "#dialog-new-email-eml" ).on("dialogopen.add_related_email", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        // $(this).find("form").removeAttr("target"); // Get rid of target to refresh page

        // Unlike new-sample below, this does not redirect us nor refresh the
        // Relationships list of the Sample, so delay for a few seconds then reload the
        // page after uploaded.  Added a fileUploadComplete event to work around this.
        $(this).find("form").bind("fileUploadComplete",
                    function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
        }
    });
    // Add a related Email (Using the related dialog persona)
    $( "#dialog-new-email-outlook" ).on("dialogopen.add_related_email", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        // $(this).find("form").removeAttr("target"); // Get rid of target to refresh page

        // Unlike new-sample below, this does not redirect us nor refresh the
        // Relationships list of the Sample, so delay for a few seconds then reload the
        // page after uploaded.  Added a fileUploadComplete event to work around this.
        $(this).find("form").bind("fileUploadComplete",
                    function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
        }
    });
    // Add a related Email (Using the related dialog persona)
    $( "#dialog-new-email-raw" ).on("dialogopen.add_related_event", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related Email (Using the related dialog persona)
    $( "#dialog-new-email-yaml" ).on("dialogopen.add_related_event", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related Email (Using the related dialog persona)
    $( "#dialog-new-email-fields" ).on("dialogopen.add_related_event", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related Event (Using the related dialog persona)
    $( "#dialog-new-event" ).on("dialogopen.add_related_event", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related Exploit (Using the related dialog persona)
    $( "#dialog-new-exploit" ).on("dialogopen.add_related_exploit", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related Indicator (Using the related dialog persona)
    $( "#dialog-new-indicator" ).on("dialogopen.add_related_indicator", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related Indicator (Using the related dialog persona)
    $( "#dialog-new-indicator-csv" ).on("dialogopen.add_related_indicator", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("fileUploadComplete",
                    function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
        }
    });
    // Add a related Indicator (Using the related dialog persona)
    $( "#dialog-indicator-blob" ).on("dialogopen.add_related_indicator", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related IP (Using the related dialog persona)
    $( "#dialog-new-ip" ).on("dialogopen.add_related_ip", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related backdoor (Using the related dialog persona)
    $( "#dialog-new-backdoor" ).on("dialogopen.add_related_backdoor", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    // Add a related campaign (Using the related dialog persona)
    $( "#dialog-new-campaign" ).on("dialogopen.add_related_campaign", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    $( "#dialog-new-certificate" ).on("dialogopen.add_related_certificate", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("fileUploadComplete",
                    function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
        }
    });
    // Add a related Raw Data (Using the related dialog persona)
    $( "#dialog-new-raw-data" ).on("dialogopen.add_related_raw_data", function() {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
    $( "#dialog-new-raw-data-file" ).on("dialogopen.add_related_raw_data_file", function() {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("fileUploadComplete",
                    function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
        }
    });
    $( "#dialog-new-signature" ).on("dialogopen.add_related_signatures", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(id);
        $(this).find("form #id_related_type").val(type);
        $(this).find("form").bind("addEditSubmitComplete",
            function(e, response) {
                    $.ajax({
                      type: "POST",
                      success: function() {
                          $('#relationship_box_container').load(location.href + " #relationship_box_container");
                      }
                    })
              });
          }
    });
}

function delete_item_click(e, item_type, del_label, data) {
    e.preventDefault();

    var elem = $(e.currentTarget);

    var fn = function(e) {
        return function() {
            $.ajax({
                type:'POST',
                data:data,
                url: elem.attr('action'),
                success: function(data) {
                    if (data.success) {
            if (data.html) { // ajax provided replacement html, use it.
                elem.closest(".guardian").html(data.html);
            } else if (data.last) { //used for collapsible items
                            var to_delete = me = elem.parentsUntil('tr').parent();
                            if (to_delete.hasClass('expand-child')) {
                                //last item in listing, not "delete all" button
                                to_delete = to_delete.add(me.prev());
                            }

                            to_delete = to_delete.add(me.nextUntil('[class!="expand-child"]'));
                            $(to_delete).remove();
                        } else {
                incrementCount(elem.closest(".content_box"), -1, false);
                // For objects that have local count as well
                incrementCount(elem.closest("tr").parent().closest("tr"), -1, true);

                            elem.closest('tr').remove();
                        }
                    } else {
                        var msg = "";
                        if (data.message) {
                            if ($.isArray(data.message)) {
                                data.message = data.message.join('<br>');
                            }
                            msg = data.message;
                        } else {
                            msg = "Unknown error; unable to delete "+item_type;
                        }
                        error_message_dialog('Delete Item Error', msg);
                    }
                }
            });
        }
    }(e);
    confirmDelete(del_label, fn);
}

function confirmDelete(del_label, success_callback, args) {
    var buttons = {};

    // Figure out how to bring more details back, object_delete did this:
    // $('#confirm_delete .deletemsg').html("Delete " + trow.attr('type') +
    //                      " Object: <br/><b>" +
    //                      trow.find("[name='object_value']").text() +
    //                      "</b>");

    buttons[del_label] = function() {
        $(this).dialog('close');
        success_callback(args);
    };
    buttons["Cancel"] = function() {$(this).dialog('close');};


    $('<div><span>Are you sure you want to delete?  This action cannot be undone.</span></div>').dialog({
        autoOpen: true,
    width: "auto",
    height: "auto",
        modal: true,
        buttons: buttons,
        title: del_label
    });
}

function add_edit_post_success(data,dialog,loc,item_type,e,final_callback) {
    form = dialog.find("form");

    if (data.success) {
    form.find('ul.errorlist').remove(); // Clear any errors now, if they still exist we'll get a new form back
    //update listing with new item
    var new_i = $(data.html);
    var listing_type = item_type;
    //if this is a static form (e.g., the "Tools" tab on samples/details), make sure we
    if (data.inline) {
        append_inline_comment(data);
        if (data.message) {
            display_server_msg(data.message, dialog); // item_type);
        }
        return;
    }
    //  update the main listing
    var idx = item_type.indexOf('-static');
    if (idx != -1) {
        listing_type = item_type.substring(0, idx);
    }
    var listing = $('#'+listing_type+'_listing tbody');
    if (listing.length && listing_type != "indicator") {
        //  replace old item with new if 'edit'
        if (loc !== null && loc !== undefined) {
        listing.find('tr').eq(loc).replaceWith($(new_i));
        } else { //'add', so add new item to list
        //if collapsible, replace the entire object

        //NOTE: we're assuming that collapsible lists have their Add button
        //  somewhere other than the end of the listing.  If that assumption changes
        //  in the future, this code will need to be modified.  This may be a good
        //  instance variable if we end up converting these helper functions into
        //  (a) jQuery plugin(s).

        if (data.header) {
            listing = listing.find('tr');
            //find list to replace
            var added = listing.find('[data-field="'+data.data_field+'"]:contains("'+data.header+'")').parentsUntil('table','tr').prev().remove().end().replaceWith($(new_i));
            if (!added.length) { //nothing to replace; this is the first of its type

            // make sure it's before the "OTHER" item if that item exists
            //n(currently used only for non-allowed sources)

            // NOTE: again, this may be a good candidate for an instance
            // variable (something like a boolean indicating whether the "OTHER"
            // object may exist).
            var other = listing.find('.other_'+item_type);
            if (!other.size()) { //check if at the top level
                other = listing.filter('.other_'+item_type);
            }
            if (!other.size()) { //doesn't exist; put before "Add" button
                listing.last().after($(new_i));
            } else { //place before "OTHER" item
                other.before($(new_i));
            }
            }
            // XXXX Why Collapse? Show them what they did
            collapse();
        } else {
            // dirty hack for determining if this is a comment on the aggregate page
            if (item_type == "comment" && !$('#add_comment').length) {

            // aggregate comments are listed in reverse order (order would be a
            // good instance variable...)
            listing.find('tr').first().before($(new_i));
            } else {
            var tmp_lst = listing.find('tr');
            //if this is the first we're adding
            if (!tmp_lst.length) {
                listing.append($(new_i));
                //also show the header
                listing.prev('thead').find('tr').show();
            } else {
                tmp_lst.last().after($(new_i));
            }
            }

            incrementCount(listing.closest('div'), 1);
        }
        }

        clear_form(dialog);
        set_date_field(form);

        // If we we just did an update and it was successful, close it.
        if (dialog.hasClass("ui-dialog-content") && dialog.dialog("persona") == "update") {
        dialog.dialog("close");
        }

        //close the dialog only if we're on a listing page. Otherwise we want to
        //  provide a link for redirecting to the details page.
        //$('#add-'+item_type+'-form').dialog('close');
    }
    } else if (data.form) {
    re_render_form(dialog, data.form, e);
    }

    if (data.message) {
    form.trigger("addEditSubmitComplete");
    display_server_msg(data.message, dialog); // item_type);
    }

    if (final_callback && typeof(final_callback) == "function") {
        final_callback();
     }
}

function addEditSubmit(e) {
    e.preventDefault();

    var dialog = $(e.currentTarget).closest(".ui-dialog").find(".ui-dialog-content");
    if (!dialog.length) {
    dialog = $(e.currentTarget).closest("div"); // At least find a container mainly for
                            // -static versions
    }
    var form = dialog.find("form");

    var sel = form.find('#id_action_type');
    if (typeof sel !== "undefined") {
        sel.attr('disabled', false);
    }

    var type = form.attr('item-type');
    if (!type)
    log("Form (" + form.attr('id') + ") should have a defined item-type");

    var updateloc;
    if ($(dialog).data("crits")) {
    updateloc = $(dialog).data("crits").updateloc;
        delete $(dialog).data("crits").updateloc;
    }

    var submit_url = form.attr('action');
    if (submit_url === undefined) {
    return error_message_dialog("Internal JS Error",
                    "Form did not have a action url <br/>" +
                    "Dialog: " + dialog.attr("id"));
    } else {
    var data;
    if (form.attr('data')) {
        data = form.serializeArray();
        data.push({'name':'key', 'value': form.attr('data')});
        data = $.param(data);
    } else {
        data = form.serialize();
    }

    $.ajax({
        type: "POST",
            data: data,
            url: submit_url,
            success: function(data) { add_edit_post_success(data,dialog,updateloc,type,e); }
        });
    }
};

function flashMessage(elem, message) {
    // If the given element doesn't have .message class, insert a following element
    // This might be better as a tooltip?
    elem = $(elem);
    var msgbox = elem.find(".message");
    if (! msgbox.length) {
    if (! elem.next(".message").length) {
        elem.after(" <span class='message'/>");
    }
    msgbox = elem.next(".message");
    }

    msgbox.stop(true,false)
    .show().fadeTo(0,1)
    .effect('highlight', {}, 8000)
    .effect('fade', function() { $(this).html(""); }, 2000)
    .html(message);
}


function ajaxPostSuccess(data,elem, e) {
    log(data);
    log(elem);

    if (data.html) {
    elem.replaceWith(data.html);
    }
    if (data.text) {
    elem.find("span").html(data.text).attr('title', data.title);
    } else if (data.title) {
    $(elem).attr('title', data.title);
    }
    if (data.message) {
    flashMessage(elem, data.message);
    }
    if (data.reload || elem.data("reloadAfter")) { /* Refresh page */
    window.location.reload(true);
    }
}

function ajaxPost(e) {
    e.preventDefault();
    var elem = $(e.currentTarget).closest("form");

    var submit_url = elem.attr('action');
    if (submit_url === undefined) {
    return error_message_dialog("Internal JS Error",
                    "Elem did not have a action url <br/>");
    } else if (!elem.data('key')) {
    return error_message_dialog("Internal JS Error",
                    "Elem did not have json key <br/>");
    } else {
    var data;
    if (elem.attr('data')) {
        data = elem.serializeArray();
        data.push({'name':'key', 'value': elem.attr('data')});
        data = $.param(data);
    } else {
        data = elem.serialize();
    }

    $.ajax({
        type: "POST",
        data: data,
        url: submit_url,
            success: function(data) { ajaxPostSuccess(data,elem,e); }
        });

    }
};

function preference_toggle(e) {
    e.preventDefault();
    var elem = $(e.currentTarget);
    log(elem);
    $.ajax({
        type: 'POST',
        data: '',
        url: elem.attr('action'),
        success: function(data) { ajaxPostSuccess(data,elem,e); }
    });
}


function defaultSubmit(e) {
    var dialog = $(e.currentTarget).closest(".ui-dialog").find(".ui-dialog-content");
    var form = dialog.find('form');
    var csrftoken = readCookie('csrftoken');
    var input = $("<input>")
               .attr("type", "hidden")
               .attr("name", "csrfmiddlewaretoken").val(csrftoken);
    form.append($(input));
    form.submit();
}

function comment_reply_dialog(e) {
    $.proxy(update_dialog, this)(); // Copies over the parent reference and analyst
    $(this).find("#id_comment").val("");  // Give the user a blank slate..
}

function update_dialog(e) {
    var dialog = $(this);
    var form = dialog.find("form");
    var elem = dialog.dialog("activatedBy");  // dialog-persona saves the element that opened the dialog

    var cur_data_tds = elem.parent().siblings();

    // allow this function to be used by objects that don't want to
    // replace the old item after "edit" (This is the case with
    // comments, where we use essentially the same functionality for
    // replying as for editing, but obviously don't want to replace
    // the replied-to comment.)

    var replace = elem.attr("replace"); // Should this just tell us the element to replace?
    if (replace !== 'false' && (replace || replace === undefined ) ) {
    //save this item's location in the listing so we can replace it after edit
    var loc;

        //this is icky... :(
        //find the position of the parent tr so we can replace it
        // The tr is at a different level for comment rows.
        var parent = cur_data_tds.parentsUntil('tr').parent('tr');
        if (!parent.length) {
            parent = cur_data_tds.parent();
        }
        loc = parent.index();

    dialog.data("crits", {updateloc: loc});
    }

    // Give the form a placeholder for extra data fields if not already there.
    var dataelem = cur_data_tds.find(".extradata").filter("[data-field]");
    $.each(dataelem, function(k,v) {
            var field = $(v).attr("data-field");
            var value = $(v).text();

            if (!form.find("[name='" + field + "']").length) {
            form.append("<input type='hidden' name='" + field + "' value=''>");
            }
        });

    // get the form's inputs
    var inputs = form.find('input,select,textarea');
    var sel_val = null;

    // pre-populate form
    inputs.each(function(index) {
        var input = $(this);
        var field = input.attr('name');
        var value;

        // map input to table cell with "data-field" (changed from class) matching input name
        // first look at the top level
        // skip any fields with class of "no_edit" to allow static values to persist
        var data_elem = cur_data_tds.filter("[data-field='" + field + "']").not(".no_edit");

        if (!data_elem.length) {
            //look at child elems if not in the top level
            data_elem = cur_data_tds.find("[data-field='" + field + "']");
        }

    if (data_elem.length) { // some fields are set by default on page request and don't
                // need to be set here set here
        var value = data_elem.text();
        if (field == 'action_type') {
            sel_val = value;
        }
        if (input.attr('type') == 'radio') {
            // check the correct radio element
            input.filter('[value="'+value+'"]').prop('checked', true);
        } else {
            // handle empty analysis fields (default to current user)
            if (field == 'analyst' && !value) {
                input.val(username);                // defined in base.html
            } else {
                input.val(value.trim());
            }
        }
        }
     });
    var sel = form.find('#id_action_type');
    if (typeof sel !== "undefined") {
        if (typeof subscription_type !== "undefined") {
            $.ajax({
                type:'GET',
                data: {type: subscription_type},
                url: get_actions_for_tlo,
                success: function(data) {
                    $.each(data.results, function(x,y) {
                        sel.append($('<option></option>').val(y).html(y));
                    });
                    sel.find('option[value="' + sel_val + '"]').attr('selected', true);
                    sel.attr('disabled', true);
                }
            });
        }
    }
}

function timenow() {
    var newDate = new Date();
    return (newDate.today() + " " + newDate.timeNow());
}

// Forms used to set this in template, but with updates it could be incorrect
function set_date_field(form) {
    form.find("[name='date']").val(timenow());
}

function clear_form(dialog) {
    var form = dialog.find("form");

    //clear any values from last edit, unless they are radio buttons
    var input_clear_filter = form.attr('input_clear_filter');


    var inputs = form.find('input,select,textarea').not(".no_clear").not('[type="radio"],[type="checkbox"],[type="submit"]');
    if (input_clear_filter) {
    inputs = inputs.filter(input_clear_filter);
    }

    // Note: 'select' intentionally removed from resetting for now (as it was before)
    // Defaulting selects to an option that says "Please select ..." with a blank/null value may be preferred in future
    inputs.not("select").val('');

    // Remove old errors.
    form.find('ul.errorlist').remove();

    //default radio buttons to the first option
    var radios = form.find('input[type="radio"]').parents('li');
    for (var i = 0; i < radios.length; ++i) {
        if ($(radios[i]).index() == 0) {
            $(radios[i]).find('input').prop('checked', true);
        }
    }

    //default analyst, if it exists, to current user
    form.find('input[name="analyst"]').val(username);
}


function dialogClick(e) {
    e.stopPropagation();
    e.preventDefault();

    var dialog = $(this).attr('dialog') || $(this).attr('name') || $(this).attr('id');
    //  var opts = dialogOptions[dialog];

    if (dialog === undefined) {
    return error_message_dialog("Internal JS Error",
                    "Selected widget did not provide a dialog name to open.<br/>" +
                    "<br/>Node: " + this.nodeName +
                    "<br/>Attributes looked at:" +
                    "<br/>Dialog: " + $(this).attr('dialog') +
                    "<br/>Name: " + $(this).attr('name') +
                    "<br/>ID: " + $(this).attr('id')
                    );
    }

    var persona = $(this).attr("persona");
    var $dialog = $('#dialog-' + dialog);

    if ($dialog.length) {
    // The dialog may not be open yet, so delay some setup until it is.
    var that = this;
    $dialog.on("dialogopen.dialogClick", function(e) {
        var form = $dialog.find("form");

        if (persona === "new") { // Clear the forms
            clear_form($dialog);
            set_date_field(form);
        }
        clear_server_msg(dialog);

        // Register the correct action for the form
        // XXX Might be nice to register the onsubmit function here as well, for those single
        // input forms that someone hits enter for example?
        if ($(that).attr("action") && form) {
            form.attr("action", $(that).attr("action"));
        }

        // Make sure the dialog has a message box for result messages
        if (!$dialog.find('.message').length) {
            form.append('<div class="message"></div>');
        }
        form.find('.message').hide().html('');
            // Only show Relationship Type dropdown if needed
        if (persona == "related") {
            $dialog.find('#relationship_type').parents('tr').show();
        }
        else {
            $dialog.find('#relationship_type').parents('tr').hide();
        }

        $dialog.off("dialogopen.dialogClick");
        });

    if ($dialog.data("ui-dialog")) { // If it has been initialized
        $dialog.dialog("open", e);
    } else {
        $dialog.dialog();
        $dialog.dialog("open", e);
    }
    }
}

function activateDialogClicks() {
    $(document).on('click', '.dialogClick', dialogClick);
}

function deleteClick (e) {
    var elem = $(e.currentTarget);
    var data = {};
    var type = null;

    // XXXX Maybe cleaner to convert all this to a "data-" prefix and just slurp it all in
    if (elem.attr('source_name'))
    data["name"] = $(e.currentTarget).attr('source_name'); // from delete_source_button

    if (elem.attr('prefix'))
    data['prefix'] = elem.attr('prefix');  // from delete_campaign_button

    // From delete_object
    if (elem.attr("type")) {
    type = elem.attr('type');

    $.extend(data,
         {coll: elem.attr('coll'),
             oid: elem.attr('oid'),
             name: elem.attr('name'),
             object_type: type,
             value: elem.attr('vvalue')
             });
    }

    // For generic case, freshly implemented using data-del- attributes..
    // data-* attributes are also available in jQuery .data camel cased.
    if (elem.data("delId")) {
    type = elem.data("delType");

    $.each(elem.data(), function(field,value) {
        if (field.substring(0,3) === "del") {
            var f = field.substring(3).toLowerCase();
            data[f] = value;
        }
        });
    }

    if (elem.attr('key')) {
    $.extend(data, {'key':elem.attr('key')});
    }

    var del_label = elem.attr('title') || 'Delete ' + type.capitalize();
    if (elem.data("isObject")) {
    delete_object_click(e, type, del_label, data);
    } else {
    delete_item_click(e, type, del_label, data);
    }
}

$(document).ready(function() {
    activateDialogClicks();

    createPickers();    // Just added back for any non-dynamic dialogs at this point
});

//
// Dialog support functions
//

function file_upload_dialog(e) {
    var dialog = $(this);
    var form = dialog.find("form");

    if (form.find(".toggle_upload_type").length) {
    // Simpler way to toggle file upload dialog widgets based on file or meta upload type
    // classes are defined in forms...
    // thunk().thunk().thunk()
    form.on('change', ".toggle_upload_type", function(e) {
        if ($(this).prop('checked')) {
            var type = $(this).attr('id');
            var form = $(this).closest("form");
            // Hide and disable the inputs so they are not serialized
            form.find(".id_upload_type_0").attr("disabled",true).closest("tr").hide();
            form.find(".id_upload_type_1").attr("disabled",true).closest("tr").hide();
            // Enable the type that is active
            form.find("." + type).attr("disabled",false).closest("tr").show();
        }
        });

    // If one is already set, should just trigger change...
    if (form.find('#id_upload_type_0').prop('checked')) {
        form.find('#id_upload_type_0').trigger('change');
    } else if (form.find('#id_upload_type_1').prop('checked')) {
        form.find('#id_upload_type_1').trigger('change');
    } else { // Set the initial view to File Upload
        form.find('#id_upload_type_0').prop('checked',true);
        form.find('#id_upload_type_0').trigger('change');
    }

    // Client side fix for the django forms issue mentioned in samples/forms.py
    form.find("input.required").closest("tr").addClass("required");
    }

    // XXXXXXXXX THIS NEEDS SOME FIXING.

    //setup "AJAX" file uploading
    // inspired by http://blog.manki.in/2011/08/ajax-fie-upload.html

    // Previously this was loaded at ready(), the selector could be more targetted given
    // use as a callback now..
    $('.file-submit-iframe').load(function(e) {
        var $curTar = $(e.currentTarget);
        var response = this.contentDocument.body.innerHTML;
        if (!response) {
            return;
        }

        try {
           response = $.parseJSON($.parseJSON(response));
        } catch (err) {
            //Server errors will cause JSON not to be able to parse
            //  the response. Show the user an error message so
            //  they know what happened.
            /*var dlg = $('<html></html>').append($(response))
                .dialog({
                    modal:true,
                    width:window.screen.width/2,
                    height:window.screen.height/2
                });*/
            response = {'message': 'Error uploading file.', 'success': false}
        }

        //clear the content of the iframe
        this.contentDocument.body.innerText = '';

        //handle the return value
    var dialog = $curTar.closest(".ui-dialog");
    var item_type = $(dialog).find('form').attr('item-type');
        if (!response.success && response.form) {
            re_render_form(dialog, response.form, e);
        }

        if (response.message) {
            display_server_msg(response.message, dialog);
        } else {
            clear_server_msg(dialog);
        }

        // If we are being told to redirect, do so.
        if (response.redirect_url) {
            document.location = response.redirect_url;
        }

    // XXX TODO: Make this more general for special dialog callbacks, etc..
        if (item_type == "object" || item_type == "object-static") {
            $curTar.parent('form').find('.object-types').change();
            if (response.success)
                post_add_patchup($curTar.parent('form'), response);
        }
    form.trigger("fileUploadComplete", response);

    })
    .parent('form').submit(function(e) {
        //Show progress message when files are uploading
        display_server_msg('Uploading File...', $(e.currentTarget).closest('.ui-dialog'));
    });
}


function display_server_msg(message, dialog) {
    if ($.isArray(message)) {
        message = message.join('<br>')
    }

    if (!dialog.find('.message').length) {
    dialog.find('form').append('<div class="message"></div>');
    }
    dialog.find('.message').css('display', 'table')
    .stop(true,false)
      //    .show().fadeTo(0,1)
    .effect('highlight', {}, 8000)
      //    .effect('fade', function() { this.html(""); }, 2000)
    .html(message);
}

function clear_server_msg(item_type_or_dlg) {
    var form = item_type_or_dlg;
    if (typeof(form) == "string") {
        form = $('#add-'+item_type_or_dlg+'-form');
    }
    form.find('.message').hide().html('');
}

function re_render_form(dialog, form, e) {
    $(dialog).find('table.form tbody').html(form);
    var form = $(dialog).find("form");

    if (form.find(".toggle_upload_type").length) {
    $.proxy(file_upload_dialog, dialog)(e);
    }

    createPickers();
}

function createPickers(context) {
// XXXX this is called whenever a new form needs it, but could it just
// be done on a .click of the class if it isn't widgetized?
    $(".datetimeclass", context || document).datetimepicker({
            showSecond: true,
            showMillisecond: true,
            timeFormat: 'hh:mm:ss.l',
            dateFormat: 'yy-mm-dd',
        });
}


$(document).ready(function() {

//
// Some dialog specific callacks below
//


function releasability_add_submit(e) {
    var widget = $(e.currentTarget);
    var dialog;
    var name, action, date;

    if ($(this).hasClass("ui-dialog-content")) {
    dialog = $(this);
    name = dialog.find("form :input[name='source']").val();
    action = "add"; // this dialog is just used for adds, no edits
    } else {
    name = widget.attr('data-name');
    date = widget.attr('data-date');
    action = widget.attr('data-action');
    }

    // XXXX For the action types of remove, do we want to confirm
    // with the user first?
    var me = $('#releasability_list tbody');
    var data = {'type': type, 'id': id, 'name': name, 'action': action};
    if (date)
    data["date"] = date;

    $.ajax({
            type: "POST",
        url: widget.attr("action") || $('#form-releasability-add').attr('action'),
        data: data,
        async: false,
        datatype: 'json',
        success: function(result) {
                if (result.success) {
                    me.html(result.html);

            if (dialog)
            dialog.dialog("close");

            collapse2(); // XXXX Might be nice if this wasn't collapsed, we just
                 // changed it, left it on because the icon changes in the
                 // new div
                }
            }
        });
}

function check_selected(type, dialog) {
    if (selected_text) {
        var obj = null;
        if (type == 'ip') {
            obj = '#id_ip';
        } else if (type == 'domain') {
            obj = '#id_domain';
        } else if (type == 'indicator') {
            obj = '#id_value';
        }
        if (obj) {
            dialog.find(obj).val(selected_text);
            selected_text = null;
        }
    }
}

function new_ip_dialog(e) {
    var dialog = $(this).find("form");
    var ref = dialog.find('#id_indicator_reference').closest('tr');

    dialog.find('#id_add_indicator').unbind('change')
        .bind('change', function(e) {
        if ($(this).prop('checked')) {
            ref.show();
        } else {
            ref.hide();
        }
        }).trigger('change');

    // If there is selected text, default the value in the form
    check_selected('ip', dialog);
}

function new_domain_dialog(e) {
    dialog = $(this).find("form"); // $("#form-new-domain");

    //setup the Add Domain form to display and hide fields properly
    //save on DOM lookups
    var ip_check = dialog.find('#id_add_ip');
    var ip_fields = dialog.find('.togglewithip').parents('tr');

    //define function for seeing source dropdown should be visible
    var toggle_source_visibility = function() {
    //definitely should hide if use domain source is checked
    if (dialog.find('#id_same_source').prop('checked')) {
        dialog.find('.togglewithipsource').parents('tr').hide();
            //otherwise, should show only if we're trying to add an ip
    } else if (ip_check.prop('checked')) {
        dialog.find('.togglewithipsource').parents('tr').show();
    }
    };

    //define function for seeing if ip fields should be visible
    var toggle_ip_visibility = function() {
    if (ip_check.prop('checked')) {
        ip_fields.show();
        toggle_source_visibility();
    } else {
        ip_fields.hide();
    }
    };

    //initialize with ip fields hidden
    toggle_ip_visibility();

    //setup checkbox events
    //just make form look neater if they don't want to add an IP
    dialog.find("#id_add_ip").change(toggle_ip_visibility);

    //don't require selecting a source if they want to use the same source as the domain
    // and initialize same source to true (will prob. be true in most cases...?)
    dialog.find("#id_same_source").change(toggle_source_visibility).prop('checked', true);

    //reinitialize ip date field (since this function can be called after page load)
    createPickers();

    // If there is selected text, default the value in the form
    check_selected('domain', dialog);

}

function new_event_dialog() {
    createPickers();
}

function add_email_yaml_template() {
var template = "\
to: \n\
cc: \n\
from_address: \n\
sender: \n\
reply_to: \n\
date: \n\
subject: \n\
message_id: \n\
x_mailer: \n\
helo: \n\
originating_ip: \n\
x_originating_ip: \n\
raw_header: \n\
raw_body: ";
$("#id_yaml_data").val(template);
}

function new_email_yaml_dialog(e) {
    var buttons = $("#dialog-new-email-yaml").dialog("option", "buttons");
    $.extend(buttons, {"Add Template": function() {
                add_email_yaml_template();
        // $('#upload-email-yaml-form').parent().find('button:contains("Add Template")').attr('disabled', true).addClass('ui-state-disabled');
            }});
    $("#dialog-new-email-yaml").dialog("option", "buttons", buttons);

    file_upload_dialog(e);
}

function new_indicator_dialog(e) {
    var dialog = $("#dialog-new-indicator").closest(".ui-dialog");
    var form = dialog.find("form");

    // If there is selected text, default the value in the form
    check_selected('indicator', dialog);
}

// We may want to do something like this generally, but for now just doing it for single text entry form
function fix_form_submit(submitAction) {
    return function(e) {
    var dialog = $(this).closest(".ui-dialog");
    var form = dialog.find("form");

    form.on('submit', submitAction);
    return true;
    }
}

function new_sample_dialog() {
    // Upload a related sample (Using the related dialog persona), used from events, samples
    // The action target takes care of passing the parent sample_id here
    if ($(this).dialog("persona") === "related") {
    $('id_related_md5, label[for="id_related_md5"]').closest("tr").hide();
    $('#id_related_md5').prop('value', '');
    $('#id_inherit_sources').prop('checked', true);
    $('#id_inherit_campaigns').prop('checked', true);
    }
    else {
    $('id_related_md5, label[for="id_related_md5"]').closest("tr").show();
    $('#id_related_md5').prop('value', '');
    $('#id_inherit_sources').prop('checked', false);
    $('#id_inherit_campaigns').prop('checked', false);
    }
}

function new_target_dialog(e) {
    var element = document.getElementById('id_campaign');
    var className = $(this).dialog("activatedBy")[0].className
    if (className === "ui-icon ui-icon-plusthick add dialogClick") {
        var campaign = this.baseURI.match(/\/campaigns\/details\/(.*)\//);
        element.value = decodeURI(campaign[1]);
    }
    else {
        element.value = '';
    }
}

/// Standard Dialog setup below

var stdDialogs = {
      "new-actor": {title: "Actor", personas: {related: newPersona("Add Related Actor", {}, addEditSubmit) } },
      "new-actor-identifier": {title: "Actor Identifier"},
      "actor_identifier_type_add": {title: "Actor Identifier Type"},
      "new-email-raw": {title: "Email (Raw)", personas: {related: newPersona("Add Related Email (raw)", {}, addEditSubmit) } },
      "new-email-fields": {title: "Email", personas: {related: newPersona("Add Related Email", {}, addEditSubmit) } },
      "new-email-yaml": {title: "Email (YAML)", personas: {related: newPersona("Add Related Email (YAML)", {open: new_email_yaml_dialog}, addEditSubmit ) }, open: new_email_yaml_dialog },
      "new-campaign": {title: "Campaign", personas: {related: newPersona("Add Related Campaign", {}, addEditSubmit) } },
      "new-backdoor": {title: "Backdoor", personas: {related: newPersona("Add Related Backdoor", {}, addEditSubmit) } },
      "new-exploit": {title: "Exploit", personas: {related: newPersona("Add Related Exploit",{}, addEditSubmit) } },
      "new-domain": {title: "Domain", personas: {related: newPersona("Add Related Domain", {open: new_domain_dialog}, addEditSubmit ) }, open: new_domain_dialog },
      "new-indicator": {title: "Indicator",  personas: {related: newPersona("Add Related Indicator", {open: new_indicator_dialog}, addEditSubmit ) }, open: new_indicator_dialog},
      "action_add": {title: "Action"},
      "add-action": {title: "Action", href:"",
		       new: {open: function(e) {
                    $('#id_action_performed_date').val(timenow());
                    var sel = $('#form-add-action').find('#id_action_type');
                    sel.children().remove();
                    if (typeof subscription_type !== "undefined") {
                        $.ajax({
                            type:'GET',
                            data: {type: subscription_type},
                            url: get_actions_for_tlo,
                            success: function(data) {
                                $.each(data.results, function(x,y) {
                                    sel.append($('<option></option>').val(y).html(y));
                                });
                            }
                        });
                    }
               }},
		       update: { open: update_dialog} },
      "indicator-blob": {title: "New Indicator Blob", personas: {related: newPersona("Add Related Indicator Blob", {open: new_indicator_dialog}, addEditSubmit ) }, open: new_indicator_dialog },

      "new-event": {title: "Event", personas: {related: newPersona("Add Related Event", {open: new_event_dialog}, addEditSubmit ) }, open: new_event_dialog },
      "new-ip": {title: "IP Address", personas: {related: newPersona("Add Related IP", {open: new_ip_dialog}, addEditSubmit ) }, open: new_ip_dialog },
      "new-raw-data": {title: "Raw Data", personas: {related: newPersona("Add Related Raw Data", {}, addEditSubmit) } },
      "raw_data_type_add": {title: "Raw Data Type"},

      "new-signature": {title: "Signature", personas: {related: newPersona("Add Related Signature", {}, addEditSubmit) } },
      "signature_type_add": {title: "Signature Type"},
      "signature_dependency_add": {title: "Signature Dependency"},

      "new-target": {title: "Target", personas: {related: newPersona("Add Related Target", {open: new_target_dialog}, addEditSubmit ) }, open: new_target_dialog },

      "source_create": {title: "Source"},
      "user_role": {title: "User Role"},

      "campaign-add": { title: "Assign Campaign", personas: {
          promote: newPersona("Promote to Campaign",
                  { title: "Promote to Campaign" },
                  addEditSubmit)
      }
      },
      "location-add": {title: "Add Location"},
      "ticket": {title: "Ticket",
         update: { open: update_dialog} },

      "shortcut_help": {title: "Shortcut Keys", is_prevent_buttons: true,
              modal: false, maxHeight: 500},

      "source-add": {title: "Source",
             update: { open:
                   function(e) { $("#form-source-add").find("#id_name").attr("disabled","disabled");
                         $.proxy(update_dialog, this)(e); },
                   submit:
                   function(e) { $("#form-source-add").find("#id_name").removeAttr("disabled");
                         $.proxy(addEditSubmit, this)(e); } }
      },

      "releasability-add": {title: "Add Releasability",
                new: { submit: releasability_add_submit} },
  };

  var fileDialogs = {
      // File Upload Dialogs
      "new-email-outlook": {title: "Upload Outlook Email", personas: {related: newPersona("Upload Related Email (Outlook)", {open: file_upload_dialog}, defaultSubmit) }, open: file_upload_dialog },
      "new-email-eml": {title: "Email", personas: {related: newPersona("Upload Related Email",
                        {open: file_upload_dialog}, defaultSubmit) }, open: file_upload_dialog },
      "new-pcap": {title: "PCAP", personas: {related: newPersona("Upload Related PCAP",
                   {open: file_upload_dialog}, defaultSubmit) }, open: file_upload_dialog },
      "upload_tlds": {title: "TLDS" },
      "new-sample": {title: "Sample", personas: {related: newPersona("Upload Related Sample",
                     {open: file_upload_dialog}, defaultSubmit) }, open: file_upload_dialog },
      "new-certificate": {title: "Certificate", personas: {related: newPersona("Upload Related Certificate", {open: new_sample_dialog}, defaultSubmit) }, open: new_sample_dialog },
      "new-raw-data-file": {title: "Raw Data File", personas: {related: newPersona("Upload Related Raw Data", {open: file_upload_dialog}, defaultSubmit) }, open: file_upload_dialog },
      "new-indicator-csv": {title: "New Indicator CSV", personas: {related: newPersona("Upload Related Indicators", {open: file_upload_dialog}, defaultSubmit) }, open: file_upload_dialog },
  };

  // Ok, now initialize all the dialogs, with the href they are lazy-loaded
  $.each(stdDialogs, function(id,opt) {
      stdDialog(id, opt, {update: { open: update_dialog}} );
      });

  $.each(fileDialogs, function(id,opt) {
      stdDialog(id, opt, {
          new: { open: file_upload_dialog, submit: defaultSubmit }}
      )
  });

  // New Sample dialog has some additional setup, so add that as an event callback
  $("#dialog-new-sample").on("dialogopen", new_sample_dialog);

  // Fixup for ticket dialog that only has one input field - enter
  // does a default submit, not our submit handler function.
  //
  // There might be a more general fix to this, like assigning the
  // action to the form's submit action by default, but I don't want
  // to make that sort of global change before 3.0.
  var singleInputDialogs = "#dialog-actor-identifier-type,#dialog-ticket,"+
      "#dialog-source_create,#dialog-user_role," +
      "#dialog-action_add,#dialog-raw_data_type_add,#dialog-signature_type_add,#dialog-signature_dependency_add";
  $(singleInputDialogs).on("dialogopen", fix_form_submit(addEditSubmit));


  // Serialize any other forms that want to be ajaxPost'ed
  $(document).on("submit", "form.ajaxPost", ajaxPost);

  // This could be in comments.js, but that doesn't seem to get included.
  var commentsDialogs = {
      "comments": {title: "Comment",
           new: { title: "Add Comments"  },
           personas: { update: { open: update_dialog},
                              reply: newPersona("Reply to Comment",
                                                    {title: "Reply to Comment",
                             open: comment_reply_dialog },
                            addEditSubmit),
              }
      },
  };

  $.each(commentsDialogs, function(id,opt) { stdDialog(id, opt); });

  $("#dialog-comments").on("dialogopen", function() {
      // XXXX comments_url_key is set in comments_listing_widget, there might be a better option for this bit.
      $('#dialog-comments').find('#id_url_key,#id_subscribable').val(comments_url_key);
      });


  $("#dialog-new-indicator").on("dialogcreate", new_indicator_dialog);

  // Releasability has plus instance and delete buttons that use same callback
  $(document).on('click', '.add_releasability_instance_button',
         releasability_add_submit);

  // XXX We may want confirmation dialogs on these remove buttons...
  // Perhaps convert these to "deleteClick" style in the future.
  $(document).on('click', '.remove_releasability_button',
         releasability_add_submit);
  $(document).on('click', '.remove_releasability_instance_button',
         releasability_add_submit);

  // Standard delete prompt for most elements, needed data is supplied via element attrs
  $(document).on('click', '.deleteClick', function (e) { deleteClick(e); });

});
