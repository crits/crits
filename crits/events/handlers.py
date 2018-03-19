from bson.objectid import ObjectId
import datetime
import json
import uuid

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError

from crits.core import form_consts
from crits.core.class_mapper import class_from_id
from crits.campaigns.campaign import Campaign
from crits.campaigns.forms import CampaignForm
from crits.core.crits_mongoengine import create_embedded_source, json_handler
from crits.core.crits_mongoengine import EmbeddedCampaign
from crits.core.exceptions import ZipFileError
from crits.core.forms import DownloadFileForm
from crits.core.handlers import build_jtable, jtable_ajax_list
from crits.core.handlers import jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import user_sources, is_user_favorite
from crits.core.user_tools import is_user_subscribed
from crits.events.event import Event
from crits.notifications.handlers import remove_user_from_notification
from crits.samples.handlers import handle_uploaded_file, mail_sample
from crits.services.handlers import run_triage, get_supported_services

from crits.vocabulary.relationships import RelationshipTypes
from crits.vocabulary.acls import EventACL


def generate_event_csv(request):
    """
    Generate a CSV file of the Event information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,Event)
    return response

def get_event_details(event_id, user):
    """
    Generate the data to render the Event details template.

    :param event_id: The ObjectId of the Event to get details for.
    :type event_id: str
    :param user: The user requesting this information.
    :type user: str
    :returns: template (str), arguments (dict)
    """

    template = None
    sources = user_sources(user)
    event = Event.objects(id=event_id, source__name__in=sources).first()

    if not user.check_source_tlp(event):
        event = None

    if not event:
        template = "error.html"
        args = {'error': "ID does not exist or insufficient privs for source"}
        return template, args

    event.sanitize("%s" % user)

    campaign_form = CampaignForm()
    download_form = DownloadFileForm(initial={"obj_type": 'Event',
                                              "obj_id": event_id})

    # remove pending notifications for user
    remove_user_from_notification("%s" % user, event.id, 'Event')

    # subscription
    subscription = {
            'type': 'Event',
            'id': event.id,
            'subscribed': is_user_subscribed("%s" % user,
                                             'Event', event.id),
    }

    #objects
    objects = event.sort_objects()

    #relationships
    relationships = event.sort_relationships("%s" % user, meta=True)

    # Get count of related Events for each related Indicator
    for ind in relationships.get('Indicator', []):
        count = Event.objects(relationships__object_id=ind['id'],
                              source__name__in=sources).count()
        ind['rel_ind_events'] = count

    # Get count of related Events for each related Sample
    for smp in relationships.get('Sample', []):
        count = Event.objects(relationships__object_id=smp['id'],
                              source__name__in=sources).count()
        smp['rel_smp_events'] = count

    # relationship
    relationship = {
            'type': 'Event',
            'value': event.id
    }

    #comments
    comments = {'comments': event.get_comments(), 'url_key': event.id}

    #screenshots
    screenshots = event.get_screenshots(user)

    # favorites
    favorite = is_user_favorite("%s" % user, 'Event', event.id)

    # services
    service_list = get_supported_services('Event')

    # analysis results
    service_results = event.get_analysis_results()

    args = {'service_list': service_list,
            'objects': objects,
            'relationships': relationships,
            'comments': comments,
            'favorite': favorite,
            'relationship': relationship,
            'subscription': subscription,
            'screenshots': screenshots,
            'event': event,
            'campaign_form': campaign_form,
            'service_results': service_results,
            'download_form': download_form,
            'EventACL': EventACL}

    return template, args

def generate_event_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Event
    type_ = "event"
    mapper = obj_type._meta['jtable_opts']
    if option == "jtlist":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']

        # filter list on relationship to given ObjectId
        query = {}
        if 'related' in request.GET:
            try:
                oid = ObjectId(request.GET.get('related'))
                query = {'relationships.value': oid}
            except:
                pass

        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request,
                                    includes=fields,
                                    query=query)
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
        'title': "Events",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits-%ss-views-%ss_listing' % (type_,
                                                            type_),
                           args=('jtlist',)),
        'deleteurl': reverse('crits-%ss-views-%ss_listing' % (type_,
                                                              type_),
                             args=('jtdelete',)),
        'searchurl': reverse('crits-%ss-views-%ss_listing' % (type_,
                                                              type_)),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    jtable = build_jtable(jtopts,request)
    jtable['toolbar'] = [
        {
            'tooltip': "'All Events'",
            'text': "'All'",
            'click': "function () {$('#event_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Events'",
            'text': "'New'",
            'click': "function () {$('#event_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Events'",
            'text': "'In Progress'",
            'click': "function () {$('#event_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Events'",
            'text': "'Analyzed'",
            'click': "function () {$('#event_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Events'",
            'text': "'Deprecated'",
            'click': "function () {$('#event_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add Event'",
            'text': "'Add Event'",
            'click': "function () {$('#new-event').click()}",
        },
    ]
    if option == "inline":
        return render(request, "jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_,
                                   'button' : '%ss_tab' % type_},
                                  )
    else:
        return render(request, "%s_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%s_listing' % type_},
                                  )

def generate_event_id(event):
    """
    Generate an Event ID.

    :param event: The event.
    :type event: :class:`crits.events.event.Event`
    :returns: `uuid.uuid4()`
    """

    return uuid.uuid4()

def add_new_event(title, description, event_type, source_name, source_method,
                  source_reference, source_tlp, date, user,
                  bucket_list=None, ticket=None, campaign=None, campaign_confidence=None,
                  related_id=None, related_type=None, relationship_type=None):
    """
    Add a new Event to CRITs.

    :param title: Event title.
    :type title: str
    :param description: Event description.
    :type description: str
    :param event_type: Event type.
    :type event_type: str
    :param source: The source which provided this information.
    :type source: str
    :param method: THe method of acquiring this information.
    :type method: str
    :param reference: Reference to this data.
    :type reference: str
    :param date: Date of acquiring this data.
    :type date: datetime.datetime
    :param user: The user adding this Event.
    :type user: str
    :param bucket_list: The bucket(s) to associate with this Event.
    :type: str
    :param ticket: Ticket to associate with this event.
    :type ticket: str
    :param related_id: ID of object to create relationship with
    :type related_id: str
    :param related_type: Type of object to create relationship with
    :type related_type: str
    :param relationship_type: Type of relationship to create.
    :type relationship_type: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    :param campaign: Campaign to associate with this Event
    :type campaign: str
    :param campaign_confidence: Confidence to associate with the Campaign
    :type campaign_confidence: str
    """

    if not source_name:
        return {'success': False, 'message': "Missing source information."}

    result = dict()
    event = Event()
    event.title = title
    event.description = description
    event.set_event_type(event_type)

    if user.check_source_write(source_name):
        s = create_embedded_source(source_name,
                                   reference=source_reference,
                                   method=source_method,
                                   tlp=source_tlp,
                                   analyst=user.username,
                                   date=date)
    else:
        return {"success": False,
                "message": "User does not have permission to add object \
                            using source %s." % source_name}
    event.add_source(s)

    valid_campaign_confidence = {
        'low': 'low',
        'medium': 'medium',
        'high': 'high'}
    valid_campaigns = {}
    for c in Campaign.objects(active='on'):
        valid_campaigns[c['name'].lower()] = c['name']

    if campaign:
        if isinstance(campaign, basestring) and len(campaign) > 0:
            if campaign.lower() not in valid_campaigns:
                result = {'success':False, 'message':'{} is not a valid campaign.'.format(campaign)}
            else:
                confidence = valid_campaign_confidence.get(campaign_confidence, 'low')
                campaign = EmbeddedCampaign(name=campaign,
                                                   confidence=confidence,
                                                   description="",
                                                   analyst=user.username,
                                                   date=datetime.datetime.now())
                event.add_campaign(campaign)

    if bucket_list:
        event.add_bucket_list(bucket_list, user.username)

    if ticket:
        event.add_ticket(ticket, user.username)

    related_obj = None
    if related_id:
        related_obj = class_from_id(related_type, related_id)
        if not related_obj:
            retVal['success'] = False
            retVal['message'] = 'Related Object not found.'
            return retVal

    try:
        event.save(username=user.username)

        if related_obj and event and relationship_type:
            relationship_type=RelationshipTypes.inverse(relationship=relationship_type)
            event.add_relationship(related_obj,
                                  relationship_type,
                                  analyst=user.username,
                                  get_rels=False)
            event.save(username=user.username)

        # run event triage
        event.reload()
        run_triage(event, user.username)

        message = ('<div>Success! Click here to view the new event: <a href='
                   '"%s">%s</a></div>' % (reverse('crits-events-views-view_event',
                                                  args=[event.id]),
                                          title))
        result = {'success': True,
                  'message': message,
                  'id': str(event.id),
                  'object': event}

    except ValidationError, e:
        result = {'success': False,
                  'message': e}
    return result

def event_remove(_id, username):
    """
    Remove an event from CRITs.

    :param _id: The ObjectId of the Event to remove.
    :type _id: str
    :param username: The user removing this Event.
    :type username: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    event = Event.objects(id=_id).first()
    if event:
        event.delete(username=username)
    return {'success':True}

def update_event_title(event_id, title, analyst):
    """
    Update event title.

    :param event_id: The ObjectId of the Event to update.
    :type event_id: str
    :param title: The new title.
    :type title: str
    :param analyst: The user updating this Event.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if not title:
        return {'success': False, 'message': "No title to change"}
    event = Event.objects(id=event_id).first()
    event.title = title
    try:
        event.save(username=analyst)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': e}

def update_event_type(event_id, type_, analyst):
    """
    Update event type.

    :param event_id: The ObjectId of the Event to update.
    :type event_id: str
    :param type_: The new type.
    :type type_: str
    :param analyst: The user updating this Event.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    if not type_:
        return {'success': False, 'message': "No event type to change"}
    event = Event.objects(id=event_id).first()
    event.set_event_type(type_)
    try:
        event.save(username=analyst)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': e}

def add_sample_for_event(event_id, data, analyst, filedata=None, filename=None,
                         md5=None, email_addr=None, inherit_sources=False):
    """
    Add a sample related to this Event.

    :param event_id: The ObjectId of the Event to associate with.
    :type event_id: str
    :param data: The form data.
    :type data: dict
    :param analyst: The user adding this Sample.
    :type analyst: str
    :param filedata: The sample data.
    :type filedata: file handle.
    :param filename: The name of the file.
    :type filename: str
    :param md5: The MD5 of the file.
    :type md5: str
    :param email_addr: Email address to which to email the sample
    :type email_addr: str
    :param inherit_sources: 'True' if Sample should inherit Event's Source(s)
    :type inherit_sources: bool
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    response = {'success': False,
                'message': 'Unknown error; unable to upload file.'}
    users_sources = user_sources(analyst)
    event = Event.objects(id=event_id, source__name__in=users_sources).first()
    if not event:
        return {'success': False,
                'message': "No matching event found"}
    source = data['source']
    reference = data['reference']
    file_format = data['file_format']
    campaign = data['campaign']
    confidence = data['confidence']
    bucket_list = data[form_consts.Common.BUCKET_LIST_VARIABLE_NAME]
    ticket = data[form_consts.Common.TICKET_VARIABLE_NAME]
    method = data['method']
    if filename:
        filename = filename.strip()

    # If selected, new sample inherits the campaigns of the related event.
    if data['inherit_campaigns']:
        if campaign:
            event.campaign.append(EmbeddedCampaign(name=campaign, confidence=confidence, analyst=analyst))
        campaign = event.campaign

    inherited_source = event.source if inherit_sources else None

    try:
        if filedata:
            result = handle_uploaded_file(filedata,
                                          source,
                                          method,
                                          reference,
                                          file_format,
                                          data['password'],
                                          analyst,
                                          campaign,
                                          confidence,
                                          related_id=event.id,
                                          related_type='Event',
                                          filename=filename,
                                          bucket_list=bucket_list,
                                          ticket=ticket,
                                          inherited_source=inherited_source)
        else:
            if md5:
                md5 = md5.strip().lower()
            result = handle_uploaded_file(None,
                                          source,
                                          method,
                                          reference,
                                          file_format,
                                          None,
                                          analyst,
                                          campaign,
                                          confidence,
                                          related_id=event.id,
                                          related_type='Event',
                                          filename=filename,
                                          md5=md5,
                                          bucket_list=bucket_list,
                                          ticket=ticket,
                                          inherited_source=inherited_source,
                                          is_return_only_md5=False)
    except ZipFileError, zfe:
        return {'success': False, 'message': zfe.value}
    else:
        if len(result) > 1:
            response = {'success': True, 'message': 'Files uploaded successfully. '}
        elif len(result) == 1:
            if not filedata:
                response['success'] = result[0].get('success', False)
                if(response['success'] == False):
                    response['message'] = result[0].get('message', response.get('message'))
                else:
                    result = [result[0].get('object').md5]
                    response['message'] = 'File uploaded successfully. '
            else:
                response = {'success': True, 'message': 'Files uploaded successfully. '}
        if not response['success']:
            return response
        else:
            if email_addr:
                for s in result:
                    email_errmsg = mail_sample(s, [email_addr])
                    if email_errmsg is not None:
                        response['success'] = False
                        msg = "<br>Error emailing sample %s: %s\n" % (s, email_errmsg)
                        response['message'] = response['message'] + msg
    return response
