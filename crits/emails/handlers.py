from __future__ import absolute_import

import datetime
import email as eml
from email.parser import Parser
from email.utils import parseaddr, getaddresses, mktime_tz, parsedate_tz
import hashlib
import json
import magic
import re
import yaml
import io
import sys
import olefile

from dateutil.parser import parse as date_parser
from django.conf import settings
from crits.core.forms import DownloadFileForm
from crits.emails.forms import EmailYAMLForm
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

from crits.campaigns.forms import CampaignForm
from crits.config.config import CRITsConfig
from crits.core.crits_mongoengine import json_handler, create_embedded_source
from crits.core.crits_mongoengine import EmbeddedCampaign
from crits.core.data_tools import clean_dict
from crits.core.exceptions import ZipFileError
from crits.core.handlers import class_from_id
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.user_tools import user_sources, is_admin, is_user_favorite
from crits.core.user_tools import is_user_subscribed
from crits.domains.handlers import get_valid_root_domain
from crits.emails.email import Email
from crits.indicators.handlers import handle_indicator_ind
from crits.indicators.indicator import Indicator
from crits.notifications.handlers import remove_user_from_notification
from crits.samples.handlers import handle_file, handle_uploaded_file, mail_sample
from crits.services.handlers import run_triage

from crits.vocabulary.relationships import RelationshipTypes
from crits.vocabulary.indicators import (
    IndicatorTypes,
    IndicatorAttackTypes,
    IndicatorThreatTypes
)

def create_email_field_dict(field_name,
                            field_type,
                            field_value,
                            field_displayed_text,
                            is_allow_create_indicator,
                            is_href,
                            is_editable,
                            is_email_list,
                            is_splunk,
                            href_search_field=None):
    """
    Generates a 1:1 dictionary from all of the input fields.

    Returns:
        A dictionary of all the input fields, with the input parameter names
        each as a key and its associated value as the value pair.
    """

    return {"field_name": field_name,
            "field_type": field_type,
            "field_value": field_value,
            "field_displayed_text": field_displayed_text,
            "is_allow_create_indicator": is_allow_create_indicator,
            "is_href": is_href,
            "is_editable": is_editable,
            "is_email_list": is_email_list,
            "is_splunk": is_splunk,
            "href_search_field": href_search_field
            }

def generate_email_csv(request):
    """
    Generate a CSV file of the Email information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request, Email)
    return response

def get_email_formatted(email_id, analyst, data_format):
    """
    Format an email in YAML or JSON.

    :param email_id: The ObjectId of the email.
    :type email_id: str
    :param analyst: The user requesting the data.
    :type analyst: str
    :param data_format: The format you want the data in.
    :type data_format: "json" or "yaml"
    :returns: :class:`django.http.HttpResponse`
    """

    sources = user_sources(analyst)
    email = Email.objects(id=email_id, source__name__in=sources).first()
    if not email:
        return HttpResponse(json.dumps({}), content_type="application/json")
    exclude = [
                "created",
                "source",
                "relationships",
                "schema_version",
                "campaign",
                "analysis",
                "bucket_list",
                "ticket",
                "releasability",
                "unsupported_attrs",
                "status",
                "objects",
                "modified",
                "analyst",
                "_id",
                "to",
                "cc",
                "raw_headers",
              ]
    if data_format == "yaml":
        data = {"email_yaml": email.to_yaml(exclude=exclude)}
    elif data_format == "json":
        data = {"email_yaml": email.to_json(exclude=exclude)}
    else:
        data = {"email_yaml": {}}
    return HttpResponse(json.dumps(data), content_type="application/json")

def get_email_detail(email_id, analyst):
    """
    Generate the email details page.

    :param email_id: The ObjectId of the email.
    :type email_id: str
    :param analyst: The user requesting the data.
    :type analyst: str
    :returns: tuple
    """

    template = None
    sources = user_sources(analyst)
    email = Email.objects(id=email_id, source__name__in=sources).first()
    if not email:
        template = "error.html"
        args = {'error': "ID does not exist or insufficient privs for source"}
    else:
        email.sanitize(username="%s" % analyst, sources=sources)
        update_data_form = EmailYAMLForm(analyst)
        campaign_form = CampaignForm()
        download_form = DownloadFileForm(initial={"obj_type": 'Email',
                                                  "obj_id":email_id})

        # remove pending notifications for user
        remove_user_from_notification("%s" % analyst, email.id, 'Email')

        # subscription
        subscription = {
                'type': 'Email',
                'id': email.id,
                'subscribed': is_user_subscribed("%s" % analyst, 'Email',
                                                 email.id),
        }

        # objects
        objects = email.sort_objects()

        # relationships
        relationships = email.sort_relationships("%s" % analyst, meta=True)

        # relationship
        relationship = {
                'type': 'Email',
                'value': email.id
        }

        # comments
        comments = {'comments': email.get_comments(),
                    'url_key': email.id}

        #screenshots
        screenshots = email.get_screenshots(analyst)

        # favorites
        favorite = is_user_favorite("%s" % analyst, 'Email', email.id)

        email_fields = []
        email_fields.append(create_email_field_dict(
                "from_address",  # field_name
                IndicatorTypes.EMAIL_FROM,  # field_type
                email.from_address,  # field_value
                "From",  # field_displayed_text
                # is_allow_create_indicator
                # is_href
                # is_editable
                # is_email_list
                # is_splunk
                True, True, True, False, True,
                href_search_field="from"  # href_search_field
                ))
        email_fields.append(create_email_field_dict(
                "sender",
                IndicatorTypes.EMAIL_SENDER,
                email.sender,
                "Sender",
                True, True, True, False, True,
                href_search_field="sender"
                ))
        email_fields.append(create_email_field_dict(
                "Email To",
                None,
                email.to,
                "To",
                False, True, True, True, False,
                href_search_field=None
                ))
        email_fields.append(create_email_field_dict(
                "cc",
                "Email CC",
                email.cc,
                "CC",
                False, True, True, True, False,
                href_search_field=None
                ))
        email_fields.append(create_email_field_dict(
                "date",
                "Email Date",
                email.date,
                "Date",
                False, False, True, False, False,
                href_search_field=None
                ))
        email_fields.append(create_email_field_dict(
                "isodate",
                "Email ISODate",
                email.isodate,
                "ISODate",
                False, False, False, False, False,
                href_search_field=None
                ))
        email_fields.append(create_email_field_dict(
                "subject",
                IndicatorTypes.EMAIL_SUBJECT,
                email.subject,
                "Subject",
                True, True, True, False, False,
                href_search_field="subject"
                ))
        email_fields.append(create_email_field_dict(
                "x_mailer",
                IndicatorTypes.EMAIL_X_MAILER,
                email.x_mailer,
                "X-Mailer",
                True, True, True, False, False,
                href_search_field="x_mailer"
                ))
        email_fields.append(create_email_field_dict(
                "reply_to",
                IndicatorTypes.EMAIL_REPLY_TO,
                email.reply_to,
                "Reply To",
                True, True, True, False, False,
                href_search_field="reply_to"
                ))
        email_fields.append(create_email_field_dict(
                "message_id",
                IndicatorTypes.EMAIL_MESSAGE_ID,
                email.message_id,
                "Message ID",
                True, False, True, False, False,
                href_search_field=None
                ))
        email_fields.append(create_email_field_dict(
                "helo",
                IndicatorTypes.EMAIL_HELO,
                email.helo,
                "helo",
                True, True, True, False, False,
                href_search_field="helo"
                ))
        email_fields.append(create_email_field_dict(
                "boundary",
                IndicatorTypes.EMAIL_BOUNDARY,
                email.boundary,
                "Boundary",
                True, False, True, False, False,
                href_search_field=None
                ))
        email_fields.append(create_email_field_dict(
                "originating_ip",
                IndicatorTypes.EMAIL_ORIGINATING_IP,
                email.originating_ip,
                "Originating IP",
                True, True, True, False, True,
                href_search_field="originating_ip"
                ))
        email_fields.append(create_email_field_dict(
                "x_originating_ip",
                IndicatorTypes.EMAIL_X_ORIGINATING_IP,
                email.x_originating_ip,
                "X-Originating IP",
                True, True, True, False, True,
                href_search_field="x_originating_ip"
                ))

        # analysis results
        service_results = email.get_analysis_results()

        args = {'objects': objects,
                'email_fields': email_fields,
                'relationships': relationships,
                'comments': comments,
                'favorite': favorite,
                'relationship': relationship,
                'screenshots': screenshots,
                'subscription': subscription,
                'email': email,
                'campaign_form': campaign_form,
                'download_form': download_form,
                'update_data_form': update_data_form,
                'admin': is_admin(analyst),
                'service_results': service_results,
                'rt_url': settings.RT_URL}
    return template, args

def generate_email_jtable(request, option):
    """
    Generate email jtable.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Email
    type_ = "email"
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
        if 'Records' in response:
            for doc in response['Records']:
                if doc['to']:
                    doc['recip'] = len(doc['to'].split(','))
                else:
                   doc['recip'] = 0
                if doc['cc']:
                    doc['recip'] += len(doc['cc'].split(','))
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type="application/json")
    if option == "jtdelete":
        response = {"Result": "ERROR"}
        if jtable_ajax_delete(obj_type, request):
            response = {"Result": "OK"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Emails",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                            type_), args=('jtlist',)),
        'deleteurl': reverse('crits.%ss.views.%ss_listing' % (type_,
                                                              type_), args=('jtdelete',)),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link'],
        'no_sort': mapper['no_sort']
    }
    jtable = build_jtable(jtopts, request)
    jtable['toolbar'] = [
        {
            'tooltip': "'All Emails'",
            'text': "'All'",
            'click': "function () {$('#email_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Emails'",
            'text': "'New'",
            'click': "function () {$('#email_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Emails'",
            'text': "'In Progress'",
            'click': "function () {$('#email_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Emails'",
            'text': "'Analyzed'",
            'click': "function () {$('#email_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Emails'",
            'text': "'Deprecated'",
            'click': "function () {$('#email_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add Email'",
            'text': "'Add Email'",
            'click': "function () {$('#new-email-fields').click()}",
        },
        {
            'tooltip': "'Upload Outlook Email'",
            'text': "'Upload .msg'",
            'click': "function () {$('#new-email-outlook').click()}",
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

def handle_email_fields(data, analyst, method, related_id=None, related_type=None, relationship_type=None):
    """
    Take email fields and convert them into an email object.

    :param data: The fields to include in the email.
    :type data: dict
    :param analyst: The user creating this email object.
    :type analyst: str
    :param method: The method of acquiring this email.
    :type method: str
    :returns: dict with keys:
              "status" (boolean),
              "object" The email object if successful,
              "reason" (str).
    """
    result = {
            'status': False,
            'reason': "",
            'object': None,
            'data': None
          }

    # Date and source are the only required ones.
    # If there is no campaign confidence, default it to low.
    # Remove these items from data so they are not added when merged.
    sourcename = data.get('source', None)
    del data['source']
    if data.get('source_method', None):
        method = method + " - " + data.get('source_method', None)
    try:
        del data['source_method']
    except:
        pass
    reference = data.get('source_reference', None)
    try:
        del data['source_reference']
    except:
        pass
    bucket_list = data.get('bucket_list', None)
    try:
        del data['bucket_list']
    except:
        pass
    ticket = data.get('ticket', None)
    try:
        del data['ticket']
    except:
        pass
    campaign = data.get('campaign', None)
    try:
        del data['campaign']
    except:
        pass
    confidence = data.get('campaign_confidence', 'low')
    try:
        del data['campaign_confidence']
    except:
        pass

    try:
        for x in ('cc', 'to'):
            y = data.get(x, None)
            if isinstance(y, basestring):
                if len(y) > 0:
                    tmp_y = y.split(',')
                    y_final = [ty.strip() for ty in tmp_y if len(ty.strip()) > 0]
                    data[x] = y_final
                else:
                    data[x] = []
            elif not y:
                data[x] = []
    except:
        pass

    new_email = Email()
    new_email.merge(data)
    if bucket_list:
        new_email.add_bucket_list(bucket_list, analyst)
    if ticket:
        new_email.add_ticket(ticket, analyst)
    new_email.source = [create_embedded_source(sourcename,
                                               reference=reference,
                                               method=method,
                                               analyst=analyst)]

    if campaign:
        ec = EmbeddedCampaign(name=campaign,
                              confidence=confidence,
                              description="",
                              analyst=analyst,
                              date=datetime.datetime.now())
        new_email.add_campaign(ec)


    new_email.save(username=analyst)

    # Relate the email to any other object 
    related_obj = None
    if related_id and related_type and relationship_type:
        related_obj = class_from_id(related_type, related_id)
        if not related_obj:
            retVal['success'] = False
            retVal['message'] = 'Related Object not found.'
            return retVal

    if related_obj:
        relationship_type=RelationshipTypes.inverse(relationship=relationship_type)
        new_email.add_relationship(related_obj,
                                          relationship_type,
                                          analyst=analyst,
                                          get_rels=False)

    try:
        new_email.save(username=analyst)
        new_email.reload()
        run_triage(new_email, analyst)
        result['object'] = new_email
        result['status'] = True
    except Exception, e:
        result['reason'] = "Failed to save object.\n<br /><pre>%s</pre>" % str(e)

    return result

def handle_json(data, sourcename, reference, analyst, method,
                save_unsupported=True, campaign=None, confidence=None,
                bucket_list=None, ticket=None):
    
    """
    Take email in JSON and convert them into an email object.

    :param data: The data for the email.
    :type data: dict
    :param sourcename: The name of the source providing this email.
    :type sourcename: str
    :param reference: The reference to the data from the source.
    :type reference: str
    :param analyst: The user creating this email object.
    :type analyst: str
    :param method: The method of acquiring this email.
    :type method: str
    :param save_unsupported: Save any unsupported fields instead of ignoring.
    :type save_unsupported: boolean
    :param campaign: The campaign to attribute to this email.
    :type campaign: str
    :param confidence: Confidence level of the campaign.
    :type confidence: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :returns: dict with keys:
              "status" (boolean),
              "object" The email object if successful,
              "data" the converted email data.
              "reason" (str).
    """

    result = {
            'status': False,
            'reason': "",
            'object': None,
            'data': None
          }

    try:
        converted = json.loads(data)
        if isinstance(converted, dict) == False:
            raise
    except Exception, e:
        result["reason"] = "Cannot convert data to JSON.\n<br /><pre>%s</pre>" % str(e)
        return result

    result['data'] = converted

    new_email = dict_to_email(result['data'], save_unsupported=save_unsupported)
    if bucket_list:
        new_email.add_bucket_list(bucket_list, analyst)
    if ticket:
        new_email.add_ticket(ticket, analyst)
    if campaign:
        if not confidence:
            confidence = "low"
        ec = EmbeddedCampaign(name=campaign,
                              confidence=confidence,
                              description="",
                              analyst=analyst,
                              date=datetime.datetime.now())
        new_email.add_campaign(ec)

    result['object'] = new_email

    result['object'].source = [create_embedded_source(sourcename,
                                                    reference=reference,
                                                    method=method,
                                                    analyst=analyst)]

    try:
        result['object'].save(username=analyst)
        result['object'].reload()
        run_triage(result['object'], analyst)
    except Exception, e:
        result['reason'] = "Failed to save object.\n<br /><pre>%s</pre>" % str(e)

    result['status'] = True
    return result

# if email_id is provided it is the existing email id to modify.
def handle_yaml(data, sourcename, reference, analyst, method, email_id=None,
                save_unsupported=True, campaign=None, confidence=None,
                bucket_list=None, ticket=None, related_id=None, 
                related_type=None, relationship_type=None):
    """
    Take email in YAML and convert them into an email object.

    :param data: The data for the email.
    :type data: dict
    :param sourcename: The name of the source providing this email.
    :type sourcename: str
    :param reference: The reference to the data from the source.
    :type reference: str
    :param analyst: The user creating this email object.
    :type analyst: str
    :param method: The method of acquiring this email.
    :type method: str
    :param email_id: The ObjectId of the existing email to update.
    :type email_id: str
    :param save_unsupported: Save any unsupported fields instead of ignoring.
    :type save_unsupported: boolean
    :param campaign: The campaign to attribute to this email.
    :type campaign: str
    :param confidence: Confidence level of the campaign.
    :type confidence: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :returns: dict with keys:
              "status" (boolean),
              "object" The email object if successful,
              "data" the converted email data.
              "reason" (str).
    """

    result = {
            'status': False,
            'reason': "",
            'object': None,
            'data': None
          }

    try:
        converted = yaml.load(data)
        if isinstance(converted, dict) == False:
            raise
    except Exception, e:
        result["reason"] = "Cannot convert data to YAML.\n<br /><pre>%s</pre>" % str(e)
        return result

    result['data'] = converted

    new_email = dict_to_email(result['data'], save_unsupported=save_unsupported)
    if bucket_list:
        new_email.add_bucket_list(bucket_list, analyst)
    if ticket:
        new_email.add_ticket(ticket, analyst)
    if campaign:
        if not confidence:
            confidence = "low"
        ec = EmbeddedCampaign(name=campaign,
                              confidence=confidence,
                              description="",
                              analyst=analyst,
                              date=datetime.datetime.now())
        new_email.add_campaign(ec)

    result['object'] = new_email

    if email_id:
        old_email = class_from_id('Email', email_id)
        if not old_email:
            result['reason'] = "Unknown email_id."
            return result
        # Can not merge with a source?
        # For now, just save the original source and put it back after merge.
        saved_source = old_email.source
        # XXX: If you use the "Edit YAML" button and edit the "from" field
        # it gets put into the new email object in dict_to_email() correctly
        # but calling to_dict() on that object results in a 'from' key being
        # put into the dictionary. Thus, the following line will result in
        # your new 'from' field being stuffed into unsupported_attrs.

        # old_email.merge(result['object'].to_dict(), True)

        # To work around this (for now) convert the new email object to a
        # dictionary and manually replace 'from' with the from_address
        # property.
        tmp = result['object'].to_dict()
        if 'from' in tmp:
            tmp['from_address'] = result['object'].from_address
        old_email.merge(tmp, True)
        old_email.source = saved_source
        try:
            old_email.save(username=analyst)
        except Exception, e:
            result['reason'] = "Failed to save object.\n<br /><pre>%s</pre>" % str(e)
            return result
    else:
        result['object'].source = [create_embedded_source(sourcename,
                                                        reference=reference,
                                                        method=method,
                                                        analyst=analyst)]

        result['object'].save(username=analyst)

        # Relate the email to any other object 
        related_obj = None
        if related_id and related_type and relationship_type:
            related_obj = class_from_id(related_type, related_id)
            if not related_obj:
                retVal['success'] = False
                retVal['message'] = 'Related Object not found.'
                return retVal

        if related_obj:
            relationship_type=RelationshipTypes.inverse(relationship=relationship_type)
            result['object'].add_relationship(related_obj,
                                              relationship_type,
                                              analyst=analyst,
                                              get_rels=False)
        try:
            result['object'].save(username=analyst)
            result['object'].reload()
            run_triage(result['object'], analyst)
        except Exception, e:
            result['reason'] = "Failed to save object.\n<br /><pre>%s</pre>" % str(e)
            return result

    result['status'] = True
    return result


def handle_msg(data, sourcename, reference, analyst, method, password='',
               campaign=None, confidence=None, bucket_list=None, ticket=None,
               related_id=None, related_type=None, relationship_type=None):
    """
    Take email in MSG and convert them into an email object.

    :param data: The data for the email.
    :type data: dict
    :param sourcename: The name of the source providing this email.
    :type sourcename: str
    :param reference: The reference to the data from the source.
    :type reference: str
    :param analyst: The user creating this email object.
    :type analyst: str
    :param method: The method of acquiring this email.
    :type method: str
    :param password: The password for the attachment.
    :type password: str
    :param campaign: The campaign to attribute to this email.
    :type campaign: str
    :param confidence: Confidence level of the campaign.
    :type confidence: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :returns: dict with keys:
              "status" (boolean),
              "obj_id" The email ObjectId if successful,
              "message" (str)
              "reason" (str).
    """
    response = {'status': False}

    result = parse_ole_file(data)

    if result.has_key('error'):
        response['reason'] = result['error']
        return response

    result['email']['source'] = sourcename
    result['email']['source_reference'] = reference
    result['email']['campaign'] = campaign
    result['email']['campaign_confidence'] = confidence
    result['email']['bucket_list'] = bucket_list
    result['email']['ticket'] = ticket

    if result['email'].has_key('date'):
        result['email']['isodate'] = date_parser(result['email']['date'],
                                                 fuzzy=True)

    obj = handle_email_fields(result['email'], analyst, method, 
                              related_id=related_id, related_type=related_type, relationship_type=relationship_type)

    if not obj["status"]:
        response['reason'] = obj['reason']
        return response

    email = obj.get('object')

    # Process attachments and upload as samples
    attach_messages = []
    for file in result['attachments']:
        type_ = file.get('type', '')
        if 'pkcs7' not in type_:
            mimetype = magic.from_buffer(file.get('data', ''), mime=True)
            if mimetype is None:
                file_format = 'raw'
            elif 'application/zip' in mimetype:
                file_format = 'zip'
            elif 'application/x-rar' in mimetype:
                file_format = 'rar'
            else:
                file_format = 'raw'
            try:
                cleaned_data = {'file_format': file_format,
                                'password': password}
                r = create_email_attachment(email, cleaned_data, analyst, sourcename,
                                        method, reference, campaign, confidence,
                                        "", "", file.get('data', ''), file.get('name', ''))
                if 'success' in r:
                    if not r['success']:
                        attach_messages.append("%s: %s" % (file.get('name', ''),
                                                         r['message']))
                    else:
                        attach_messages.append("%s: Added Successfully!" % file.get('name', ''))
            except BaseException:
                error_message = 'The email uploaded successfully, but there was an error\
                                uploading the attachment ' + file['name'] + '\n\n' + str(sys.exc_info())
                response['reason'] = error_message
                return response
        else:
            attach_messages.append('%s: Cannot decrypt attachment (pkcs7).' % file.get('name', ''))
    if len(attach_messages):
        response['message'] = '<br/>'.join(attach_messages)
    response['status'] = True
    response['obj_id'] = obj['object'].id
    return response

def handle_pasted_eml(data, sourcename, reference, analyst, method,
                      parent_type=None, parent_id=None, campaign=None,
                      confidence=None, bucket_list=None, ticket=None,
                      related_id=None, related_type=None, relationship_type=None):
    """
    Take email in EML and convert them into an email object.

    :param data: The data for the email.
    :type data: dict
    :param sourcename: The name of the source providing this email.
    :type sourcename: str
    :param reference: The reference to the data from the source.
    :type reference: str
    :param analyst: The user creating this email object.
    :type analyst: str
    :param method: The method of acquiring this email.
    :type method: str
    :param parent_type: The top-level object type of the parent.
    :type parent_type: str
    :param parent_id: The ObjectId of the parent.
    :type parent_id: str
    :param campaign: The campaign to attribute to this email.
    :type campaign: str
    :param confidence: Confidence level of the campaign.
    :type confidence: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :returns: dict with keys:
              "status" (boolean),
              "reason" (str),
              "object" The email object if successful,
              "data" the converted email data,
              "attachments" (dict).
    """

    # Try to fix headers where we lost whitespace indents
    # Split by newline, parse/fix headers, join by newline
    hfieldre = re.compile('^\S+:\s')
    boundaryre = re.compile('boundary="?([^\s"\']+)"?')
    emldata = []
    boundary = None
    isbody = False
    if not isinstance(data, basestring):
        data = data.read()
    for line in data.split("\n"):
        # We match the regex for a boundary definition
        m = boundaryre.search(line)
        if m:
            boundary = m.group(1)
        # content boundary exists and we reached it
        if boundary and boundary in line:
            isbody = True
        # If we are not in the body and see somethign that does not look
        # like a valid header field, prepend a space to attach this line
        # to the previous header we found
        if not isbody and not hfieldre.match(line):
            line = " %s" % line
        emldata.append(line)
    emldata = "\n".join(emldata)
    return handle_eml(emldata, sourcename, reference, analyst, method, parent_type,
                      parent_id, campaign, confidence, bucket_list, ticket, 
                      related_id=related_id, related_type=related_type, relationship_type=relationship_type)


def handle_eml(data, sourcename, reference, analyst, method, parent_type=None,
               parent_id=None, campaign=None, confidence=None, bucket_list=None,
               ticket=None, related_id=None, related_type=None, relationship_type=None):
    """
    Take email in EML and convert them into an email object.

    :param data: The data for the email.
    :type data: dict
    :param sourcename: The name of the source providing this email.
    :type sourcename: str
    :param reference: The reference to the data from the source.
    :type reference: str
    :param analyst: The user creating this email object.
    :type analyst: str
    :param method: The method of acquiring this email.
    :type method: str
    :param parent_type: The top-level object type of the parent.
    :type parent_type: str
    :param parent_id: The ObjectId of the parent.
    :type parent_id: str
    :param campaign: The campaign to attribute to this email.
    :type campaign: str
    :param confidence: Confidence level of the campaign.
    :type confidence: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :param related_id: ID of object to create relationship with
    :type related_id: str
    :param related_type: Type of object to create relationship with
    :type related_id: str
    :param relationship_type: Type of relationship to create.
    :type relationship_type: str
    :returns: dict with keys:
              "status" (boolean),
              "reason" (str),
              "object" The email object if successful,
              "data" the converted email data,
              "attachments" (dict).
    """

    result = {
            'status': False,
            'reason': "",
            'object': None,
            'data': None,
            'attachments': {}
          }
    if not sourcename:
        result['reason'] = "Missing source information."
        return result

    msg_import = {'raw_header': ''}
    reImap = re.compile(r"(\*\s\d+\sFETCH\s.+?\r\n)(.+)\).*?OK\s(UID\sFETCH\scompleted|Success)", re.M | re.S)

    # search for SMTP dialog
    start = data.find("DATA")
    end = data.find("\x0d\x0a\x2e\x0d\x0a")

    if start >= 0 and end >= 0:
        premail = data[:start]
        mailfrom = None
        rcptto = None
        for preheaders in premail.splitlines():
            mfpos = preheaders.find("MAIL FROM")
            if mfpos > -1:
                try:
                    mailfrom = unicode(preheaders[mfpos + 10:])
                except UnicodeDecodeError:
                    mailfrom = unicode(preheaders[mfpos + 10:], errors="replace")
            rcpos = preheaders.find("RCPT TO")
            if rcpos > -1:
                try:
                    rcptto = unicode(preheaders[rcpos + 9:])
                except UnicodeDecodeError:
                    rcptto = unicode(preheaders[rcpos + 9:], errors="replace")
        if mailfrom:
            msg_import['mailfrom'] = mailfrom
        if rcptto:
            msg_import['rcptto'] = rcptto
        mail1 = data[start + 6:end]
        stripped_mail = ""
        for line in mail1.splitlines(True):
            # Strip SMTP response codes. Some people like to grab a single
            # TCP session in wireshark and save it to disk and call it an EML.
            if line[:4] in ['200 ', '211 ', '214 ', '220 ', '221 ', '250 ',
                            '250-', '251 ', '354 ', '421 ', '450 ', '451 ',
                            '452 ', '500 ', '501 ', '502 ', '503 ', '504 ',
                            '521 ', '530 ', '550 ', '551 ', '552 ', '553 ',
                            '554 ']:
                continue
            stripped_mail += line
    else:
        # No SMTP dialog found, search for IMAP markers
        match = reImap.search(data)
        if match:
            stripped_mail = match.groups()[1]
        else:
            stripped_mail = data

    msg = eml.message_from_string(str(stripped_mail))

    if not msg.items():
        result['reason'] = """Could not parse email. Possibly the input does
                           not conform to a Internet Message style headers
                           and header continuation lines..."""
        return result

    # clean up headers
    for d in msg.items():
        cleand = ''.join([x for x in d[1] if (ord(x) < 127 and ord(x) >= 32)])
        msg_import[d[0].replace(".",
                                "").replace("$",
                                            "").replace("\x00",
                                                        "").replace("-",
                                                                    "_").lower()] = cleand
        msg_import['raw_header'] += d[0] + ": " + cleand + "\n"

    # Rip out anything that looks like an email address and store it.
    if 'to' in msg_import:
        to_list = re.findall(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}',
                             msg_import['to'])
        msg_import['to'] = []
        msg_import['to'] = [i for i in to_list if i not in msg_import['to']]

    # Parse the body of the email
    msg_import["raw_body"] = ""
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get_content_maintype() == "text":
            content = part.get_payload(decode=True)
            if content:
                try:
                    message_part = unicode(content)
                except UnicodeDecodeError:
                    message_part = unicode(content, errors="replace")

                msg_import["raw_body"] = msg_import["raw_body"] + \
                                         message_part + "\n"

        # Check for attachment in mail parts
        filename = part.get_filename()
        attach = part.get_payload(decode=True)
        if attach is not None and len(attach):
            md5 = hashlib.md5(attach).hexdigest()
            mtype = magic.from_buffer(attach)

            if filename is not None:
                try:
                    filename = unicode(filename)
                except UnicodeDecodeError:
                    filename = unicode(filename, errors="replace")
            else:
                filename = md5

            result['attachments'][md5] = {
                                           'filename': filename,
                                           'magic': mtype,
                                           'blob': attach
                                         }

    result['data'] = msg_import

    new_email = dict_to_email(result['data'])
    if bucket_list:
        new_email.add_bucket_list(bucket_list, analyst)
    if ticket:
        new_email.add_ticket(ticket, analyst)
    if campaign:
        if not confidence:
            confidence = "low"
        ec = EmbeddedCampaign(name=campaign,
                              confidence=confidence,
                              description="",
                              analyst=analyst,
                              date=datetime.datetime.now())
        new_email.add_campaign(ec)

    result['object'] = new_email

    result['object'].source = [create_embedded_source(sourcename,
                                                      reference=reference,
                                                      method=method,
                                                      analyst=analyst)]

    # Save the Email first, so we can have the id to use to create
    # relationships.
    if not result['object'].date:
        result['object'].date = None
    try:
        result['object'].save(username=analyst)
        result['object'].reload()
        run_triage(result['object'], analyst)
    except Exception, e:
        result['reason'] = "Failed1 to save email.\n<br /><pre>" + \
            str(e) + "</pre>"
        return result

    # Relate the email back to the pcap, if it came from PCAP.
    if parent_id and parent_type:
        rel_item = class_from_id(parent_type, parent_id)
        if rel_item:
            rel_type = RelationshipTypes.CONTAINED_WITHIN
            ret = result['object'].add_relationship(rel_item,
                                                    rel_type,
                                                    analyst=analyst,
                                                    get_rels=False)
            if not ret['success']:
                result['reason'] = "Failed to create relationship.\n<br /><pre>"
                + result['message'] + "</pre>"
            return result

        # Save the email again since it now has a new relationship.
        try:
            result['object'].save(username=analyst)
        except Exception, e:
            result['reason'] = "Failed to save email.\n<br /><pre>"
            + str(e) + "</pre>"
            return result

    # Relate the email to any other object 
    related_obj = None
    if related_id and related_type and relationship_type:
        related_obj = class_from_id(related_type, related_id)
        if not related_obj:
            retVal['success'] = False
            retVal['message'] = 'Related Object not found.'
            return retVal

    if related_obj:
        relationship_type=RelationshipTypes.inverse(relationship=relationship_type)
        result['object'].add_relationship(related_obj,
                                          relationship_type,
                                          analyst=analyst,
                                          get_rels=False)
        #result['object'].save(username=analyst)

        # Save the email again since it now has a new relationship.
        try:
            result['object'].save(username=analyst)
        except Exception, e:
            result['reason'] = "Failed to save email.\n<br /><pre>"
            + str(e) + "</pre>"
            return result


    for (md5_, attachment) in result['attachments'].items():
        if handle_file(attachment['filename'],
                       attachment['blob'],
                       sourcename,
                       method='eml_processor',
                       reference=reference,
                       related_id=result['object'].id,
                       user=analyst,
                       md5_digest=md5_,
                       related_type='Email',
                       campaign=campaign,
                       confidence=confidence,
                       bucket_list=bucket_list,
                       ticket=ticket,
                       relationship=RelationshipTypes.CONTAINED_WITHIN) == None:
            result['reason'] = "Failed to save attachment.\n<br /><pre>"
            + md5_ + "</pre>"
            return result

    result['status'] = True
    return result

def dict_to_email(d, save_unsupported=True):
    """
    Convert a dictionary to an email.
    Standardize all key names:
    - Convert hyphens and whitespace to underscores
    - Remove all non-alphanumeric and non-underscore characters.
    - Combine multiple underscores.
    - convert alpha characters to lowercase.

    :param d: The dictionary to convert.
    :type d: dict
    :param save_unsupported: Whether or not to save unsupported fields.
    :type save_unsupported: boolean
    :returns: :class:`crits.email.email.Email`
    """

    for key in d:
        newkey = re.sub('[\s-]', '_', key)
        newkey = re.sub('[\W]', '', newkey)
        newkey = re.sub('_+', '_', newkey)
        newkey = newkey.lower()
        if key != newkey:
            d[newkey] = d[key]
            del d[key]

    # Remove keys which we don't want the user to modify via YAML.
    keys = ('schema_version', 'comments', 'objects', 'campaign',
            'relationships', 'source', 'releasability', 'analysis',
            'bucket_list', 'ticket', 'objects')

    clean_dict(d, keys)

    if 'x_originating_ip' in d and d['x_originating_ip']:
        d['x_originating_ip'] = re.findall(r'[0-9]+(?:\.[0-9]+){3}',
                                           d['x_originating_ip'])[0]

    if 'date' in d and d['date']:
        if isinstance(d['date'], datetime.datetime):
            d['isodate'] = d['date']
            d['date'] = str(d['date'])
        else:
            d['isodate'] = date_parser(d['date'], fuzzy=True)

    if 'to' in d and isinstance(d['to'], basestring) and len(d['to']) > 0:
        d['to'] = [d['to']]

    if 'cc' in d and isinstance(d['cc'], basestring) and len(d['cc']) > 0:
        d['cc'] = [d['cc']]

    if 'from' in d:
        d['from_address'] = d['from']
        del d['from']

    if save_unsupported:
        for (k, v) in d.get('unsupported_attrs', {}).items():
            d[k] = v

    if 'unsupported_attrs' in d:
        del d['unsupported_attrs']

    crits_email = Email()
    crits_email.merge(d)
    return crits_email

def update_email_header_value(email_id, type_, value, analyst):
    """
    Update a header value for an email.

    :param email_id: The ObjectId of the email to update.
    :type email_id: str
    :param type_: The header type.
    :type type_: str
    :param value: The header value.
    :type value: str
    :param analyst: The user updating the header field.
    :type analyst: str
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
              "isodate" (datetime.datetime) if the header field was "date".
    """

    if type_ in ('to', 'cc'):
        bad_chars = "<>^&(){}[]!#$%=+;:'/\|?~`"
        if any((bad_char in value) for bad_char in bad_chars):
            return {'success': False, 'message': "Invalid characters in list"}
    email = Email.objects(id=email_id).first()
    if email:
        try:
            if type_ in ('to', 'cc'):
                vlist = value.split(",")
                vfinal = []
                for v in vlist:
                    if len(v.strip()) > 0:
                        vfinal.append(v.strip())
                value = vfinal
            setattr(email, type_, value)
            if type_ == 'date':
                isodate = date_parser(value, fuzzy=True)
                email.isodate = isodate
            email.save(username=analyst)
            if type_ == 'date':
                result = {'success': True,
                          'message': "Successfully updated email",
                          'isodate': email.isodate.strftime("%Y-%m-%d %H:%M:%S.%f")}
            elif type_ in ('to', 'cc'):
                links = ""
                for v in value:
                    # dirty ugly hack to "urlencode" the resulting URL
                    url = reverse('crits.targets.views.target_info',
                                  args=[v]).replace('@', '%40')
                    links += '<a href="%s">%s</a>, ' % (url, v)
                result = {'success': True,
                          'message': "Successfully updated email",
                          'links': links}
            else:
                result = {'success': True,
                          'message': "Successfully updated email"}
        except Exception, e:
            result = {'success': False, 'message': e}
    else:
        result = {'success': False, 'message': "Could not find email"}
    return result

def create_indicator_from_header_field(email, header_field, ind_type,
                                       analyst, request):
    """
    Create an indicator out of the header field.

    :param email: The email to get the header from.
    :type email: :class:`crits.emails.email.Email`
    :param header_field: The header type.
    :type header_field: str
    :param ind_type: The Indicator type to use.
    :type ind_type: str
    :param analyst: The user updating the header field.
    :type analyst: str
    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: dict with keys:
              "success" (boolean),
              "message" (str),
    """

    value = getattr(email, header_field)

    # Check to make sure the "value" is valid
    if value == None or value.strip() == "":
        result = {
            'success':  False,
            'message':  "Can't create indicator from email field [" +
                        str(header_field) + "] with an empty value field",
        }
        return result
    elif ind_type == None or ind_type.strip() == "":
        result = {
            'success':  False,
            'message':  "Can't create indicator from email field " +
                        "with an empty type field",
        }
        return result

    newindicator = handle_indicator_ind(value,
                                        email.source,
                                        ind_type,
                                        threat_type=IndicatorThreatTypes.UNKNOWN,
                                        attack_type=IndicatorAttackTypes.UNKNOWN,
                                        analyst=analyst)
    if newindicator.get('objectid'):
        indicator = Indicator.objects(id=newindicator['objectid']).first()
        results = email.add_relationship(indicator,
                                         RelationshipTypes.RELATED_TO,
                                         analyst=analyst,
                                         get_rels=True)
        if results['success']:
            email.save(username=analyst)
            relationship = {'type': 'Email', 'value': email.id}
            message = render_to_string('relationships_listing_widget.html',
                                        {'relationship': relationship,
                                        'relationships': results['message']},
                                        RequestContext(request))
            result = {'success': True, 'message': message}
        else:
            result = {
                'success':  False,
                'message':  "Error adding relationship: %s" % results['message']
            }
    else:
        result = {
            'success':  False,
            'message':  "Error adding relationship: Could not find email/indicator",
        }

    return result

def create_email_attachment(email, cleaned_data, analyst, source, method="Upload",
                            reference="", campaign=None, confidence='low',
                            bucket_list=None, ticket=None, filedata=None,
                            filename=None, md5=None, email_addr=None, inherit_sources=False):
    """
    Create an attachment for an email.

    :param email: The email to use.
    :type email: :class:`crits.emails.email.Email`
    :param cleaned_data: Cleaned form information about the email.
    :type cleaned_data: dict
    :param analyst: The user creating this attachment.
    :type analyst: str
    :param source: The name of the source.
    :type source: str
    :param method: The method for this file upload.
    :type method: str
    :param reference: The source reference.
    :type reference: str
    :param campaign: The campaign to attribute to this attachment.
    :type campaign: str
    :param confidence: The campaign confidence.
    :type confidence: str
    :param bucket_list: The list of buckets to assign to this attachment.
    :type bucket_list: str
    :param ticket: The ticket to assign to this attachment.
    :type ticket: str
    :param filedata: The attachment.
    :type filedata: request file data.
    :param filename: The name of the file.
    :type filename: str
    :param md5: The MD5 of the file.
    :type md5: str
    :param email_addr: Email address to which to email the sample
    :type email_addr: str
    :param inherit_sources: 'True' if attachment should inherit Email's Source(s)
    :type inherit_sources: bool
    :returns: dict with keys "success" (boolean) and "message" (str).
    """

    response = {'success': False,
                'message': 'Unknown error; unable to upload file.'}
    if filename:
        filename = filename.strip()

    # If selected, new sample inherits the campaigns of the related email.
    if cleaned_data.get('inherit_campaigns'):
        if campaign:
            email.campaign.append(EmbeddedCampaign(name=campaign, confidence=confidence, analyst=analyst))
        campaign = email.campaign

    inherited_source = email.source if inherit_sources else None

    try:
        if filedata:
            result = handle_uploaded_file(filedata,
                                          source,
                                          method,
                                          reference,
                                          cleaned_data['file_format'],
                                          cleaned_data['password'],
                                          analyst,
                                          campaign,
                                          confidence,
                                          related_id=email.id,
                                          related_type='Email',
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
                                          cleaned_data['file_format'],
                                          None,
                                          analyst,
                                          campaign,
                                          confidence,
                                          related_id=email.id,
                                          related_type='Email',
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

def parse_ole_file(file):
    """
    Parse an OLE2.0 file to obtain data inside an email including attachments.

    References:
    http://www.fileformat.info/format/outlookmsg/
    http://www.decalage.info/en/python/olefileio
    https://code.google.com/p/pyflag/source/browse/src/FileFormats/OLE2.py
    http://cpansearch.perl.org/src/MVZ/Email-Outlook-Message-0.912/lib/Email/Outlook/Message.pm
    """

    header = file.read(len(olefile.MAGIC))

    # Verify the file is in OLE2 format first
    if header != olefile.MAGIC:
        return {'error': 'The upload file is not a valid Outlook file. It must be in OLE2 format (.msg)'}

    msg = {'subject': '_0037',
           'body': '_1000',
           'header': '_007D',
           'message_class': '_001A',
           'recipient_email': '_39FE',
           'attachment_name': '_3707',
           'attachment_data': '_3701',
           'attachment_type': '_370E',
    }

    file.seek(0)
    data = file.read()
    msg_file = io.BytesIO(data)
    ole = olefile.OleFileIO(msg_file)

    # Helper function to grab data out of stream objects
    def get_stream_data(entry):
        stream = ole.openstream(entry)
        data = stream.read()
        stream.close()
        return data

    # Parse the OLE streams and get attachments, subject, body, headers, and class
    # The email dict is what will be put into MongoDB for CRITs
    attachments = {}
    email = {}
    email['to'] = []
    for entry in ole.listdir():
        if 'attach' in entry[0]:
            # Attachments are keyed by directory entry in the stream
            # e.g. '__attach_version1.0_#00000000'
            if entry[0] not in attachments:
                attachments[entry[0]] = {}
            if msg['attachment_name'] in entry[-1]:
                attachments[entry[0]].update({'name': get_stream_data(entry).decode('utf-16')})
            if msg['attachment_data'] in entry[-1]:
                attachments[entry[0]].update({'data': get_stream_data(entry)})
            if msg['attachment_type'] in entry[-1]:
                attachments[entry[0]].update({'type': get_stream_data(entry).decode('utf-16')})
        else:
            if msg['subject'] in entry[-1]:
                email['subject'] = get_stream_data(entry).decode('utf-16')
            if msg['body'] in entry[-1]:
                email['raw_body'] = get_stream_data(entry).decode('utf-16')
            if msg['header'] in entry[-1]:
                email['raw_header'] = get_stream_data(entry).decode('utf-16')
            if msg['recipient_email'] in entry[-1]:
                email['to'].append(get_stream_data(entry).decode('utf-16').lower())
            if msg['message_class'] in entry[-1]:
                message_class = get_stream_data(entry).decode('utf-16').lower()
    ole.close()

    # Process headers to extract data
    headers = Parser().parse(io.StringIO(email.get('raw_header', '')), headersonly=True)
    email['from_address'] = headers.get('From', '')
    email['reply_to'] = headers.get('Reply-To', '')
    email['date'] = headers.get('Date', '')
    email['message_id'] = headers.get('Message-ID', '')
    email['x_mailer'] = headers.get('X-Mailer', '')
    email['x_originating_ip'] = headers.get('X-Originating-IP', '')
    email['sender'] = getaddresses(headers.get_all('Sender', '')) # getaddresses returns list [(name, email)]

    # If no sender, set the email address found in From:
    if not email['sender']:
        email['sender'] = getaddresses(headers.get_all('From', ''))
    if len(email['sender']) > 0:
        email['sender'] = email['sender'][0][1]
    else:
        email['sender'] = ''

    # Get list of recipients and add to email['to'] if not already there
    # Some emails do not have a stream for recipients (_39FE)
    to = headers.get_all('To', [])
    cc = headers.get_all('CC', [])
    resent_to = headers.get_all('Resent-To', [])
    resent_cc = headers.get_all('Resent-CC', [])
    recipients = getaddresses(to + cc + resent_to + resent_cc)
    for r in recipients:
        addr = r[1].lower()
        # If BCC then addr could be blank or set to undisclosed-recipients:
        if addr and addr not in email['to'] and not re.match(r'^undisclosed-recipients[:;]?(?::;)?$', addr):
            email['to'].append(addr)

    # Check for encrypted and signed messages. The body will be empty in this case
    # Message classes: http://msdn.microsoft.com/en-us/library/ee200767%28v=exchg.80%29.aspx
    if message_class == 'ipm.note.smime' and not email.has_key('raw_body'):
        email['raw_body'] = '<ENCRYPTED>'
    if message_class == 'ipm.note.smime.multipartsigned' and not email.has_key('raw_body'):
        email['raw_body'] = '<DIGITALLY SIGNED: body in smime.p7m>'

    # Parse Received headers to get Helo and X-Originating-IP
    # This can be unreliable since Received headers can be reordered by gateways
    # and the date may not be in sync between systems. This is best effort based
    # on the date as it appears in the Received header. In some cases there is no
    # Received header present
    #
    # Received: from __ by __ with __ id __ for __ ; date
    #
    # See helper functions _get_received_from, _get_received_by, _get_received_date
    current_datetime = datetime.datetime.now()
    earliest_helo_date = current_datetime
    earliest_ip_date = current_datetime
    email['helo'] = ''
    originating_ip = ''
    last_from = ''
    helo_for = ''
    all_received = headers.get_all('Received')
    crits_config = CRITsConfig.objects().first()
    if crits_config:
        email_domain = get_valid_root_domain(crits_config.crits_email.split('@')[-1])[0]
    else:
        email_domain = ''

    if all_received:
        for received in all_received:
            received_from = _get_received_from(received).lower() # from __
            received_by = _get_received_by(received).lower() # by __ with __ id __
            received_for = _get_received_for(received).lower() # for <email>
            date = _get_received_date(received) # date
            try:
                current_date = datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(date))) # rfc2822 -> Time -> Datetime
            except:
                # Exception will occur if the date is not in the Received header. This could be
                # where the originating IP is. e.g. Received: from 11.12.13.14 by rms-us019 with HTTP
                current_date = datetime.datetime.min

            grp = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', received_from)
            if grp and not _is_reserved_ip(grp.group()) and ' localhost ' not in received_from:
                if email_domain not in received_from and email_domain in received_by:
                    if(current_date < earliest_helo_date):
                        helo_for = parseaddr(received_for.strip())[1]
                        earliest_helo_date = current_date
                        email['helo'] = received_from
                else:
                    last_from = received_from


            if grp and not email['x_originating_ip'] and not _is_reserved_ip(grp.group()):
                if current_date < earliest_ip_date:
                    earliest_ip_date = current_date
                    originating_ip = grp.group()

    # If no proper Helo found, just use the last received_from without a reserved IP
    if not email['helo']:
        email['helo'] = last_from

    # Set the extracted originating ip. If not found, then just use the IP from Helo
    if not email['x_originating_ip']:
        if originating_ip:
            email['x_originating_ip'] = originating_ip
        else:
            grp = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', email['helo'])
            if grp:
                email['x_originating_ip'] = grp.group()

    # Add the email address found in Helo
    if helo_for and '@' in helo_for:
        if helo_for not in email['to']:
            email['to'].append(helo_for)

    # If no Helo date found, then try to use the Date field
    if earliest_helo_date == current_datetime and email['date']:
        earliest_helo_date = datetime.datetime.fromtimestamp(mktime_tz(parsedate_tz(email['date'])))

    return {'email': email, 'attachments': attachments.values(), 'received_date': earliest_helo_date}

def _get_received_from(received_header):
    """
    Helper function to grab the 'from' part of a Received email header.
    """

    received_header = received_header.replace('\r', '').replace('\n', '')
    info = received_header.split('by ')
    try:
        return info[0]
    except:
        ''
def _get_received_by(received_header):
    """
    Helper function to grab the 'by' part of a Received email header.
    """

    received_header = received_header.replace('\r', '').replace('\n', '')
    info = received_header.split('by ')
    try:
        return info[-1].split('for ')[0]
    except:
        return ''

def _get_received_for(received_header):
    """
    Helper function to grab the 'for' part of a Received email header
    WARNING: If 'for' is not there, the entire Received header is returned.
    """

    received_header = received_header.replace('\r', '').replace('\n', '')
    info = received_header.split('for ')
    try:
        return info[-1].split(';')[0]
    except:
        return ''

def _get_received_date(received_header):
    """
    Helper function to grab the date part of a Received email header.
    """

    received_header = received_header.replace('\r', '').replace('\n', '')
    date = received_header.split(';')
    try:
        return date[-1]
    except:
        ''
def _is_reserved_ip(ip):
    """
    Simple test to detect if an IP is private or loopback. Does not check
    validity of the address.
    """

    grp = re.match(r'127.\d{1,3}.\d{1,3}.\d{1,3}', ip) # 127.0.0.0/8
    if grp:
        return True
    grp = re.match(r'10.\d{1,3}.\d{1,3}.\d{1,3}', ip) # 10.0.0.0/8
    if grp:
        return True
    grp = re.match(r'192.168.\d{1,3}.\d{1,3}', ip) # 192.168.0.0/16
    if grp:
        return True
    grp = re.match(r'172.(1[6-9]|2[0-9]|3[0-1]).\d{1,3}.\d{1,3}', ip) # 172.16.0.0/12
    if grp:
        return True
    # No matches
    return False
