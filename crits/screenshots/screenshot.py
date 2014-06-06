import StringIO

from mongoengine import Document, StringField, ListField, IntField
from django.conf import settings
from PIL import Image

from crits.core.crits_mongoengine import CritsBaseDocument, CritsSourceDocument
from crits.core.crits_mongoengine import CritsSchemaDocument, CritsDocument
from crits.core.fields import getFileField

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
    }

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
