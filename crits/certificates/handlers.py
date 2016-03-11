import datetime
import hashlib
import json

from bson.objectid import ObjectId
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core.class_mapper import class_from_id, class_from_value
from crits.core.crits_mongoengine import EmbeddedSource
from crits.core.crits_mongoengine import create_embedded_source, json_handler
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import is_admin, user_sources
from crits.core.user_tools import is_user_subscribed
from crits.certificates.certificate import Certificate
from crits.notifications.handlers import remove_user_from_notification
from crits.services.analysis_result import AnalysisResult
from crits.services.handlers import run_triage, get_supported_services

from crits.vocabulary.relationships import RelationshipTypes


def generate_cert_csv(request):
    """
    Generate a CSV file of the Certificate information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,Certificate)
    return response

def get_certificate_details(md5, analyst):
    """
    Generate the data to render the Certificate details template.

    :param md5: The MD5 of the Certificate to get details for.
    :type md5: str
    :param analyst: The user requesting this information.
    :type analyst: str
    :returns: template (str), arguments (dict)
    """

    template = None
    sources = user_sources(analyst)
    cert = Certificate.objects(md5=md5, source__name__in=sources).first()
    if not cert:
        template = "error.html"
        args = {'error': 'Certificate not yet available or you do not have access to view it.'}
    else:

        cert.sanitize("%s" % analyst)

        # remove pending notifications for user
        remove_user_from_notification("%s" % analyst, cert.id, 'Certificate')

        # subscription
        subscription = {
                'type': 'Certificate',
                'id': cert.id,
                'subscribed': is_user_subscribed("%s" % analyst,
                                                 'Certificate', cert.id),
        }

        #objects
        objects = cert.sort_objects()

        #relationships
        relationships = cert.sort_relationships("%s" % analyst, meta=True)

        # relationship
        relationship = {
                'type': 'Certificate',
                'value': cert.id
        }

        #comments
        comments = {'comments': cert.get_comments(),
                    'url_key': md5}

        #screenshots
        screenshots = cert.get_screenshots(analyst)

        # services
        service_list = get_supported_services('Certificate')

        # analysis results
        service_results = cert.get_analysis_results()

        args = {'service_list': service_list,
                'objects': objects,
                'relationships': relationships,
                'comments': comments,
                'relationship': relationship,
                "subscription": subscription,
                "screenshots": screenshots,
                'service_results': service_results,
                "cert": cert}

    return template, args

def generate_cert_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Certificate
    type_ = "certificate"
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
        'title': "Certificates",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                            type_),
                           args=('jtlist',)),
        'deleteurl': reverse('crits.%ss.views.%ss_listing' % (type_,
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
            'tooltip': "'All Certificates'",
            'text': "'All'",
            'click': "function () {$('#certificate_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Certificates'",
            'text': "'New'",
            'click': "function () {$('#certificate_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Certificates'",
            'text': "'In Progress'",
            'click': "function () {$('#certificate_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Certificates'",
            'text': "'Analyzed'",
            'click': "function () {$('#certificate_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Certificates'",
            'text': "'Deprecated'",
            'click': "function () {$('#certificate_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add Certificate'",
            'text': "'Add Certificate'",
            'click': "function () {$('#new-certificate').click()}",
        },
    ]
    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button' : '%ss_tab' % type_},
                                  RequestContext(request))
    else:
        return render_to_response("%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  RequestContext(request))

def handle_cert_file(filename, data, source_name, user=None,
                     description=None, related_md5=None, method='', 
                     reference='', relationship=None, bucket_list=None, 
                     ticket=None, related_id=None, related_type=None,
                     relationship_type=None):
    """
    Add a Certificate.

    :param filename: The filename of the Certificate.
    :type filename: str
    :param data: The filedata of the Certificate.
    :type data: str
    :param source_name: The source which provided this Certificate.
    :type source_name: str,
                       :class:`crits.core.crits_mongoengine.EmbeddedSource`,
                       list of :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param user: The user adding the Certificate.
    :type user: str
    :param description: Description of the Certificate.
    :type description: str
    :param related_md5: MD5 of a top-level object related to this Certificate.
    :type related_md5: str
    :param related_type: The CRITs type of the related top-level object.
    :type related_type: str
    :param method: The method of acquiring this Certificate.
    :type method: str
    :param reference: A reference to the source of this Certificate.
    :type reference: str
    :param relationship: The relationship between the parent and the Certificate.
    :type relationship: str
    :param bucket_list: Bucket(s) to add to this Certificate
    :type bucket_list: str(comma separated) or list.
    :param ticket: Ticket(s) to add to this Certificate
    :type ticket: str(comma separated) or list.
    :param related_id: ID of object to create relationship with
    :type related_id: str
    :param related_type: Type of object to create relationship with
    :type related_id: str
    :param relationship_type: Type of relationship to create.
    :type relationship_type: str
    :returns: dict with keys:
              'success' (boolean),
              'message' (str),
              'md5' (str) if successful.
    """

    if not data:
        status = {
            'success':   False,
            'message':  'No data object passed in'
        }
        return status
    if len(data) <= 0:
        status = {
            'success':   False,
            'message':  'Data length <= 0'
        }
        return status
    if ((related_type and not (related_id or related_md5)) or
        (not related_type and (related_id or related_md5))):
        status = {
            'success':   False,
            'message':  'Must specify both related_type and related_id or related_md5.'
        }
        return status

    related_obj = None
    if related_id or related_md5:
        if related_id:
            related_obj = class_from_id(related_type, related_id)
        else:
            related_obj = class_from_value(related_type, related_md5)
        if not related_obj:
            status = {
                'success': False,
                'message': 'Related object not found.'
            }
            return status

    # generate md5 and timestamp
    md5 = hashlib.md5(data).hexdigest()
    timestamp = datetime.datetime.now()

    # generate Certificate
    cert = Certificate.objects(md5=md5).first()
    if not cert:
        cert = Certificate()
        cert.filename = filename
        cert.created = timestamp
        cert.size = len(data)
        cert.description = description
        cert.md5 = md5

    # generate source information and add to certificate
    if isinstance(source_name, basestring) and len(source_name) > 0:
        s = create_embedded_source(source_name,
                                   method=method,
                                   reference=reference,
                                   analyst=user)
        cert.add_source(s)
    elif isinstance(source_name, EmbeddedSource):
        cert.add_source(source_name, method=method, reference=reference)
    elif isinstance(source_name, list) and len(source_name) > 0:
        for s in source_name:
            if isinstance(s, EmbeddedSource):
                cert.add_source(s, method=method, reference=reference)

    if bucket_list:
        cert.add_bucket_list(bucket_list, user)

    if ticket:
        cert.add_ticket(ticket, user)

    # add file to GridFS
    if not isinstance(cert.filedata.grid_id, ObjectId):
        cert.add_file_data(data)

    # save cert
    cert.save(username=user)
    cert.reload()

    # run certificate triage
    if len(AnalysisResult.objects(object_id=str(cert.id))) < 1 and data:
        run_triage(cert, user)

    # update relationship if a related top-level object is supplied
    if related_obj and cert:
        if relationship_type:
            relationship=RelationshipTypes.inverse(relationship=relationship_type)
        if not relationship:
            relationship = RelationshipTypes.RELATED_TO
            
        cert.add_relationship(related_obj,
                              relationship,
                              analyst=user,
                              get_rels=False)
        cert.save(username=user)

    status = {
        'success':      True,
        'message':      'Uploaded certificate',
        'md5':          md5,
        'id':           str(cert.id),
        'object':       cert
    }

    return status

def delete_cert(md5, username=None):
    """
    Delete a Certificate.

    :param md5: The MD5 of the Certificate to delete.
    :type md5: str
    :param username: The user deleting the certificate.
    :type username: str
    :returns: True, False
    """

    if is_admin(username):
        cert = Certificate.objects(md5=md5).first()
        if cert:
            cert.delete(username=username)
            return True
        else:
            return False
    else:
        return False
