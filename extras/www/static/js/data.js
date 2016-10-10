$(document).ready(function() {
$('#object_data').editable(function(value, settings) {
    var revert = this.revert;
    return function(value, settings, elem) {
        var data = {
            type: subscription_type,
            id: subscription_id,
            data: value,
        };
        $.ajax({
            type: "POST",
            async: false,
            url: data_update,
            data: data,
            success: function(data) {
                if (!data.success) {
                    value = revert;
                    $('#object_data_error').text(' Error: ' + data.message);
                }
            }
        });
        var escapes = {
            '&': '&amp;',
            '"': '&quot;',
            "'": '&apos;',
            '>': '&gt;',
            '<': '&lt;'
        };

        return value.replace(/&(?!amp;|quot;|apos;|gt;|lt;)|["'><]/g,
                             function (s) { return escapes[s]; });
    }(value, settings, this);
    },
    {
        type: 'textarea',
        height: "200px",
        width: "800px",
        tooltip: "",
        cancel: "Cancel",
        submit: "Ok",
        onblur: 'ignore',
});
});
