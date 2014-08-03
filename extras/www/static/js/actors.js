$(document).ready(function() {
    details_copy_id('Actor');
    toggle_favorite('Actor');
});


var actor_tags = true;
var available_intended_effects = [];
var available_motivations = [];
var available_sophistications = [];
var available_threat_types = [];
$(document).ready(function() {

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
}); //document.ready
