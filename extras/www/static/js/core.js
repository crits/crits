String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

// IE8 support for String.trim()
if (typeof(String.prototype.trim) === "undefined") {
    String.prototype.trim = function() {
        return String(this).replace(/^\s+|\s+$/g, '');
    }
}

//For todays date;
Date.prototype.today = function() {
    return this.getFullYear() + "-" + (((this.getMonth()+1) < 10)?"0":"") + (this.getMonth()+1) + "-" + ((this.getDate() < 10)?"0":"") + this.getDate()
};
//For the time now
Date.prototype.timeNow = function() {
     return ((this.getHours() < 10)?"0":"") + this.getHours() +":"+ ((this.getMinutes() < 10)?"0":"") + this.getMinutes() +":"+ ((this.getSeconds() < 10)?"0":"") + this.getSeconds() + ".000";
};

var collapse = function() {};

$.urlParam = function(name){
    var results = new RegExp('[\\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results==null){
       return null;
    } else {
       return results[1] || 0;
    }
}

function processLogin() {
    var uname = $('#l_username').val();
    var password = $('#l_password').val();
    var token = $('#l_token').val();
    var data = {
        username: uname,
        password: password,
        totp_pass: token,
        next_url: $.urlParam('next'),
    };
    $.ajax({
        type: "POST",
        url: login_user,
        data: data,
        datatype: 'json',
        success: function(data) {
            if (data.success) {
                window.location.replace(data.message);
            } else {
                var count = 10;
                var login_submit_button = $('.login_submit_button');
                var timer_element = $('<span id="timer"><br />Please wait ' + count + ' seconds.</span>');
                login_submit_button.attr('disabled', true).addClass("disabled");
                $('#ajax_response').html(data.message);
                $('#login_form').append(timer_element);
                function timer() {
                    count = count - 1;
                    if (count <= 0) {
                        clearInterval(counter);
                        timer_element.remove();
                        login_submit_button.attr('disabled', false).removeClass("disabled");
                        return;
                    }
                    timer_element.html("<br />Please wait " + count + " seconds.");
                }
                var counter = setInterval(timer, 1000);
            }
        }
    });
}

function createCookie(name,value,minutes) {
    if (minutes) {
        var date = new Date();
        date.setTime(date.getTime()+(minutes*1000*60));
        var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    if (secure_cookie == "True") {
        document.cookie = name+"="+value+expires+"; path=/; secure";
    } else {
        document.cookie = name+"="+value+expires+"; path=/;";
    }
}

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function searchCookie(regex) {
  var cs = document.cookie.split(/;\s*/), ret=[];
  $.each(cs, function(i,c) {
      if (c.match(regex)) {
          var cook = c.split('=');
          ret.push({"name": cook[0], "val": cook[1]});
      }
      });
  return ret;
};

function getCookie(name) {
    ca = searchCookie('^' + name + '=');
    if (ca.length)
    return ca[0];
    else
    return {"name": name, "val" : ""};
}

function eraseCookie(name) {
    createCookie(name,"",-1);
}

function setPagingSize(size) {
    if (!size)
    return;

    // If the globPgSz doesn't match the locPgSz then we'll reset jtable, with this
    // trick this only happens once after a user has changed their profile preference
    var globPgSz = getCookie('globPgSz');
    var locPgSz = getCookie('locPgSz');

    if (size != globPgSz.val) {
    globPgSz.val = size;
    document.cookie = globPgSz.name + '=' + globPgSz.val + ';path=/;';
    }

    if (locPgSz.val != globPgSz.val) {
    document.cookie = locPgSz.name + "=" + globPgSz.val;
    ca = searchCookie('page-size');
    $.each(ca, function(i,c) {
        document.cookie = c.name + '=' + size + ';';
        });
    }
}

function get_stored_item_data(url) {
    var rid = readCookie('crits_rel_id');
    var rtype = readCookie('crits_rel_type');
    var cbc = $('#clipboard_container');
    var cbi = $('#clipboard_icon');
    var cbq = $('#selected_item_topbar');
    if (rid && rtype) {
        $.ajax({
            url: url,
            type: "POST",
            dataType: 'json',
            data: {id: rid, type: rtype},
        }).done(function(msg) {
            var idText = "Type: " + rtype + "<br />";
            idText += "ID: " + rid + "<br />";
            if (msg['OK']) {
                for (var item in msg.data) {
                    if (msg.data[item]) {
                        idText += item+ ': ' + msg.data[item] + '<br />';
                    }
                }
                cbi.removeClass('clipboard_icon_empty');
                cbi.addClass('clipboard_icon_full');
                cbi.attr('title', 'Click to see clipboard contents');
                cbq.html(idText);
                cbc.css('width', "35px");
                $('span#delete_stored_cookie').remove();
                cbc.append('<span id="delete_stored_cookie" class="ui-icon ui-icon-close ui-icon-delete-stored-cookie" title="Clear your clipboard"></span>');
                $('span#delete_stored_cookie').click(function() {
                    $('button.id_copy#' + readCookie('crits_rel_id')).css('background-color', '');
                    $('span#' + readCookie('crits_rel_id') + '.id_copy').css('background-color', '');
                    cbq.text("Your clipboard is empty.");
                    eraseCookie('crits_rel_id');
                    eraseCookie('crits_rel_type');
                    cbi.removeClass('clipboard_icon_full');
                    cbi.addClass('clipboard_icon_empty');
                    cbi.attr('title', 'Your clipboard is empty.');
                    $(this).remove();
                    cbc.css('width', 'auto');
                });
            } else {
                cbi.removeClass('clipboard_icon_full');
                cbi.addClass('clipboard_icon_empty');
                cbi.attr('title', 'Your clipboard is empty.');
            }
        });
    } else {
        cbi.removeClass('clipboard_icon_full');
        cbi.addClass('clipboard_icon_empty');
        cbi.attr('title', 'Your clipboard is empty.');
    }
}

function modify_tlp(itype, oid, tlp) {
    var res = false;
    $.ajax({
        type: "POST",
        url: tlp_modify,
        async: false,
        data: {
            'tlp': tlp,
            'oid': oid,
            'itype': itype
        },
        datatype: 'json',
        success: function(data) {
            res = data.success;
        }
    });
    return res;
}

function reset_tlp_color(e, tlp) {
    d = {
        white: '#ffffff',
        green: '#00ff00',
        amber: '#ffcc22',
        red: '#ff0000'
    }
    e.simplecolorpicker('selectColor', d[tlp]);
}

function getUserSources(user) {
  $.ajax({
      type: "POST",
      url: user_source_access,
      data: {'username': user.value},
      datatype: 'json',
      success: function(data) {
          if (data.success) {
              $("#form-add-new-user table").html(data.message);
              $('.multiselect').multiselect({dividerLocation:0.5});
          }
      }
  });
}

function toggleUserActive(user) {
    var me = $('#is_active_' + user);
    $.ajax({
        type: 'POST',
        url: toggle_user_active,
        data: {
            username: user,
        },
        datatype: 'json',
        success: function(data) {
            if (data.success) {
                if (me.text() == "True") {
                    me.text("False")
                } else {
                    me.text("True")
                }
            }
        }
    });
}

function editUser(user) {
    var me = $( "#add-new-user-form select[name='user']");
    me.val(user);
    me.change();
    $( "#add-new-user-form" ).dialog( "open" );
}

function editAction(action, object_types, preferred) {
    var me = $("#add-new-action-form input[name='action']");
    var ots = $("#add-new-action-form select[name='object_types']");
    var prefs = $("#add-new-action-form textarea[name='preferred']");
    me.val(action);
    me.change();
	var ot_list = object_types.split(",");
	ots.val(ot_list);
	var prep = preferred.replace(/\|\|/g, "\n").replace(/\|/g, ", ");
	prefs.val(prep);
    $("#add-new-action-form").dialog("open");
}

function deleteSignatureDependency(coll, oid)
{
   //get the attribute of the row tr element, if success, this will be removed
   var rowString = "[data-record-key='" + oid + "']";
   var rowSel = "tr" + rowString;

   var answer = confirm("This will delete the Signature Dependency. Are you sure?" );
   if(answer) {
    var me = $("a#to_delete_"+oid);
    $.ajax({
        type: "POST",
        url: delete_signature_dependency,
        data: {
            coll: coll,
            oid: oid,
        },
        datatype: 'json',
        success: function(data) {
                //delete the row
                if(data.success) {
                //should be equal to 1 selecting on key
                  if($(rowSel).length>0) {
                   $(rowSel).get(0).remove();
                  }

                } else {
                    //console.log("Failed to delete the signature, returned");
                }
        },
        });
    } else {
        //console.log("Deletion cancelled by user");
    }

}

function toggleItemActive(coll, oid) {
    var me = $( "a#is_active_" + oid);
    $.ajax({
        type: "POST",
        url: toggle_item_active,
        data: {
            coll: coll,
            oid: oid,
        },
        datatype: 'json',
        success: function(data) {
            if (data.success) {
                if (me.text() == "on") {
                    me.text("off");
                } else {
                    me.text("on");
                }
            }
        }
    });
}

function create_dialog(elem, width, height) {
    var dlg = $(elem).dialog({
        autoOpen:false,
        modal:true,
        width: "auto",
        height: "auto"
    });
    dlg.append('<div class="message"></div>').hide();
    return dlg;
};

function error_message_dialog(title, message) {
    if ($.isArray(message)) {
        message = message.join('<br>');
    }
    var msg = $('<span></span>').html(message);
    $('<div></div>').append(msg).dialog({
        buttons: {'OK':function() {$(this).dialog('close');}},
        title: title
    });
};

function close_nav_menu() {
    $('#nav-menu').trigger("close");
}

function close_search_menu() {
    $('#search-menu').trigger("close");
}

function disable_mmenu_buttons() {
    // This function is generallly used to disable open/close buttons until
    // the menu is fully open or fully closed. An issue exists where if
    // both are opened/closed while another menu is opening or closing then
    // the menus will permanently appear BEHIND the page contents.

    $('.search-menu-icon').off()
    $('.nav-menu-icon').off()
}

function open_nav_menu() {
    $('#nav-menu').trigger("open");
}

function open_search_menu() {
    $('#search-menu').trigger("open");
}

function clear_notifications_click(e) {
    e.preventDefault();
    var elem = $(e.currentTarget);
    $.ajax({
        type: 'POST',
        data: '',
        url: elem.attr('action'),
        success: function(data) {
            if (data.success) {
                $('.notifications').html(data.message);
            }
        }
    });
}

function delete_notification_click(e) {
    e.preventDefault();
    var elem = $(e.currentTarget);
    $.ajax({
        type: 'POST',
        data: '',
        url: elem.attr('action'),
        success: function(data) {
            if (data.success) {
                elem.parent().parent().remove();
            }
        }
    });
}

function toggle_preferred_action_from_jtable(e) {
    e.preventDefault();
    var me = $(e.currentTarget);
    var obj_id = me.attr('data-id');
    var obj_type = me.attr('data-type');
    $.ajax({
        type: "POST",
        data: {'obj_type': obj_type, 'obj_id': obj_id},
        url: add_preferred_actions,
        success: function(data) {
            if (data.success == false) {
                error_message_dialog("Error", data.message);
            }
        }
    });
}

function favorites_button_click(e) {
    e.preventDefault();
    if ($('#favorites_results').is(":visible")) {
        $('#favorites_results').slideToggle(100);
    } else {
        $.ajax({
            type: 'POST',
            data: '',
            url: $(e.currentTarget).attr('action'),
            success: function(data) {
                $('#favorites_results').slideToggle(100);
                $('#favorites_results').html(data.results);
            }
        });
    }
}

function toggle_favorite_from_jtable(e) {
    e.preventDefault();
    var me = $(e.currentTarget);
    var data = {
                'type': me.attr('data-type'),
                'id': me.attr('id'),
               };
    $.ajax({
        type: 'POST',
        data: data,
        url: favorite_url,
        success: function(data) {
            if ($(me).hasClass('favorites_icon_active')) {
                $(me).css('background-color', 'buttonface');
                $(me).removeClass('favorites_icon_active');
                favorite_count--;
            } else {
                $(me).css('background-color', '#1AC932');
                $(me).addClass('favorites_icon_active');
                favorite_count++;
            }
            if (favorite_count == 0) {
                $('span.favorites_icon').removeClass('favorites_icon_active');
                $('span.favorites_icon').addClass('favorites_icon_inactive');
            }
            else {
                $('span.favorites_icon').removeClass('favorites_icon_inactive');
                $('span.favorites_icon').addClass('favorites_icon_active');
            }
        }
    });
}

function remove_favorite(e) {
    e.preventDefault();
    var me = $(e.currentTarget);
    var id = me.attr('data-id');
    var data = {
                'type': me.attr('data-type'),
                'id': id,
               };
    $.ajax({
        type: 'POST',
        data: data,
        url: favorite_url,
        success: function(data) {
            me.closest('tr').remove();
            // If removing current object, reset button color.
            if (is_favorite) {
                $('button.favorite').css('background-color', 'buttonface');
                is_favorite = false;
            }
            // Reset button color on jtable pages too.
            $('span.favorites_icon_active#' + id).removeClass('favorites_icon_active').css('background-color', 'buttonface');
            favorite_count--;
            if (favorite_count == 0) {
                $('#favorites_results').slideToggle(100);
                $('span.favorites_icon').removeClass('favorites_icon_active');
                $('span.favorites_icon').addClass('favorites_icon_inactive');
            }
        }
    });
}

function subscription_button_click(e) {
    e.preventDefault();
    var elem = $(e.currentTarget);
    $.ajax({
        type: 'POST',
        data: '',
        url: elem.attr('action'),
        success: function(data) {
            if (data.success) {
                elem.html(data.message);
            }
        }
    });
}

function jtCSVDownload(jtid) {
    var jtable = $("#" + jtid);
    var fields = jtable.data('hikJtable')._columnList;
    var indx = fields.indexOf("details");
    var list_url = jtable.data('hikJtable').options.actions.listAction;
    var csvurl = null;
    // Handle fields
    if (indx != -1) {
        fields.splice(indx,1);
    }
    indx = fields.indexOf("id");
    if (indx != -1) {
        fields.splice(indx,1);
    }
    fields = fields.join();
    // Build CSV download URL
    csvurl = list_url.replace("jtlist","csv");
    if (csvurl) {
        // Add the fields
        if (csvurl.indexOf("?") != -1) {
            csvurl = csvurl + "&fields=" + fields;
        } else {
            csvurl = csvurl + "?fields=" + fields;
        }
        window.location.href = csvurl;
    }
}

/*
 * Called from each details page. This will highlight the favorite button
 * if the current object is a favorite. It also handles the event for
 * clicking that same button. When the button is clicked it will send
 * an AJAX request to record that in the database and toggle the button
 * and top-menu star appropriately.
 */
function toggle_favorite(crits_type) {
    if (is_favorite) {
        $('button.favorite').css('background-color', '#1AC932');
        $('span.favorites_icon').removeClass('favorites_icon_inactive');
        $('span.favorites_icon').addClass('favorites_icon_active');
    }

    $('button.favorite').unbind('click').click(function() {
        $.ajax({
            type: "POST",
            url: favorite_url,
            data: {'type': crits_type, 'id': $(this).attr('id')},
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    if (is_favorite) {
                        is_favorite = false;
                        favorite_count--;
                        $('button.favorite').css('background-color', 'buttonface');
                        if (favorite_count == 0) {
                            $('span.favorites_icon').removeClass('favorites_icon_active');
                            $('span.favorites_icon').addClass('favorites_icon_inactive');
                        }
                    } else {
                        is_favorite = true;
                        favorite_count++;
                        $('span.favorites_icon').removeClass('favorites_icon_inactive');
                        $('span.favorites_icon').addClass('favorites_icon_active');
                        $('button.favorite').css('background-color', '#1AC932')
                    }
                }
            }
        });
    });
}

function details_copy_id (crits_type) {
    // Highlight the icon if we have it selected
    if (readCookie('crits_rel_id')) {
        $('button#'+readCookie('crits_rel_id')).css('background-color', '#1AC932');
    }
    $('button.id_copy').click(function() {
        createCookie('crits_rel_id',$(this).attr('id'),60);
        createCookie('crits_rel_type',crits_type,60);
        $('button#'+readCookie('crits_rel_id')).css('background-color', '#1AC932');
        get_stored_item_data(get_item_data_url);
    });
}

function jtRecordsLoaded(event,data, button) {
    var jtable = event.target;
    var jtTitle = $(jtable).data().hikJtable.options.title;

    if (button) {
        var inTab = $("#" + button);
        if (inTab) {
            inTab.find('span').html(jtTitle + " (" + data.serverResponse.TotalRecordCount + ")");
        }
    }

    if (data.serverResponse.term) {
        $(jtable).find('.jtable-title-text').html(jtTitle + " - " + data.serverResponse.term);
    }
    // When the table loads, highlight the icon if it is already stored
    $('span#'+readCookie('crits_rel_id') + '.id_copy').css('background-color', '#1AC932');
    // Set top bar information
    $(jtable).find('.id_copy').click(function() {
        // Uncolor the previous stored value's icon
        $('span#' + readCookie('crits_rel_id') + '.id_copy').css('background-color', '#D5DFE6');
        // Save the new value
        createCookie('crits_rel_id', $(this).attr('id'), 60);
        createCookie('crits_rel_type', data.serverResponse.crits_type, 60);
        // Adjust background
        $('span#' + readCookie('crits_rel_id') + '.id_copy').css('background-color', '#1AC932');
        get_stored_item_data(get_item_data_url);
    });
    // Light up the favorite icon for any that are favorites.
    favorites_list = user_favorites[data.serverResponse.crits_type];
    if (favorites_list) {
        for (var id = 0; id < favorites_list.length; id++) {
            $('span#' + favorites_list[id] + '.favorites_icon_jtable').css('background-color', '#1AC932').addClass('favorites_icon_active');
        }
    }

    // Also add an attribute for the data type.
    $(jtable).find('.favorites_icon_jtable').attr('data-type', data.serverResponse.crits_type);

    // Also add an attribute for the data type to the actions button
    $(jtable).find('.preferred_actions_jtable').attr('data-type', data.serverResponse.crits_type);
}

function link_jtable_column (data, column, baseurl, campbase) {
    var coltext = "";
    if (typeof data.record[column] == "string") {
        var items = data.record[column].split('|||');
        for (var i = 0; i < items.length; i++) {
            if (column == "campaign" && items[i]) {
                var campurl = campbase.replace("__CAMPAIGN__", items[i]);
                /*jshint multistr: true */
                coltext += '<span style="float: left;"> \
                               <a href="'+baseurl+'?'+column+'='+encodeURIComponent(items[i])+'">'+items[i]+'</a> \
                            </span> \
                            <span style="float: top;"> \
                                <a href="'+campurl+'" class="ui-icon ui-icon-triangle-1-e"></a> \
                            </span>';
            } else {
                var decoded = $('<div/>').html(items[i]).text();
                coltext += '<a href="'+baseurl+'?'+column+'='+encodeURIComponent(decoded)+'&force_full=1">'+items[i]+'</a>';
                if (i !== (items.length - 1)) {
                    coltext += ', ';
                }
            }
        }
    } else {
        coltext = '<a href="'+baseurl+'?'+column+'='+encodeURIComponent(data.record[column])+'">'+data.record[column]+'</a>';
    }
    return coltext;
}

// Prevent fatal runtime errors for IE if the DevTools (F12) is not active
var log = (function() {
    var debuglog;
    if (window.console &&
        typeof window.console !== "undefined" &&
        typeof window.console.log !== "undefined") {
        debuglog = Function.prototype.bind.call(console.log, console);
    } else {
        debuglog = function() {};
    }
    return debuglog;
    })();


var objlog = function(obj, indent) {
      indent = indent || "";
      $.each(obj, function(k,v) {
          log(indent + k + " = " + v);
          if (typeof v == "object") {
          log(indent + ">>>> " + k );
          objlog(v, indent + "   ");
          log("<<<");
          }
      });
};


function initTabNav() {
    $(".tabnav").tabs({
        activate: function(event, ui) {
            var tabid = ui.newPanel.attr('id');
            var id = $('.tabnav').find('[aria-controls="'+ tabid + '"]').find('a').attr('id');
            window.location.hash = id;
        },
        create: function(event, ui) {
            var id = event.target.id;
            // activate the first tab that has results, unless another tab other than the first tab is active
            if ($('#'+id+' li').not('.empty_tab_results').length > 0 && $('#'+id).tabs("option", "active") == 0) {
                $('#'+id).tabs('option', 'active', $('#'+id+' li').not('.empty_tab_results').first().index());
            }
            // disable the tabs that don't have results
            $('#'+id+' li.empty_tab_results a').removeAttr('href');
            $('#'+id+' li.empty_tab_results a').css('color', 'grey');
            $('#'+id+' li.empty_tab_results').each( function() { $('#'+id).tabs("disable", $(this).index() )});
            $('#'+id).show();
            if (window.location.hash !== "") {
                $('#'+id).tabs('option', 'active',
                $('#'+id+' a' + window.location.hash).parent().index());
            }
        },
        beforeLoad: function( event, ui ) {
            if ( ui.tab.data( "loaded" ) ) {
                event.preventDefault();
                return;
            }
            ui.jqXHR.success(function() {
                ui.tab.data( "loaded", true );
            });
        }
    });
}

var csrftoken = readCookie('csrftoken');
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    // Set request header for ajax POST
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

var selected_text = null;

function getSelected() {
    if (window.getSelection) {
        return window.getSelection();
    } else if (document.getSelection) {
        return document.getSelection();
    } else {
        var selection = document.selection && document.selection.createRange();
        if (selection.text) {
            return selection.text;
        }
        return false;
    }
    return false;
}

$(document).ready(function() {

    $(document).mouseup(function(e) {
        var selected = getSelected();
        if (selected.toString().length == 0) {
            $('#selectedNodeMenu').hide();
        }
    });

    $(document).on('keydown', function(e){
        if (e.altKey){
            var selected = getSelected();
            if (selected.toString().length > 0) {
                selected_text = selected.toString()
                var span = $('<span>')
                .attr('id', 'tmpSelectedNode');
                var range = selected.getRangeAt(0);
                range.insertNode($(span).get(0));
                var position = $('#tmpSelectedNode').position();
                var fspan = $('#selectedNodeMenu')
                .css('top', position.top)
                .css('left', position.left)
                .attr('data-selected', selected_text)
                //.show();
                .toggle();
                $('#tmpSelectedNode').remove();
            } else {
                $('#selectedNodeMenu').hide();
            }
        }
    });

    $(document).on('click', '.selected_text_button', function(e) {
        var selected = $(this).parent().attr('data-selected');
        if ($(this).attr('id') == 'selected_to_indicator') {
            $('#new-indicator').click();
        } else if ($(this).attr('id') == 'selected_to_domain') {
            $('#new-domain').click();
        } else if ($(this).attr('id') == 'selected_to_ip') {
            $('#new-ip').click();
        }
    });

    var src_filter = '[name!="analyst"]';

    // Enable Preference Toggle buttons
    $(document).on('click', '.preference_toggle', function(e) {
	    preference_toggle(e);
    });

    //bind clear_notifications click
    $('.clear_notifications').click(function(e) {
        clear_notifications_click(e);
    });

    //bind delete_notification button click
    $('.delete_notification').click(function(e) {
        delete_notification_click(e);
    });

    //bind subscription_button click
    $('.subscription_button').click(function(e) {
        subscription_button_click(e);
    });

    //bind favorites_button click
    $('.favorites_button').click(function(e) {
        favorites_button_click(e);
    });

    // If the user has favorites, highlight the star icon.
    if (favorite_count > 0) {
        $('span.favorites_icon').removeClass('favorites_icon_inactive');
        $('span.favorites_icon').addClass('favorites_icon_active');
    }

    // bind the favorite toggle from jtable.
    $(document).on('click', '.favorites_icon_jtable', function(e) {
        toggle_favorite_from_jtable(e);
    });

    //bind remove_favorite click
    $(document).on('click', '.remove_favorite', function(e) {
        remove_favorite(e);
    });

    // bind the preferred actions from jtable.
    $(document).on('click', '.preferred_actions_jtable', function(e) {
        toggle_preferred_action_from_jtable(e);
    });
    //setup source "accordion" effect
    //  toggle on arrow icon

    //TODO: at some point may be helpful to abstract this so objects other than source can call it
    collapse = function() {
        var collapser = $('.collapser').collapsible('td.collapsible', {'collapse':true, toggleAllSelector:'#toggle_sources_', 'textExpand':'', 'textCollapse':'', classExpand: 'ui-icon-triangle-1-s', classCollapse: 'ui-icon-triangle-1-e'});//.tablesorter();
        //  toggle on first column
        collapser.find('.collapsible_alt a').unbind('click').click(function(e) {
            $(this).parents('.collapsible_alt').siblings('.collapsible').find('a').click();
            return false;
        });
    }
    collapse2 = function() {
        var collapser = $('.rcollapser').collapsible('td.rcollapsible', {'collapse':true, toggleAllSelector:'#toggle_releasability_', 'textExpand':'', 'textCollapse':'', classExpand: 'ui-icon-triangle-1-s', classCollapse: 'ui-icon-triangle-1-e'});//.tablesorter();
        //  toggle on first column
        collapser.find('.rollapsible_alt a').unbind('click').click(function(e) {
            $(this).parents('.rcollapsible_alt').siblings('.rcollapsible').find('a').click();
            return false;
        });
    }

    $(document).on('click', '.titleheader span.collapsible', function(e) {
        $(this).parent().next().toggle();
        $(this).filter('.ui-icon').toggleClass('ui-icon-triangle-1-e ui-icon-triangle-1-s');
    });
    collapse();
    collapse2();

    // evidently collapsible is broken for collapsing "all", so this is a quick
    // hack to fix it :(
    $(document).on('click', '#toggle_sources', function(e) {
        var me = $(this);
        var classes = $(this).attr('class').split(/\s+/);
        $('#source_listing.collapser tr td.collapsible').each(function(e) {
            var link = $(this).children('a')
            for (var i=0, len=classes.length; i<len; i++){
                if (link.hasClass(classes[i])){
                    link.click();
                }
            }
        });
        if (me.hasClass('ui-icon-triangle-1-e')) {
            me.removeClass('ui-icon-triangle-1-e');
            me.addClass('ui-icon-triangle-1-s');
        } else {
            me.removeClass('ui-icon-triangle-1-s');
            me.addClass('ui-icon-triangle-1-e');
        }
    });
    $(document).on('click', '#toggle_releasability', function(e) {
        var me = $(this);
        var classes = $(this).attr('class').split(/\s+/);
        $('#releasability_list.rcollapser tr td.rcollapsible').each(function(e) {
            var link = $(this).children('a')
            for (var i=0, len=classes.length; i<len; i++){
                if (link.hasClass(classes[i])){
                    link.click();
                }
            }
        });
        if (me.hasClass('ui-icon-triangle-1-e')) {
            me.removeClass('ui-icon-triangle-1-e');
            me.addClass('ui-icon-triangle-1-s');
        } else {
            me.removeClass('ui-icon-triangle-1-s');
            me.addClass('ui-icon-triangle-1-e');
        }
    });

    $('a').each(function(){
        var href = $(this).attr('href');
        if (href) {
            if( (href.match(/^http?\:/i)) && (!href.match(document.domain))) {
                $(this).addClass('external');
            }
        }
    });
    $(document).on('click', 'a.external', function(e) {
        e.preventDefault();
        var answer = confirm("You are about to leave CRITs and view the content of another website.\n\n" + $(this).attr('href') + "\n\nCRITs cannot be held responsible for the content of external websites.");
        if (answer){
            window.location = $(this).attr('href');
        }
    });

    $('.multiselect').multiselect({dividerLocation:0.5});

    $('.advanced_search').click(function(e) {
      e.stopPropagation();
    });
    $('.asearch').click(function(e) {
      e.stopPropagation();
      $('.advanced_search_container').toggle();

      //collect object types for search
      // Let's just call this when needed, until search is converted to a dynamic dialog
      if ($('select#object_s').find("option").length === 0)
          getAllObjectTypes($('select#object_s'));
    });
    $('.notify_enable').click(function(e) {
      e.stopPropagation();
        var pos = $(this).position();
        var height = $(this).outerHeight();
        $('.notifications').css({
            position: 'absolute',
            top: (pos.top + height + 10) + "px",
            left: pos.left + "px"
        }).toggle();
    });
    $('.notifications').click(function(e) {
        e.stopPropagation();
    });

    var isSearchObjectsLoaded = false;
    var isOpenSearchMenu = false;
    var isOpenNavMenu = false;

    $('#search-menu').mmenu({
        slidingSubmenus: false,
        zposition: "next",
        position: "right",
        dragOpen: true,
	modal: false,
	onClick: {close: true},
        header: {
            add: true,
            update: true,
            title: "Advanced Search",
        },
    },
    {
        transitionDuration: 0,
	pageSelector: ".content",
	preventTabbing: false,
    })
    .on(
        'opening.mm',
        function() {
            disable_mmenu_buttons();
            isOpenSearchMenu = false;
            $('#mm-blocker').remove();

            if(isSearchObjectsLoaded === false) {
                getAllObjectTypes($('select#object_s'));
                isSearchObjectsLoaded = true;
            }

            $('#search-menu ul').show();
        }
    )
    .on(
        'opened.mm',
        function() {
            $('.content').css('left', '0px');
            $('.content').css('width', 'auto');
            $('.search-menu-icon').click(function() {
                close_search_menu()
            });

            $('.nav-menu-icon').click(function() {
                isOpenNavMenu = true;
                close_search_menu()
            });
        }
    )
    .on(
        'closing.mm',
        function() {
            disable_mmenu_buttons();
        }
    )
    .on(
        'closed.mm',
        function() {
            $('.search-menu-icon').click(function() {
                open_search_menu()
            });

            if(isOpenNavMenu) {
                isOpenNavMenu = false;
                open_nav_menu()
            } else {
                $('.nav-menu-icon').click(function() {
                    open_nav_menu()
                });
            }
        }
    );


    // Don't let disabled menu items close the menu
    $("a.noclick").wrapInner("<div/>").on('click', "div", function(e) {
	    e.preventDefault(); e.stopPropagation(); });

    $('#nav-menu').mmenu({
        slidingSubmenus: false,
        zposition: "next",
	position: "left",
        dragOpen: true,
	modal: false,
	onClick: {close: true},
        searchfield: {
            add: true,
            search: true,
            placeholder: "Search Menu Options",
            showLinksOnly: true,
        },
        header: {
            add: true,
            update: true,
            title: "Welcome to CRITs",
	    preventTabbing: false,
        },
    },
    {
        transitionDuration: 0,
	pageSelector: ".content",
    })
    .on(
        'opening.mm',
        function() {
            disable_mmenu_buttons();
            isOpenNavMenu = false;
            $('#mm-blocker').remove()

            $('#nav-menu ul:first').show();
        }
    )
    .on(
        'opened.mm',
        function() {

            $('.nav-menu-icon').off().click(function() {
                close_nav_menu()
            });

            $('.search-menu-icon').off().click(function() {
                isOpenSearchMenu = true;
                close_nav_menu()
            });

            // set focus on the search bar
            // $('.mm-search input').focus()
        }
    )
    .on(
        'closing.mm',
        function() {
            disable_mmenu_buttons();
        }
    )
    .on(
        'closed.mm',
        function() {
            $('.nav-menu-icon').off().click(function() {
                open_nav_menu()
            });

            if(isOpenSearchMenu) {
                isOpenSearchMenu = false;
                open_search_menu()
            } else {
                $('.search-menu-icon').off().click(function() {
                    open_search_menu()
                });
            }
        }
    );

    $(document).click(function() {
        $('.notifications').hide();
        $('.advanced_search_container').hide();
    });

    $('.nav-menu-icon').off().click(function() {
	    open_nav_menu();
	});

    $('.search-menu-icon').off().click(function() {
	    open_search_menu();
	});


    $("#form-add-new-user").off().submit(function(e) {
        e.preventDefault();
        var result = $(this).serialize();
        $.ajax({
            type: "POST",
            url: source_access,
            data: result,
            datatype: 'json',
            success: function(data) {
                $("#form-add-new-user-results").show().css('display', 'table');
                $("#form-add-new-user-results").html(data.message);
                $('#users_listing').jtable('reload');
                if (data.form) {
                   $('#form-add-new-user').children('table').contents().replaceWith($(data.form));
                   $('.multiselect').multiselect({dividerLocation:0.5});
                }
            }
        });
    });
    $( "#add-new-user-form" ).dialog({
        autoOpen: false,
        modal: true,
        width: "auto",
        height: "auto",
        buttons: {
            "Add/Edit User": function(e) {
                $("#form-add-new-user").submit();
            },
            "Cancel": function() {
                $(":input", "#form-add-new-user").each(function() {
                    $(this).val('');
                });
                $( this ).dialog( "close" );
            },
        },
        close: function() {
                        $(":input", "#form-add-new-user").each(function() {
                                $(this).val('');
                        });
        },
    });

    $("#form-add-new-action").off().submit(function(e) {
        e.preventDefault();
        var result = $(this).serialize();
        $.ajax({
            type: "POST",
            url: new_action,
            data: result,
            datatype: 'json',
            success: function(data) {
                $("#form-add-new-action-results").show().css('display', 'table');
                $("#form-add-new-action-results").html(data.message);
                if (data.form) {
                   $('#form-add-new-action').children('table').contents().replaceWith($(data.form));
                }
            }
        });
    });
    $( "#add-new-action-form" ).dialog({
        autoOpen: false,
        modal: true,
        width: "auto",
        height: "auto",
        buttons: {
            "Add/Edit Action": function(e) {
                $("#form-add-new-action").submit();
            },
            "Cancel": function() {
                $(":input", "#form-add-new-action").each(function() {
                    $(this).val('');
                });
                $( this ).dialog( "close" );
            },
        },
        close: function() {
                        $(":input", "#form-add-new-action").each(function() {
                                $(this).val('');
                        });
        },
    });



    $(".source_subscription").click(function(e) {
        var me = $(this);
        e.stopPropagation();
    // Preventing the default causes more of a delay for the user, but if the ajax fails it changes it below.
    //  e.preventDefault();
        $.ajax({
            type: "POST",
            url: source_subscription,
            data: {source: me.attr("data")},
            datatype: 'json',
            success: function(data) {
            if (data.message == "subscribed") {
            me.prop('checked', true);
            } else {
            me.prop('checked', false);
            }
            }
        });
    });

    $("#enable_totp").click(function(e) {
        $('#change_password').toggle();
        $('#totp_pin').toggle();
        $('#submit_pin').toggle();
        if ($(this).text() == 'Enable/Change TOTP') {
            $(this).text('Cancel');
        } else {
            $(this).text('Enable/Change TOTP');
        }
    });

    $("#submit_pin").off().click(function(e) {
        var new_pin = $('#new_totp_pin').val();
        $.ajax({
            type: "POST",
            url: change_totp_pin,
            data: {'new_pin': new_pin},
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    $('#change_password').toggle();
                    $('#totp_pin').toggle();
                    $('#submit_pin').toggle();
                    $('#new_pin').val('');
                    $('#password_change_results').text(data.message);
                    $('#password_change_results').append(data.qr_img);
                    $('#enable_totp').text('Enable/Change TOTP');
                } else {
                    $('#password_change_results').text(data.message);
                }
            }
        });
    });

    $("#change_password").click(function(e) {
        $('#current_password').toggle();
        $('#new_password').toggle();
        $('#new_password_confirm').toggle();
        $('#submit_password').toggle();
        $('#enable_totp').toggle();
        if ($(this).text() == 'Change Password') {
            $(this).text('Cancel');
        } else {
            $(this).text('Change Password');
        }
    });

    $("#submit_password").off().click(function(e) {
        var current_p = $('#current_p').val();
        var new_p = $('#new_p').val();
        var new_p_c = $('#new_p_c').val();
        $.ajax({
            type: "POST",
            url: change_password,
            data: {'current_p': current_p, 'new_p': new_p, 'new_p_c': new_p_c},
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    $('#enable_totp').toggle();
                    $('#current_password').toggle();
                    $('#new_password').toggle();
                    $('#new_password_confirm').toggle();
                    $('#submit_password').toggle();
                    $('#current_p').val('');
                    $('#new_p').val('');
                    $('#new_p_c').val('');
                    $('#password_change_results').text(data.message);
                } else {
                    $('#password_change_results').text(data.message);
                }
            }
        });
    });

    $('#reset_password').off().click(function(e) {
        var state = $(this).attr('data-state');
        if (state == 'email') {
            data = {
                action: 'send_email',
                username: $('#r_username').val(),
                email: $('#r_email').val(),
            }
            $.ajax({
                type: "POST",
                url: reset_password,
                data: data,
                datatype: 'json',
                success: function(data) {
                    if (data.success) {
                        $('#reset_password').attr('data-state', 'reset_code');
                        $('#reset_password').text('Submit Reset Code');
                        $('#rcode').show();
                    }
                    $('#ajax_response').text(data.message);
                }
            });
        } else if (state == 'reset_code') {
            data = {
                action: 'submit_reset_code',
                username: $('#r_username').val(),
                email: $('#r_email').val(),
                reset_code: $('#reset_code').val(),
            }
            $.ajax({
                type: "POST",
                url: reset_password,
                data: data,
                datatype: 'json',
                success: function(data) {
                    if (data.success) {
                        $('#new_password').show();
                        $('#new_password_confirm').show();
                        $('#reset_password').attr('data-state', 'submit_reset');
                        $('#reset_password').text('Submit New Password');
                    }
                    $('#ajax_response').text(data.message);
                }
            });
        } else if (state == 'submit_reset') {
            data = {
                action: 'submit_passwords',
                username: $('#r_username').val(),
                email: $('#r_email').val(),
                reset_code: $('#reset_code').val(),
                new_p: $('#new_p').val(),
                new_p_c: $('#new_p_c').val(),
            }
            $.ajax({
                type: "POST",
                url: reset_password,
                data: data,
                datatype: 'json',
                success: function(data) {
                    if (data.success) {
                        $('div.reset_password').css('margin-left', '-115px');
                        $('div.reset_password').text(data.message + ' You may now log in!');
                    } else {
                        $('#ajax_response').text(data.message);
                    }
                }
            });
        }
    });

    $('.clipboard_qtip').each(function() {
      $(this).qtip({
          content: $(this).next('div.clipboard_qtip_body'),
          show: 'click',
          events: {
              hide: function(event, api) {
                  // Reset hide event when it hides...?
                  if (api.get('hide.event') === false) {
                      api.set('hide.event', 'mouseleave');
                  }
              }
          },
          style: {
              classes: 'ui-tooltip-dark ui-tooltip-rounded ui-tooltip-shadow',
              width: '415px'
          },
          position: {
              my: 'top left',
              at: 'bottom right',
              adjust: {
                  x: -5
              }
          }
      }).bind('click', function() {
          $(this).qtip('option', 'hide.event', 'click');
      })
    })
    // dirty hacks so we can close qtip clicking on anything but the qtip and
    // sub-elements for the qtip-body
    $(document).click(function(e) {
        $('.clipboard_qtip').qtip('hide');
        if ($(e.target).closest('#favorites_results').length == 0) {
            $('#favorites_results').hide();
        }
    });

    initTabNav();

    //edit status in place
    $('#object_status.edit').editable(function(value, settings) {
        revert = this.revert;
        var her = $(this).closest('tr').find('.object_status_response');
        return function(value, settings, elem) {
            $.ajax({
                type:"POST",
                async:false,
                url: $(elem).attr('action'),
                data: {'value':value},
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
        type:'select',
        data: {"New":"New", "In Progress":"In Progress", "Analyzed":"Analyzed",
"Deprecated":"Deprecated"},
        style:'display:inline',
        submit:'OK'
    });

    setTimeout(function(){
        var t = performance.timing;
        if ($("#pageLoadTiming").length) {
        $("#pageLoadTiming").text((t.loadEventEnd - t.fetchStart)/1000 + "s");
        }
        // console.log("Page Load: " + (t.loadEventEnd - t.fetchStart)/1000 + "s");
    }, 500);

    //help!
    $('#help_overlay').click(function(e) {
        $('body').chardinJs('start');
    });

    if (typeof subscription_type !== "undefined") {
        if (subscription_type) {
            $('[id^="form-download-"]').find('option[value="' + subscription_type + '"]').prop('selected', true);
        }
    }

    $('#global_search_box').focus(function(e) {
        $.ajax({
            type:"GET",
            url: get_search_help_url,
            success: function(data) {
                if (data.template) {
                    var rdiv = $("<div id='global_search_help' class='z-11' />");
                    $('body').append(rdiv);
                    $('#global_search_help')
                    .css('position', 'absolute')
                    .css('top', '25px')
                    .css('right', '0px')
                    .css('background-color', '#eee')
                    .css('border', '1px solid #ccc')
                    .css('display', 'none')
                    .css('height', '300px')
                    .css('width', '300px')
                    .css('overflow-x', 'wrap')
                    .css('overflow-y', 'auto')
                    .html(data.template)
                    .show();
                }
            }
        });
    })
    .focusout(function(e) {
        $('#global_search_help').remove();
    });

    $(document).on('click', '.make_default_api_key', function(e) {
        var me = $(this)
        $.ajax({
            type: 'POST',
            url: make_default_api_key,
            data: {name: me.attr('data-name')},
            success: function(data) {
                if (data.success) {
                    $('span#default_api_key').remove();
                    var defapi = '<span id="default_api_key">(default)</span>';
                    me.closest('tr').find('td:first').append(defapi);
                    me.closest('tbody').find('button:hidden').show();
                    me.closest('tr').find('td:nth-child(5)').find('button').hide();
                    me.closest('tr').find('td:nth-child(4)').find('button').hide();
                }
            }
        });
    });

    $(document).on('click', '.revoke_api_key', function(e) {
        var me = $(this)
        $.ajax({
            type: 'POST',
            url: revoke_api_key,
            data: {name: me.attr('data-name')},
            success: function(data) {
                if (data.success) {
                    me.closest('tr').remove();
                }
            }
        });
    });

    $(document).on('click', '.view_api_key', function(e) {
        var me = $(this)
        var name = me.attr('data-name');
        if (me.text() == 'Hide Key') {
            view = '<button class="view_api_key" data-name="' + name + '">View Key</button>';
            me.closest('td').html(view);
        } else {
            $.ajax({
                type: 'POST',
                url: get_api_key,
                data: {name: name},
                success: function(data) {
                    if (data.success) {
                        var parent = me.closest('td');
                        parent.append('<br />' + data.message);
                        me.text('Hide Key');
                    }
                }
            });
        }
    });

    $('#add_api_key').on('click', function(e) {
        var tbl = $('#api_key_table > tbody:last');
        var ib = "<form id='new_api_form'><input type='text' size=30 id='new_api_name' /></form>";
        var cancel = "<button id='cancel_api_add'>Cancel</button>";
        var new_row = "<tr><td>" + ib + cancel + "</td><td></td><td></td><td></td><td></td></tr>";
        tbl.append(new_row);
        $('#new_api_name').focus();
    });

    $(document).on('click', '#cancel_api_add', function(e) {
        $(this).closest('tr').remove();
    });

    $(document).on('submit', '#new_api_form', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var me = $(this);
        var name = $('#new_api_name').val();
        $.ajax({
            type: 'POST',
            url: create_api_key,
            data: {name: name},
            success: function(data) {
                if (data.success) {
                    var parent = me.closest('tr');
                    defkey = '<button class="make_default_api_key" data-name="' + data.message.name + '">Make Default</button>';
                    revoke = '<button class="revoke_api_key" data-name="' + data.message.name + '">Revoke Key</button>';
                    view = '<button class="view_api_key" data-name="' + data.message.name + '">Hide Key</button>';
                    parent.find('td:nth-child(1)').html('').text(data.message.name);
                    parent.find('td:nth-child(2)').text(data.message.date);
                    parent.find('td:nth-child(3)').html(view + '<br />' + data.message.key);
                    parent.find('td:nth-child(4)').html(defkey);
                    parent.find('td:nth-child(5)').html(revoke);
                }
            }
        });
    });

    // Handle preferred action clicks
    $("#preferred_actions").click(function() {
        $.ajax({
            type: "POST",
            async: false,
            url: add_preferred_actions,
            data: {'obj_type': subscription_type, 'obj_id': subscription_id},
            success: function(data) {
                if (data.success) {
                    $("#action_listing_header").show();
                    $("#action_listing > tbody:last-child").append(data.html);
                } else {
                    error_message_dialog('Action Error', data.message);
                }
            }
        });
    });
}); //document.ready
