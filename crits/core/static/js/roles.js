$(document).ready(function() {

    var cur_sources = $('#id_sources').val();
    $('.multiselect').multiselect({dividerLocation:0.5});
    $('ul.connected-list').css('height', '100px');

    $(document).on('change', '#id_sources', function(e) {
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
                        console.log("removing " + s);
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
    });
});
