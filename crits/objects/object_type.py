from mongoengine import Document, StringField
from mongoengine import BooleanField, DictField
from django.conf import settings

from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument

class ObjectType(CritsDocument, CritsSchemaDocument, Document):
    """
    Object Type class.
    """

    meta = {
        "collection": settings.COL_OBJECT_TYPES,
        "crits_type": 'ObjectType',
        "latest_schema_version": 1,
        "schema_doc": {
            'name': 'The name of this Object',
            'type': 'The Object Type of this Object',
            'name_type': 'The type of the object name',
            'active': 'Enabled in the UI (on/off)',
            'description': 'CybOX description of this Object Type',
            'is_subtype': 'Boolean if this is a sub-type of another Object Type',
            'datatype': ('Dictionary {} with a key defining the datatype of the'
                        'Object (string, bigstring, file) and a currently unused'
                        ' value (0)')
        },
    }

    active = StringField(default="on")
    datatype = DictField()
    description = StringField()
    is_subtype = BooleanField(required=True)
    name = StringField(required=True)
    name_type = StringField()
    object_type = StringField(required=True, db_field="type")
    version = StringField()

    def migrate(self):
        pass
