import StringIO

from mongoengine import Document, StringField, ListField, IntField
from django.conf import settings
from PIL import Image

from crits.core.crits_mongoengine import CritsBaseDocument, CritsSourceDocument
from crits.core.crits_mongoengine import CritsSchemaDocument, CritsDocument
from crits.core.crits_mongoengine import EmbeddedSource
from crits.core.fields import getFileField
from crits.core.user_tools import user_sources

class Screenshot(CritsBaseDocument, CritsSourceDocument, CritsSchemaDocument,
                 CritsDocument, Document):
    """
    Screenshot Class.
    """

    meta = {
        "collection": settings.COL_SCREENSHOTS,
        "crits_type": 'Screenshot',
        "latest_schema_version": 1,
        "schema_doc": {
            'filename': 'The name of the screenshot',
            'thumb': 'Thumbnail of screenshot',
            'screenshot': 'The screenshot',
            'width': 'The width in pixels',
            'height': 'The height in pixels',
            'description': 'Description of the screenshot',
            'tags': 'List of tags about this screenshot',
            'source': 'List [] of source information about who provided the screenshot'
        },
        "jtable_opts": {
                         'details_url': 'crits.screenshots.views.render_screenshot',
                         'details_url_key': 'id',
                         'default_sort': "created DESC",
                         'searchurl': 'crits.screenshots.views.screenshots_listing',
                         'fields': [ "thumb", "description", "created",
                                     "source", "id", "md5", "tags" ],
                         'jtopts_fields': [ "details",
                                            "thumb",
                                            "description",
                                            "created",
                                            "source",
                                            "md5",
                                            "tags",
                                            "favorite"],
                         'hidden_fields': ["md5"],
                         'linked_fields': ["source", "tags"],
                         'details_link': 'details',
                         'no_sort': ['details']
                       },
    }

    analyst = StringField()
    # Description is used here instead of inheriting from CritsBaseAttributes
    # because screenshots don't need the rest of the attributes that come with
    # inheriting.
    description = StringField()
    filename = StringField()
    height = IntField()
    md5 = StringField()
    screenshot = getFileField(collection_name=settings.COL_SCREENSHOTS,
                              required=True)
    tags = ListField(StringField())
    thumb = getFileField(collection_name=settings.COL_SCREENSHOTS,
                         required=True)
    width = IntField()

    def migrate(self):
        """
        Migrate the Screenshot to the latest schema version.
        """
        pass

    def add_screenshot(self, screenshot=None, tags=None):
        """
        Add the screenshot to the class. This will write the screenshot to
        GridFS, set the filename, width, height, and generate the thumbnail.

        :param screenshot: The screenshot to add.
        :type screenshot: file handle
        :param tags: A tag or list of tags for this screenshot
        :type param: str, list
        """

        if not screenshot:
            return
        self.filename = screenshot.name
        im = Image.open(screenshot)
        self.width, self.height = im.size
        fs = StringIO.StringIO()
        im.save(fs, "PNG")
        fs.seek(0)
        self.screenshot = fs.read()
        self.generate_thumbnail(im)
        if isinstance(tags, basestring):
            tlist = tags.split(',')
            self.tags = [t.strip() for t in tlist if len(t.strip())]
        elif isinstance(tags, list):
            self.tags = tags

    def add_tags(self, tags):
        """
        Add tags to a screenshot.

        :param tags: The tags to add.
        :type tags: str, list
        """

        tag_list = []
        if isinstance(tags, basestring):
            tag_list = [t.strip() for t in tags.split(',') if len(t.strip())]
        if isinstance(tags, list):
            tag_list = [t.strip() for t in tags if len(t.strip())]
        for t in tag_list:
            if t not in self.tags:
                self.tags.append(t)

    def generate_thumbnail(self, im=None):
        """
        Generate a thumbnail out of a screenshot. Will write the thumbnail to
        GridFS.

        :param im: The PIL Image.
        :type im: :class:`PIL.Image`
        """

        if not im:
            return
        size = (128, 128)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(self.thumb, "PNG")
        fs = StringIO.StringIO()
        im.save(fs, "PNG")
        fs.seek(0)
        self.thumb = fs.read()

    def sanitize(self, username=None, sources=None, rels=None):
        """
        Sanitize the source list down to only those a user has access to see.
        This was sniped from core/crits_mongoengine.

        :param username: The user requesting this data.
        :type username: str
        :param sources: A list of sources the user has access to.
        :type sources: list
        """

        if username and hasattr(self, 'source'):
            length = len(self.source)
            if not sources:
                sources = user_sources(username)
            # use slice to modify in place in case any code is referencing
            # the source already will reflect the changes as well
            self.source[:] = [s for s in self.source if s.name in sources]
            # a bit of a hack but we add a poorly formatted source to the
            # source list which has an instances length equal to the amount
            # of sources that were sanitized out of the user's list.
            # not tested but this has the added benefit of throwing a
            # ValidationError if someone were to try and save() this.
            new_length = len(self.source)
            if length > new_length:
                i_length = length - new_length
                s = EmbeddedSource()
                s.name = "Other"
                s.instances = [0] * i_length
                self.source.append(s)
