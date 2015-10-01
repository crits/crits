/*******************************************************************************
 * Name: email_indicator_duplicate_crosscheck
 *
 * Description: Performs client-side crosschecking of email and
 * indicator relationships to indicate to a user if an email field might
 * already have an indicator created already. This is to prevent duplicate
 * indicators from existing and also to reduce the manual cross checking a
 * user would have to manually perform.
 *
 * This method should be called only within the page context where a
 * email_detail is loaded.
 *
 * @params - None
 * @returns - None. Icons are changed in the email details listing table
 * 		to indicate any email fields that might already have indicators.
 ******************************************************************************/
function email_indicator_duplicate_crosscheck() {
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

    $('#email_listing_table tr').each(function() {
        var email_data_type = $(this).attr('data-type')
        if(email_data_type) {
            if(email_data_type in textTypeValueSet) {
                var value = $(this).find('span.header_value').text()
                if(value !== 'Click pencil to edit...') {
                    var iconNode = $(this).find('.indicator_from_object')

                    if(iconNode) {
                        if(value in textTypeValueSet[email_data_type]) {
                            var iconNode = $(this).find('.create-indicator')
                            var originalTitle = $(iconNode).prop('title')
                            $(iconNode).removeClass('ui-icon-plusthick').addClass('ui-icon-circle-plus')
                            %(iconNode).prop('title', originalTitle + ": Warning: Indicator might already exist")
                        }
                    }
                } else {
                    var iconNode = $(this).find('.create-indicator')
                    var originalTitle = $(iconNode).prop('title')
                    $(iconNode).removeClass('ui-icon-plusthick').addClass('ui-icon-alert')
                    %(iconNode).prop('title', originalTitle + ": Warning: A value should be supplied first")
                }
            }
        }
    })
}

$(document).ready(function(){
    $(".create-indicator").off().click(function(event) {
        var me = $(this);
        data = {
            'type': $(this).attr('data-type'),
            'field': $(this).attr('data-field'),
        };

        // Might be nicer if this was a spinning icon, but working with what we have handy
        me.removeClass('ui-icon-plusthick');
        me.removeClass('ui-icon-circle-plus');
        me.removeClass('ui-icon-alert');
        me.addClass('ui-icon-clock');

        $.ajax({
            type: "POST",
            url: indicator_from_header_field,
            data: data,
            dataType: "json",
            success: function(data) {
                me.removeClass('ui-icon-clock');
                me.removeClass('ui-icon-plusthick');
                me.removeClass('ui-icon-circle-plus');
                me.removeClass('ui-icon-alert');
                if (data.success) {
                    $('#relationships_div_container').html(data.message);
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
    $("#json_button").click(function(event) {
        event.preventDefault();
        $.ajax({
            type: "GET",
            url: email_detail + "?format=json",
            dataType: "json",
            success: function(data) {
                $("#json_display").val(data.email_yaml);
            }
        });
    });
    $("#yaml_button").click(function(event) {
        event.preventDefault()
        $.ajax({
            type: "GET",
            url: email_detail + "?format=yaml",
            dataType: "json",
            success: function(data) {
                $("#yaml_display").val(data.email_yaml);
            }
        });
    });

    $("#yaml_edit").click(function(event) {
	    $.ajax({
		    type: "GET",
		    url: email_detail + "?format=yaml",
		    dataType: "json",
		    success: function(data) {
			$("#yaml-edit-form #id_yaml_data").val(data.email_yaml);
			$("#yaml-edit-form #yaml_update_section").show();
			$("#yaml-edit-form #id_source").hide();
			$("#yaml-edit-form #id_source_reference").hide();
			$("#yaml-edit-form #id_source_date").hide();
		    }
		});
	    $( "#yaml-edit-form" ).dialog( "open" );
	});
    $("#form-yaml-edit").off().submit(function(e) {
	    e.preventDefault();
	    var result = $(this).serialize();
	    $.ajax({
		    type: "POST",
		    url: email_yaml_add,
		    data: result,
		    datatype: 'json',
		    success: function(data) {
			if (!data.success) {
			    if (data.form) {
				$('#yaml-edit-form').find('table').contents().replaceWith($(data.form));
				$("#yaml-edit-form #yaml_update_section").show();
				$("#yaml-edit-form #id_source").hide();
				$("#yaml-edit-form #id_source_reference").hide();
				$("#yaml-edit-form #id_source_date").hide();
			    }
			    if (data.message) {
				$("#form-yaml-edit-results").show().css('display', 'table');
				$("#form-yaml-edit-results").html(data.message);
			    }
			} else {
			    $(":input", "#form-yaml-edit").each(function() {
				    $(this).val('');
				});
			    location.reload(true);
			}
		    }
		});
    });
    $( "#yaml-edit-form" ).dialog({
    autoOpen: false,
    modal: true,
    width: "auto",
    height: "auto",
    buttons: {
        "Update YAML": function() {
        $("#form-yaml-edit").submit();
        },
        "Cancel": function() {
        $( this ).dialog( "close" );
        },
    },
    });
    $(document).on('click', 'a.header_search', function(e) {
        var cv = $(this).find('form');
        if (cv.length) {
            return false;
        } else {
            return true;
        }
    });
    $('.edit_header_value').click( function(e) {
        var header_edit = $(this).parent().find('span.header_value');
        header_edit.trigger('custom_header_edit');
    });
    $('span.header_value').editable(function(value, settings) {
        revert = this.revert;
        var her = $(this).closest('tr').find('.header_edit_response');
        return function(value, settings, elem) {
            var pre_value = value;
            var dt = $(elem).attr('data-type');
            var data = {
                type: dt,
                value: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_header_value,
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
                        her.attr('title', "Edit Successful!");
                        if (data.isodate) {
                            $('span[data-type="isodate"]').text(data.isodate);
                        }
                        if (data.links) {
                            value = data.links;
                        }
                        if ($(elem).parent().is('a')) {
                            var link_edit = $(elem).parent();
                            var link_url = link_edit.attr('href');
                            var link_split = link_url.split('=');
                            link_split[link_split.length -1] = value;
                            var new_url = link_split.join('=');
                            link_edit.attr('href', new_url);
                        }
                        var parent_td = $(elem).closest('td');
                        var splunk_link = parent_td.find('a.splunk_link');
                        if (splunk_link.length > 0) {
                            var new_splunk_url = splunk_search_url + value;
                            splunk_link.attr('href', new_splunk_url);
                        }
                        if (dt == 'to' || dt == 'cc') {
                            $(elem).attr('data-list', pre_value);
                        }
                        if (!data.links) {
                            value = value.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
                        }
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    // console.log(textStatus + errorThrown);
                    her.removeClass('ui-icon-circle-check');
                    her.addClass('ui-icon');
                    her.addClass('ui-icon-alert');
                    her.attr('title', textStatus + ": " + errorThrown);
                    value = revert;
                }
            });
            return value;
        }(value, settings, this);
        },
        {
            event: 'custom_header_edit',
            style: 'inherit',
            type: 'textarea',
            height: '20px',
            width: '400px',
            placeholder: "Click pencil to edit...",
            onblur: "submit",
            data: function(value, settings) {
                var dt = $(this).attr('data-type');
                if (dt === 'to' || dt === 'cc') {
                    return $(this).attr('data-list');
                } else {
                    return value.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&amp;/g, '&');
                }
            }
    });

    $('.edit_raw_email').click( function(e) {
        var type_ = $(this).attr('data-type');
        if (type_ == 'raw_header') {
            $('#email_header_raw_header').prop('readonly', false);
            $('#form_edit_raw_header').show();
        } else {
            $('#email_header_raw_body').prop('readonly', false);
            $('#form_edit_raw_body').show();
        }
    });
    $('.raw_submit').off().click( function(e) {
        e.preventDefault();
        var type_ = $(this).attr('data-type');
        var action = $(this).text();
        if (action == 'Cancel') {
            if (type_ == 'header') {
                $('#email_header_raw_header').prop('readonly', true);
                $('#form_edit_raw_header').hide();
            } else {
                $('#email_header_raw_body').prop('readonly', true);
                $('#form_edit_raw_body').hide();
            }
        } else {
            var her = $(this).closest('div').prev('h3').find('.raw_edit_response');
            if (type_ == 'header') {
                var dt = 'raw_header';
                var value = $('#email_header_raw_header').val();
            } else {
                var dt = 'raw_body';
                var value = $('#email_header_raw_body').val();
            }
            var data = {
                type: dt,
                value: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_header_value,
                data: data,
                success: function(data) {
                    if (!data.success) {
                        her.removeClass('ui-icon-circle-check');
                        her.addClass('ui-icon');
                        her.addClass('ui-icon-alert');
                        her.attr('title', data.message);
                    } else {
                        her.removeClass('ui-icon-alert');
                        her.addClass('ui-icon');
                        her.addClass('ui-icon-circle-check');
                        her.attr('title', "Edit Successful!");
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    // console.log(textStatus + errorThrown);
                    her.removeClass('ui-icon-circle-check');
                    her.addClass('ui-icon');
                    her.addClass('ui-icon-alert');
                    her.attr('title', textStatus + ": " + errorThrown);
                }
            });
        }
    });

    // $("#download-email-form").dialog({
    // autoOpen: false,
    // modal: true,
    // width: "auto",
    // height: "auto",
    // buttons: {
    //     "Download Email": function() {
    //     $("#form-download-email").submit();
    //     $(this).dialog("close");
    //     },
    //     "Cancel": function() {
    //     $(this).dialog("close");
    //     },
    // },

    // create: function() {
    //     var meta = $("#id_meta_format");
    //     var bin = $("#id_binary_format");
    //     var no_meta = $(meta).children("option[value='none']");
    //     var no_bin = $(bin).children("option[value='none']");

    //     //Makes no sense to download empty file, so either binaries or metadata have to be downloaded.
    //     //don't allow user to select downloading neither
    //     var mutually_exc = function(e) {
    //     //alert($(primary).prop("selected"));
    //       var elem = e.data['elem'];
    //     if ($(this).val() == "none") {
    //         $(elem).hide();
    //     } else {
    //         $(elem).show();
    //     }
    //     };
    //     meta.change({elem: no_bin}, mutually_exc);
    //     bin.change({elem: no_meta}, mutually_exc);
    // },

    // close: function() {
    //     // allFields.val("").removeClass("ui-state-error");
    // },
    // });

    var localDialogs = {
    	"download-email": {title: "Download Email", submit: defaultSubmit, href:""},
    };

    $.each(localDialogs, function(id,opt) { stdDialog(id, opt); });
    details_copy_id('Email');
    toggle_favorite('Email');
});
