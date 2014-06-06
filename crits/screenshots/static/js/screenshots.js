function add_screenshot_dialog(e) {
    var dialog = $("#dialog-add-screenshot").closest(".ui-dialog");
    var form = dialog.find("form");
    file_upload_dialog(e);
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

    //XXX: This isn't working at all, so we get no message response in the
    //     form, and it doesn't update the screenshot gallery.
    $('.screenshot-submit-iframe').load(function(e) {
        console.log("hi");
        var $curTar = $(e.currentTarget);
        var response = this.contentDocument.body.innerHTML;
        if (!response) {
            return;
        }
        try {
            response = $.parseJSON($.parseJSON(response));
        } catch (err) {
            response = {'message': 'Error uploading file.', 'success': false}
        }

        this.contentDocument.body.innerText = '';

        var dialog = $curTar.closest(".ui-dialog");
        dialog.find(".message").text(response.message).show();
        if (response.html) {
            $('div#links').append(data.html);
        }
    });
});
