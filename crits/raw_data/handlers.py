import datetime
import hashlib
import json

from dateutil.parser import parse
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError

from crits.core.crits_mongoengine import EmbeddedSource, create_embedded_source, json_handler
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.class_mapper import class_from_id
from crits.core.handlers import csv_export
from crits.core.user_tools import is_admin, user_sources, is_user_favorite
from crits.core.user_tools import is_user_subscribed
from crits.notifications.handlers import remove_user_from_notification
from crits.raw_data.raw_data import RawData, RawDataType
from crits.services.handlers import run_triage, get_supported_services


def generate_raw_data_csv(request):
    """
    Generate a CSV file of the RawData information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,RawData)
    return response

def get_id_from_link_and_version(link, version):
    """
    Get the ObjectId from a link_id and version number.

    :param link: The link_id of the RawData.
    :type link: str
    :param version: The version number of the RawData.
    :type version: int
    :returns: None, ObjectId
    """

    raw_data = RawData.objects(link_id=link, version=version).only('id').first()
    if not raw_data:
        return None
    else:
        return raw_data.id

def get_raw_data_details(_id, analyst):
    """
    Generate the data to render the RawData details template.

    :param _id: The ObjectId of the RawData to get details for.
    :type _id: str
    :param analyst: The user requesting this information.
    :type analyst: str
    :returns: template (str), arguments (dict)
    """

    template = None
    sources = user_sources(analyst)
    if not _id:
        raw_data = None
    else:
        raw_data = RawData.objects(id=_id, source__name__in=sources).first()
    if not raw_data:
        template = "error.html"
        args = {'error': 'raw_data not yet available or you do not have access to view it.'}
    else:

        raw_data.sanitize("%s" % analyst)

        # remove pending notifications for user
        remove_user_from_notification("%s" % analyst, raw_data.id, 'RawData')

        # subscription
        subscription = {
                'type': 'RawData',
                'id': raw_data.id,
                'subscribed': is_user_subscribed("%s" % analyst,
                                                 'RawData', raw_data.id),
        }

        #objects
        objects = raw_data.sort_objects()

        #relationships
        relationships = raw_data.sort_relationships("%s" % analyst, meta=True)

        # relationship
        relationship = {
                'type': 'RawData',
                'value': raw_data.id
        }

        versions = len(RawData.objects(link_id=raw_data.link_id).only('id'))

        #comments
        comments = {'comments': raw_data.get_comments(),
                    'url_key': _id}

        #screenshots
        screenshots = raw_data.get_screenshots(analyst)

        # favorites
        favorite = is_user_favorite("%s" % analyst, 'RawData', raw_data.id)

        # services
        service_list = get_supported_services('RawData')

        # analysis results
        service_results = raw_data.get_analysis_results()

        args = {'service_list': service_list,
                'objects': objects,
                'relationships': relationships,
                'comments': comments,
                'favorite': favorite,
                'relationship': relationship,
                "subscription": subscription,
                "screenshots": screenshots,
                "versions": versions,
                "service_results": service_results,
                "raw_data": raw_data}

    return template, args

def generate_inline_comments(_id):
    """
    Generate the inline comments for RawData.

    :param _id: The ObjectId of the RawData to generate inline comments for.
    :type _id: str
    :returns: list
    """

    raw_data = RawData.objects(id=_id).first()
    if not raw_data:
        return []
    else:
        inlines = []
        for i in raw_data.inlines:
            html = render_to_string('inline_comment.html',
                                    {'username': i.analyst,
                                    'comment': i.comment,
                                    'date': i.date,
                                    'line': i.line,
                                    'raw_data': {'id': _id}})
            inlines.append({'line': i.line, 'html': html})
        return inlines

def generate_raw_data_versions(_id):
    """
    Generate a list of available versions for this RawData.

    :param _id: The ObjectId of the RawData to generate versions for.
    :type _id: str
    :returns: list
    """

    raw_data = RawData.objects(id=_id).only('link_id').first()
    if not raw_data:
        return []
    else:
        versions = []
        rvs = RawData.objects(link_id=raw_data.link_id).only('id',
                                                             'title',
                                                             'version',
                                                             'data')
        for rv in rvs:
            link = reverse('crits.raw_data.views.raw_data_details',
                           args=(rv.id,))
            versions.append({'title': rv.title,
                            'version': rv.version,
                            'data': rv.data,
                             'link': link})
        return versions

def generate_raw_data_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = RawData
    type_ = "raw_data"
    mapper = obj_type._meta['jtable_opts']
    if option == "jtlist":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']
        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request,
                                    includes=fields)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    if option == "jtdelete":
        response = {"Result": "ERROR"}
        if jtable_ajax_delete(obj_type,request):
            response = {"Result": "OK"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Raw Data",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.%s.views.%s_listing' % (type_,
                                                            type_),
                           args=('jtlist',)),
        'deleteurl': reverse('crits.%s.views.%s_listing' % (type_,
                                                              type_),
                             args=('jtdelete',)),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    jtable = build_jtable(jtopts,request)
    jtable['toolbar'] = [
        {
            'tooltip': "'All Raw Data'",
            'text': "'All'",
            'click': "function () {$('#raw_data_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Raw Data'",
            'text': "'New'",
            'click': "function () {$('#raw_data_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Raw Data'",
            'text': "'In Progress'",
            'click': "function () {$('#raw_data_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Raw Data'",
            'text': "'Analyzed'",
            'click': "function () {$('#raw_data_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Raw Data'",
            'text': "'Deprecated'",
            'click': "function () {$('#raw_data_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add Raw Data'",
            'text': "'Add Raw Data'",
            'click': "function () {$('#new-raw-data').click()}",
        },
    ]

    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button' : '%s_tab' % type_},
                                  RequestContext(request))
    else:
        return render_to_response("%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  RequestContext(request))

def handle_raw_data_file(data, source_name, user=None,
                         description=None, title=None, data_type=None,
                         tool_name=None, tool_version=None, tool_details=None,
                         link_id=None, method='', reference='',
                         copy_rels=False, bucket_list=None, ticket=None):
    """
    Add RawData.

    :param data: The data of the RawData.
    :type data: str
    :param source_name: The source which provided this RawData.
    :type source_name: str,
                       :class:`crits.core.crits_mongoengine.EmbeddedSource`,
                       list of :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param user: The user adding the RawData.
    :type user: str
    :param description: Description of the RawData.
    :type description: str
    :param title: Title of the RawData.
    :type title: str
    :param data_type: Datatype of the RawData.
    :type data_type: str
    :param tool_name: Name of the tool used to acquire/generate the RawData.
    :type tool_name: str
    :param tool_version: Version of the tool.
    :type tool_version: str
    :param tool_details: Details about the tool.
    :type tool_details: str
    :param link_id: LinkId to tie this to another RawData as a new version.
    :type link_id: str
    :param method: The method of acquiring this RawData.
    :type method: str
    :param reference: A reference to the source of this RawData.
    :type reference: str
    :param copy_rels: Copy relationships from the previous version to this one.
    :type copy_rels: bool
    :param bucket_list: Bucket(s) to add to this RawData
    :type bucket_list: str(comma separated) or list.
    :param ticket: Ticket(s) to add to this RawData
    :type ticket: str(comma separated) or list.
    :returns: dict with keys:
              'success' (boolean),
              'message' (str),
              '_id' (str) if successful.
    """

    if not data or not title or not data_type:
        status = {
            'success':   False,
            'message':  'No data object, title, or data type passed in'
        }
        return status

    if not source_name:
        return {"success" : False, "message" : "Missing source information."}

    rdt = RawDataType.objects(name=data_type).first()
    if not rdt:
        status = {
            'success':   False,
            'message':  'Invalid data type passed in'
        }
        return status

    if len(data) <= 0:
        status = {
            'success':   False,
            'message':  'Data length <= 0'
        }
        return status

    # generate md5 and timestamp
    md5 = hashlib.md5(data.encode('utf-8')).hexdigest()
    timestamp = datetime.datetime.now()

    # generate raw_data
    is_rawdata_new = False
    raw_data = RawData.objects(md5=md5).first()
    if not raw_data:
        raw_data = RawData()
        raw_data.created = timestamp
        raw_data.description = description
        raw_data.md5 = md5
        #raw_data.source = [source]
        raw_data.data = data
        raw_data.title = title
        raw_data.data_type = data_type
        raw_data.add_tool(name=tool_name,
                          version=tool_version,
                          details=tool_details)
        is_rawdata_new = True

    # generate new source information and add to sample
    if isinstance(source_name, basestring) and len(source_name) > 0:
        source = create_embedded_source(source_name,
                                   date=timestamp,
                                   method=method,
                                   reference=reference,
                                   analyst=user)
        # this will handle adding a new source, or an instance automatically
        raw_data.add_source(source)
    elif isinstance(source_name, EmbeddedSource):
        raw_data.add_source(source_name, method=method, reference=reference)
    elif isinstance(source_name, list) and len(source_name) > 0:
        for s in source_name:
            if isinstance(s, EmbeddedSource):
                raw_data.add_source(s, method=method, reference=reference)

    #XXX: need to validate this is a UUID
    if link_id:
        raw_data.link_id = link_id
        if copy_rels:
            rd2 = RawData.objects(link_id=link_id).first()
            if rd2:
                if len(rd2.relationships):
                    raw_data.save(username=user)
                    raw_data.reload()
                    for rel in rd2.relationships:
                        # Get object to relate to.
                        rel_item = class_from_id(rel.rel_type, rel.object_id)
                        if rel_item:
                            raw_data.add_relationship(rel_item,
                                                      rel.relationship,
                                                      rel_date=rel.relationship_date,
                                                      analyst=user)


    raw_data.version = len(RawData.objects(link_id=link_id)) + 1

    if bucket_list:
        raw_data.add_bucket_list(bucket_list, user)

    if ticket:
        raw_data.add_ticket(ticket, user);

    # save raw_data
    raw_data.save(username=user)

    # run raw_data triage
    if is_rawdata_new:
        raw_data.reload()
        run_triage(raw_data, user)

    status = {
        'success':      True,
        'message':      'Uploaded raw_data',
        '_id':          raw_data.id,
        'object':       raw_data
    }

    return status

def update_raw_data_tool_details(_id, details, analyst):
    """
    Update the RawData tool details.

    :param _id: ObjectId of the RawData to update.
    :type _id: str
    :param details: The detail to set.
    :type detail: str
    :param analyst: The user updating the details.
    :type analyst: str
    :returns: None
    :raises: ValidationError
    """

    raw_data = RawData.objects(id=_id).first()
    raw_data.tool.details = details
    try:
        raw_data.save(username=analyst)
        return None
    except ValidationError, e:
        return e

def update_raw_data_tool_name(_id, name, analyst):
    """
    Update the RawData tool name.

    :param _id: ObjectId of the RawData to update.
    :type _id: str
    :param name: The name to set.
    :type name: str
    :param analyst: The user updating the name.
    :type analyst: str
    :returns: None
    :raises: ValidationError
    """

    raw_data = RawData.objects(id=_id).first()
    raw_data.tool.name = name
    try:
        raw_data.save(username=analyst)
        return None
    except ValidationError, e:
        return e

def update_raw_data_type(_id, data_type, analyst):
    """
    Update the RawData data type.

    :param _id: ObjectId of the RawData to update.
    :type _id: str
    :param data_type: The data type to set.
    :type data_type: str
    :param analyst: The user updating the data type.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    raw_data = RawData.objects(id=_id).first()
    data_type = RawDataType.objects(name=data_type).first()
    if not data_type:
        return None
    else:
        raw_data.data_type = data_type.name
        try:
            raw_data.save(username=analyst)
            return {'success': True}
        except ValidationError, e:
            return {'success': False, 'message': str(e)}

def update_raw_data_highlight_comment(_id, comment, line, analyst):
    """
    Update a highlight comment.

    :param _id: ObjectId of the RawData to update.
    :type _id: str
    :param comment: The comment to add.
    :type comment: str
    :param line: The line this comment is associated with.
    :type line: str, int
    :param analyst: The user updating the comment.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    raw_data = RawData.objects(id=_id).first()
    if not raw_data:
        return None
    else:
        for highlight in raw_data.highlights:
            if highlight.line == int(line):
                highlight.comment = comment
                try:
                    raw_data.save(username=analyst)
                    return {'success': True}
                except ValidationError, e:
                    return {'success': False, 'message': str(e)}
        return {'success': False, 'message': 'Could not find highlight.'}

def update_raw_data_highlight_date(_id, date, line, analyst):
    """
    Update a highlight date.

    :param _id: ObjectId of the RawData to update.
    :type _id: str
    :param date: The date to set.
    :type date: str
    :param line: The line this date is associated with.
    :type line: str, int
    :param analyst: The user updating the date.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    raw_data = RawData.objects(id=_id).first()
    if not raw_data:
        return None
    else:
        for highlight in raw_data.highlights:
            if highlight.line == int(line):
                highlight.line_date = parse(date, fuzzy=True)
                try:
                    raw_data.save(username=analyst)
                    return {'success': True}
                except ValidationError, e:
                    return {'success': False, 'message': str(e)}
        return {'success': False, 'message': 'Could not find highlight.'}

def new_inline_comment(_id, comment, line_num, analyst):
    """
    Add a new inline comment.

    :param _id: ObjectId of the RawData to update.
    :type _id: str
    :param comment: The comment to add.
    :type comment: str
    :param line_num: The line this comment is associated with.
    :type line_num: str, int
    :param analyst: The user adding this comment.
    :type analyst: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "line" (int),
              "html" (str)
    :raises: ValidationError
    """

    raw_data = RawData.objects(id=_id).first()
    raw_data.add_inline_comment(comment, line_num, analyst)
    try:
        raw_data.save(username=analyst)
        html = render_to_string('inline_comment.html',
                                {'username': analyst,
                                 'comment': comment,
                                 'date': datetime.datetime.now(),
                                 'line': line_num,
                                 'raw_data': {'id': _id}})
        return {'success': True,
                'message': 'Comment for line %s added successfully!' % line_num,
                'inline': True,
                'line': line_num,
                'html': html,
                }
    except ValidationError, e:
        return e

def new_highlight(_id, line_num, line_data, analyst):
    """
    Add a new highlight.

    :param _id: ObjectId of the RawData to update.
    :type _id: str
    :param line_num: The line to highlight.
    :type line_num: str, int
    :param line_data: The data on this line.
    :type line_data: str
    :param analyst: The user highlighting this line.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "html" (str)
    :raises: ValidationError
    """

    raw_data = RawData.objects(id=_id).first()
    raw_data.add_highlight(line_num, line_data, analyst)
    try:
        raw_data.save(username=analyst)
        html = render_to_string('raw_data_highlights.html',
                                {'raw_data': {'id': _id,
                                              'highlights': raw_data.highlights}})
        return {'success': True,
                'html': html,
                }
    except ValidationError, e:
        return e

def delete_highlight(_id, line_num, analyst):
    """
    Delete a highlight from RawData.

    :param _id: The ObjectId of the RawData to update.
    :type _id: str
    :param line_num: Line number of the highlight to delete.
    :type line_num: str, int
    :param analyst: The user deleting this highlight.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "html" (str)
    """

    raw_data = RawData.objects(id=_id).first()
    highlights = len(raw_data.highlights)
    raw_data.remove_highlight(line_num, analyst)
    if len(raw_data.highlights) < highlights:
        try:
            raw_data.save(username=analyst)
            html = render_to_string('raw_data_highlights.html',
                                    {'raw_data': {'id': _id,
                                                'highlights': raw_data.highlights}})
            return {'success': True,
                    'html': html,
                    }
        except ValidationError, e:
            return e
    else:
        return {'success': False}

def delete_raw_data(_id, username=None):
    """
    Delete RawData from CRITs.

    :param _id: The ObjectId of the RawData to delete.
    :type _id: str
    :param username: The user deleting this RawData.
    :type username: str
    :returns: bool
    """

    if is_admin(username):
        raw_data = RawData.objects(id=_id).first()
        if raw_data:
            raw_data.delete(username=username)
            return True
        else:
            return False
    else:
        return False

def add_new_raw_data_type(data_type, analyst):
    """
    Add a new RawData datatype to CRITs.

    :param data_type: The new datatype to add.
    :type data_type: str
    :param analyst: The user adding the new datatype.
    :type analyst: str
    :returns: bool
    """

    data_type = data_type.strip()
    try:
        raw_data_type = RawDataType.objects(name=data_type).first()
        if raw_data_type:
            return False
        raw_data_type = RawDataType()
        raw_data_type.name = data_type
        raw_data_type.save(username=analyst)
        return True
    except ValidationError:
        return False
