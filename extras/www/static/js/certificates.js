$(document).ready(function() {
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
