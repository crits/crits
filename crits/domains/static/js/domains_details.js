  $(document).ready(function() {
    $('[id^="tabnav"]').tabs();
        $( '[id^="accordion"]' ).accordion({
            collapsible: true,
            active: false,
            autoHeight: false,
            navigation: true
        });

//      var choices = {'a':1, 'b':2};
        //setup editing
        $('.edit.text').editable(function(value, settings) {
                return editDomain(value, settings, this);
        }, {
            type:'text',
            style:'display: inline',
            submit:'Save',
            //callback: function(value, settings) {
            //  alert($(this).attr('action'));
            //  $(this).attr('action', '');
            //},
        });
        $('.edit.textarea').editable(function(value, settings) {
                return editDomain(value, settings, this);
        }, {
            type: 'textarea',
            submit:'Save'});
//      $('.edit.select').editable(function(value, settings) {
//          return editDomain(value, settings, this);
//      },{
//          type:'select',
//          submit:'Save',
//          data: choices,
//          callback: function(value, settings) {
//              $(this).before('<div></div>').append('foo');
//          }
//      });
    // Upload a related pcap (Using the related dialog persona)
    $( "#dialog-new-pcap" ).on("dialogopen.add_related_pcap", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
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
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
        }
    });
    // Add a related Actor (Using the related dialog persona)
    $( "#dialog-new-actor" ).on("dialogopen.add_related_actor", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
        }
    });
    // Add a related Target (Using the related dialog persona)
    $( "#dialog-new-target" ).on("dialogopen.add_related_target", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
        }
    });
    // Add a related Email (Using the related dialog persona)
    $( "#dialog-new-email-eml" ).on("dialogopen.add_related_email", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
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
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
        }
    });
    // Add a related Exploit (Using the related dialog persona)
    $( "#dialog-new-exploit" ).on("dialogopen.add_related_exploit", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
        }
    });
    // Add a related IP (Using the related dialog persona)
    $( "#dialog-new-indicator" ).on("dialogopen.add_related_indicator", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
        }
    });
    // Add a related IP (Using the related dialog persona)
    $( "#dialog-new-ip" ).on("dialogopen.add_related_ip", function(e) {
        if ($(this).dialog("persona") == "related") {
        $(this).find("form #id_related_id").val(domain_id);
        $(this).find("form #id_related_type").val("Domain");
        }
    });
        details_copy_id('Domain');
        toggle_favorite('Domain');
    }); //$(document).ready

    function editDomain(value, settings, elem) {
        var result = "";
        $.ajax({
            type: "POST",
            async: false,
            url: $(elem).attr('action'),
            success: function(data) {
                result = data;
            },
            data: {'value':value}
        });
        if (result != value) {
            alert("Please enter a valid domain name.");
        } else {
            //update url
            $(elem).attr('action', $(elem).attr('action').replace(/\/[^/]+\/$/, '/'+result+'/'));
            //alert($(elem).attr('action'));
        }
        return result;
    };

    function getWhois() {
        if (true) {
            alert("This functionality is not yet implemented.");
        } else {
            $.ajax({
         type: "GET",
       url: "http://localhost/",
         async: false,
         success: function(html){
        $("#id_data").val(html);
         },
         error: function(xhr, err){
        //alert("Error: "+xhr.status);
         }
       });
        }
  }

    function diffUsingJS(from_text, to_text, from_header, to_header, output_div) {
        var base = difflib.stringAsLines(from_text);
        var newtxt = difflib.stringAsLines(to_text);
        var sm = new difflib.SequenceMatcher(base, newtxt);
        var opcodes = sm.get_opcodes();
        $(output_div).empty()
            .append(diffview.buildView({
                baseTextLines:base,
                newTextLines:newtxt,
                opcodes:opcodes,
                baseTextName:from_header,
                newTextName:to_header,
                viewType:0}));
        //console.log(result);
    }

