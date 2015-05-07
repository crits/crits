from mongoengine import Document
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes
from crits.core.crits_mongoengine import CritsSourceDocument


class UnreleasableEventError(Exception):
    """
    Exception for attempting to release an event relationship that is
    unreleasable.
    """

    def __init__(self, value, **kwargs):
        self.message = "Relationship %s cannot be released to the event's \
releasability list." % value
        super(UnreleasableEventError, self).__init__(**kwargs)

    def __str__(self):
        return repr(self.message)


class Source(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Source class.
    """

    meta = {
        "collection": settings.COL_SOURCES,
        "crits_type": 'Source',
        "latest_schema_version": 2,
    }
