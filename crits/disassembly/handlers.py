import crits.service_env
import datetime
import hashlib
import json

from dateutil.parser import parse
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from mongoengine.base import ValidationError

from crits.core.crits_mongoengine import create_embedded_source, json_handler
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import is_admin, user_sources, is_user_favorite
from crits.core.user_tools import is_user_subscribed
from crits.notifications.handlers import remove_user_from_notification
from crits.disassembly.disassembly import Disassembly, DisassemblyType 
from crits.services.handlers import run_triage


def generate_disassembly_csv(request):
    """
    Generate a CSV file of the Disassembly information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request, Disassembly)
    return response

def get_id_from_link_and_version(link, version):
    """
    Get the ObjectId from a link_id and version number.

    :param link: The link_id of the Disassembly.
    :type link: str
    :param version: The version number of the Disassembly.
    :type version: int
    :returns: None, ObjectId
    """

    dis = Disassembly.objects(link_id=link, version=version).only('id').first()
    if not dis:
        return None
    else:
        return dis.id

def get_disassembly_details(_id, analyst):
    """
    Generate the data to render the Disassembly details template.

    :param _id: The ObjectId of the Disassembly to get details for.
    :type _id: str
    :param analyst: The user requesting this information.
    :type analyst: str
    :returns: template (str), arguments (dict)
    """

    template = None
    sources = user_sources(analyst)
    if not _id:
        dis = None
    else:
        dis = Disassembly.objects(id=_id, source__name__in=sources).first()
    if not dis:
        template = "error.html"
        args = {'error': 'Disassembly not yet available or you do not have access to view it.'}
    else:

        dis.sanitize("%s" % analyst)

        # remove pending notifications for user
        remove_user_from_notification("%s" % analyst, dis.id, 'Disassembly')

        # subscription
        subscription = {
                'type': 'Disassembly',
                'id': dis.id,
                'subscribed': is_user_subscribed("%s" % analyst,
                                                 'Disassembly', dis.id),
        }

        #objects
        objects = dis.sort_objects()

        #relationships
        relationships = dis.sort_relationships("%s" % analyst, meta=True)

        # relationship
        relationship = {
                'type': 'Disassembly',
                'value': dis.id
        }

        versions = len(Disassembly.objects(link_id=dis.link_id).only('id'))

        #comments
        comments = {'comments': dis.get_comments(),
                    'url_key': _id}

        #screenshots
        screenshots = dis.get_screenshots(analyst)

        # favorites
        favorite = is_user_favorite("%s" % analyst, 'Disassembly', dis.id)

        # services
        manager = crits.service_env.manager
        service_list = manager.get_supported_services('Disassembly', True)

        args = {'service_list': service_list,
                'objects': objects,
                'relationships': relationships,
                'comments': comments,
                'favorite': favorite,
                'relationship': relationship,
                "subscription": subscription,
                "screenshots": screenshots,
                "versions": versions,
                "disassembly": dis}

    return template, args

def generate_disassembly_versions(_id):
    """
    Generate a list of available versions for this Disassembly.

    :param _id: The ObjectId of the Disassembly to generate versions for.
    :type _id: str
    :returns: list
    """

    dis = Disassembly.objects(id=_id).only('link_id').first()
    if not dis:
        return []
    else:
        versions = []
        dvs = Disassembly.objects(link_id=dis.link_id).only('id',
                                                            'name',
                                                            'version')
        for dv in dvs:
            link = reverse('crits.disassembly.views.disassembly_details',
                           args=(dv.id,))
            versions.append({'name': dv.name,
                             'version': dv.version,
                             'link': link})
        return versions

def generate_disassembly_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Disassembly
    type_ = "disassembly"
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
        'title': "Disassembly",
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
            'tooltip': "'All Disassemblies'",
            'text': "'All'",
            'click': "function () {$('#disassembly_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Disassemblies'",
            'text': "'New'",
            'click': "function () {$('#disassembly_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Disassemblies'",
            'text': "'In Progress'",
            'click': "function () {$('#disassembly_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Disassemblies'",
            'text': "'Analyzed'",
            'click': "function () {$('#disassembly_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Disassemblies'",
            'text': "'Deprecated'",
            'click': "function () {$('#disassembly_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add Disassembly'",
            'text': "'Add Disassembly'",
            'click': "function () {$('#new-disassembly').click()}",
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

def handle_disassembly_file(data, source_name, user=None,
                         description=None, name=None, data_type=None,
                         tool_name=None, tool_version=None, tool_details=None,
                         link_id=None, method=None, copy_rels=False,
                         bucket_list=None, ticket=None):
    """
    Add Disassembly.

    :param data: The data of the Disassembly.
    :type data: str
    :param source_name: The source which provided this Disassembly.
    :type source_name: str,
                       :class:`crits.core.crits_mongoengine.EmbeddedSource`,
                       list of :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param user: The user adding the Disassembly.
    :type user: str
    :param description: Description of the Disassembly.
    :type description: str
    :param name: Name of the Disassembly.
    :type name: str
    :param data_type: Datatype of the Disassembly.
    :type data_type: str
    :param tool_name: Name of the tool used to acquire/generate the Disassembly.
    :type tool_name: str
    :param tool_version: Version of the tool.
    :type tool_version: str
    :param tool_details: Details about the tool.
    :type tool_details: str
    :param link_id: LinkId to tie this to another Disassembly as a new version.
    :type link_id: str
    :param method: The method of acquiring this Disassembly.
    :type method: str
    :param copy_rels: Copy relationships from the previous version to this one.
    :type copy_rels: bool
    :param bucket_list: Bucket(s) to add to this Disassembly 
    :type bucket_list: str(comma separated) or list.
    :param ticket: Ticket(s) to add to this Disassembly
    :type ticket: str(comma separated) or list.
    :returns: dict with keys:
              'success' (boolean),
              'message' (str),
              '_id' (str) if successful.
    """

    status = { 'success': False }
    if not data or not name or not data_type:
        status['message'] = 'No data object, name, or data type passed in'
        return status

    dt = DisassemblyType.objects(name=data_type).first()
    if not dt:
        status['message'] = 'Invalid data type passed in'
        return status

    if len(data) <= 0:
        status['message'] = 'Data length <= 0'
        return status

    # generate md5 and timestamp
    md5 = hashlib.md5(data).hexdigest()
    timestamp = datetime.datetime.now()

    # create source
    source = create_embedded_source(source_name,
                                    date=timestamp,
                                    reference='',
                                    method=method,
                                    analyst=user)

    # generate disassembly
    is_disassembly_new = False
    dis = Disassembly.objects(md5=md5).first()
    if dis:
        dis.add_source(source)
    else:
        dis = Disassembly()
        dis.created = timestamp
        dis.description = description
        dis.md5 = md5
        dis.source = [source]
        # XXX: This needs to do the whole "do i have this" dance like samples.
        dis._generate_file_metadata(data)
        dis.add_file_data(data)
        dis.name = name
        dis.data_type = data_type
        dis.add_tool(name=tool_name,
                          version=tool_version,
                          details=tool_details)
        is_disassembly_new = True
    #XXX: need to validate this is a UUID
    if link_id:
        dis.link_id = link_id
        if copy_rels:
            d2 = Disassembly.objects(link_id=link_id).first()
            if d2:
                if len(d2.relationships):
                    dis.save(username=user)
                    dis.reload()
                    for rel in d2.relationships:
                        dis.add_relationship(rel_id=rel.object_id,
                                             type_=rel.rel_type,
                                             rel_type=rel.relationship,
                                             rel_date=rel.relationship_date,
                                             analyst=user)


    dis.version = len(Disassembly.objects(link_id=link_id)) + 1

    if bucket_list:
        dis.add_bucket_list(bucket_list, user)

    if ticket:
        dis.add_ticket(ticket, user);

    # save disassembly 
    dis.save(username=user)

    # run disassembly triage
    if is_disassembly_new:
        dis.reload()
        run_triage(None, dis, user)

    status['success'] = True
    status['message'] = 'Uploaded disassembly'
    status['id'] = str(dis.id)

    return status

def update_disassembly_description(_id, description, analyst):
    """
    Update the Disassembly description.

    :param _id: ObjectId of the Disassembly to update.
    :type _id: str
    :param description: The description to set.
    :type description: str
    :param analyst: The user updating the description.
    :type analyst: str
    :returns: None
    :raises: ValidationError
    """

    dis = Disassembly.objects(id=_id).first()
    dis.description = description
    try:
        dis.save(username=analyst)
        return None
    except ValidationError, e:
        return e

def update_disassembly_tool_details(_id, details, analyst):
    """
    Update the Disassembly tool details.

    :param _id: ObjectId of the Disassembly to update.
    :type _id: str
    :param details: The detail to set.
    :type detail: str
    :param analyst: The user updating the details.
    :type analyst: str
    :returns: None
    :raises: ValidationError
    """

    dis = Disassembly.objects(id=_id).first()
    dis.tool.details = details
    try:
        dis.save(username=analyst)
        return None
    except ValidationError, e:
        return e

def update_disassembly_tool_name(_id, name, analyst):
    """
    Update the Disassembly tool name.

    :param _id: ObjectId of the Disassembly to update.
    :type _id: str
    :param name: The name to set.
    :type name: str
    :param analyst: The user updating the name.
    :type analyst: str
    :returns: None
    :raises: ValidationError
    """

    dis = Disassembly.objects(id=_id).first()
    dis.tool.name = name
    try:
        dis.save(username=analyst)
        return None
    except ValidationError, e:
        return e

def update_disassembly_type(_id, data_type, analyst):
    """
    Update the Disassembly data type.

    :param _id: ObjectId of the Disassembly to update.
    :type _id: str
    :param data_type: The data type to set.
    :type data_type: str
    :param analyst: The user updating the data type.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str) if failed.
    """

    dis = Disassembly.objects(id=_id).first()
    data_type = DisassemblyType.objects(name=data_type).first()
    if not data_type:
        return None
    else:
        dis.data_type = data_type.name
        try:
            dis.save(username=analyst)
            return {'success': True}
        except ValidationError, e:
            return {'success': False, 'message': str(e)}

def delete_disassembly(_id, username=None):
    """
    Delete Disassembly from CRITs.

    :param _id: The ObjectId of the Disassembly to delete.
    :type _id: str
    :param username: The user deleting this Disassembly.
    :type username: str
    :returns: bool
    """

    if is_admin(username):
        dis = Disassembly.objects(id=_id).first()
        if dis:
            dis.delete(username=username)
            return True
    return False

def add_new_disassembly_type(data_type, analyst):
    """
    Add a new Disassembly datatype to CRITs.

    :param data_type: The new datatype to add.
    :type data_type: str
    :param analyst: The user adding the new datatype.
    :type analyst: str
    :returns: bool
    """

    data_type = data_type.strip()
    try:
        dis_type = DisassemblyType.objects(name=data_type).first()
        if dis_type:
            return False
        dis_type = DisassemblyType()
        dis_type.name = data_type
        dis_type.save(username=analyst)
        return True
    except ValidationError:
        return False
