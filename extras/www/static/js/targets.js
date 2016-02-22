$(document).ready(function(){
    $(".target_tablesorter").tablesorter({sortList: [[4,2]]});
    $(".division_tablesorter").tablesorter({sortList: [[1]]});
    $( "#edit_details" ).click( function() {
        $( "#edit-details-form" ).dialog( "open" );
    });
    $( "#edit-details-form" ).dialog({
        autoOpen: false,
        modal: true,
        width: "auto",
        height: "auto",
        buttons: {
            "Update Details": function() {
            $("#form-edit-details").submit();
            },
            "Cancel": function() {
            $( this ).dialog( "close" );
            },
        },
    });
    populate_id(target_id, 'Target');
    details_copy_id('Target');
    toggle_favorite('Target');
});
