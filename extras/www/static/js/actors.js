var actor_tags = true;
var available_intended_effects = [];
var available_motivations = [];
var available_sophistications = [];
var available_threat_types = [];

$(document).ready(function() {

    populate_id(id,'Actor');

    details_copy_id('Actor');
    toggle_favorite('Actor');

    window.add_actor_aliases = false;
    $("#actor_aliases").tagit({
        allowSpaces: true,
        allowDuplicates: false,
        removeCOnfirmation: true,
        afterTagAdded: function(event, ui) {
            var my_aliases = $("#actor_aliases").tagit("assignedTags");
            update_aliases(my_aliases);
        },
        afterTagRemoved: function(event, ui) {
            var my_aliases = $("#actor_aliases").tagit("assignedTags");
            update_aliases(my_aliases);
        },
    });

    $(document).trigger('enable_actor_aliases');

    function update_aliases(my_aliases) {
        if (window.add_actor_aliases) {
            var data = {
                        'oid': subscription_id,
                        'aliases': my_aliases.toString(),
            };
            $.ajax({
                type: "POST",
                url: update_actor_aliases,
                data: data,
                datatype: 'json',
                success: function(data) {
                    if (!data.success) {
                        alert("Failed to update aliases!");
                    }
                }
            });
        }
    }

    $("#intended_effects_list").tagit({
        allowSpaces: true,
        allowDuplicates: false,
        removeCOnfirmation: true,
        showAutocompleteOnFocus: true,
        beforeTagAdded: function(event, ui) {
            if (available_intended_effects.indexOf(ui.tagLabel) == -1) {
                return false;
            }
            if (ui.tagLabel == "not found") {
                return false;
            }
        },
        afterTagAdded: function(event, ui) {
            var my_intended_effects = $("#intended_effects_list").tagit("assignedTags");
            update_actor_tags('ActorIntendedEffect', my_intended_effects);
        },
        afterTagRemoved: function(event, ui) {
            var my_intended_effects = $("#intended_effects_list").tagit("assignedTags");
            update_actor_tags('ActorIntendedEffect', my_intended_effects);
        },
        onTagClicked: function(event, ui) {
            var url = global_search + "?search_type=global&force_full=1&search=Search&q=" + ui.tagLabel;
            window.location.href = url;
        },
        availableTags: (function() {
            var results = get_available_tags('ActorIntendedEffect');
            return results;
        })(),
        autocomplete: {
            delay: 0,
            minLength: 0,
        },
    });

    $("#motivations_list").tagit({
        allowSpaces: true,
        allowDuplicates: false,
        removeCOnfirmation: true,
        showAutocompleteOnFocus: true,
        beforeTagAdded: function(event, ui) {
            if (available_motivations.indexOf(ui.tagLabel) == -1) {
                return false;
            }
            if (ui.tagLabel == "not found") {
                return false;
            }
        },
        afterTagAdded: function(event, ui) {
            var my_motivations = $("#motivations_list").tagit("assignedTags");
            update_actor_tags('ActorMotivation', my_motivations);
        },
        afterTagRemoved: function(event, ui) {
            var my_motivations = $("#motivations_list").tagit("assignedTags");
            update_actor_tags('ActorMotivation', my_motivations);
        },
        onTagClicked: function(event, ui) {
            var url = global_search + "?search_type=global&force_full=1&search=Search&q=" + ui.tagLabel;
            window.location.href = url;
        },
        availableTags: (function() {
            var results = get_available_tags('ActorMotivation');
            return results;
        })(),
        autocomplete: {
            delay: 0,
            minLength: 0,
        },
    });

    $("#sophistications_list").tagit({
        allowSpaces: true,
        allowDuplicates: false,
        removeCOnfirmation: true,
        showAutocompleteOnFocus: true,
        beforeTagAdded: function(event, ui) {
            if (available_sophistications.indexOf(ui.tagLabel) == -1) {
                return false;
            }
            if (ui.tagLabel == "not found") {
                return false;
            }
        },
        afterTagAdded: function(event, ui) {
            var my_sophistications = $("#sophistications_list").tagit("assignedTags");
            update_actor_tags('ActorSophistication', my_sophistications);
        },
        afterTagRemoved: function(event, ui) {
            var my_sophistications = $("#sophistications_list").tagit("assignedTags");
            update_actor_tags('ActorSophistication', my_sophistications);
        },
        onTagClicked: function(event, ui) {
            var url = global_search + "?search_type=global&force_full=1&search=Search&q=" + ui.tagLabel;
            window.location.href = url;
        },
        availableTags: (function() {
            var results = get_available_tags('ActorSophistication');
            return results;
        })(),
        autocomplete: {
            delay: 0,
            minLength: 0,
        },
    });


    $("#threat_types_list").tagit({
        allowSpaces: true,
        allowDuplicates: false,
        removeCOnfirmation: true,
        showAutocompleteOnFocus: true,
        beforeTagAdded: function(event, ui) {
            if (available_threat_types.indexOf(ui.tagLabel) == -1) {
                return false;
            }
            if (ui.tagLabel == "not found") {
                return false;
            }
        },
        afterTagAdded: function(event, ui) {
            var my_threat_types = $("#threat_types_list").tagit("assignedTags");
            update_actor_tags('ActorThreatType', my_threat_types);
        },
        afterTagRemoved: function(event, ui) {
            var my_threat_types = $("#threat_types_list").tagit("assignedTags");
            update_actor_tags('ActorThreatType', my_threat_types);
        },
        onTagClicked: function(event, ui) {
            var url = global_search + "?search_type=global&force_full=1&search=Search&q=" + ui.tagLabel;
            window.location.href = url;
        },
        availableTags: (function() {
            var results = get_available_tags('ActorThreatType');
            return results;
        })(),
        autocomplete: {
            delay: 0,
            minLength: 0,
        },
    });

    function get_available_tags(tag_type) {
        var tmp = [];
        $.ajax({
            async: false,
            type: "POST",
            url: actor_tags_list,
            data: {'type': tag_type},
            datatype: 'json',
            success: function(data) {
                if (tag_type == 'ActorIntendedEffect') {
                    available_intended_effects = tmp = data;
                } else if (tag_type == 'ActorMotivation') {
                    available_motivations = tmp = data;
                } else if (tag_type == 'ActorSophistication') {
                    available_sophistications = tmp = data;
                } else if (tag_type == 'ActorThreatType') {
                    available_threat_types = tmp = data;
                }
            }
        });
        return tmp;
    }
    function update_actor_tags(tag_type, my_tags) {
        if (!actor_tags) {
            var oid = subscription_id;
            var itype = subscription_type;
            var data = {
                        'oid': oid,
                        'tags': my_tags.toString(),
                        'tag_type': tag_type,
            };
            $.ajax({
                type: "POST",
                url: actor_tags_modify,
                data: data,
                datatype: 'json',
            });
        }
    }
    $(document).trigger('enable_actor_tags');


    function identifier_attribution_dialog(e) {
        var dialog = $(this).find("form").find("table");
        var it_drop = $('#form-attribute_actor_identifier select#id_identifier_type');
        var id_drop = $('#form-attribute_actor_identifier select#id_identifier');
        it_drop.find('option').remove()
        id_drop.find('option').remove()
        $('<input>').attr({
            type: 'hidden',
            id: 'id',
            name: 'id',
            value: subscription_id
        }).appendTo(dialog);
        get_identifier_types();
    }

    function get_identifier_types() {
        if (typeof get_actor_identifier_types !== 'undefined') {
            $.ajax({
                type: "POST",
                url: get_actor_identifier_types,
                async: true,
                success: function(data) {
                    var it_drop = $('#form-attribute_actor_identifier select#id_identifier_type');
                    it_drop.find('option').remove()
                    $.each(data.items, function(index, value) {
                        it_drop.append($('<option/>', {
                            value: value,
                            text : value
                        }));
                    });
                    $("#form-attribute_actor_identifier select#id_identifier_type :first-child").attr('selected', 'selected');
                    get_identifier_values($('#id_identifier_type').val());
                },
            });
        }
    }

        $(document).on('change', "#form-attribute_actor_identifier select#id_identifier_type", function(e) {
            var type = this.value;
            get_identifier_values(type);
        });

    function get_identifier_values(type) {
        if (typeof get_actor_identifier_type_values !== 'undefined') {
            $.ajax({
                type: "POST",
                data: {'type': type},
                datatype: 'json',
                url: get_actor_identifier_type_values,
                success: function(data) {
                    var id_drop = $('#form-attribute_actor_identifier select#id_identifier');
                    id_drop.find('option').remove()
                    $.each(data.items, function(index, value) {
                        id_drop.append($('<option/>', {
                            value: value[0],
                            text : value[1],
                        }));
                    });
                },
            });
        }
    }

    function identifier_attribution_submit(e) {
        var dialog = $(this).closest(".ui-dialog").find(".ui-dialog-content");
        var form = $(this).find("form");
        var data = form.serialize();
        $.ajax({
            type: "POST",
            url: form.attr('action'),
            data: data,
            datatype: 'json',
            success: function(data) {
                if (data.success) {
                    $('#actor_identifier_widget_container').html(data.message);
                    dialog.dialog("close");
                } else {
                    if (data.message) {
                        var message = form.find(".message");
                        message.show().css('display', 'table');
                        message.html(data.message);
                    }
                }
            }
        });
    }

    var localDialogs = {
      "attribute_actor_identifier": {title: "Attribute Actor Identifier",
                                     open: identifier_attribution_dialog,
                                     new: { submit: identifier_attribution_submit },
      },
      "download-actor": {title: "Download Actor", submit: defaultSubmit, href:"" },
    };

    $.each(localDialogs, function(id,opt) { stdDialog(id, opt) });


    $('.edit_attribution_confidence').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var id = $(elem).attr('data-id');
            var data = {
                confidence: value,
                identifier_id: id,
                id: subscription_id
            };
            $.ajax({
                type: "POST",
                async: false,
                url: edit_identifier_attribution,
                data: data,
                success: function(data) {
                }
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'select',
            data: {'low': 'low', 'medium': 'medium', 'high': 'high'},
            tooltip: "Edit Confidence",
            cancel: "Cancel",
            submit: "Ok",
            style: 'display:inline',
    });

    $('#edit_actor_name').editable(function(value, settings) {
        var revert = this.revert;
        return function(value, settings, elem) {
            var data = {
                name: value
            };
            $.ajax({
                type: "POST",
                async: false,
                url: edit_actor_name,
                data: data,
                success: function(data) {
                }
            });
            return value;
        }(value, settings, this);
        },
        {
            type: 'textarea',
            width: "400px",
            tooltip: "",
            cancel: "Cancel",
            submit: "Ok",
            onblur: 'ignore',
    });

}); //document.ready
