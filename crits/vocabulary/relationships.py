from crits.vocabulary.vocab import vocab

class RelationshipTypes(vocab):
    """
    Vocabulary for Relationship Types.
    """


    COMPRESSED_FROM = "Compressed From"
    COMPRESSED_INTO = "Compressed Into"

    CONNECTED_FROM = "Connected From"
    CONNECTED_TO = "Connected To"

    CONTAINS = "Contains"
    CONTAINED_WITHIN = "Contained Within"

    CREATED = "Created"
    CREATED_BY = "Created By"
    
    DECODED = "Decoded"
    DECODED_BY = "Decoded By"

    DECRYPTED = "Decrypted"
    DECRYPTED_BY = "Decrypted By"

    DOWNLOADED = "Downloaded"
    DOWNLOADED_BY = "Downloaded By"

    DOWNLOADED_FROM = "Downloaded From"
    DOWNLOADED_TO = "Downloaded To"

    DROPPED = "Dropped"
    DROPPED_BY = "Dropped By"

    INSTALLED = "Installed"
    INSTALLED_BY = "Installed By"

    LOADED_FROM = "Loaded From"
    LOADED_INTO = "Loaded Into"

    PACKED_FROM = "Packed From"
    PACKED_INTO = "Packed Into"

    RECEIVED_FROM = "Received From"
    SENT_TO = "Sent To"

    REGISTERED = "Registered"
    REGISTERED_TO = "Registered To"

    RELATED_TO = "Related To"

    RESOLVED_TO = "Resolved To"

    SENT = "Sent"
    SENT_BY = "Sent By"

    SUB_DOMAIN_OF = "Sub-domain Of"
    SUPRA_DOMAIN_OF = "Supra-domain Of"

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
        elif relationship == cls.DECODED:
            return cls.DECODED_BY
        elif relationship == cls.DECODED_BY:
            return cls.DECODED
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
