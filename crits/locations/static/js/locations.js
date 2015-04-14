$(document).ready(function() {
    var localDialogs = {
        "add-location": {
            title: "Location",
            href:"",
        },
    };
    $.each(localDialogs, function(id,opt) {
        stdDialog(id,opt);
    });
    $(document).on('click', '.location_description', function(e) {
        $(this).editable(function(value, settings) {
            return function(value, settings, elem) {
                var ln = $(elem).parent().siblings('#location').text();
                var lt = $(elem).parent().siblings('#location_type').text();
                var ld = $(elem).parent().siblings('#location_date').text();
                var data = {
                    location_name: ln,
                    location_type: lt,
                    date: ld,
                    description: value
                };
                $.ajax({
                    type: "POST",
                    async: false,
                    url: edit_location,
                    data: data,
                });
                return value;
            }(value, settings, this);
            },
            {
                type: 'text',
                height: "25px",
                width: "150px",
                tooltip: "",
                cancel: "Cancel",
                submit: "Ok",
                placeholder: "Edit..."
        });
    });
    $(document).on('click', '.location_latitude', function(e) {
        $(this).editable(function(value, settings) {
            return function(value, settings, elem) {
                var ln = $(elem).parent().siblings('#location').text();
                var lt = $(elem).parent().siblings('#location_type').text();
                var ld = $(elem).parent().siblings('#location_date').text();
                var data = {
                    location_name: ln,
                    location_type: lt,
                    date: ld,
                    latitude: value
                };
                $.ajax({
                    type: "POST",
                    async: false,
                    url: edit_location,
                    data: data,
                });
                return value;
            }(value, settings, this);
            },
            {
                type: 'text',
                height: "25px",
                width: "150px",
                tooltip: "",
                cancel: "Cancel",
                submit: "Ok",
                placeholder: "Edit..."
        });
    });
    $(document).on('click', '.location_longitude', function(e) {
        $(this).editable(function(value, settings) {
            return function(value, settings, elem) {
                var ln = $(elem).parent().siblings('#location').text();
                var lt = $(elem).parent().siblings('#location_type').text();
                var ld = $(elem).parent().siblings('#location_date').text();
                var data = {
                    location_name: ln,
                    location_type: lt,
                    date: ld,
                    longitude: value
                };
                $.ajax({
                    type: "POST",
                    async: false,
                    url: edit_location,
                    data: data,
                });
                return value;
            }(value, settings, this);
            },
            {
                type: 'text',
                height: "25px",
                width: "150px",
                tooltip: "",
                cancel: "Cancel",
                submit: "Ok",
                placeholder: "Edit..."
        });
    });
}); // document.ready
