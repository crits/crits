function strip(html) {
    var tmp = document.createElement("DIV");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText;
}

function add_screenshot_dialog(e) {
    var dialog = $("#dialog-add-screenshot").closest(".ui-dialog");
    var form = dialog.find("form");
    file_upload_dialog(e);

    $('.screenshot-submit-iframe').load(function(e) {
        var $curTar = $(e.currentTarget);
        var response = strip(this.contentDocument.body.innerHTML);
        if (!response) {
            return;
        }
        try {
            response = $.parseJSON(response);
        } catch (err) {
            alert(err);
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

    form.find("#id_oid").val(my_id);
    form.find("#id_otype").val(my_type);
    form.submit();
}

$(document).ready(function() {
    var ssDialogs = {
        "add-screenshot": {title: "Add Screenshot", open: add_screenshot_dialog,
            new: {submit: add_screenshot_submit }},
    };

    $.each(ssDialogs,function(id,opt) {
        stdDialog(id,opt);
    });
});
