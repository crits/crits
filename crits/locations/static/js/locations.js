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
}); // document.ready
