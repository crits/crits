$(document).ready(function() {
    $('#pcap_description').editable(function(value, settings) {
        return function(value, settings, elem) {
            var data = {
                description: value,
            };
            $.ajax({
                type: "POST",
                async: false,
                url: update_pcap_description,
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
            onblur: 'ignore',
    });
    details_copy_id('PCAP');
    toggle_favorite('PCAP');
    populate_id(pcap_id, 'PCAP');
}); //document.ready

