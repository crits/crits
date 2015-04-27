function strip(html) {
    var tmp = document.createElement("DIV");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText;
}

function add_screenshot_dialog(e) {
    var dialog = $("#dialog-add-screenshot").closest(".ui-dialog");
    var form = dialog.find("form");
    file_upload_dialog(e);
    var btn = $('<button id="get_ss_ids">Copy IDs</button>');
    if ($('#get_ss_ids').length < 1) {
        $('#form-add-screenshot').find('#id_screenshot_ids').after(btn);
    }

    $(document).on('click', '#get_ss_ids', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var sids = readCookie('screenshot_ids');
        $('#id_screenshot_ids').val(sids);
    });

    $('.screenshot-submit-iframe').load(function(e) {
        var $curTar = $(e.currentTarget);
        var response = strip(this.contentDocument.body.innerHTML);
        if (!response) {
            return;
        }
        try {
            response = $.parseJSON(response);
        } catch (err) {
            response = {'message': 'Error uploading file.', 'success': false}
        }

        this.contentDocument.body.innerText = '';

        var dialog = $curTar.closest(".ui-dialog");
        dialog.find(".message").text(response.message).show();
        if (response.html) {
            // don't add it again if it's already on the page
            if ($('a[data-id="' + response.id + '"]').length < 1) {
                $('div#links').append(response.html);
            };
        }
    });
}

function add_screenshot_submit(e) {
    var elem = $(e.currentTarget);
    var dialog = elem.closest(".ui-dialog");
    var form = dialog.find("form");
    var csrftoken = readCookie('csrftoken');
    var input = $("<input>")
               .attr("type", "hidden")
               .attr("name", "csrfmiddlewaretoken").val(csrftoken);
    form.append($(input));
    form.find("#id_oid").val(my_id);
    form.find("#id_otype").val(my_type);
    form.submit();
}

function check_ss_cookie() {
    var check_ss = readCookie('screenshot_ids');
    if (check_ss !== null) {
        $('.clear_ss_cookie').css({'outline': 'none',
                                  'background-image': "url('/css/images/ui-icons_70b2e1_256x240.png')"});
    } else {
        $('.clear_ss_cookie').css({'outline': 'none',
                                  'background-image': "url('/css/images/ui-icons_222222_256x240.png')"});
    }
}

function remove_ss_from_cookie(sid) {
    var existing_ss = readCookie('screenshot_ids');
    existing_ss = existing_ss.replace(sid, '') .replace(',,', ',');
    while(existing_ss.charAt(0) === ',')
            existing_ss = existing_ss.substr(1);
    if (existing_ss.length) {
        createCookie('screenshot_ids',existing_ss, 60);
    } else {
        eraseCookie('screenshot_ids');
    }
}

$(document).ready(function() {
    var ssDialogs = {
        "add-screenshot": {title: "Add Screenshot", open: add_screenshot_dialog,
            new: {submit: add_screenshot_submit }},
    };

    $.each(ssDialogs,function(id,opt) {
        stdDialog(id,opt);
    });

    check_ss_cookie();

    $('.copy_ss_id').each(function(id, opt) {
        var me = $(this);
        var existing_ss = readCookie('screenshot_ids');
        if (existing_ss !== null) {
            var sid = me.attr('data-id');
            if (existing_ss.indexOf(sid) > -1) {
                me.removeClass('ui-icon-radio-on')
                .addClass('ui-icon-bullet')
                .addClass('copied')
                .show();
            }
        }
    });

    $(document).on('mouseenter', '#links a', function(e) {
        $(this).find('.remove_screenshot').show();
        $(this).find('.copy_ss_id').show();
    });

    $(document).on('mouseleave', '#links a', function(e) {
        $(this).find('.remove_screenshot').hide();
        if (!$(this).find('.copy_ss_id').hasClass('copied')) {
            $(this).find('.copy_ss_id').hide();
        }
    });

    $(document).on('click', '.remove_screenshot', function(e) {
        e.preventDefault();
        e.stopPropagation();
        me = $(this);
        var sid = me.attr('data-id');
        var obj = me.attr('data-type');
        var objid = me.attr('data-obj');
        var data = {obj: obj, sid: sid, oid: objid};
        $.ajax({
            type: "POST",
            url: remove_screenshot_url,
            data: data,
            dataType: "json",
            success: function(data) {
                if (data.success) {
                    me.closest('a').remove();
                    remove_ss_from_cookie(sid);
                }
            }
        });
    });

    $(document).on('click', '.copy_ss_id', function(e) {
        e.preventDefault();
        e.stopPropagation();
        me = $(this);
        var sid = me.attr('data-id');
        if (me.hasClass('copied')) {
            me.removeClass('ui-icon-bullet')
            .removeClass('copied')
            .addClass('ui-icon-radio-on');
            remove_ss_from_cookie(sid);
        } else {
            me.removeClass('ui-icon-radio-on')
            .addClass('ui-icon-bullet')
            .addClass('copied');
            var existing_ss = readCookie('screenshot_ids');
            if (existing_ss !== null) {
                sid += "," + existing_ss;
            }
            createCookie('screenshot_ids',sid, 60);
        }
        check_ss_cookie();
    });

    $(document).on('click', '.clear_ss_cookie', function(e) {
        eraseCookie('screenshot_ids');
        check_ss_cookie();
        $('.copied').each(function(e) {
            $(this).removeClass('ui-icon-bullet')
            .removeClass('copied')
            .addClass('ui-icon-radio-on')
            .hide();
        });
    });

    // Normally description editing is done in description_widget.html,
    // but not for screenshots because descriptions of screenshots are
    // only editable from the listing page.
    $(document).on('click', '.edit_ss_description', function(e) {
        e.preventDefault();
        $(this).editable(function(value, settings) {
            var revert = this.revert;
            return function(value, settings, elem) {
                var data = {
                    description: value,
                    id: $(elem).attr('data-id'),
                    type: "Screenshot"
                };
                $.ajax({
                    type: "POST",
                    async: false,
                    url: update_ss_description,
                    data: data,
                    success: function(data) {
                        if (!data.success) {
                            value = revert;
                        }
                    }
                });
                return value;
            }(value, settings, this);
            },
            {
                type: 'textarea',
                placeholder: 'None',
                height: "50px",
                width: "200px",
                tooltip: "",
                cancel: "Cancel",
                submit: "Ok",
                onblur: 'ignore',
        });
    });

    // hack to get the "Ok" button for inline description editing to actually
    // fire the form submission.
    $(document).on('click', '.edit_ss_description form button[type="submit"]', function(e) {
        e.preventDefault();
        $(this).closest('form').submit();
    });
});
