  $(document).ready(function() {
    $('[id^="tabnav"]').tabs();
        $( '[id^="accordion"]' ).accordion({
            collapsible: true,
            active: false,
            autoHeight: false,
            navigation: true
        });

//      var choices = {'a':1, 'b':2};
        //setup editing
        $('.edit.text').editable(function(value, settings) {
                return editDomain(value, settings, this);
        }, {
            type:'text',
            style:'display: inline',
            submit:'Save',
            //callback: function(value, settings) {
            //  alert($(this).attr('action'));
            //  $(this).attr('action', '');
            //},
        });
        $('.edit.textarea').editable(function(value, settings) {
                return editDomain(value, settings, this);
        }, {
            type: 'textarea',
            submit:'Save'});
//      $('.edit.select').editable(function(value, settings) {
//          return editDomain(value, settings, this);
//      },{
//          type:'select',
//          submit:'Save',
//          data: choices,
//          callback: function(value, settings) {
//              $(this).before('<div></div>').append('foo');
//          }
//      });
        populate_id(id,'Domain');
        details_copy_id('Domain');
        toggle_favorite('Domain');
    }); //$(document).ready

    function editDomain(value, settings, elem) {
        var result = "";
        $.ajax({
            type: "POST",
            async: false,
            url: $(elem).attr('action'),
            success: function(data) {
                result = data;
            },
            data: {'value':value}
        });
        if (result != value) {
            alert("Please enter a valid domain name.");
        } else {
            //update url
            $(elem).attr('action', $(elem).attr('action').replace(/\/[^/]+\/$/, '/'+result+'/'));
            //alert($(elem).attr('action'));
        }
        return result;
    };

    function getWhois() {
        if (true) {
            alert("This functionality is not yet implemented.");
        } else {
            $.ajax({
         type: "GET",
       url: "http://localhost/",
         async: false,
         success: function(html){
        $("#id_data").val(html);
         },
         error: function(xhr, err){
        //alert("Error: "+xhr.status);
         }
       });
        }
  }

    function diffUsingJS(from_text, to_text, from_header, to_header, output_div) {
        var base = difflib.stringAsLines(from_text);
        var newtxt = difflib.stringAsLines(to_text);
        var sm = new difflib.SequenceMatcher(base, newtxt);
        var opcodes = sm.get_opcodes();
        $(output_div).empty()
            .append(diffview.buildView({
                baseTextLines:base,
                newTextLines:newtxt,
                opcodes:opcodes,
                baseTextName:from_header,
                newTextName:to_header,
                viewType:0}));
        //console.log(result);
    }

