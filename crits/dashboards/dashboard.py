from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from mongoengine import DynamicDocument, ListField, ObjectIdField, StringField, DictField, IntField, BooleanField

class SavedSearch(CritsDocument, CritsSchemaDocument, DynamicDocument):
    """
    savedSearch class
    """
    meta = {
        "collection": "saved_search",
        "auto_create_index": False,
        "crits_type": "saved_search",
        "latest_schema_version": 1,
        "schema_doc": {}
    }
    name = StringField(required=True)
    dashboard = ObjectIdField(required=True)
    tableColumns = ListField(required=True)
    sortBy = DictField(required=False)
    searchTerm = StringField(required=False)
    objType =  StringField(required=False)
    top = IntField(required=False, default=-1)
    left = IntField(required=False, default=-1)
    width = IntField(required=False)
    maxRows = IntField(required=False)
    isDefaultOnDashboard = BooleanField(required=True, default=False)
    isPinned = BooleanField(required=True, default=True)
    
    sizex = IntField(required=True, default=50)
    sizey = IntField(required=True, default=8)
    row = IntField(required=True, default=1)
    col = IntField(required=True, default=1)

    def getSortByText(self):
        textString = "None"
        if self.sortBy:
            for col in self.tableColumns:
                if col["field"] == self.sortBy["field"]:
                    textString = col["caption"] + " - " + self.sortBy['direction'].upper()
                    break;
        return textString
    
class Dashboard(CritsDocument, CritsSchemaDocument, DynamicDocument):
    """
    dashboard class
    """
    meta = {
        "collection": "dashboard",
        "auto_create_index": False,
        "crits_type": "dashboard",
        "latest_schema_version": 1,
        "schema_doc": {}
    }
    name = StringField(required=True)
    analystId = ObjectIdField(required=False)
    theme = StringField(required=True,default="default")
    isPublic = BooleanField(required=True, default=False)
    parent = ObjectIdField(required=False)
    hasParentChanged = BooleanField(required=True, default=False)