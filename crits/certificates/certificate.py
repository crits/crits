import base64

from mongoengine import Document, StringField, IntField
from django.conf import settings

from crits.certificates.migrate import migrate_certificate
from crits.core.crits_mongoengine import CritsBaseAttributes, CritsSourceDocument
from crits.core.fields import getFileField

from cybox.common.object_properties import CustomProperties, Property
from cybox.objects.artifact_object import Artifact, Base64Encoding
from cybox.objects.file_object import File
from cybox.core import Observable

class Certificate(CritsBaseAttributes, CritsSourceDocument, Document):
    """
    Certificate Class.
    """

    meta = {
        "collection": settings.COL_CERTIFICATES,
        "crits_type": 'Certificate',
        "latest_schema_version": 2,
        "schema_doc": {
            'filename': 'The filename of the certificate',
            'filetype': 'The filetype of the certificate',
            'md5': 'The MD5 of the certificate file',
            'size': 'The filesize of the certificate',
            'source': 'List [] of source information about who provided the certificate'
        },
        "jtable_opts": {
                         'details_url': 'crits.certificates.views.certificate_details',
                         'details_url_key': 'md5',
                         'default_sort': "modified DESC",
                         'searchurl': 'crits.certificates.views.certificates_listing',
                         'fields': [ "filename", "description", "filetype",
                                     "size", "modified", "source", "campaign",
                                     "id", "md5", "status" ],
                         'jtopts_fields': [ "details",
                                            "filename",
                                            "description",
                                            "filetype",
                                            "size",
                                            "modified",
                                            "source",
                                            "campaign",
                                            "status",
                                            "md5",
                                            "favorite",
                                            "id" ],
                         'hidden_fields': ["md5"],
                         'linked_fields': ["source", "campaign"],
                         'details_link': 'details',
                         'no_sort': ['details']
                       },
    }

    filedata = getFileField(collection_name=settings.COL_CERTIFICATES)
    filename = StringField(required=True)
    filetype = StringField(required=True)
    size = IntField(default=0)
    md5 = StringField()

    def migrate(self):
        """
        Migrate the Certificate tot he latest schema version.
        """
        migrate_certificate(self)

    def add_file_data(self, file_data):
        """
        Add the Certificate to GridFS.

        :param file_data: The Certificate.
        :type file_data: str
        """

        self._generate_file_metadata(file_data)
        self.filedata = file_data

    def add_file_obj(self, file_obj):
        """
        Add the Certificate to GridFS.

        :param file_obj: The Certificate.
        :type file_data: file handle
        """

        data = file_obj.read()
        self._generate_file_metadata(data)
        self.filedata = data

    def _generate_file_metadata(self, data):
        """
        Set the filetype, size, and MD5 of the Certificate.

        :param data: The Certificate.
        :type data: str
        """

        import magic
        from hashlib import md5
        self.filetype = magic.from_buffer(data)
        self.size = len(data)
        # this is a shard key. you can't modify it once it's set.
        # MongoEngine will still mark the field as modified even if you set it
        # to the same value.
        if not self.md5:
            self.md5 = md5(data).hexdigest()

    def discover_binary(self):
        """
        Queries GridFS for a matching binary to this Certificate document.
        """

        from crits.core.mongo_tools import mongo_connector

        fm = mongo_connector("%s.files" % self._meta['collection'])
        objectid = fm.find_one({'md5': self.md5}, {'_id': 1})
        if objectid:
            self.filedata.grid_id = objectid['_id']
            self.filedata._mark_as_changed()

    def to_cybox_observable(self):
        """
            Convert a Certificate to a CybOX Observables.
            Returns a tuple of (CybOX object, releasability list).

            To get the cybox object as xml or json, call to_xml() or
            to_json(), respectively, on the resulting CybOX object.
        """
        custom_prop = Property() # make a custom property so CRITs import can identify Certificate exports
        custom_prop.name = "crits_type"
        custom_prop.description = "Indicates the CRITs type of the object this CybOX object represents"
        custom_prop._value = "Certificate"
        obj = File() # represent cert information as file
        obj.md5 = self.md5
        obj.file_name = self.filename
        obj.file_format = self.filetype
        obj.size_in_bytes = self.size
        obj.custom_properties = CustomProperties()
        obj.custom_properties.append(custom_prop)
        obs = Observable(obj)
        obs.description = self.description
        data = self.filedata.read()
        if data: # if cert data available
            a = Artifact(data, Artifact.TYPE_FILE) # create artifact w/data
            a.packaging.append(Base64Encoding())
            obj.add_related(a, "Child_Of") # relate artifact to file
        return ([obs], self.releasability)

    @classmethod
    def from_cybox(cls, cybox_obs):
        """
        Convert a Cybox DefinedObject to a MongoEngine Certificate object.

        :param cybox_obs: The cybox object to create the Certificate from.
        :type cybox_obs: :class:`cybox.core.Observable``
        :returns: :class:`crits.certificates.certificate.Certificate`
        """
        cybox_object = cybox_obs.object_.properties
        if cybox_object.md5:
            db_obj = Certificate.objects(md5=cybox_object.md5).first()
            if db_obj:
                return db_obj

        cert = cls()
        cert.md5 = cybox_object.md5
        cert.filename = cybox_object.file_name
        cert.filetype = cybox_object.file_format
        cert.size = cybox_object.size_in_bytes.value if cybox_object.size_in_bytes else 0
        cert.description = cybox_obs.description
        for obj in cybox_object.parent.related_objects: # attempt to find data in cybox
            if isinstance(obj.properties, Artifact):
                cert.add_file_data(base64.b64decode(obj.properties.data))
        return cert
