  $(document).ready(function() {
    $('[id^="tabnav"]').tabs();
        $( '[id^="accordion"]' ).accordion({
            collapsible: true,
            active: false,
            autoHeight: false,
            navigation: true
        });

        //update displayed whois data depending on date selected
        //var whois_data = $.parseJSON("{{ whois_data|escapejs }}");
        $('#whois_section').find('#whois_detail').find('#id_date').change(function(e, stop_now) {
//          console.log(whois_data);
            $('#whois_section').find('#whois_detail').find('#id_data').val(whois_data[$(this).val()][0]);
            //make the other view display the same data, but keep them from calling each other infinitely
            if (!stop_now) {
                $('#whois_section').find('#whois_raw').find('#id_date').val($(this).val()).trigger('change', true);
            }
        });

        //make sure the data actually gets populated to begin with
        // (This call seems to be necessary only when the back button has been hit--the form ends
        //  up empty in this case.)
        $('#whois_section').find('#id_date').trigger('change');

        //update displayed whois data depending on date selected
        //var whois_data = $.parseJSON("{{ whois_data|escapejs }}");
        $('#whois_section').find('#whois_raw').find('#id_date').change(function(e, stop_now) {
            //console.log(whois_data);
            $('#whois_section').find('#whois_raw').find('#id_data').val(whois_data[$(this).val()][1]);
            //make the other view display the same data, but keep them from calling each other infinitely
            if (!stop_now) {
                $('#whois_section').find('#whois_detail').find('#id_date').val($(this).val()).trigger('change', true);
            }
        });

        $('#form-add-whois').submit(function(e) {
            e.preventDefault();
            var data = $(this).serialize();
            //console.log(data);
            //var date_select = $('#whois_section').find('#id_date');
            $.ajax({
                type: "POST",
                data: data,
                datatype: 'json',
                url: whois_update_url,
                success: function(data) {
                    if (data.success) {
                        //Add new data to our whois_data object
                        var date_exists = false;
                        if (data.date in whois_data) {
                            date_exists = true;
                        }
                        whois_data[data.date] = [data.data, $('#whois_section').find('#id_data').val()];

                        //Add new date to dropdown and select it
                        if (!date_exists) {
                            $('#whois_section').find('#whois_detail').find('#id_date').find('option[value=""]').after($('<option></option>').val(data.date).text(data.date));
                            $('#whois_section').find('#whois_raw').find('#id_date').prepend($('<option></option>').val(data.date).text(data.date));
                            $('#whois_section').find('#id_date').val(data.date).trigger('change');
                            $('#whois_section').find('#form-diff-whois').find('[id*="id"][id*="date"]').prepend($('<option></option>').val(data.date).text(data.date));
                        }
                        $('#whois_section').find('#whois_detail').find('#id_data')
                            .before($('<div id="message">Whois data successfully updated.</div>')
                            .delay(5000).queue(function(e) {$(this).html("").css('display', 'none').dequeue();}));
                    } else {
                        if (data.form) {
                            //display form with error messages
                            var form = $(data.form);
                            //repopulate the date-select box
                            $('#form-add-whois').children('table').contents().replaceWith(form)
                        } else if (data.message) {
                            alert(data.message);
                        }
                    }
                },
                error: function(xhr, err) {
                    alert("Error: "+xhr.status);
                }
            });
        });

        $('#form-diff-whois').submit(function(e) {
            e.preventDefault();
            var from_date = $(this).find('#id_from_date').val();
            var to_date = $(this).find('#id_to_date').val();
            if (!from_date || !to_date) {
                alert("Please select two whois dates to compare");
                return false;
            }
            diffUsingJS(whois_data[from_date][0], whois_data[to_date][0], from_date, to_date,
                $(this).find('#id_diff_data'));
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

