$(document).ready(function() {
    $('#cert_description').editable(function(value, settings) {
        return function(value, settings, elem) {
            var data = {
                description: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_cert_description,
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
    $( "#delete_cert" ).click( function() {
                    $( "#delete-cert-form" ).dialog( "open" );
    });
    $( "#delete-cert-form" ).dialog({
                    autoOpen: false,
                    modal: true,
                    width: "auto",
                    height: "auto",
                    buttons: {
                                    "Delete Certificate": function() {
                                                    $("#form-delete-cert").submit();
                                    },
                                    "Cancel": function() {
                                                    $( this ).dialog( "close" );
                                    },
                    },
                    close: function() {
                                    // allFields.val( "" ).removeClass( "ui-state-error" );
                    },
    });
    details_copy_id('Certificate');
    toggle_favorite('Certificate');
}); //document.ready
