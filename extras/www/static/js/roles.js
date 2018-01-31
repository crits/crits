$(document).ready(function() {

    var cur_sources = $('#id_sources').val();
    $('.multiselect').multiselect({dividerLocation:0.5});
    $('ul.connected-list').css('height', '100px');

    $(document).on('change', '#id_sources', function(e) {
        if (!no_submit) {
            var new_sources = $(this).val();
            if (cur_sources === null) {
                cur_sources = [];
            } else if (new_sources === null) {
                new_sources = [];
            }
            if (cur_sources.length > new_sources.length) {
                // removing
                // TODO: find out why "Remove All" leaves one behind :(
                var sdiff = $(cur_sources).not(new_sources).get();
                for (var i=0; i<sdiff.length; i++) {
                    s = sdiff[i];
                    var data = {
                        rid: rid,
                        name: s,
                    }
                    $.ajax({
                        type: 'POST',
                        url: role_remove_source,
                        data: data,
                        async: false,
                        dataType: 'json',
                        success: function(data) {
                            $('label#' + s).closest('tr').remove();
                        }
                    });
                }
            } else {
                // adding
                var sdiff = $(new_sources).not(cur_sources).get();
                for (var i=0; i<sdiff.length; i++) {
                    s = sdiff[i];
                    var data = {
                        rid: rid,
                        name: s,
                    }
                    $.ajax({
                        type: 'POST',
                        url: role_add_source,
                        data: data,
                        dataType: 'json',
                        success: function(data) {
                            $('table#role_source_table tbody').append(data.html);
                        }
                    });
                }
            }
            cur_sources = new_sources;
        }
    });

    $('#role_description').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var data = {
                rid: rid,
                description: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_role_description,
                data: data,
                success: function(data) {
                    if (!data.success) {
                        value = revert;
                    }
                }
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'textarea',
            height: "50px",
            width: "190px",
            tooltip: "",
            cancel: "Cancel",
            submit: "Ok",
            onblur: 'ignore',
    });

    $('#role_name').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var data = {
                rid: rid,
                name: value,
                old_name: revert,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_role_name,
                data: data,
                success: function(data) {
                    if (!data.success) {
                        value = revert;
                    }
                }
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'text',
            height: "25px",
            width: "190px",
            tooltip: "",
            cancel: "Cancel",
            submit: "Ok",
            onblur: 'ignore',
    });

    $(document).on('change', '.role_value', function(e) {
        if (!no_submit) {
            var data = {
                rid: rid,
                name: $(this).attr('name'),
                value: $(this).prop('checked')
            }
            $.ajax({
                type: 'POST',
                url: role_value_change,
                data: data,
                success: function(data) {
                }
            });
        }
    });

    $(document).on('click', '.copy_role', function(e) {
        if (!no_submit) {
            do_copy = true;
        }
    });
});
