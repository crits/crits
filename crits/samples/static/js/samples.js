$(document).ready(function(){
    $('[id^="accordion"]').accordion({
        collapsible: true,
        active: false,
        autoHeight: false,
        navigation: true
    });
    $( "#tool_forms_button" ).click( function() {
        $( "#tool_forms" ).toggle( "fast" );
    });

    $("#strings_button").click(function() {
        $.ajax({
            type: "GET",
            url: get_strings,
            dataType: "json",
            success: function(data) {
                $("#tools_span").html("Strings");
                $("#tools_display").text(data.strings);
            }
        });
    });
    $("#stack_button").click(function() {
        $.ajax({
        type: "GET",
        url: get_stackstrings,
        dataType: "json",
        success: function(data) {
            $("#tools_span").html("Stack Strings");
            $("#tools_display").text(data.strings);
        }
        });
    });
    $("#hex_button").click(function() {
        $.ajax({
        type: "GET",
        url: get_hex,
        dataType: "json",
        success: function(data) {
            $("#tools_span").html("Hex");
            $("#tools_display").text(data.strings);
        }
        });
    });
    $("form#form-xor").submit(function(e) {
        e.preventDefault();
        var result = $(this).serialize();
        $.ajax({
            type: "POST",
            url: xor_search,
            data: result,
            dataType: "json",
            success: function(data) {
                $("#xor_search_results").show();
                var options = "";
                for (var i = 0; i < data['keys'].length; i++) {
                    options +='<option value="' + data['keys'][i] + '">' + data['keys'][i] + '</option>';
                }
                $("#xor_key_select").html(options);
                $.ajax({
                    type: "GET",
                    url: get_xor + data['keys'][0],
                    dataType: "json",
                    success: function(data) {
                        $("#tools_span").html("XOR");
                        $("#tools_display").text(data.strings);
                    }
                });
            }
        });
    });
    $("#xor_key_select").change(function() {
        $.ajax({
            type: "GET",
            url: get_xor + $("#xor_key_select").val(),
            dataType: "json",
            success: function(data) {
                $("#tools_span").html("XOR");
                $("#tools_display").text(data.strings);
            }
        });
    });

    var localDialogs = {
    // XXX None of these currently update in-place, so we need to make the
    // submit do a default action for now to refresh the whole page.
    "add-backdoor": {title: "Backdoor", submit: defaultSubmit, href:"" },
    "add-exploit": {title: "Add Exploit", submit: defaultSubmit, href:"" },
    "add-child": {title: "Add Child Sample", submit: defaultSubmit, href:"" },
    "unzip-sample": {title: "Unzip Sample", submit: defaultSubmit, href:"" },
    "delete-sample": {title: "Delete Sample", submit: defaultSubmit, href:"" },
    "download-sample": {title: "Download Sample", submit: defaultSubmit, href:"" },
    };

    $.each(localDialogs, function(id,opt) {
        stdDialog(id,opt, {update: { open: update_dialog}});
    });

    // Moved here, as these appear to be only used in sample tools
    // setup static form for samples details tools tab
    $('#form-add-object-static').prepend($('#form-add-object').contents().clone())
    $('#form-add-object-static').find('#add_object_static').click(function(e) {
        // XXXX For some reason file_upload status is still not displaying here...
        $.proxy(file_upload_dialog, $('#form-add-object-static').parent())();
        add_object_submit(e);
    })

    // For samples_tools_widgets
    var comment_form = $('#form-comments');
    $('#form-comments').find('#id_url_key,#id_subscribable').val(comments_url_key);
    $('#form-add-comment-static').prepend(comment_form.contents().clone());

    $('#form-add-comment-static').submit(function(e) {
        addEditSubmit(e);
    });

    $('#sample_filename').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var data = {
                'filename': value,
                'id': sample_id_escaped,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_sample_filename,
                data: data,
                success: function(data) {
                    if (!data.success) {
                        value = revert;
                        $('#sample_filename_error').text(data.message);
                    }
                }
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'textarea',
            width: "400px",
            tooltip: "",
            cancel: "Cancel",
            submit: "Ok",
            onblur: 'ignore',
    });
    $("#sample_filenames").tagit({
        allowSpaces: true,
        removeConfirmation: false,
        afterTagAdded: function(event, ui) {
            var my_tags = $("#sample_filenames").tagit("assignedTags");
            update_filenames(my_tags);
        },
        beforeTagRemoved: function(event, ui) {
            if (is_admin != "True") {
                return false;
            }
        },
        afterTagRemoved: function(event, ui) {
            var my_tags = $("#sample_filenames").tagit("assignedTags");
            update_filenames(my_tags);
        },
    });

    function update_filenames(my_tags) {
        if (window.add_filenames) {
            var data = {
                        'id': sample_id_escaped,
                        'tags': my_tags.toString(),
            };
            $.ajax({
                type: "POST",
                url: update_sample_filenames,
                data: data,
                datatype: 'json',
                success: function(data) {
                    if (!data.success) {
                        alert("Failed to update filenames!");
                    }
                }
            });
        }
    }

    $(document).trigger('enable_filenames');

    details_copy_id('Sample');
    toggle_favorite('Sample');
    populate_id(sample_id_escaped, 'Sample');

});
