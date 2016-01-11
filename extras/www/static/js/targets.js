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
    // Upload a related pcap (Using the related dialog persona)
    $( "#dialog-new-pcap" ).on("dialogopen.add_related_pcap", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(target_id);
        $(this).find("form #id_related_type").val("Target");
        // $(this).find("form").removeAttr("target"); // Get rid of target to refresh page
        // Unlike new-sample below, this does not redirect us nor refresh the
        // Relationships list of the Sample, so delay for a few seconds then reload the
        // page after uploaded.  Added a fileUploadComplete event to work around this.
        $(this).find("form").bind("fileUploadComplete",
                      function(e, response) {
                          if (response.success)
                          setTimeout(function() {
                              document.location = document.location },
                              3000); });
        }
    });
    // Upload a related Domain (Using the related dialog persona)
    $( "#dialog-new-domain" ).on("dialogopen.add_related_domain", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(target_id);
        $(this).find("form #id_related_type").val("Target");
        }
    });
    // Add a related Actor (Using the related dialog persona)
    $( "#dialog-new-actor" ).on("dialogopen.add_related_actor", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(target_id);
        $(this).find("form #id_related_type").val("Target");
        }
    });
    // Add a related Target (Using the related dialog persona)
    $( "#dialog-new-target" ).on("dialogopen.add_related_target", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(target_id);
        $(this).find("form #id_related_type").val("Target");
        }
    });
    // Add a related Email (Using the related dialog persona)
    $( "#dialog-new-email-eml" ).on("dialogopen.add_related_email", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(target_id);
        $(this).find("form #id_related_type").val("Target");
        // $(this).find("form").removeAttr("target"); // Get rid of target to refresh page

        // Unlike new-sample below, this does not redirect us nor refresh the
        // Relationships list of the Sample, so delay for a few seconds then reload the
        // page after uploaded.  Added a fileUploadComplete event to work around this.
        $(this).find("form").bind("fileUploadComplete",
                      function(e, response) {
                          if (response.success)
                          setTimeout(function() {
                              document.location = document.location },
                              3000); });
        }
    });
    // Add a related Event (Using the related dialog persona)
    $( "#dialog-new-event" ).on("dialogopen.add_related_event", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(target_id);
        $(this).find("form #id_related_type").val("Target");
        }
    });
    // Add a related Exploit (Using the related dialog persona)
    $( "#dialog-new-exploit" ).on("dialogopen.add_related_exploit", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(target_id);
        $(this).find("form #id_related_type").val("Target");
        }
    });
    // Add a related IP (Using the related dialog persona)
    $( "#dialog-new-ip" ).on("dialogopen.add_related_ip", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(target_id);
        $(this).find("form #id_related_type").val("Target");
        }
    });
    details_copy_id('Target');
    toggle_favorite('Target');
});
