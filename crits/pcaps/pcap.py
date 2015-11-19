from mongoengine import Document, StringField, IntField
from django.conf import settings

from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.crits_mongoengine import CritsActionsDocument
from crits.core.fields import getFileField
from crits.pcaps.migrate import migrate_pcap


class PCAP(CritsBaseAttributes, CritsSourceDocument, CritsActionsDocument,
           Document):
    """
    PCAP class.
    """

    meta = {
        "collection": settings.COL_PCAPS,
        "crits_type": 'PCAP',
        "latest_schema_version": 3,
        "shard_key": ('md5',),
        "schema_doc": {
            'filename': 'The filename of the PCAP',
            'md5': 'The MD5 of the PCAP file',
            'length': 'The filesize of the PCAP',
            'uploadDate': 'The ISODate when the PCAP was uploaded',
            'contentType': 'The filetype of the PCAP',
            'source': 'List [] of source information about who provided the PCAP'
        },
        "jtable_opts": {
                         'details_url': 'crits.pcaps.views.pcap_details',
                         'details_url_key': 'md5',
                         'default_sort': "modified DESC",
                         'searchurl': 'crits.pcaps.views.pcaps_listing',
                         'fields': [ "filename", "description", "length",
                                     "modified", "source", "campaign", "id",
                                     "md5", "status"],
                         'jtopts_fields': [ "details",
                                            "filename",
                                            "description",
                                            "length",
                                            "modified",
                                            "source",
                                            "campaign",
                                            "status",
                                            "md5",
                                            "favorite",
                                            "id"],
                         'hidden_fields': ['md5'],
                         'linked_fields': ["source", "campaign"],
                         'details_link': 'details',
                         'no_sort': ['details']
                       }
    }

    contentType = StringField()
    filedata = getFileField(collection_name=settings.COL_PCAPS)
    filename = StringField(required=True)
    length = IntField(default=0)
    md5 = StringField()

    def migrate(self):
        """
        Migrate to the latest schema version.
        """

        migrate_pcap(self)

    def add_file_data(self, file_data):
        """
        Add filedata to this PCAP.

        :param file_data: The filedata to add.
        :type file_data: str
        """

        self._generate_file_metadata(file_data)
        self.filedata = file_data

    def add_file_obj(self, file_obj):
        """
        Add filedata to this PCAP.

        :param file_data: The filedata to add.
        :type file_data: file handle
        """

        data = file_obj.read()
        self._generate_file_metadata(data)
        self.filedata = data

    def _generate_file_metadata(self, data):
        """
        Generate metadata from the file data. Will add content-type, length, and
        MD5.

        :param data: The data to generate metadata from.
        :type data: str
        """

        import magic
        from hashlib import md5
        self.contentType = magic.from_buffer(data)
        self.length = len(data)
        # this is a shard key. you can't modify it once it's set.
        # MongoEngine will still mark the field as modified even if you set it
        # to the same value.
        if not self.md5:
            self.md5 = md5(data).hexdigest()

    def discover_binary(self):
        """
        Queries GridFS for a matching binary to this pcap document.
        """

        from crits.core.mongo_tools import mongo_connector

        fm = mongo_connector("%s.files" % self._meta['collection'])
        objectid = fm.find_one({'md5': self.md5}, {'_id': 1})
        if objectid:
            self.filedata.grid_id = objectid['_id']
            self.filedata._mark_as_changed()
