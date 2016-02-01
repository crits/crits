$(document).ready(function() {
    $('#event_title').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var data = {
                title: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_event_title,
                data: data,
                success: function(data) {
                    if (!data.success) {
                        value = revert;
                        $('#event_title_error').text(data.message);
                    }
                }
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
    });
    $('#event_type').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var data = {
                type: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_event_type,
                data: data,
                success: function(data) {
                    if (!data.success) {
                        value = revert;
                        $('#event_type_error').text(data.message);
                    }
                }
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'select',
            data: function() {
                var etypes = {};
                var sorted = [];
                $.ajax({
                    type: "GET",
                    async: false,
                    url: get_event_types,
                    success: function(data) {
                        data.types.sort();
                        len = data.types.length;
                        for (var i=0; i < len; i++) {
                            etypes[data.types[i]] = data.types[i];
                        }
                    }
                });
                return etypes;
            },
            style:'display:inline',
            cancel: "Cancel",
            submit: "Ok",
            //onblur:"submit"
    });

    // $("#download_event").click(function() {
    //     $("#download-event-form").dialog("open");
    // });
    // $("#download-event-form").dialog({
    //     autoOpen: false,
    //     modal: true,
    //     width: "auto",
    //     height: "auto",
    //     buttons: {
    //         "Download Event": function() {
    //         $("#form-download-event").submit();
    //         $(this).dialog("close");
    //         },
    //         "Cancel": function() {
    //         $(this).dialog("close");
    //         },
    //     },

    //     create: function() {
    //         var meta = $("#id_meta_format");
    //         var bin = $("#id_binary_format");
    //         var no_meta = $(meta).children("option[value='none']");
    //         var no_bin = $(bin).children("option[value='none']");

    //         //Makes no sense to download empty file, so either binaries or metadata have
    //         //to be downloaded. don't allow user to select downloading neither
    //         var mutually_exc = function(e) {
    //         //alert($(primary).prop("selected"));
    //           var elem = e.data['elem'];
    //         if ($(this).val() == "none") {
    //             $(elem).hide();
    //         } else {
    //             $(elem).show();
    //         }
    //         };
    //         meta.change({elem: no_bin}, mutually_exc);
    //         bin.change({elem: no_meta}, mutually_exc);
    //     },
    // });

    var localDialogs = {
    	"download-event": {title: "Download Event", submit: defaultSubmit, href:""},
    };

    $.each(localDialogs, function(id,opt) { stdDialog(id, opt); });
    // Upload a related pcap (Using the related dialog persona)
    $( "#dialog-new-pcap" ).on("dialogopen.add_related_pcap", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
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
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
        }
    });
    // Add a related Actor (Using the related dialog persona)
    $( "#dialog-new-actor" ).on("dialogopen.add_related_actor", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
        }
    });
    // Add a related Target (Using the related dialog persona)
    $( "#dialog-new-target" ).on("dialogopen.add_related_target", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
        }
    });
    // Add a related Email (Using the related dialog persona)
    $( "#dialog-new-email-eml" ).on("dialogopen.add_related_email", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
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
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
        }
    });
    // Add a related Exploit (Using the related dialog persona)
    $( "#dialog-new-exploit" ).on("dialogopen.add_related_exploit", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
        }
    });
    // Add a related Indicator (Using the related dialog persona)
    $( "#dialog-new-indicator" ).on("dialogopen.add_related_indicator", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
        }
    });
    // Add a related IP (Using the related dialog persona)
    $( "#dialog-new-ip" ).on("dialogopen.add_related_ip", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(event_id);
        $(this).find("form #id_related_type").val("Event");
        }
    });
    details_copy_id('Event');
    toggle_favorite('Event');
}); //document.ready

