

class ChangeParser():
    """
    Provides many different notification change parsers and utility methods.
    """

    @staticmethod
    def get_changed_field_handler(top_level_type, field):
        """
        Returns a change handler for the field and top level object type. If
        not found then None is returned.

        :param top_level_type: The top level object type.
        :type message: str
        :param field: The field name.
        :type message: str
        :returns: function: Returns a change field handler, None if not found
        """

        specific_mapped_type = __specific_field_to_change_handler__.get(top_level_type)

        # Check for a specific mapped field first, if there isn't one
        # then just try to use the general mapped fields.
        if specific_mapped_type is not None:
            specific_mapped_handler = specific_mapped_type.get(field)

            if specific_mapped_handler is not None:
                return specific_mapped_handler

        return __general_field_to_change_handler__.get(field)


    ############################################################################
    # Generic change parsers
    ############################################################################
    @staticmethod
    def flatten_objects_to_list(objects, key):
        """
        Flattens an object list to list values from the input key.

        :type objects: list of complex objects
        :param objects: list(object).
        :type key: The name of the field/key to extract for the flattened list
        :param key: str
        :returns: str: Returns a list of extracted keys.
        """

        return_list = []

        for object in objects:
            return_list.append(object[key])

        return return_list

    @staticmethod
    def generic_child_fields_change_handler(old_value, new_value, fields, base_fqn=None):
        """
        Handles processing of changed fields where the input is a dictionary of
        values. This will only process the immediate children.

        :type old_value: The old mongo object to compare values against.
        :param old_value: A Mongo Document
        :type new_value: The updated/new mongo object to compare values against.
        :param new_value: A Mongo Document
        :type fields: list of field names to compare against
        :param fields: list(str).
        :type base_fqn: The base descriptor of the object
        :param base_fqn: str
        :returns: str: Returns a message summarizing the changes.
        """

        message = ""

        for field in fields:
            old_field_value = ""
            new_field_value = ""

            if old_value is not None:
                old_field_value = old_value[field]

            if new_value is not None:
                new_field_value = new_value[field]

            if old_field_value != new_field_value:
                change_message = ChangeParser.generic_single_field_change_handler(
                        old_field_value, new_field_value, field, base_fqn)
                message += change_message[:1].capitalize() + change_message[1:]

        return message

    @staticmethod
    def generic_list_change_handler(old_value, new_value, changed_field):
        """
        Handles the processing of changed fields where the changed field
        is a list of items. Displays the changed value in unicode format.

        :type old_value: The old mongo object to compare values against.
        :param old_value: A Mongo Document
        :type new_value: The updated/new mongo object to compare values against.
        :param new_value: A Mongo Document
        :type changed_field: The field name that the comparisons will be against.
        :param changed_field: str
        :returns: str: Returns a message summarizing the changes.
        """

        removed_names = [x for x in old_value if x not in new_value and x != '']
        added_names = [x for x in new_value if x not in old_value and x != '']

        message = ""
        if len(added_names) > 0:
            message += "Added to %s: %s. " % (changed_field, unicode(', '.join(added_names)))
        if len(removed_names) > 0:
            message += "Removed from %s: %s. " % (changed_field, unicode(', '.join(removed_names)))

        return message

    @staticmethod
    def generic_list_json_change_handler(old_value, new_value, changed_field):
        """
        Handles the processing of changed fields where the changed field
        is a list of items. Displays the changed value in json format via to_json().

        :type old_value: The old mongo object to compare values against.
        :param old_value: A Mongo Document
        :type new_value: The updated/new mongo object to compare values against.
        :param new_value: A Mongo Document
        :type changed_field: The field name that the comparisons will be against.
        :param changed_field: str
        :returns: str: Returns a message summarizing the changes.
        """

        removed_names = [x.to_json() for x in old_value if x not in new_value and x != '']
        added_names = [x.to_json() for x in new_value if x not in old_value and x != '']

        message = ""
        if len(added_names) > 0:
            message += "Added to %s: %s. " % (changed_field, unicode(', '.join(added_names)))
        if len(removed_names) > 0:
            message += "Removed from %s: %s. " % (changed_field, unicode(', '.join(removed_names)))

        return message

    @staticmethod
    def generic_single_field_change_handler(old_value, new_value, changed_field, base_fqn=None):
        """
        Handles the processing of a changed field where the changed field
        is displayable in string format.

        :type old_value: The old mongo object to compare values against.
        :param old_value: A value that can be stringified
        :type new_value: The updated/new mongo object to compare values against.
        :param new_value: A value that can be stringified
        :type changed_field: The field name that the comparisons will be against.
        :param changed_field: str
        :type base_fqn: The base descriptor of the object
        :param base_fqn: str
        :returns: str: Returns a message summarizing the changes.
        """

        if base_fqn is None:
            return "%s changed from \"%s\" to \"%s\"\n" % (changed_field, old_value, new_value)
        else:
            return "%s.%s changed from \"%s\" to \"%s\"\n" % (base_fqn, changed_field, old_value, new_value)

    @staticmethod
    def generic_single_field_json_change_handler(old_value, new_value, changed_field, base_fqn=None):
        """
        Handles the processing of a changed field where the changed field
        is displayable in json format via to_json().

        :type old_value: The old mongo object to compare values against.
        :param old_value: A Mongo Document
        :type new_value: The updated/new mongo object to compare values against.
        :param new_value: A Mongo Document
        :type changed_field: The field name that the comparisons will be against.
        :param changed_field: str
        :type base_fqn: The base descriptor of the object
        :param base_fqn: str
        :returns: str: Returns a message summarizing the changes.
        """

        if base_fqn is None:
            return "%s changed from \"%s\" to \"%s\"\n" % (changed_field, old_value.to_json(), new_value.to_json())
        else:
            return "%s.%s changed from \"%s\" to \"%s\"\n" % (base_fqn, changed_field, old_value.to_json(), new_value.to_json())

    @staticmethod
    def get_changed_object_list(old_objects, new_objects, object_key):
        """
        Detects which objects have changed by comparing the 'object_key'
        from both the input old_objects and new_objects parameters.

        :type old_objects: A list of the old values.
        :param old_objects: An iterable segment of a Mongo Document
        :type new_objects: A list of the new values
        :param new_objects: An iterable segment of a Mongo Document
        :type object_key: The field name that will be the key in the returned dict.
        :param object_key: str
        :returns: dict(key, dict): Returns a dictionary of changed objects,
                  in the format of {key: {old, new}}
        """

        changed_objects = {}

        # Try and detect which objects have changed
        for old_object in old_objects:
            if old_object not in new_objects:
                if old_object[object_key] not in changed_objects:
                    changed_objects[old_object[object_key]] = {'old': old_object}
                else:
                    changed_objects[old_object[object_key]]['old'] = old_object

        for new_object in new_objects:
            if new_object not in old_objects:
                if new_object[object_key] not in changed_objects:
                    changed_objects[new_object[object_key]] = {'new': new_object}
                else:
                    changed_objects[new_object[object_key]]['new'] = new_object

        return changed_objects

    @staticmethod
    def get_changed_primitive_list(old_objects, new_objects):
        """
        Detects which objects have changed by comparing the value of
        both the input old_objects and new_objects parameters.

        :type old_objects: A list of the old values.
        :param old_objects: An iterable segment of a Mongo Document
        :type new_objects: A list of the new values
        :param new_objects: An iterable segment of a Mongo Document
        :returns: dict(key, dict): Returns a dictionary of changed objects,
                  in the format of {key: {old, new}}
        """

        changed_objects = {}

        # Try and detect which items have changed
        for old_object in old_objects:
            if old_object not in new_objects:
                if old_object not in changed_objects:
                    changed_objects[old_object] = {'old': old_object}
                else:
                    changed_objects[old_object]['old'] = old_object

        for new_object in new_objects:
            if new_object not in old_objects:
                if new_object not in changed_objects:
                    changed_objects[new_object] = {'new': new_object}
                else:
                    changed_objects[new_object]['new'] = new_object

        return changed_objects

    @staticmethod
    def get_short_name(obj, summary_handler, default):
        """
        Generates and returns a human readable short name of the input object
        by using the input summary_handler parameter. Returns the default
        parameter if the summary_handler is None.

        :param obj: The object.
        :type obj: class which inherits from
                   :class:`crits.core.crits_mongoengine.CritsBaseAttributes`
        :type summary_handler: A summary handler function that will be used
                               to generate the short name, if not None.
        :param summary_handler: function
        :type default: The default value to use if the summary handler is not
                       able to generate a short name value.
        :param default: str
        :returns: str: Returns a short name description.
        """

        short_name = default

        if summary_handler is not None:
            short_name = summary_handler(obj)

        return short_name

    @staticmethod
    def parse_generic_change_object_list(change_dictionary, field_name, object_key,
                                         change_parser_handler=None, summary_handler=None):
        """
        Parses a list of complex objects and tries to determine if the object
        was modified, added, or deleted. Returns a string of the summary of
        changes.

        :type change_dictionary: A dict of changes in the format {key: {old, new}}.
        :param change_dictionary: dict(key, dict)
        :type field_name: A description of the field that changed, e.g. its name.
        :param field_name: str
        :type object_key: A secondary description of the field that changed, e.g. its name.
        :param object_key: str
        :type change_parser_handler: A handler function that determines the
                                     fields that were changed for the object.
                                     This is used if the object was modified and
                                     if the handler function is not None
        :param change_parser_handler: function
        :type summary_handler: A handler function that, if not None, generates
                               a short description of the compared object.
        :param summary_handler: function
        """

        message = ""

        for changed_key_name in change_dictionary:
            old_value = change_dictionary[changed_key_name].get('old')
            new_value = change_dictionary[changed_key_name].get('new')

            if old_value is not None and new_value is not None:
                short_name = ChangeParser.get_short_name(old_value, summary_handler, changed_key_name)
                message += "%s %s modified: %s\n" % (field_name, object_key, short_name)

                if change_parser_handler is not None:
                    message += change_parser_handler(old_value, new_value, field_name)
            elif old_value is not None and new_value is None:
                short_name = ChangeParser.get_short_name(old_value, summary_handler, changed_key_name)
                message += "%s %s removed: %s\n" % (field_name, object_key, short_name)
            elif old_value is None and new_value is not None:
                short_name = ChangeParser.get_short_name(new_value, summary_handler, changed_key_name)
                message += "%s %s added: %s\n" % (field_name, object_key, short_name)
            else:
                message += "Unknown operation on %s %s: %s\n" % (field_name, object_key, changed_key_name)

        return message

    ############################################################################
    # Summary generation handlers
    #
    # These methods generates and returns a human readable short name of
    # the input object
    ############################################################################
    @staticmethod
    def actions_summary_handler(object):
        return "%s - %s" % (object.action_type, unicode(object.date))

    @staticmethod
    def indicator_activity_summary_handler(object):
        return object.description

    @staticmethod
    def objects_summary_handler(object):
        return "%s - %s" % (object.name, object.value)

    @staticmethod
    def raw_data_highlights_summary_handler(object):
        return "line %s: %s" % (object.line, unicode(object.line_data))

    @staticmethod
    def raw_data_inlines_summary_handler(object):
        return "line %s: %s" % (object.line, object.comment)

    @staticmethod
    def relationships_summary_handler(object):
        #target_of_relationship = class_from_id(object.type, object.value)

        # TODO: Print out a meaningful relationship summary, should consolidate
        # relationships code to generically get the "key" that best describes
        # a generic mongo object.

        return "%s - %s" % (object.rel_type, object.object_id)

    ############################################################################
    # Specific Change Handlers/Parsers
    #
    # These methods parse the modified field and determine the specific change
    # that was made.
    ############################################################################
    @staticmethod
    def actions_change_handler(old_value, new_value, changed_field):
        changed_data = ChangeParser.get_changed_object_list(old_value, new_value, 'date')
        message = ChangeParser.parse_generic_change_object_list(
                changed_data,
                changed_field,
                'instance',
                ChangeParser.actions_parse_handler,
                ChangeParser.actions_summary_handler)

        return message

    @staticmethod
    def actions_parse_handler(old_value, new_value, base_fqn):

        fields = ['action_type', 'active', 'reason', 'begin_date', 'end_date', 'performed_date']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, base_fqn)

        return message

    @staticmethod
    def bucket_list_change_handler(old_value, new_value, changed_field):
        return ChangeParser.generic_list_change_handler(old_value, new_value, changed_field)

    @staticmethod
    def campaign_change_handler(old_value, new_value, changed_field):
        changed_data = ChangeParser.get_changed_object_list(old_value, new_value, 'name')
        message = ChangeParser.parse_generic_change_object_list(
                changed_data, changed_field, 'name',
                ChangeParser.campaign_parse_handler)

        return message

    @staticmethod
    def campaign_parse_handler(old_value, new_value, base_fqn):

        fields = ['name', 'confidence', 'description']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, base_fqn)

        return message

    @staticmethod
    def indicator_activity_change_handler(old_value, new_value, changed_field):
        changed_data = ChangeParser.get_changed_object_list(old_value, new_value, 'date')
        message = ChangeParser.parse_generic_change_object_list(changed_data, changed_field, 'instance',
                ChangeParser.indicator_activity_parse_handler,
                ChangeParser.indicator_activity_summary_handler)

        return message

    @staticmethod
    def indicator_activity_parse_handler(old_value, new_value, base_fqn):

        fields = ['description', 'end_date', 'start_date']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, base_fqn)

        return message

    @staticmethod
    def indicator_confidence_change_handler(old_value, new_value, changed_field):
        fields = ['rating']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, changed_field)

        return message

    @staticmethod
    def indicator_impact_change_handler(old_value, new_value, changed_field):
        fields = ['rating']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, changed_field)

        return message

    @staticmethod
    def objects_change_handler(old_value, new_value, changed_field):
        changed_objects = ChangeParser.get_changed_object_list(old_value, new_value, 'name')
        message = ChangeParser.parse_generic_change_object_list(changed_objects, 'Objects', 'item',
                ChangeParser.objects_parse_handler,
                ChangeParser.objects_summary_handler)

        return message

    @staticmethod
    def objects_parse_handler(old_value, new_value, base_fqn):

        fields = ['name', 'value']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, base_fqn)

        return message

    @staticmethod
    def relationships_parse_handler(old_value, new_value, base_fqn):

        fields = ['relationship', 'rel_type', 'rel_reason', 'rel_confidence']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, base_fqn)

        return message

    @staticmethod
    def raw_data_highlights_change_handler(old_value, new_value, changed_field):
        changed_data = ChangeParser.get_changed_object_list(old_value, new_value, 'date')
        message = ChangeParser.parse_generic_change_object_list(changed_data, changed_field, 'instance',
                ChangeParser.raw_data_highlights_parse_handler,
                ChangeParser.raw_data_highlights_summary_handler)

        return message

    @staticmethod
    def raw_data_highlights_parse_handler(old_value, new_value, base_fqn):

        fields = ['line', 'line_data']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, base_fqn)

        return message

    @staticmethod
    def raw_data_inlines_change_handler(old_value, new_value, changed_field):
        changed_data = ChangeParser.get_changed_object_list(old_value, new_value, 'date')
        message = ChangeParser.parse_generic_change_object_list(changed_data, changed_field, 'instance',
                ChangeParser.raw_data_inlines_parse_handler,
                ChangeParser.raw_data_inlines_summary_handler)

        return message

    @staticmethod
    def raw_data_inlines_parse_handler(old_value, new_value, base_fqn):

        fields = ['line', 'comment']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, base_fqn)

        return message

    @staticmethod
    def relationships_change_handler(old_value, new_value, changed_field):
        changed_data = ChangeParser.get_changed_object_list(old_value, new_value, 'date')
        message = ChangeParser.parse_generic_change_object_list(changed_data, changed_field, 'instance',
                ChangeParser.relationships_parse_handler,
                ChangeParser.relationships_summary_handler)

        return message

    @staticmethod
    def screenshots_change_handler(old_value, new_value, changed_field):
        changed_screenshots = ChangeParser.get_changed_primitive_list(old_value, new_value)
        message = ChangeParser.parse_generic_change_object_list(changed_screenshots, changed_field, 'id')

        return message

    @staticmethod
    def skip_change_handler(old_value, new_value, changed_field):
        return None

    @staticmethod
    def source_change_handler(old_value, new_value, changed_field):
        changed_sources = ChangeParser.get_changed_object_list(old_value, new_value, 'name')
        message = ChangeParser.parse_generic_change_object_list(changed_sources, changed_field, 'name',
                ChangeParser.source_parse_handler)

        return {'message': message, 'source_filter': changed_sources.keys()}

    @staticmethod
    def source_instances_parse_handler(old_value, new_value, base_fqn):

        fields = ['method', 'reference']
        message = ChangeParser.generic_child_fields_change_handler(old_value, new_value, fields, base_fqn)

        return message

    @staticmethod
    def source_parse_handler(old_value, new_value, base_fqn):

        changed_source_instances = ChangeParser.get_changed_object_list(
                old_value['instances'], new_value['instances'], 'date')

        message = ChangeParser.parse_generic_change_object_list(changed_source_instances, 'source', 'instances',
                ChangeParser.source_instances_parse_handler)

        return message

    @staticmethod
    def tickets_change_handler(old_value, new_value, changed_field):
        old_tickets_list = ChangeParser.flatten_objects_to_list(old_value, 'ticket_number')
        new_tickets_list = ChangeParser.flatten_objects_to_list(new_value, 'ticket_number')

        return ChangeParser.generic_list_change_handler(old_tickets_list, new_tickets_list, changed_field)


class MappedMongoFields():

    @staticmethod
    def get_mapped_mongo_field(top_level_type, field):

        specific_mapped_type = __specific_mongo_to_doc_field__.get(top_level_type)

        # Check for a specific mapped field first, if there isn't one
        # then just try to use the general mapped fields.
        if specific_mapped_type is not None:
            specific_mapped_value = specific_mapped_type.get(field)

            if specific_mapped_value is not None:
                return specific_mapped_value

        return __general_mongo_to_doc_field__.get(field, field)


class NotificationHeaderManager():
    """
    The following generate_*_header() functions generate a meaningful description
    for that specific object type.
    """

    @staticmethod
    def get_header_handler(obj_type):
        return __notification_header_handler__.get(obj_type)

    @staticmethod
    def generate_actor_header(obj):
        return "Actor: %s" % (obj.name)

    @staticmethod
    def generate_backdoor_header(obj):
        return "Backdoor: %s" % (obj.name)

    @staticmethod
    def generate_campaign_header(obj):
        return "Campaign: %s" % (obj.name)

    @staticmethod
    def generate_certificate_header(obj):
        return "Certificate: %s" % (obj.filename)

    @staticmethod
    def generate_domain_header(obj):
        return "Domain: %s" % (obj.domain)

    @staticmethod
    def generate_email_header(obj):
        return "Email: %s" % (obj.subject)

    @staticmethod
    def generate_event_header(obj):
        return "Event: %s" % (obj.title)

    @staticmethod
    def generate_exploit_header(obj):
        return "Exploit: %s" % (obj.name)

    @staticmethod
    def generate_indicator_header(obj):
        return "Indicator: %s - %s" % (obj.ind_type, obj.value)

    @staticmethod
    def generate_ip_header(obj):
        return "IP: %s" % (obj.ip)

    @staticmethod
    def generate_pcap_header(obj):
        return "PCAP: %s" % (obj.filename)

    @staticmethod
    def generate_raw_data_header(obj):
        return "RawData: %s (version %s)" % (obj.title, obj.version)

    @staticmethod
    def generate_sample_header(obj):
        return "Sample: %s" % (obj.filename)

    @staticmethod
    def generate_screenshot_header(obj):
        return "Screenshot: %s" % (obj.filename)

    @staticmethod
    def generate_target_header(obj):
        return "Target: %s" % (obj.email_address)



# Use dictionaries to hold the list of handlers because dictionary
# lookup time is O(1) whereas a list or a long 'if/else' block is worst
# case O(n). The consequence of using a dict is that this
# consumes more memory on startup since the dict needs to be constructed.
__general_field_to_change_handler__ = {
    "actions": ChangeParser.actions_change_handler,
    "analysis": ChangeParser.skip_change_handler,
    "bucket_list": ChangeParser.bucket_list_change_handler,
    "campaign": ChangeParser.campaign_change_handler,
    "obj": ChangeParser.objects_change_handler,
    "relationships": ChangeParser.relationships_change_handler,
    "screenshots": ChangeParser.screenshots_change_handler,
    "source": ChangeParser.source_change_handler,
    "tickets": ChangeParser.tickets_change_handler,
}

__specific_field_to_change_handler__ = {
    "Indicator": {
        "activity": ChangeParser.indicator_activity_change_handler,
        "confidence": ChangeParser.indicator_confidence_change_handler,
        "impact": ChangeParser.indicator_impact_change_handler,
    },
    "RawData": {
        "tool": ChangeParser.generic_single_field_json_change_handler,
        "highlights": ChangeParser.raw_data_highlights_change_handler,
        "inlines": ChangeParser.raw_data_inlines_change_handler,
    }
}

__notification_header_handler__ = {
    "Actor": NotificationHeaderManager.generate_actor_header,
    "Backdoor": NotificationHeaderManager.generate_backdoor_header,
    "Campaign": NotificationHeaderManager.generate_campaign_header,
    "Certificate": NotificationHeaderManager.generate_certificate_header,
    "Domain": NotificationHeaderManager.generate_domain_header,
    "Email": NotificationHeaderManager.generate_email_header,
    "Event": NotificationHeaderManager.generate_event_header,
    "Exploit": NotificationHeaderManager.generate_exploit_header,
    "Indicator": NotificationHeaderManager.generate_indicator_header,
    "IP": NotificationHeaderManager.generate_ip_header,
    "PCAP": NotificationHeaderManager.generate_pcap_header,
    "RawData": NotificationHeaderManager.generate_raw_data_header,
    "Sample": NotificationHeaderManager.generate_sample_header,
    "Screenshot": NotificationHeaderManager.generate_screenshot_header,
    "Target": NotificationHeaderManager.generate_target_header,
}

__general_mongo_to_doc_field__ = {
    "objects": "obj"
}

__specific_mongo_to_doc_field__ = {
    "Email": {
        "from": "from_address",
        "raw_headers": "raw_header",
    },
    "Indicator": {
        "type": "ind_type"
    }
}
