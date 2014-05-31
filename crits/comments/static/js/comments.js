$(document).ready(function() {
    $(document).on('click', '#show_comments', function(e) {
        toggleCommentRows();
    });
    $("div#calendar").datepicker({
        altField: 'input#activitydate',
        altFormat: 'yy-mm-dd',
        onSelect: function() {
            getActivity($("#activitydate").val());
        }
    });
    $(document).on('keyup', '#activitydate', function(e) {
        getActivity($(this).val());
    });
    $(document).on('click', '.previousdate', function(e) {
        getActivity($(this).text());
    });
    $(document).on('click', '.nextdate', function(e) {
        getActivity($(this).text());
    });
    function getActivity(day) {
        var data = {
            'date': day,
            'atype': atype,
            'value': value
        };
        $.ajax({
            type: "POST",
            url: activity_url,
            data: data,
            datatype: 'json',
            cache: false,
            statusCode: {
                500: function() {
                    $('#activity_date_error').html('<font color="red">Error: invalid date?</font>');
                    $('#activity_date_error').css({'display': 'inline-block'});
                }
            },
            success: function(data) {
                if (data.success) {
                    $('span.activity_list').html(data.html);
                    toggleCommentRows();
                    $('#activitydate').val(day);
                    $('#activity_date_error').css({'display': 'none'});
                    $('#activity_date_error').html('');
                }
            }
        });
    }
    function toggleCommentRows() {
        if ($("#show_comments").is(":checked")) {
            if ($(".comment_row").length) {
                $(".comment_row").show();
            }
        } else {
            if ($(".comment_row").length) {
                $(".comment_row").hide();
            }
        }
    }
    function getNewComments() {
        var day = $("table.comment_table tr:first-child td:nth-child(2) div.comment_info span:first-child b:first-child").text();
        var convert = false;
        if (day.length < 1) {
            day = new Date().setHours(0,0,0,0);
            convert = true;
        }
        data = {
            'date': day,
            'atype': atype,
            'value': value,
            'convert': convert
        }
        var today = $('#activitydate').val()
        var check = $.datepicker.formatDate('yy-mm-dd', new Date());
        if (today == check) {
            $.ajax({
                type: "POST",
                url: new_comments_url,
                data: data,
                datatype: 'json',
                success: function(data) {
                    if (data.success) {
                        $(data.html).prependTo("table.comment_table > tbody");
                        toggleCommentRows();
                    }
                },
            });
        }
        setTimeout(getNewComments, 60000);
    }
    setTimeout(getNewComments, 60000);
});
