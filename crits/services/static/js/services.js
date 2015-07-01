$(document).ready(function() {
    $(document).on('click', '#info_button', function(e) {
        $(this).parent().next().toggle();
    });
    $(document).on('click', 'a#log_button', function(e) {
        $(this).parent().next().next().toggle();
    });
    $(document).on('click', 'a#results_button', function(e) {
        $(this).parent().next().next().next().toggle();
    });
    $(document).on('click', '.delete_analysis', function(e) {
        var url = $(this).attr('href');
        var msg = $(this).attr('msg');
        e.preventDefault();
        $('<div title="Delete Analysis" id="tmp_delete">' + msg + '</div>').dialog({
            close: function() {
                    $(this).dialog("destroy");
                },
            buttons: {
                "Delete": function() {
                    $.ajax({
                        async: false,
                        type: "POST",
                        url: url,
                        data: {},
                        datatype: 'json',
                        success: function(data) {
                            if (data) {
                                $('#analysis_section').html(data.html);
                                var count = $('.analysis_result_summary_item', data.html).length;
                                $('#analysis_button > span').text('Analysis (' + count + ')');
                                $('#tmp_delete').remove();
                            }
                        }
                    });
                },
                "Cancel": function() {
                    $(this).dialog("destroy");
                }
            }
        });
    });
    $(document).on('click', '#refresh_services', function(e) {
        e.preventDefault();
        var url = $(this).attr('data-url');
        $.ajax({
            async: false,
            type: "POST",
            url: url,
            data: {},
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    $('#analysis_section').html(data.html);
                    var count = $('.analysis_result_summary_item', data.html).length;
                    $('#analysis_button > span').text('Analysis (' + count + ')');
                }
            }
        });
    });
    $(document).on('submit', '#form-run-service', function(e) {
        e.preventDefault();
        var data = $(this).serialize();
        var url = $(this).attr('action')
        $.ajax({
            async: false,
            type: "POST",
            url: url,
            data: data,
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    $('#analysis_section').html(data.html);
                    var count = $('.analysis_result_summary_item', data.html).length;
                    $('#analysis_button > span').text('Analysis (' + count + ')');
                    $('#run-service-form').remove();
                } else {
                    $('#run-service-form').append('<div>' + data.html + '</div>');
                }
            }
        });
    });
    $(document).on('click', '.service_run_button', function(e) {
        e.preventDefault();
        var service_url = $(this).attr('data-url');
        $.ajax({
            async: false,
            type: "POST",
            url: service_url,
            data: {},
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    $('#analysis_section').html(data.html);
                } else {
                    if (data.form) {
                        $('.service_run_form').html(data.form);
                        $('#run-service-form').dialog({
                            autoOpen: true,
                            modal: true,
                            width: "auto",
                            height: "auto",
                            close: function() {
                                    $(this).html('');
                                    $(this).dialog("destroy");
                                },
                            buttons: {
                                "Run Service": function(e) {
                                    $('#form-run-service').submit();
                                },
                                "Cancel": function() {
                                    $('#run-service-form').html('');
                                    $('#run-service-form').dialog("destroy");
                                },
                            },
                        });
                    }
                    if (data.html) {
                        $('.service_run_form').html("Failed: " + data.html);
                        $('.service_run_form').dialog({
                            autoOpen: true,
                            modal: true,
                            width: "auto",
                            height: "auto",
                            title: "Failure",
                            close: function() {
                                    $(this).html('');
                                    $(this).dialog("destroy");
                                },
                            buttons: {
                                "OK": function() {
                                    $(this).html('');
                                    $(this).dialog("destroy");
                                },
                            },
                        });
                    }
                }
            }
        });
    });
    $(document).on("click", "span.enabled", function(e) {
         var me = $(this);
         var url = me.attr('data-url');
         $.ajax({
             type: 'POST',
             url: url,
             data: {},
             datatype: 'json',
             success: function(data) {
                 if (data.success) {
                     if (me.text() == "Yes") {
                         me.text("No");
                     } else {
                         me.text("Yes")
                     }
                     me.attr('data-url', data.url);
                 }
             }
         });
    });
    $(document).on('submit', '#form-config-service', function(e) {
        e.preventDefault();
        var data = $(this).serialize();
        var url = $(this).attr('action')
        $.ajax({
            async: false,
            type: "POST",
            url: url,
            data: data,
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    $('#service_edit_results').text("Success!");
                } else {
                    $('#service_edit_results').text(data.config_error);
                }
            }
        });
    });
});
