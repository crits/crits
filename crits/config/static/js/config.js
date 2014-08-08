$(document).ready(function() {
    $('#config_form_submit').off().click(function(e) {
        e.preventDefault();
        $('#config_form').submit();
    });
    
    $(document).on("keypress", ".error", function(){
    	$(this).removeClass("error"); 
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
                if(data.errors.length > 0)
                	for(index in data.errors) 
                		$("#id_"+data.errors[index]).addClass("error");
            },
        });
    });
    
   
}); //document.ready

