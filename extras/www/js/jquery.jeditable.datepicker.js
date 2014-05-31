$.editable.addInputType('datetimepicker', {
    element : function(settings, original) {
        var input = $('<input>');
        if (settings.width  != 'none') { input.width(settings.width);  }
        if (settings.height != 'none') { input.height(settings.height); }
        input.attr('autocomplete','off');
        $(this).append(input);
        return(input);
    },
    plugin : function(settings, original) {
        /* Workaround for missing parentNode in IE */
        var form = this;
        settings.onblur = 'ignore';
        $(this).find('input').datetimepicker().bind('click', function() {
            $(this).datetimepicker('show');
            return false;
        }).bind('dateSelected', function(e, selectedDate, $td) {
            $(form).submit();
        });
    }
});
