import datetime
import re

from bson.objectid import ObjectId
try:
	from django_mongoengine import Document
except ImportError:
	from mongoengine import Document

from mongoengine import EmbeddedDocument
from mongoengine import ObjectIdField, StringField, ListField, EmbeddedDocumentField
from django.conf import settings
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from crits.core.user import CRITsUser
from crits.core.fields import CritsDateTimeField
from crits.core.crits_mongoengine import CritsDocument, CritsSchemaDocument
from crits.core.crits_mongoengine import CritsDocumentFormatter, CritsSourceDocument
from crits.core.class_mapper import class_from_type


class EmbeddedParentField(EmbeddedDocument, CritsDocumentFormatter):
    """
    Embedded Parent Field
    """

    date = CritsDateTimeField()
    analyst = StringField()

class Comment(CritsDocument, CritsSchemaDocument, CritsSourceDocument, Document):
    """
    Comment Class.
    """

    meta = {
        "collection": settings.COL_COMMENTS,
        "auto_create_index": False,
        "crits_type": "Comment",
        "latest_schema_version": 1,
        "schema_doc": {
            'comment': 'The comment body',
            'obj_type': 'The type of the object this comment is for',
            'obj_id': 'The MongoDB ObjectId for the object this comment is for',
            'created': 'ISODate when this comment was made',
            'users': 'List [] of users mentioned in the comment',
            'tags': 'List [] of hashtags in the comment',
            'url_key': 'The key used to redirect to the object for this comment',
            'analyst': 'The analyst, if any, that made this comment',
            'parent': {
                'date': 'The date of the parent comment if this is a reply',
                'analyst': 'Analyst who made the comment this is a reply to'
            },
            'source': ('List [] of source information about who provided this'
                       ' comment')
        },
        "jtable_opts": {
            'details_url': '',
            'details_url_key': 'id',
            'default_sort': 'date DESC',
            'search_url': '',
            'fields': ["obj_type", "comment", "url_key", "created",
                       "analyst", "source", "id"],
            'jtopts_fields': ["details", "obj_type", "comment", "date",
                              "analyst", "source", "id"],
            'hidden_fields': ["id", ],
            'linked_fields': ["analyst", "source"],
            'details_link': 'details',
            'no_sort': ['details', ],
        }

    }
    # This is not a date field!
    # It exists to provide default values for created and edit_date
    date = datetime.datetime.now()

    analyst = StringField()
    comment = StringField()
    created = CritsDateTimeField(default=date, db_field="date")
    edit_date = CritsDateTimeField(default=date)
    obj_id = ObjectIdField()
    obj_type = StringField()
    #TODO: seems like this might be a good candidate for
    #   a reference field?
    parent = EmbeddedDocumentField(EmbeddedParentField)
    tags = ListField(StringField())
    url_key = StringField()
    users = ListField(StringField())

    def get_parent(self):
        """
        Get the parent CRITs object.

        :returns: class which inherits from
                  :class:`crits.core.crits_mongoengine.CritsBaseAttributes`.
        """

        col_obj = class_from_type(self.obj_type)
        doc = col_obj.objects(id=self.obj_id).first()
        return doc

    def comment_to_html(self):
        """
        Convert the comment from str to HTML.
        """

        if len(self.comment) > 0:
            self.comment = parse_comment(self.comment)['html']

    def parse_comment(self):
        """
        Parse the comment str for users and tags.
        """

        if len(self.comment) > 0:
            pc = parse_comment(self.comment)
            self.users = pc['users']
            self.tags = pc['tags']

    def edit_comment(self, new_comment):
        """
        Edit comment contents. Reparse for users and tags, and set the edit
        date.

        :param new_comment: The new comment.
        :type new_comment: str
        """

        self.comment = new_comment
        self.parse_comment()
        self.edit_date = datetime.datetime.now()

    def set_parent_comment(self, date, analyst):
        """
        Set the parent comment if this is a reply.

        :param date: The date of the parent comment.
        :type date: datetime.datetime
        :param analyst: The user replying to the comment.
        :type analyst: str
        """

        p = EmbeddedParentField()
        p.date = date
        p.analyst = analyst
        self.parent = p

    def set_parent_object(self, type_, id_):
        """
        Set the top-level object this comment is for.

        :param type_: The CRITs type of the object this comment is for.
        :type type_: str
        :param id_: The ObjectId of the object this comment is for.
        :type id_: str
        """

        if type_:
            self.obj_type = type_
        if isinstance(id_, ObjectId):
            self.obj_id = id_
        else:
            self.obj_id = ObjectId(id_)

    def set_url_key(self, url_key):
        """
        Set the url_key to link back to the parent object.

        :param url_key: The URL key to use.
        :type url_key: str
        """

        if isinstance(url_key, basestring):
                self.url_key = url_key

def parse_comment(comment):
    """
    Parse the comment for users and hashes, and generate html. HTML is escaped
    prior to parsing out users and tags.

    :param comment: The comment to parse.
    :type comment: str
    :returns: dict with keys "users", "tags", and "html"
    """

    re_user = re.compile(r'@[0-9a-zA-Z+_]*',re.IGNORECASE)
    re_tag = re.compile(r'#[0-9a-zA-Z+_]*',re.IGNORECASE)

    c = {'users': [],
         'tags': [],
         'html': ""}
    users = []
    tags = []

    # escape for safety
    # from https://wiki.python.org/moin/EscapingHtml
    comment = ''.join({'&': '&amp;',
                       '"': '&quot;',
                       '\'': '&apos;',
                       '>': '&gt;',
                       '<': '&lt;',}.get(c, c) for c in comment)
    comment = comment.replace('\n', '<br>') # make newlines html linebreaks

    # get users
    for i in re_user.finditer(comment):
        user = i.group(0).replace('@','').strip()
        if len(user) and CRITsUser.objects(username=user).count() == 1:
            users.append(user)
    # dedupe
    users = list(set(users))
    c['users'] = users

    # get tags
    for i in re_tag.finditer(comment):
        tag = i.group(0).replace('#','').strip()
        if len(tag):
            tags.append(tag)
    # dedupe
    tags = list(set(tags))
    c['tags'] = tags

    # generate html
    for user in users:
        link = '<a href="%s" class="comment_link">@%s</a>'\
               % (reverse('crits-comments-views-activity', args=['byuser',
                                                                 user]),
                  user)
        comment = comment.replace('@%s' % user, link)
    for tag in tags:
        link = '<a href="%s" class="comment_link">#%s</a>'\
               % (reverse('crits-comments-views-activity', args=['bytag',
                                                                 tag]),
                  tag)
        comment = comment.replace('#%s' % tag, link)
    c['html'] = comment

    return c
