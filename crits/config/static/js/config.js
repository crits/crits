$(document).ready(function() {
    $('#config_form_submit').off().click(function(e) {
        e.preventDefault();
        $('#config_form').submit();
    });
    $('#config_form').off().submit(function(e) {
        e.preventDefault();
        $.ajax({
            type:"POST",
            url: $('#config_form').attr('action'),
            data: $(this).serialize(),
            datatype: 'json',
            success: function(data) {
                $("#config_results").text(data.message);
            },
        });
    });
}); //document.ready

