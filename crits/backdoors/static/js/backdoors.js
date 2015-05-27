var backdoor_tags = true;

$(document).ready(function() {

    details_copy_id('Backdoor');
    toggle_favorite('Backdoor');

    window.add_backdoor_aliases = false;
    $("#backdoor_aliases").tagit({
        allowSpaces: true,
        allowDuplicates: false,
        removeCOnfirmation: true,
        afterTagAdded: function(event, ui) {
            var my_aliases = $("#backdoor_aliases").tagit("assignedTags");
            update_aliases(my_aliases);
        },
        afterTagRemoved: function(event, ui) {
            var my_aliases = $("#backdoor_aliases").tagit("assignedTags");
            update_aliases(my_aliases);
        },
    });

    $(document).trigger('enable_backdoor_aliases');

    function update_aliases(my_aliases) {
        if (window.add_backdoor_aliases) {
            var data = {
                        'oid': subscription_id,
                        'aliases': my_aliases.toString(),
            };
            $.ajax({
                type: "POST",
                url: update_backdoor_aliases,
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

    $('#edit_backdoor_name').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var data = {
                name: value
            };
            $.ajax({
                type: "POST",
                async: false,
                url: edit_backdoor_name,
                data: data,
                success: function(data) {
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

    $('#edit_backdoor_version').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var data = {
                version: value
            };
            $.ajax({
                type: "POST",
                async: false,
                url: edit_backdoor_version,
                data: data,
                success: function(data) {
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

}); //document.ready
