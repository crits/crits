import copy
import crits.service_env
import json
import logging
import os
import pprint
import subprocess
import tempfile, shutil
import time

from bson.objectid import ObjectId
from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from hashlib import md5
from mongoengine.base import ValidationError

from crits.campaigns.forms import CampaignForm
from crits.core import form_consts
from crits.core.class_mapper import class_from_value, class_from_id
from crits.core.crits_mongoengine import EmbeddedSource, EmbeddedCampaign
from crits.core.crits_mongoengine import json_handler, create_embedded_source
from crits.core.data_tools import convert_string_to_bool, validate_md5_checksum
from crits.core.exceptions import ZipFileError
from crits.core.forms import DownloadFileForm
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.handlers import csv_export
from crits.core.handsontable_tools import convert_handsontable_to_rows, parse_bulk_upload
from crits.core.mongo_tools import get_file
from crits.core.source_access import SourceAccess
from crits.core.user_tools import is_admin, user_sources, get_user_organization
from crits.core.user_tools import is_user_subscribed, is_user_favorite
from crits.notifications.handlers import remove_user_from_notification
from crits.objects.handlers import object_array_to_dict
from crits.objects.handlers import validate_and_add_new_handler_object
from crits.samples.backdoor import Backdoor
from crits.samples.exploit import Exploit
from crits.samples.forms import BackdoorForm, ExploitForm, XORSearchForm
from crits.samples.forms import UnrarSampleForm, UploadFileForm
from crits.samples.sample import Sample
from crits.samples.yarahit import YaraHit
from crits.services.handlers import run_triage
from crits.stats.handlers import generate_yara_hits

logger = logging.getLogger(__name__)


def generate_sample_csv(request):
    """
    Generate a CSV file of the Sample information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request, Sample)
    return response


def get_sample_details(sample_md5, analyst, format_=None):
    """
    Generate the data to render the Sample details template.

    :param sample_md5: The MD5 of the Sample to get details for.
    :type sample_md5: str
    :param analyst: The user requesting this information.
    :type analyst: str
    :param format_: The format of the details page.
    :type format_: str
    :returns: template (str), arguments (dict)
    """

    template = None
    sources = user_sources(analyst)
    sample = Sample.objects(md5=sample_md5,
                            source__name__in=sources).first()
    if not sample:
        return ('error.html', {'error': "File not yet available or you do not have access to view it."})
    sample.sanitize_sources(username=analyst)
    if format_:
        exclude = [
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
                    "_id"
                  ]
        if format_ == "yaml":
            data = sample.to_yaml(exclude)
            return "yaml", data
        if format_ == "json":
            data = sample.to_json(exclude)
            return "json", data

    if not sample:
        template = "error.html"
        args = {'error': "No sample found"}
    elif format_ == "text":
        template = "samples_detail_text.html"
        args = {'sample': sample}
    else:
        #create forms
        backdoor_form = BackdoorForm()
        exploit_form = ExploitForm()
        xor_search_form = XORSearchForm()
        campaign_form = CampaignForm()
        unrar_sample_form = UnrarSampleForm()
        download_form = DownloadFileForm(initial={"obj_type":'Sample',
                                                    "obj_id":sample.id,
                                                    "meta_format": "none"})

        # do we have the binary?
        if isinstance(sample.filedata.grid_id, ObjectId):
            binary_exists = 1
        else:
            binary_exists = 0

        sample.sanitize("%s" % analyst)

        # remove pending notifications for user
        remove_user_from_notification("%s" % analyst, sample.id, 'Sample')

        # subscription
        subscription = {
                'type': 'Sample',
                'id': sample.id,
                'subscribed': is_user_subscribed("%s" % analyst,
                                                'Sample',
                                                sample.id),
        }

        #objects
        objects = sample.sort_objects()

        #relationships
        relationships = sample.sort_relationships("%s" % analyst,
                                                meta=True)

        # relationship
        relationship = {
                'type': 'Sample',
                'value': sample.id
        }

        #comments
        comments = {'comments': sample.get_comments(),
                    'url_key': sample_md5}

        #screenshots
        screenshots = sample.get_screenshots(analyst)

        # favorites
        favorite = is_user_favorite("%s" % analyst, 'Sample', sample.id)

        # services
        manager = crits.service_env.manager
        service_list = manager.get_supported_services('Sample', binary_exists)

        args = {'objects': objects,
                'relationships': relationships,
                'comments': comments,
                'relationship': relationship,
                'subscription': subscription,
                'sample': sample, 'sources': sources,
                'backdoor_form': backdoor_form,
                'exploit_form': exploit_form,
                'campaign_form': campaign_form,
                'download_form': download_form,
                'xor_search_form': xor_search_form,
                'unrar_sample_form': unrar_sample_form,
                'binary_exists': binary_exists,
                'favorite': favorite,
                'screenshots': screenshots,
                'service_list': service_list}

    return template, args

def generate_sample_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Sample
    type_ = "sample"
    mapper = obj_type._meta['jtable_opts']
    if option == "jtlist":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        fields = mapper['fields']
        response = jtable_ajax_list(obj_type, details_url, details_url_key,
                                    request, includes=fields)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    if option == "jtlist_by_org":
        # Sets display url
        details_url = mapper['details_url']
        details_url_key = mapper['details_url_key']
        get_values = request.GET.copy()
        get_values['source'] = get_user_organization("%s" % request.user.username)
        request.GET = get_values
        fields = mapper['fields']
        response = jtable_ajax_list(obj_type,details_url,details_url_key,
                                    request, includes=fields)
        return HttpResponse(json.dumps(response, default=json_handler),
                            content_type="application/json")
    if option == "jtdelete":
        response = {"Result": "ERROR"}
        if jtable_ajax_delete(obj_type,request):
            response = {"Result": "OK"}
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Samples",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.%ss.views.%ss_listing' %
                           (type_, type_), args=('jtlist',)),
        'deleteurl': reverse('crits.%ss.views.%ss_listing' %
                             (type_, type_), args=('jtdelete',)),
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
            'tooltip': "'All Samples'",
            'text': "'All'",
            'click': "function () {$('#sample_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Samples'",
            'text': "'New'",
            'click': "function () {$('#sample_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Samples'",
            'text': "'In Progress'",
            'click': "function () {$('#sample_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Samples'",
            'text': "'Analyzed'",
            'click': "function () {$('#sample_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Samples'",
            'text': "'Deprecated'",
            'click': "function () {$('#sample_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add Sample'",
            'text': "'Add Sample'",
            'click': "function () {$('#new-sample').click()}",
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

def generate_backdoor_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Backdoor
    type_ = "backdoor"
    if option == "jtlist":
        # Sets display url
        details_url = 'crits.samples.views.samples_listing'
        details_url_key = "name"
        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request)
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
        'title': "Backdoors",
        'default_sort': "sample_count DESC",
        'listurl': reverse('crits.samples.views.%ss_listing' % (type_,),
                           args=('jtlist',)),
        'deleteurl': reverse('crits.samples.views.%ss_listing' % (type_,),
                             args=('jtdelete',)),
        'searchurl': reverse('crits.samples.views.%ss_listing' % (type_,)),
        'fields': ["name","sample_count","_id"],
        'hidden_fields': [],
        'linked_fields': []
    }
    jtable = build_jtable(jtopts,request)

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

def generate_yarahit_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    refresh = request.GET.get("refresh", "no")
    if refresh == "yes":
        generate_yara_hits()
    obj_type = YaraHit
    type_ = "yarahit"
    if option == "jtlist":
        # Sets display url
        details_url = 'crits.samples.views.samples_listing'
        details_url_key = "detectexact"
        response = jtable_ajax_list(obj_type,
                                    details_url,
                                    details_url_key,
                                    request)
        return HttpResponse(json.dumps(response,
                                       default=json_handler),
                            content_type="application/json")
    jtopts = {
        'title': "Yara Hits",
        'default_sort': "result ASC",
        'listurl': reverse('crits.samples.views.%ss_listing' % (type_,),
                           args=('jtlist',)),
        'deleteurl': "",
        'searchurl': reverse('crits.samples.views.%ss_listing' % (type_,)),
        'fields': ["result", "engine", "version", "sample_count","_id"],
        'hidden_fields': ["_id"],
        'linked_fields': []
    }
    jtable = build_jtable(jtopts,request)
    jtable['toolbar'] = [
        {
            'tooltip': "'Refresh Yara Hits'",
            'text': "'Refresh Stats'",
            'click': "function () {$.get('"+reverse('crits.samples.views.%ss_listing' % type_)+"', {'refresh': 'yes'}, function () { $('#yarahits_listing').jtable('reload');});}"
        },
    ]

    if option == "inline":
        return render_to_response("jtable.html",
                                  {'jtable': jtable,
                                   'jtid': '%ss_listing' % type_,
                                   'button' : '%ss_button' % type_},
                                  RequestContext(request))
    else:
        return render_to_response("%ss_listing.html" % type_,
                                  {'jtable': jtable,
                                   'jtid': '%ss_listing' % type_},
                                  RequestContext(request))

def get_filename(md5=None):
    """
    Get the filename of a sample by MD5.

    :param md5: The MD5 of the sample to get the filename of.
    :type md5: str
    :returns: None, str
    """

    if not md5:
        return None
    sample = Sample.objects(md5=md5).first()
    if not sample:
        return None
    return sample.filename

def get_md5_hash(oid=None):
    """
    Get the MD5 of a sample by ObjectId.

    :param oid: The ObjectId of the sample to get the MD5 of.
    :type oid: str
    :returns: None, str
    """

    if oid is None:
        return None
    else:
        sample = Sample.objects(id=oid).first()
        if not sample:
            return None
        return sample.md5

def delete_sample(sample_md5, username=None):
    """
    Delete a sample from CRITs.

    :param sample_md5: The MD5 of the sample to delete.
    :type sample_md5: str
    :param username: The user deleting this sample.
    :type username: str
    :returns: bool
    """

    if is_admin(username):
        sample = Sample.objects(md5=sample_md5).first()
        if sample:
            sample.delete(username=username)
            return True
        else:
            return False
    else:
        return False

def mail_sample(sample_md5, recips=None):
    """
    Mail a sample to a list of recipients.

    :param sample_md5: The MD5 of the sample to send.
    :type sample_md5: str
    :param recips: List of recipients.
    :type recips: list
    :returns: None, str
    """

    if recips is not None:
        sample = Sample.objects(md5=sample_md5).first()
        if not sample:
            return None
        try:
            send_mail('Details for %s' % sample_md5,
                      '%s' % pprint.pformat(sample.to_json()),
                      settings.CRITS_EMAIL,
                      recips,
                      fail_silently=False)
        except Exception as e:
            logger.error(e)
            return str(e.args)
    return None

def get_source_counts(analyst):
    """
    Get the sources for a user.

    :param analyst: The user to get sources for.
    :type analyst: str
    :returns: :class:`crits.core.crits_mongoengine.CritsQuerySet`
    """

    allowed = user_sources(analyst)
    sources = SourceAccess.objects(name__in=allowed)
    return sources

def add_new_exploit(name, analyst):
    """
    Add a new exploit to CRITs.

    :param name: The name of the exploit.
    :type name: str
    :param analyst: The user adding the new exploit.
    :type analyst: str
    :returns: bool
    """

    try:
        name = name.strip().upper()
        exploit = Exploit.objects(name=name).first()
        if exploit:
            return False
        exploit = Exploit()
        exploit.name = name
        exploit.save(username=analyst)
        return True
    except ValidationError:
        return False

def add_exploit_to_sample(md5, cve, analyst):
    """
    Add an exploit to a sample.

    :param md5: The MD5 of the sample to add this exploit to.
    :type md5: str
    :param cve: The exploit to add.
    :type cve: str
    :param analyst: The user adding this exploit.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    sources = user_sources(analyst)
    sample = Sample.objects(md5=md5,
                            source__name__in=sources).first()
    if not sample:
        return {'success': False,
                'message': "Could not find sample."}
    try:
        sample.add_exploit(cve)
        sample.save(username=analyst)
        return {'success': True,
                'message': "Exploit added successfully."}
    except ValidationError, e:
        return {'success': False,
                'message': "Could not add exploit: %s." % e}

def get_exploits():
    """
    Get the available exploits in the database.

    :returns: :class:`crits.core.crits_mongoengine.CritsQuerySet`
    """

    e = Exploit.objects()
    return e

def add_new_backdoor(name, analyst):
    """
    Add a new backdoor to CRITs.

    :param name: The name of the backdoor.
    :type name: str
    :param analyst: The user adding the new backdoor.
    :type analyst: str
    :returns: bool
    """

    try:
        name = name.strip()
        backdoor = Backdoor.objects(name=name).first()
        if backdoor:
            return False
        backdoor = Backdoor()
        backdoor.name = name
        backdoor.save(username=analyst)
        return True
    except ValidationError:
        return False

def add_backdoor_to_sample(md5, name, version, analyst):
    """
    Add a backdoor to a sample.

    :param md5: The MD5 of the sample to add this backdoor to.
    :type md5: str
    :param name: The backdoor to add.
    :type name: str
    :param version: The backdoor version.
    :type version: str
    :param analyst: The user adding this backdoor.
    :type analyst: str
    :returns: dict with keys "success" (boolean) and "message" (str)
    """

    sources = user_sources(analyst)
    sample = Sample.objects(md5=md5,
                            source__name__in=sources).first()
    if not sample:
        return {'success': False,
                'message': "Could not find sample."}
    try:
        sample.set_backdoor(name, version, analyst)
        sample.save(username=analyst)
        return {'success': True,
                'message': "Backdoor set successfully."}
    except ValidationError, e:
        return {'success': False,
                'message': "Could not set backdoor: %s." % e}

def get_yara_hits(version=None):
    """
    Get the yara hits in the database.

    :param version: The yara hit version to search for.
    :type version: str
    :returns: :class:`crits.core.crits_mongoengine.CritsQuerySet`
    """

    if version:
        hits = YaraHit.objects(version=version).order_by('+result')
    else:
        hits = YaraHit.objects().order_by('+result')
    return hits

def handle_unrar_sample(md5, user=None, password=None):
    """
    Unrar a sample.

    :param md5: The MD5 of the sample to unrar.
    :type md5: str
    :param user: The user unraring this sample.
    :type user: str
    :param password: Password to use to unrar the sample.
    :type password: str
    :returns: list
    :raises: ZipFileError, Exception
    """

    sample = class_from_value('Sample', md5)
    if not sample:
        return None
    data = sample.filedata.read()
    source = sample.source[0].name
    campaign = sample.campaign
    reference = None
    return unrar_file(md5, user, password, data, source, method="Unrar Existing Sample",
                      reference=reference, campaign=campaign, related_md5=md5)

def handle_unzip_file(md5, user=None, password=None):
    """
    Unzip a sample.

    :param md5: The MD5 of the sample to unzip.
    :type md5: str
    :param user: The user unzipping this sample.
    :type user: str
    :param password: Password to use to unzip the sample.
    :type password: str
    :returns: list
    :raises: ZipFileError, Exception
    """

    sample = class_from_value('Sample', md5)
    if not sample:
        return
    data = sample.filedata.read()
    source = sample.source[0].name
    campaign = sample.campaign
    reference = None
    return unzip_file(md5, user, password, data, source, method="Unzip Existing Sample",
                      reference=reference, campaign=campaign, related_md5=md5, )

def unzip_file(filename, user=None, password=None, data=None, source=None,
               method='Zip', reference=None, campaign=None, confidence='low',
               related_md5=None, related_id=None, related_type='Sample',
               bucket_list=None, ticket=None, inherited_source=None):
    """
    Unzip a file.

    :param filename: The name of the file to unzip.
    :type filename: str
    :param user: The user unzipping the file.
    :type user: str
    :param password: The password to use to unzip the file.
    :type password: str
    :param data: The filedata.
    :type data: str
    :param source: The name of the source that provided the data.
    :type source: str
    :param method: The source method to assign to the data.
    :type method: str
    :param reference: A reference to the data source.
    :type reference: str
    :param campaign: The campaign to attribute to the data.
    :type campaign: str
    :param confidence: The confidence level of the campaign attribution.
    :type confidence: str ('low', 'medium', 'high')
    :param related_md5: The MD5 of a related sample.
    :type related_md5: str
    :param related_id: The ObjectId of a related top-level object.
    :type related_id: str
    :param related_type: The type of the related top-level object.
    :type related_type: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :param inherited_source: Source(s) to be inherited by the new Sample
    :type inherited_source: list, :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :returns: list
    :raises: ZipFileError, Exception
    """

    temproot = settings.TEMP_DIR
    samples = []
    zipdir = ""
    extractdir = ""
    try:
        zip_md5 = md5(data).hexdigest()

        # 7z doesn't decompress archives via stdin, therefore
        # we need to write it out as a file first
        zipdir = tempfile.mkdtemp(dir=temproot)
        zipfile = open(zipdir + "/" + filename, "wb")
        zipfile.write(data)
        zipfile.close()

        # Build argument string to popen()
        args = [settings.ZIP7_PATH]
        args.append("e")
        extractdir = tempfile.mkdtemp(dir=temproot)
        args.append("-o" + extractdir)  # Set output directory

        # Apparently 7z doesn't mind being handed a password to an
        # archive that isn't encrypted - but blocks for the opposite
        # case, so we'll always give it something for a password argument
        if password is None:
            args.append("-pNone")
        else:
            args.append("-p" + password)

        args.append("-y")       # 'Yes' on all queries - avoid blocking
        args.append(zipdir + "/" + filename)

        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

        # Give the process 30 seconds to complete, otherwise kill it
        waitSeconds = 30
        while (proc.poll() is None and waitSeconds):
            time.sleep(1)
            waitSeconds -= 1

        if proc.returncode:     # 7z spit out an error
            errmsg = "Error while extracting archive\n" + proc.stdout.read()
            raise ZipFileError, errmsg
        elif not waitSeconds:   # Process timed out
            proc.terminate()
            raise ZipFileError, "Unzip process failed to terminate"
        else:
            if related_md5 and related_md5 == zip_md5:
                relationship = "Compressed_Into"
            else:
                relationship = "Related_To"
            for root, dirs, files in os.walk(extractdir):
                for filename in files:
                    filepath = extractdir + "/" + filename
                    filehandle = open(filepath, 'rb')
                    new_sample = handle_file(filename, filehandle.read(),
                                             source, method, reference,
                                             related_md5=related_md5,
                                             related_id=related_id,
                                             related_type=related_type, backdoor='',
                                             user=user, campaign=campaign,
                                             confidence=confidence,
                                             bucket_list=bucket_list,
                                             ticket=ticket,
                                             inherited_source=inherited_source,
                                             relationship=relationship)
                    if new_sample:
                        samples.append(new_sample)
                    filehandle.close()
    except ZipFileError:  # Pass this error up the chain
        raise
    except Exception, ex:
        errmsg = ''
        for err in ex.args:
            errmsg = errmsg + " " + str(err)
        raise ZipFileError, errmsg

    finally:
        if os.path.isdir(zipdir):
            shutil.rmtree(zipdir)
        if os.path.isdir(extractdir):
            shutil.rmtree(extractdir)
    return samples

def unrar_file(filename, user=None, password=None, data=None, source=None,
               method="Generic", reference=None, campaign=None, confidence='low',
               related_md5=None, related_id=None, related_type='Sample',
               bucket_list=None, ticket=None, inherited_source=None):
    """
    Unrar a file.

    :param filename: The name of the file to unrar.
    :type filename: str
    :param user: The user unraring the file.
    :type user: str
    :param password: The password to use to unrar the file.
    :type password: str
    :param data: The filedata.
    :type data: str
    :param source: The name of the source that provided the data.
    :type source: str
    :param method: The source method to assign to the data.
    :type method: str
    :param reference: A reference to the data source.
    :type reference: str
    :param campaign: The campaign to attribute to the data.
    :type campaign: str
    :param confidence: The confidence level of the campaign attribution.
    :type confidence: str ('low', 'medium', 'high')
    :param related_md5: The MD5 of a related sample.
    :type related_md5: str
    :param related_id: The ObjectId of a related top-level object.
    :type related_id: str
    :param related_type: The type of the related top-level object.
    :type related_type: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :param inherited_source: Source(s) to be inherited by the new Sample
    :type inherited_source: list, :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :returns: list
    :raises: ZipFileError, Exception
    """

    samples = []
    try:
        rar_md5 = md5(data).hexdigest()

        # write the data to a file so we can read from it as a rar file
        temproot = settings.TEMP_DIR
        rardir = tempfile.mkdtemp(dir=temproot)
        # append '.rar' to help ensure rarfile doesn't have same
        # name as an extracted file.
        rarname = os.path.join(rardir, filename)+'.rar'
        if data is None: #unraring an existing file
            data = get_file(filename)
        with open(rarname, "wb") as f:
            f.write(data)

        # change to temp directory since unrar allows extraction
        # only to the current directory first save current directory
        old_dir = os.getcwd()
        os.chdir(rardir)
        cmd = [settings.RAR_PATH,'e'] #,'-inul'
        if password:
            cmd.append('-p'+password)
        else:
            cmd.append('-p-')
        cmd.append('-y') #assume yes to all prompts
        cmd.append(rarname)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

        waitSeconds = 30
        while (proc.poll() is None and waitSeconds):
            time.sleep(1)
            waitSeconds -= 1

        if proc.returncode:
            errmsg = "Error while unraring archive\n" + proc.stdout.read()
            raise ZipFileError, errmsg
        elif not waitSeconds:
            proc.terminate()
            raise ZipFileError, "Unrar process failed to terminate"
        else:
            if related_md5 and related_md5 == rar_md5:
                relationship = "Compressed_Into"
            else:
                relationship = "Related_To"
            for root, dirs, files in os.walk(rardir):
                for filename in files:
                    filepath = os.path.join(rardir, filename)
                    if filepath != rarname:
                        with open(filepath, 'rb') as filehandle:
                            new_sample = handle_file(filename,
                                                     filehandle.read(),
                                                     source, method, reference,
                                                     related_md5=related_md5,
                                                     related_id=related_id,
                                                     related_type=related_type,
                                                     backdoor='', user=user,
                                                     campaign=campaign,
                                                     confidence=confidence,
                                                     bucket_list=bucket_list,
                                                     ticket=ticket,
                                                     inherited_source=inherited_source,
                                                     relationship=relationship)
                            samples.append(new_sample)
    except ZipFileError:
        raise
    except Exception:
        raise
        #raise ZipFileError, str(e)
    finally:
        #change back to original current directory
        os.chdir(old_dir)
        if os.path.isdir(rardir):
            shutil.rmtree(rardir)

    return samples

def handle_file(filename, data, source, method='Generic', reference=None, related_md5=None,
                related_id=None, related_type='Sample', backdoor=None, user='',
                campaign=None, confidence='low', md5_digest=None, bucket_list=None,
                ticket=None, relationship=None, inherited_source=None, is_validate_only=False,
                is_return_only_md5=True, cache={}):
    """
    Handle adding a file.

    :param filename: The name of the file.
    :type filename: str
    :param data: The filedata.
    :type data: str
    :param source: The name of the source that provided the data.
    :type source: list, str, :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param method: The source method to assign to the data.
    :type method: str
    :param reference: A reference to the data source.
    :type reference: str
    :param related_md5: The MD5 of a related sample.
    :type related_md5: str
    :param related_id: The ObjectId of a related top-level object.
    :type related_id: str
    :param related_type: The type of the related top-level object.
    :type related_type: str
    :param backdoor: The backdoor to assign to this sample.
    :type backdoor: str
    :param user: The user uploading this sample.
    :type user: str
    :param campaign: The campaign to attribute to the data.
    :type campaign: str
    :param confidence: The confidence level of the campaign attribution.
    :type confidence: str ('low', 'medium', 'high')
    :param md5_digest: The MD5 of this sample.
    :type md5_digest: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :param relationship: The relationship between this sample and the parent.
    :type relationship: str
    :param inherited_source: Source(s) to be inherited by the new Sample
    :type inherited_source: list, :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param is_validate_only: Only validate, do not add.
    :type is_validate_only: bool
    :param is_return_only_md5: Only return the MD5s.
    :type is_return_only_md5: bool
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: str,
              dict with keys:
              "success" (boolean),
              "message" (str),
              "object" (the sample),
    """

    retVal = {}
    retVal['success'] = True
    retVal['message'] = ""
    is_sample_new = False

    # get sample from database, or create it if one doesn't exist
    if not md5_digest and not data:
        retVal['message'] += "Either the MD5 digest or data need to be supplied"
        retVal['success'] = False
    elif md5_digest:
        # validate md5
        md5_digest = md5_digest.lower().strip()
        validate_md5_result = validate_md5_checksum(md5_digest)
        retVal['message'] += validate_md5_result.get('message')
        retVal['success'] = validate_md5_result.get('success')
    else:
        md5_digest = md5(data).hexdigest()
        validate_md5_result = validate_md5_checksum(md5_digest)
        retVal['message'] += validate_md5_result.get('message')
        retVal['success'] = validate_md5_result.get('success')
    if related_id or related_md5:
        if  related_id:
            related_obj = class_from_id(related_type, related_id)
        else:
            related_obj = class_from_value(related_type, related_md5)
        if not related_obj:
            retVal['message'] += (' Related %s not found. Sample not uploaded.'
                                  % (related_type))
            retVal['success'] = False
    else:
        related_obj = None

    if retVal['success'] == False:
        if is_return_only_md5 == True:
            return None
        else:
            return retVal

    cached_results = cache.get(form_consts.Sample.CACHED_RESULTS)

    if cached_results != None:
        sample = cached_results.get(md5_digest)
    else:
        sample = Sample.objects(md5=md5_digest).first()

    if not sample:
        is_sample_new = True
        sample = Sample()
        sample.filename = filename or md5_digest
        sample.md5 = md5_digest
    else:
        if filename not in sample.filenames and filename != sample.filename:
            sample.filenames.append(filename)

        if cached_results != None:
            cached_results[md5_digest] = sample

    # attempt to discover binary in GridFS before assuming we don't
    # have it
    sample.discover_binary()

    if data:
        # we already have this binary so generate metadata from it
        if sample.filedata.grid_id:
            sample._generate_file_metadata(data)
        # add the binary to gridfs and generate metadata
        else:
            sample.add_file_data(data)
    # if we didn't get data:
    else:
        if sample.filedata:
            # get data from db and add metadata in case it doesn't exist
            data = sample.filedata.read()
            sample._generate_file_metadata(data)
        else:
            if md5_digest:
                # no data and no binary, add limited metadata
                sample.md5 = md5_digest
            else:
                retVal['message'] += ("The MD5 digest and data, or the file "
                                     "data itself, need to be supplied.")
                retVal['success'] = False

    #add copy of inherited source(s) to Sample
    if isinstance(inherited_source, EmbeddedSource):
        sample.add_source(copy.copy(inherited_source))
    elif isinstance(inherited_source, list) and len(inherited_source) > 0:
        for s in inherited_source:
            if isinstance(s, EmbeddedSource):
                sample.add_source(copy.copy(s))

    # generate new source information and add to sample
    if isinstance(source, basestring) and len(source) > 0:
        s = create_embedded_source(source,
                                   method=method,
                                   reference=reference,
                                   analyst=user)
        # this will handle adding a new source, or an instance automatically
        sample.add_source(s)
    elif isinstance(source, EmbeddedSource):
        sample.add_source(source)
    elif isinstance(source, list) and len(source) > 0:
        for s in source:
            if isinstance(s, EmbeddedSource):
                sample.add_source(s)

    if bucket_list:
        sample.add_bucket_list(bucket_list, user)

    if ticket:
        sample.add_ticket(ticket, user)

    # if no proper source has been provided, don't add the sample
    if len(sample.source) == 0:
        retVal['message'] += "The sample does not have a source."
        retVal['success'] = False
    elif is_validate_only == False:
        # assume it's a list of EmbeddedCampaign, but check if it's a string
        # if it is a string then create a new EmbeddedCampaign
        if campaign != None:
            campaign_array = campaign

            if isinstance(campaign, basestring):
                campaign_array = [EmbeddedCampaign(name=campaign, confidence=confidence, analyst=user)]

            for campaign_item in campaign_array:
                sample.add_campaign(campaign_item)

        # save sample to get an id since the rest of the processing needs it
        sample.save(username=user)
        # reloading clears the _changed_fields of the sample object. this prevents
        # situations where we save again below and the shard key (md5) is
        # still marked as changed.
        sample.reload()

        # run sample triage:
        if len(sample.analysis) < 1 and data:
            run_triage(data, sample, user)

        # update relationship if a related top-level object is supplied
        if related_obj and sample:
            if related_obj.id != sample.id: #don't form relationship to itself
                if not relationship:
                    relationship = "Related_To"
                sample.add_relationship(rel_item=related_obj,
                                        rel_type=relationship,
                                        analyst=user,
                                        get_rels=False)
                related_obj.save(username=user)
                sample.save(username=user)

    if is_sample_new == True:
        # New sample, and successfully uploaded
        if is_validate_only == False:
            retVal['message'] += ('Success: Added new sample <a href="%s">%s.</a>'
                                  % (reverse('crits.samples.views.detail',
                                             args=[sample.md5.lower()]),
                                             sample.md5.lower()))
    else:
        # Duplicate sample, but uploaded anyways
        if is_validate_only == False:
            message = ('Success: Updated sample <a href="%s">%s.</a>'
                                  % (reverse('crits.samples.views.detail',
                                             args=[sample.md5.lower()]),
                                            sample.md5.lower()))
            retVal['message'] += message
            retVal['status'] = form_consts.Status.DUPLICATE
            retVal['warning'] = message
        # Duplicate sample, but only validation
        else:
            if sample.id != None:
                warning_message = ('Warning: Trying to add file [' +
                                    filename + ']'
                                    ' when MD5 already exists as file [' +
                                    sample.filename  + ']'
                                    '<a href="%s">%s.</a>'
                                    % (reverse('crits.samples.views.detail',
                                               args=[sample.md5.lower()]),
                                               sample.md5.lower()))
                retVal['message'] += warning_message
                retVal['status'] = form_consts.Status.DUPLICATE
                retVal['warning'] = warning_message

    if is_return_only_md5 == True:
        return md5_digest
    else:
        retVal['object'] = sample
        return retVal

def handle_uploaded_file(f, source, method="", reference=None, file_format=None,
                         password=None, user=None, campaign=None, confidence='low',
                         related_md5=None, related_id=None, related_type='Sample',
                         filename=None, md5=None, bucket_list=None, ticket=None,
                         inherited_source=None, is_validate_only=False,
                         is_return_only_md5=True, cache={}):
    """
    Handle an uploaded file.

    :param f: The uploaded file.
    :type f: file handle
    :param source: The name of the source that provided the data.
    :type source: list, str, :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param method: The source method to assign to the data.
    :type method: str
    :param reference: A reference to the data source.
    :type reference: str
    :param file_format: The format the file was uploaded in.
    :type file_format: str
    :param password: A password necessary to access the file data.
    :type password: str
    :param user: The user uploading this sample.
    :type user: str
    :param campaign: The campaign to attribute to the data.
    :type campaign: str
    :param confidence: The confidence level of the campaign attribution.
    :type confidence: str ('low', 'medium', 'high')
    :param related_md5: The MD5 of a related sample.
    :type related_md5: str
    :param related_id: The ObjectId of a related top-level object.
    :type related_id: str
    :param related_type: The type of the related top-level object.
    :type related_type: str
    :param filename: The filename of the sample.
    :type filename: str
    :param md5: The MD5 of the sample.
    :type md5: str
    :param bucket_list: The bucket(s) to assign to this data.
    :type bucket_list: str
    :param ticket: The ticket to assign to this data.
    :type ticket: str
    :param inherited_source: Source(s) to be inherited by the new Sample
    :type inherited_source: list, :class:`crits.core.crits_mongoengine.EmbeddedSource`
    :param is_validate_only: Only validate, do not add.
    :type is_validate_only: bool
    :param is_return_only_md5: Only return the MD5s.
    :type is_return_only_md5: bool
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: list
    """

    samples = list()
    if method:
        method = " - " + method
    if f:
        method = "File Upload" + method
    elif md5:
        method = "Metadata Upload" + method
    else:
        method = "Upload" + method
    try:
        data = f.read()
    except AttributeError:
        data = f
    if not filename:
        filename = getattr(f, 'name', None)
        if not filename:
            try:
                filename = md5(data).hexdigest()
            except:
                filename = "unknown"
    if file_format == "zip" and f:
        return unzip_file(
            filename,
            user=user,
            password=password,
            data=data,
            source=source,
            method=method,
            reference=reference,
            campaign=campaign,
            confidence=confidence,
            related_md5=related_md5,
            related_id=related_id,
            related_type=related_type,
            bucket_list=bucket_list,
            ticket=ticket,
            inherited_source=inherited_source)
    elif file_format == "rar" and f:
        return unrar_file(
            filename,
            user=user,
            password=password,
            data=data,
            source=source,
            method=method,
            reference=reference,
            campaign=campaign,
            confidence=confidence,
            related_md5=related_md5,
            related_id=related_id,
            related_type=related_type,
            bucket_list=bucket_list,
            ticket=ticket,
            inherited_source=inherited_source)
    else:
        new_sample = handle_file(filename, data, source, method, reference,
                                 related_md5=related_md5, related_id=related_id,
                                 related_type=related_type, backdoor='', user=user,
                                 campaign=campaign, confidence=confidence, md5_digest=md5,
                                 bucket_list=bucket_list, ticket=ticket,
                                 inherited_source=inherited_source, is_validate_only=is_validate_only,
                                 is_return_only_md5=is_return_only_md5, cache=cache)

        if new_sample:
            samples.append(new_sample)
    return samples

def add_new_sample_via_bulk(data, rowData, request, errors, is_validate_only=False, cache={}):
    """
    Add a new sample from bulk upload.

    :param data: The data about the sample.
    :type data: dict
    :param rowData: Object data in the row.
    :type rowData: dict
    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param errors: List of existing errors to append to.
    :type errors: list
    :param is_validate_only: Only validate, do not add.
    :type is_validate_only: bool
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    returns: tuple of result, errors, return value
    """

    username = request.user.username
    result = False
    retVal = {}
    retVal['success'] = True

    files = None

    if request.FILES:
        files = request.FILES

    #upload_type = data.get('upload_type')
    #filedata = data.get('filedata')
    filename = data.get('filename')
    campaign = data.get('campaign')
    confidence = data.get('confidence')
    md5 = data.get('md5')
    fileformat = data.get('file_format')
    password = data.get('password')
    #is_email_results = data.get('email')
    related_md5 = data.get('related_md5')
    source = data.get('source')
    method = data.get('method', '')
    reference = data.get('reference')
    bucket_list = data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
    ticket = data.get(form_consts.Common.TICKET_VARIABLE_NAME)

    samples = handle_uploaded_file(files, source, method, reference,
                                  file_format=fileformat,
                                  password=password,
                                  user=username,
                                  campaign=campaign,
                                  confidence=confidence,
                                  related_md5=related_md5,
                                  filename=filename,
                                  md5=md5,
                                  bucket_list=bucket_list,
                                  ticket=ticket,
                                  is_validate_only=is_validate_only,
                                  is_return_only_md5=False,
                                  cache=cache)

    # This block tries to add objects to the item
    if not errors or is_validate_only == True:
        result = True

        objectsData = rowData.get(form_consts.Common.OBJECTS_DATA)

        for sample in samples:
            # repack message field into top of structure
            if retVal.get('message'):
                if sample.get('success') == False:
                    retVal['success'] = False
                    result = False
                    errors.append(sample.get('message'))
                else:
                    retVal['message'] += sample.get('message')
            else:
                if sample.get('success') == False:
                    retVal['success'] = False
                    result = False
                    errors.append(sample.get('message'))
                else:
                    retVal['message'] = sample.get('message')

            if sample.get('warning'):
                retVal['warning'] = sample.get('warning')

            if sample.get('status'):
                retVal['status'] = sample.get('status')

            # add new objects if they exist
            if objectsData:
                objectsData = json.loads(objectsData)
                object_row_counter = 1

                for objectData in objectsData:
                    if sample.get('object') != None and is_validate_only == False:
                        objectDict = object_array_to_dict(objectData, "Sample",
                                                          sample.get('object').id)
                    else:
                        if sample.get('object'):
                            if sample.get('object').id:
                                objectDict = object_array_to_dict(objectData, "Sample",
                                                                  sample.get('object').id)
                            else:
                                objectDict = object_array_to_dict(objectData, "Sample", "")
                        else:
                            objectDict = object_array_to_dict(objectData, "Sample", "")

                    (object_result, object_errors, object_retVal) = validate_and_add_new_handler_object(
                            None, objectDict, request, errors, object_row_counter,
                            is_validate_only=is_validate_only, cache=cache)

                    # if there was an error, mark the overall
                    # operation as failed
                    if object_retVal.get('success') == False:
                        retVal['success'] = False
                        result = False

                    if object_retVal.get('message'):
                        errors.append(object_retVal['message'])

                    object_row_counter += 1
    else:
        errors += "Failed to add Sample: " + md5

    return result, errors, retVal

def parse_row_to_bound_sample_form(request, rowData, cache, upload_type="File Upload"):
    """
    Parse a mass upload row into an UploadFileForm.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param rowData: The data in the row.
    :type rowData: dict
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :param upload_type: The type of upload.
    :type upload_type: str
    :returns: :class:`crits.samples.forms.UploadFileForm`
    """

    filedata = None
    fileformat = None
    password = None
    filename = None
    md5 = None

    if not upload_type:
        upload_type = rowData.get(form_consts.Sample.UPLOAD_TYPE, "")

    if upload_type == form_consts.Sample.UploadType.FILE_UPLOAD:
        filedata = rowData.get(form_consts.Sample.FILE_DATA, "")
        fileformat = rowData.get(form_consts.Sample.FILE_FORMAT, "")
        password = rowData.get(form_consts.Sample.PASSWORD, "")
    elif upload_type == form_consts.Sample.UploadType.METADATA_UPLOAD:
        filename = rowData.get(form_consts.Sample.FILE_NAME, "")
        md5 = rowData.get(form_consts.Sample.MD5, "")

    campaign = rowData.get(form_consts.Sample.CAMPAIGN, "")
    confidence = rowData.get(form_consts.Sample.CAMPAIGN_CONFIDENCE, "")
    is_email_results = convert_string_to_bool(rowData.get(form_consts.Sample.EMAIL_RESULTS, ""))
    related_md5 = rowData.get(form_consts.Sample.RELATED_MD5, "")
    source = rowData.get(form_consts.Sample.SOURCE, "")
    method = rowData.get(form_consts.Sample.SOURCE_METHOD, "")
    reference = rowData.get(form_consts.Sample.SOURCE_REFERENCE, "")
    bucket_list = rowData.get(form_consts.Sample.BUCKET_LIST, "")
    ticket = rowData.get(form_consts.Common.TICKET, "")

    data = {
        'upload_type': upload_type,
        'filedata': filedata,
        'filename': filename,
        'md5': md5,
        'file_format': fileformat,
        'campaign': campaign,
        'confidence': confidence,
        'password': password,
        'email': is_email_results,
        'related_md5': related_md5,
        'source': source,
        'method': method,
        'reference': reference,
        'bucket_list': bucket_list,
        'ticket': ticket
    }

    bound_md5_sample_form = cache.get('sample_form')

    if bound_md5_sample_form == None:
        bound_md5_sample_form = UploadFileForm(request.user, data, request.FILES)
        cache['sample_form'] = bound_md5_sample_form
    else:
        bound_md5_sample_form.data = data

    bound_md5_sample_form.full_clean()
    return bound_md5_sample_form

def parse_row_to_bound_md5_sample_form(request, rowData, cache):
    """
    Parse a mass upload row into an UploadFileForm.

    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param rowData: The data in the row.
    :type rowData: dict
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: :class:`crits.samples.forms.UploadFileForm`
    """

    upload_type = form_consts.Sample.UploadType.METADATA_UPLOAD
    return parse_row_to_bound_sample_form(request, rowData, cache, upload_type=upload_type)

def process_bulk_add_md5_sample(request, formdict):
    """
    Performs the bulk add of MD5 samples by parsing the request data. Batches
    some data into a cache object for performance by reducing large
    amounts of single database queries.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param formdict: The form representing the bulk uploaded data.
    :type formdict: dict
    :returns: :class:`django.http.HttpResponse`
    """
    md5_samples = []
    cached_results = {}

    cleanedRowsData = convert_handsontable_to_rows(request)
    for rowData in cleanedRowsData:
        if rowData != None and rowData.get(form_consts.Sample.MD5) != None:
            md5_samples.append(rowData.get(form_consts.Sample.MD5).lower())

    md5_results = Sample.objects(md5__in=md5_samples)

    for md5_result in md5_results:
        cached_results[md5_result.md5] = md5_result

    cache = {form_consts.Sample.CACHED_RESULTS: cached_results, 'cleaned_rows_data': cleanedRowsData}

    response = parse_bulk_upload(request, parse_row_to_bound_md5_sample_form, add_new_sample_via_bulk, formdict, cache)

    return response

def update_sample_filename(id_, filename, analyst):
    """
    Update a Sample filename.

    :param id_: ObjectId of the Sample.
    :type id_: str
    :param filename: The new filename.
    :type filename: str
    :param analyst: The user setting the new filename.
    :type analyst: str
    :returns: dict with key 'success' (boolean) and 'message' (str) if failed.
    """

    if not filename:
        return {'success': False, 'message': "No filename to change"}
    sample = Sample.objects(id=id_).first()
    if not sample:
        return {'success': False, 'message': "No sample to change"}
    sample.filename = filename.strip()
    try:
        sample.save(username=analyst)
        return {'success': True}
    except ValidationError, e:
        return {'success': False, 'message': e}

def modify_sample_filenames(id_, tags, analyst):
    """
    Modify the filenames for a Sample.

    :param id_: ObjectId of the Sample.
    :type id_: str
    :param tags: The new filenames.
    :type tags: list
    :param analyst: The user setting the new filenames.
    :type analyst: str
    :returns: dict with key 'success' (boolean) and 'message' (str) if failed.
    """

    sample = Sample.objects(id=id_).first()
    if sample:
        sample.set_filenames(tags)
        try:
            sample.save(username=analyst)
            return {'success': True}
        except ValidationError, e:
            return {'success': False, 'message': "Invalid value: %s" % e}
    else:
        return {'success': False}
