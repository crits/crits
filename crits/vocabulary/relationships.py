from crits.vocabulary.vocab import vocab

class RelationshipTypes(vocab):
    """
    Vocabulary for Relationship Types.
    """


    COMPRESSED_FROM = "Compressed_From"
    COMPRESSED_INTO = "Compressed_Into"

    CONNECTED_FROM = "Connected_From"
    CONNECTED_TO = "Connected_To"

    CONTAINS = "Contains"
    CONTAINED_WITHIN = "Contained_Within"

    CREATED = "Created"
    CREATED_BY = "Created_By"

    DECRYPTED = "Decrypted"
    DECRYPTED_BY = "Decrypted_By"

    DOWNLOADED = "Downloaded"
    DOWNLOADED_BY = "Downloaded_By"

    DOWNLOADED_FROM = "Downloaded_From"
    DOWNLOADED_TO = "Downloaded_To"

    DROPPED = "Dropped"
    DROPPED_BY = "Dropped_By"

    INSTALLED = "Installed"
    INSTALLED_BY = "Installed_By"

    LOADED_FROM = "Loaded_From"
    LOADED_INTO = "Loaded_Into"

    PACKED_FROM = "Packed_From"
    PACKED_INTO = "Packed_Into"

    RECEIVED_FROM = "Received_From"
    SENT_TO = "Sent_To"

    REGISTERED = "Registered"
    REGISTERED_TO = "Registered_To"

    RELATED_TO = "Related_To"

    RESOLVED_TO = "Resolved_To"

    SENT = "Sent"
    SENT_BY = "Sent_By"

    SUB_DOMAIN_OF = "Sub-domain_Of"
    SUPRA_DOMAIN_OF = "Supra-domain_Of"

    @classmethod
    def inverse(cls, relationship=None):
        """
        Return the inverse relationship of the provided relationship.

        :param relationship: The relationship to get the inverse of.
        :type relationship: str
        :returns: str or None
        """

        if relationship is None:
            return None

        if relationship == cls.COMPRESSED_FROM:
            return cls.COMPRESSED_INTO
        elif relationship == cls.COMPRESSED_INTO:
            return cls.COMPRESSED_FROM
        elif relationship == cls.CONNECTED_FROM:
            return cls.CONNECTED_TO
        elif relationship == cls.CONNECTED_TO:
            return cls.CONNECTED_FROM
        elif relationship == cls.CONTAINS:
            return cls.CONTAINED_WITHIN
        elif relationship == cls.CONTAINED_WITHIN:
            return cls.CONTAINS
        elif relationship == cls.CREATED:
            return cls.CREATED_BY
        elif relationship == cls.CREATED_BY:
            return cls.CREATED
        elif relationship == cls.DECRYPTED:
            return cls.DECRYPTED_BY
        elif relationship == cls.DECRYPTED_BY:
            return cls.DECRYPTED
        elif relationship == cls.DOWNLOADED:
            return cls.DOWNLOADED_BY
        elif relationship == cls.DOWNLOADED_BY:
            return cls.DOWNLOADED
        elif relationship == cls.DOWNLOADED_FROM:
            return cls.DOWNLOADED_TO
        elif relationship == cls.DOWNLOADED_TO:
            return cls.DOWNLOADED_FROM
        elif relationship == cls.DROPPED:
            return cls.DROPPED_BY
        elif relationship == cls.DROPPED_BY:
            return cls.DROPPED
        elif relationship == cls.INSTALLED:
            return cls.INSTALLED_BY
        elif relationship == cls.INSTALLED_BY:
            return cls.INSTALLED
        elif relationship == cls.LOADED_FROM:
            return cls.LOADED_INTO
        elif relationship == cls.LOADED_INTO:
            return cls.LOADED_FROM
        elif relationship == cls.PACKED_FROM:
            return cls.PACKED_INTO
        elif relationship == cls.PACKED_INTO:
            return cls.PACKED_FROM
        elif relationship == cls.RECEIVED_FROM:
            return cls.SENT_TO
        elif relationship == cls.SENT_TO:
            return cls.RECEIVED_FROM
        elif relationship == cls.REGISTERED:
            return cls.REGISTERED_TO
        elif relationship == cls.REGISTERED_TO:
            return cls.REGISTERED
        elif relationship == cls.RELATED_TO:
            return cls.RELATED_TO
        elif relationship == cls.RESOLVED_TO:
            return cls.RESOLVED_TO
        elif relationship == cls.SENT:
            return cls.SENT_BY
        elif relationship == cls.SENT_BY:
            return cls.SENT
        elif relationship == cls.SUB_DOMAIN_OF:
            return cls.SUPRA_DOMAIN_OF
        elif relationship == cls.SUPRA_DOMAIN_OF:
            return cls.SUB_DOMAIN_OF
        else:
            return None
