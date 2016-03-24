$(document).ready(function() {
    // Due to loading orders and scoping, we need to set this to window.
    // This prevents campaign aliases from being set every time the page
    // loads per every entry in the aliases list.
    window.add_aliases = false;
    $('[id^="accordion"]').accordion({
        collapsible: true,
        active: false,
        autoHeight: false,
        navigation: true
    });
    $(".chart").tablesorter();
    $(".chart2").tablesorter({sortList: [[4,1]]});

    $(document).on('click', '#add_ttp', function(e) {
        $("#add-ttp-form").dialog("open");
    });
    $("#add-ttp-form").dialog({
        autoOpen: false,
        modal: true,
        width: "auto",
        height: "auto",
        buttons: {
            "Add TTP": function(e) {
                add_ttp();
                e.stopImmediatePropagation();
                $(this).dialog("close");
            },
            "Cancel": function() {
                $(this).dialog("close");
            },
        },
        close: function() {
            $("#form-add-ttp :input[name='ttp']").val('');
        }
    });
    
    function add_ttp() {
        var action = "add";
        var ttp = $("#form-add-ttp :input[name='ttp']").val();
        var data = {'ttp': ttp, 'action': action};
        $.ajax({
            type: "POST",
            url: ttp_target,
            data: data,
            datatype: 'json',
            success: function(result) {
                if (result.success) {
                    $('#ttp_data').html(result.html);
                }
                else {
                    $('#ttp_data').html(result.message);
                }
            }
        });
    };
    $(document).on('click', '.ttp_ttp', function(e) {
        $(this).editable(function(value, settings) {
            return function(value, settings, elem) {
                var data = {
                    old_ttp: $(elem).attr("data-ttp"),
                    new_ttp: value,
                    action: "edit"
                };
                $.ajax({
                    type: "POST",
                    async: false,
                    url: ttp_target,
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
        });
    });
    $(document).on('click', '.remove_ttp_button', function(e) {
        var ttp = $(this).attr('data-ttp');
        $( "#remove-ttp-form" ).attr('data-ttp', ttp);
        $( "#remove-ttp-form" ).dialog( "open" );
    });
    $( "#remove-ttp-form" ).dialog({
        autoOpen: false,
        modal: true,
        width: "auto",
        height: "auto",
        buttons: {
            "Delete TTP": function(e) {
                remove_ttp();
                e.stopImmediatePropagation();
                $(this).dialog("close");
            },
            "Cancel": function() {
                $( this ).dialog( "close" );
            },
        },
    });
    function remove_ttp() {
        var action = "remove";
        var ttp = $("#remove-ttp-form").attr('data-ttp');
        var data = {'ttp': ttp, 'action': action};
        $.ajax({
            type: "POST",
            url: ttp_target,
            data: data,
            datatype: 'json',
            success: function(result) {
                if (result.success) {
                    $('#ttp_data').html(result.html);
                }
                else {
                    $('#ttp_data').html(result.message);
                }
            }
        });
    };
    $("#campaign_aliases").tagit({
        allowSpaces: true,
        removeConfirmation: false,
        afterTagAdded: function(event, ui) {
            var my_tags = $("#campaign_aliases").tagit("assignedTags");
            update_aliases(my_tags);
        },
        beforeTagRemoved: function(event, ui) {
            if (is_admin != "True") {
                return false;
            }
        },
        afterTagRemoved: function(event, ui) {
            var my_tags = $("#campaign_aliases").tagit("assignedTags");
            update_aliases(my_tags);
        },
    });
    function update_aliases(my_tags) {
        if (window.add_aliases) {
            var data = {
                        'name': campaign_name,
                        'tags': my_tags.toString(),
            };
            $.ajax({
                type: "POST",
                url: update_campaign_aliases,
                data: data,
                datatype: 'json',
                success: function(data) {
                    if (!data.success) {
                        alert("Failed to update aliases!");
                    }
                }
            });
        }
    }
    $(document).trigger('enable_aliases');

    var localDialogs = {
	"add-campaign": {title: "Campaign", href:"",
			 update: { open: update_dialog} },

    };
    $.each(localDialogs, function(id,opt) { 
	    stdDialog(id,opt); 
	});
    populate_id(campaign_id,'Campaign');
    details_copy_id('Campaign');
    toggle_favorite('Campaign');
}); // document.ready
