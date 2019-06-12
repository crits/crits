import sys
import datetime
import json
import logging

from bson import json_util
from dateutil.parser import parse
from time import gmtime, strftime

from django.conf import settings
from django import get_version
from django.contrib.auth.decorators import user_passes_test
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.template.loader import render_to_string

from crits.actors.actor import ActorThreatIdentifier
from crits.actors.forms import AddActorForm, AddActorIdentifierTypeForm
from crits.actors.forms import AddActorIdentifierForm, AttributeIdentifierForm
from crits.backdoors.forms import AddBackdoorForm
from crits.campaigns.campaign import Campaign
from crits.campaigns.forms import AddCampaignForm, CampaignForm
from crits.certificates.forms import UploadCertificateForm
from crits.comments.forms import AddCommentForm, InlineCommentForm
from crits.config.config import CRITsConfig
from crits.core.crits_mongoengine import Action
from crits.core.data_tools import json_handler
from crits.core.forms import SourceAccessForm, AddSourceForm
from crits.core.forms import ActionsForm, NewActionForm
from crits.core.forms import SourceForm, DownloadFileForm, AddReleasabilityForm
from crits.core.forms import TicketForm, AddRoleForm, RoleCombinePreview
from crits.core.handlers import add_releasability, add_releasability_instance
from crits.core.handlers import remove_releasability, remove_releasability_instance
from crits.core.handlers import add_new_source, generate_counts_jtable
from crits.core.handlers import source_add_update, source_remove, source_remove_all
from crits.core.handlers import modify_bucket_list, promote_bucket_list
from crits.core.handlers import download_object_handler, unflatten
from crits.core.handlers import modify_sector_list, validate_next
from crits.core.handlers import generate_bucket_jtable, generate_bucket_csv
from crits.core.handlers import generate_sector_jtable, generate_sector_csv
from crits.core.handlers import generate_dashboard, generate_global_search
from crits.core.handlers import login_user, reset_user_password
from crits.core.handlers import generate_user_profile, generate_user_preference
from crits.core.handlers import modify_source_access, get_bucket_autocomplete
from crits.core.handlers import dns_timeline, email_timeline, indicator_timeline
from crits.core.handlers import generate_users_jtable, generate_items_jtable
from crits.core.handlers import toggle_item_state, download_grid_file
from crits.core.handlers import get_data_for_item, generate_audit_jtable
from crits.core.handlers import details_from_id, status_update, set_role_value
from crits.core.handlers import get_favorites, favorite_update, get_role_details
from crits.core.handlers import generate_favorites_jtable, generate_roles_jtable
from crits.core.handlers import ticket_add, ticket_update, ticket_remove
from crits.core.handlers import add_new_role, render_role_graph
from crits.core.handlers import add_role_source, remove_role_source
from crits.core.handlers import edit_role_description, edit_role_name
from crits.core.handlers import modify_tlp, description_update, data_update
from crits.core.handlers import do_add_preferred_actions, add_new_action
from crits.core.handlers import action_add, action_remove, action_update
from crits.core.handlers import get_action_types_for_tlo, generate_audit_csv
from crits.core.source_access import SourceAccess
from crits.core.user import CRITsUser
from crits.core.user_tools import user_can_view_data, user_sources
from crits.core.user_tools import get_nav_template
from crits.core.user_tools import get_acl_object
from crits.core.user_tools import get_user_email_notification
from crits.core.user_tools import get_user_info, get_user_organization
from crits.core.user_tools import is_user_subscribed, unsubscribe_user
from crits.core.user_tools import subscribe_user, subscribe_to_source
from crits.core.user_tools import unsubscribe_from_source, is_user_subscribed_to_source
from crits.core.user_tools import change_user_password, toggle_active
from crits.core.user_tools import save_user_secret
from crits.core.user_tools import toggle_user_preference, update_user_preference
from crits.core.user_tools import get_api_key_by_name, create_api_key_by_name
from crits.core.user_tools import revoke_api_key_by_name, make_default_api_key_by_name
from crits.core.class_mapper import class_from_id
from crits.domains.forms import TLDUpdateForm, AddDomainForm
from crits.emails.forms import EmailUploadForm, EmailEMLForm, EmailYAMLForm, EmailRawUploadForm, EmailOutlookForm
from crits.events.forms import EventForm
from crits.exploits.forms import AddExploitForm
from crits.indicators.forms import UploadIndicatorCSVForm, UploadIndicatorTextForm
from crits.indicators.forms import UploadIndicatorForm
from crits.ips.forms import AddIPForm
from crits.locations.forms import AddLocationForm
from crits.notifications.handlers import get_user_notifications
from crits.notifications.handlers import remove_user_from_notification
from crits.notifications.handlers import remove_user_notifications
from crits.objects.forms import AddObjectForm
from crits.pcaps.forms import UploadPcapForm
from crits.raw_data.forms import UploadRawDataFileForm, UploadRawDataForm
from crits.raw_data.forms import NewRawDataTypeForm
from crits.raw_data.raw_data import RawDataType
from crits.relationships.forms import ForgeRelationshipForm
from crits.samples.forms import UploadFileForm
from crits.screenshots.forms import AddScreenshotForm
from crits.signatures.forms import UploadSignatureForm
from crits.signatures.forms import NewSignatureTypeForm
from crits.signatures.forms import NewSignatureDependencyForm
from crits.signatures.signature import SignatureType
from crits.signatures.signature import SignatureDependency
from crits.targets.forms import TargetInfoForm

from crits.vocabulary.sectors import Sectors
from crits.vocabulary.acls import *

logger = logging.getLogger(__name__)

django_version = get_version()

@user_passes_test(user_can_view_data)
def update_object_description(request):
    """
    Toggle favorite in a user profile.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user

    if request.method == "POST" and request.is_ajax():
        type_ = request.POST['type']
        id_ = request.POST['id']
        description = request.POST['description']
        acl = get_acl_object(type_)
        if user.has_access_to(acl.DESCRIPTION_EDIT):
            return HttpResponse(json.dumps(description_update(type_,
                                                          id_,
                                                          description,
                                                          user.username)),
                            content_type="application/json")
        else:
            return HttpResponse(json.dumps({'success':False,
                                            'message':'User does not have permission to edit description.'}),
                                content_type="application/json")
    else:
        return render(request, "error.html", {"error" : 'Expected AJAX POST.'})
@user_passes_test(user_can_view_data)
def update_object_data(request):
    """
    Update the data in a data element

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        type_ = request.POST['type']
        id_ = request.POST['id']
        data = request.POST['data']
        user = request.user
        return HttpResponse(json.dumps(data_update(type_,
                                                          id_,
                                                          data,
                                                          user)),
                            content_type="application/json")
    else:
        return render(request, "error.html", {"error" : 'Expected AJAX POST.'})

@user_passes_test(user_can_view_data)
def toggle_favorite(request):
    """
    Toggle favorite in a user profile.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        type_ = request.POST['type']
        id_ = request.POST['id']
        user = request.user
        return HttpResponse(json.dumps(favorite_update(type_,
                                                       id_,
                                                       user)),
                            content_type="application/json")
    else:
        return render(request, "error.html", {"error" : 'Expected AJAX POST.'})

@user_passes_test(user_can_view_data)
def favorites(request):
    """
    Get favorites for a user.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user
        return HttpResponse(json.dumps(get_favorites(user)),
                            content_type="application/json")
    else:
        return render(request, "error.html", {"error" : 'Expected AJAX POST.'})


@user_passes_test(user_can_view_data)
def favorites_list(request, ctype=None, option=None):
    """
    Get favorites for a user for jtable.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_favorites_jtable(request, ctype, option)


@user_passes_test(user_can_view_data)
def get_dialog(request):
    """
    Get a specific dialog for rendering in the UI.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """
    dialog = str(request.GET.get('dialog', ''))
    params = {}

    # Only prepare & serve the single form being requested
    try:
        # These require no params
        if dialog == 'action_add':
            params['add_new_action'] = NewActionForm()
        elif dialog == 'comments':
            params['comment_add'] = AddCommentForm()
        elif dialog == 'new-inline-comment':
            params['inline_comment_add'] = InlineCommentForm()
        elif dialog == 'new-campaign':
            params['campaign_add'] = AddCampaignForm()
        elif dialog == 'campaign-add':
            params['campaign_form'] = CampaignForm()
        elif dialog == 'location-add':
            params['location_add'] = AddLocationForm()
        elif dialog == 'raw_data_type_add':
            params['add_raw_data_type'] = NewRawDataTypeForm()
        elif dialog == 'forge-relationship':
            params['relationship_form'] = ForgeRelationshipForm()
        elif dialog == 'signature_type_add':
            params['add_signature_type'] = NewSignatureTypeForm()
        elif dialog == 'signature_dependency_add':
            params['add_signature_dependency'] = NewSignatureDependencyForm()
        elif dialog == 'upload_tlds':
            params['upload_tlds'] = TLDUpdateForm()
        elif dialog == 'actor_identifier_type_add':
            params['add_actor_identifier_type'] = AddActorIdentifierTypeForm()
        elif dialog == 'attribute_actor_identifier':
            params['attribute_actor_identifier'] = AttributeIdentifierForm()
        elif dialog == 'role_combine_preview':
            params['role_combine_preview'] = RoleCombinePreview()
        elif dialog == 'new-role':
            params['role_add'] = AddRoleForm()
        # These require user as parameter
        elif dialog == 'new-target':
            params['add_target'] = TargetInfoForm(request.user)
        elif dialog == 'new-actor':
            params['actor_add'] = AddActorForm(request.user)
        elif dialog == 'new-actor-identifier':
            params['add_actor_identifier'] = AddActorIdentifierForm(request.user)
        elif dialog == 'new-backdoor':
            params['backdoor_add'] = AddBackdoorForm(request.user)
        elif dialog == 'new-exploit':
            params['exploit_add'] = AddExploitForm(request.user)
        elif dialog == 'new-domain':
            params['add_domain'] = AddDomainForm(request.user)
        elif dialog == 'new-certificate':
            params['upload_cert'] = UploadCertificateForm(request.user)
        elif dialog == 'new-indicator-csv':
            params['upload_csv'] = UploadIndicatorCSVForm(request.user)
        elif dialog == 'new-email-outlook':
            params['upload_email_outlook'] = EmailOutlookForm(request.user)
        elif dialog == 'new-email-eml':
            params['upload_email_eml'] = EmailEMLForm(request.user)
        elif dialog == 'new-email-fields':
            params['upload_email_fields'] = EmailUploadForm(request.user)
        elif dialog == 'new-email-yaml':
            params['upload_email_yaml'] = EmailYAMLForm(request.user)
        elif dialog == 'new-email-raw':
            params['upload_email_raw'] = EmailRawUploadForm(request.user)
        elif dialog == 'new-event':
            params['upload_event'] = EventForm(request.user)
        elif dialog == 'new-indicator':
            params['upload_ind'] = UploadIndicatorForm(request.user)
        elif dialog == 'new-pcap':
            params['upload_pcap'] = UploadPcapForm(request.user)
        elif dialog == 'indicator-blob':
            params['upload_text'] = UploadIndicatorTextForm(request.user)
        elif dialog == 'new-sample':
            params['upload_sample'] = UploadFileForm(request.user)
        elif dialog == 'add-object':
            params['object_form'] = AddObjectForm(request.user)
        elif dialog == 'releasability-add':
            params['releasability_form'] = AddReleasabilityForm(request.user)
        elif dialog == 'add-screenshot':
            params['screenshots_form'] = AddScreenshotForm(request.user)
        elif dialog == 'new-raw-data':
            params['upload_raw_data'] = UploadRawDataForm(request.user)
        elif dialog == 'new-raw-data-file':
            params['upload_raw_data_file'] = UploadRawDataFileForm(request.user)
        elif dialog == 'new-signature':
            params['upload_signature'] = UploadSignatureForm(request.user)
        # Others
        elif dialog == 'ticket':
            params['new_ticket'] = TicketForm(initial={'date': datetime.datetime.now()})
        elif dialog == 'new-ip':
            params['ip_form'] = AddIPForm(request.user, None)
        elif dialog == 'action_add':
            params['new_action'] = ActionsForm(initial={'analyst': request.user.username,
                                               'active': "off",
                                               'date': datetime.datetime.now()})
        elif dialog == 'source-add':
            params['source_add'] = SourceForm(request.user, initial={'analyst': request.user.username})
        # Admin required -> Since this is checked by the method itself, we no longer check
        elif dialog == 'source_create':
            params['source_create'] = AddSourceForm()
        # If this is hit, requested dialog does not exist.
        else:
            dialog = 'error'
            params['error'] = "Dialog does not exist"

    except Exception, e:
        dialog = 'error'
        params['error'] = 'Error preparing requested dialog'
        logger.warning("Dialog error: %s" % e)

    return render(request, dialog + ".html", params)


@user_passes_test(user_can_view_data)
def update_status(request, type_, id_):
    """
    Update the status of a top-level object. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param type_: The top-level object to update.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        value = request.POST['value']
        user = request.user

        if user.has_access_to(get_acl_object(type_).STATUS_EDIT):
            return HttpResponse(json.dumps(status_update(type_,
                                                     id_,
                                                     value,
                                                     user)),
                            content_type="application/json")
        else:
            return HttpResponse(json.dumps({"success":False,
                                            "message":"User does not have permission to edit status."}),
                                content_type="application/json")
    else:
        return render(request, "error.html", {"error" : 'Expected AJAX POST.'})

@user_passes_test(user_can_view_data)
def get_item_data(request):
    """
    Get basic data for an item. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    item_id = request.POST.get('id','')
    item_type = request.POST.get('type','')
    # Right now we pass the id/type for the data we want
    # If we write a function that doesn't pass these values,
    # then grab them from the cookies
    if not item_id:
        item_id = request.COOKIES.get('crits_rel_id','')
    if not item_type:
        item_type = request.COOKIES.get('crits_rel_type','')
    response = get_data_for_item(item_type, item_id)
    return HttpResponse(json.dumps(response, default=json_handler),
                        content_type="application/json")


@user_passes_test(user_can_view_data)
def global_search_listing(request):
    """
    Return results for a global search.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    # For object searches
    if 'q' not in request.GET:
        return render(request, "error.html", {"error" : 'No valid search criteria'})
    args = generate_global_search(request)

    # If we matched a single ObjectID
    if 'url' in args:
        return redirect(args['url'], args['key'])

    # For all other searches
    if 'Result' in args and args['Result'] == "ERROR":
        return render(request, "error.html", {"error": args['Message']})

    return render(request, "search_listing.html", args)

def about(request):
    """
    Return the About page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    # All loaded modules without dot in the name, with __path__, and with __version__
    mods = [(m.__name__.lower(), getattr(m, '__version__', ''), m.__path__[0]) for m in sys.modules.values() if getattr(m, '__path__', '') and getattr(m, '__version__', '') and not '.' in m.__name__]
    mods=sorted(mods)
    return render(request, 'about.html', {"loaded_mods": mods,})

def help(request):
    """
    Return the Help page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    return render(request, 'help.html', {})

# Mongo Auth
def login(request):
    """
    Authenticate a user.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    # Gather basic request information
    crits_config = CRITsConfig.objects().first()
    url = request.GET.get('next')
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    remote_addr = request.META.get('REMOTE_ADDR', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    next_url = request.GET.get('next', request.POST.get('next', None))
    user = request.user

    # Is the user already authenticated?
    if (request.user.is_authenticated if django_version >= (1, 10) else request.user.is_authenticated()) and user.has_access_to(GeneralACL.WEB_INTERFACE) and not request.is_ajax:
        resp = validate_next(next_url)
        if not resp['success']:
            return render(request, 'error.html',
                                      {'data': resp,
                                    'error': resp['message']})
        else:
            return HttpResponseRedirect(resp['message'])

    # Setup defaults
    username = None
    login_ = True
    show_auth = True
    message = crits_config.crits_message
    token_message = """
<b>If you are not using TOTP or not sure what TOTP is,<br />leave the Token field empty.</b><br />
If you are setting up TOTP for the first time, please enter a PIN above.<br />
If you are already setup with TOTP, please enter your PIN + Key above."""
    response = {}

    # Check for remote user being enabled and check for user
    if crits_config.remote_user:
        show_auth = False
        username = request.META.get(settings.REMOTE_USER_META,None)
        if username:
            resp = login_user(username, None, next_url, user_agent,
                              remote_addr, accept_language, request,
                              totp_pass=None)
            if resp['success']:
                return HttpResponseRedirect(resp['message'])
            else:
                # Login failed, set messages/settings and continue
                message = resp['message']
                login_ = False
                if resp['type'] == "totp_required":
                    login_ = True
        else:
            logger.warn("REMOTE_USER enabled, but no user passed.")
            message = 'REMOTE_USER not provided. Please notify an admin.'
            return render(request, 'login.html',
                                      {'next': url,
                                       'theme': 'default',
                                       'login': False,
                                       'show_auth': False,
                                       'message': message,
                                       'token_message': token_message})

    # Attempt authentication
    if request.method == 'POST' and request.is_ajax():
        next_url = request.POST.get('next_url', None)
        # Get username from form if this is not Remote User
        if not crits_config.remote_user:
            username = request.POST.get('username', None)

        # Even if it is remote user, try to get password.
        # Remote user will not have one so we pass None.
        password = request.POST.get('password', None)

        # TOTP can still be required for Remote Users
        totp_pass = request.POST.get('totp_pass', None)
        if username is None:
            response['success'] = False
            response['message'] = 'Unknown user, bad password, or user does not have permission to log on using the web UI.'
            return HttpResponse(json.dumps(response),
                                content_type="application/json")
        logging_in_user = get_user_info(username)
        if logging_in_user is None:
            response['success'] = False
            response['message'] = 'Unknown user, bad password, or user does not have permission to log on using the web UI.'
            return HttpResponse(json.dumps(response),
                                content_type="application/json")
        logging_in_user.get_access_list(update=True)
        if (not username or logging_in_user is None or not logging_in_user.has_access_to(GeneralACL.WEB_INTERFACE) or
                (not totp_pass and crits_config.totp_web == 'Required')):
            response['success'] = False
            response['message'] = 'Unknown user, bad password, or user does not have permission to log on using the web UI.'
            return HttpResponse(json.dumps(response),
                                content_type="application/json")

        #This casues auth failures with LDAP and upper case name parts
        #username = username.lower()

        # login_user will handle the following cases:
        # - User logging in with no TOTP enabled.
        # - User logging in with TOTP enabled.
        # - User logging in and setting up TOTP for the first time.
        #   It should return the string to use for setting up their
        #   authenticator and then prompt the user to submit pin + token.
        resp = login_user(username, password, next_url, user_agent,
                          remote_addr, accept_language, request,
                          totp_pass=totp_pass)
        return HttpResponse(json.dumps(resp), content_type="application/json")

    # Display template for authentication
    return render(request, 'login.html',
                              {'next': url,
                               'theme': 'default',
                               'login': login_,
                               'show_auth': show_auth,
                               'message': message,
                               'token_message': token_message})

def reset_password(request):
    """
    Reset a user password.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        action = request.POST.get('action', None)
        username = request.POST.get('username', None)
        email = request.POST.get('email', None)
        submitted_rcode = request.POST.get('reset_code', None)
        new_p = request.POST.get('new_p', None)
        new_p_c = request.POST.get('new_p_c', None)
        user = request.user
        return reset_user_password(username=username,
                                   action=action,
                                   email=email,
                                   submitted_rcode=submitted_rcode,
                                   new_p=new_p,
                                   new_p_c=new_p_c,
                                   analyst=user)

    return render(request, 'login.html', {'reset': True})

@user_passes_test(user_can_view_data)
def profile(request, user=None):
    """
    Render the User Profile page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param username: The user to render the profile page for.
    :type username: str
    :returns: :class:`django.http.HttpResponse`
    """

    if user:
        username = user.username
    else:
        username = request.user.username
    args = generate_user_profile(username,request)
    if 'status'in args and args['status'] == "ERROR":
        return render(request, 'error.html',
                                  {'data': request,
                                   'error': "Invalid request"},
                                  )
    return render(request, 'profile.html', args)

@user_passes_test(user_can_view_data)
def dashboard(request):
    """
    Render the Dashboard.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_dashboard(request)

@user_passes_test(user_can_view_data)
def counts_listing(request,option=None):
    """
    Render the Counts jtable.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_counts_jtable(request, option)

@user_passes_test(user_can_view_data)
def source_releasability(request):
    """
    Modify a top-level object's releasability. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        type_ = request.POST.get('type', None)
        id_ = request.POST.get('id', None)
        name = request.POST.get('name', None)
        note = request.POST.get('note', None)
        action = request.POST.get('action', None)
        date = request.POST.get('date', datetime.datetime.now())
        user = request.user
        if not isinstance(date, datetime.datetime):
            date = parse(date, fuzzy=True)

        acl = get_acl_object(type_)

        if not type_ or not id_ or not name or not action:
            error = "Modifying releasability requires a type, id, source, and action"
            return render(request, "error.html", {"error" : error })
        if action  == "add":
            if user.has_access_to(acl.RELEASABILITY_ADD):
                result = add_releasability(type_, id_, name, user.username)
            else:
                result = {'success':False,
                          'message':'User does not have permission to add releasability.'}
        elif action  == "add_instance":
            if user.has_access_to(acl.RELEASABILITY_ADD):
                result = add_releasability_instance(type_, id_, name, user.username,
                                                    note=note)
            else:
                result = {'success':False,
                          'message':'User does not have permission to add releasability.'}
        elif action == "remove":
            if user.has_access_to(acl.RELEASABILITY_DELETE):
                result = remove_releasability(type_, id_, name, user.username)
            else:
                result = {'success':False,
                          'message':'User does not have permission to remove releasability.'}
        elif action == "remove_instance":
            if user.has_access_to(acl.RELEASABILITY_DELETE):
                result = remove_releasability_instance(type_, id_, name, date, user.username)
            else:
                result = {'success':False,
                          'message':'User does not have permission to delete releasability.'}
        else:
            error = "Unknown releasability action: %s" % action
            return render(request, "error.html", {"error" : error })
        if result['success']:
            subscription = {
                'type': type_,
                'id': id_
            }

            html = render_to_string('releasability_header_widget.html',
                                    {'releasability': result['obj'],
                                     'subscription': subscription},
                                    request=request)
            response = {'success': result['success'],
                        'html': html}
        else:
            response = {'success': result['success'],
                        'error': result['message']}
        return HttpResponse(json.dumps(response),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST!"
        return render(request, "error.html", {"error" : error })

def source_access(request):
    """
    Modify a user's profile. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        form = SourceAccessForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            result = modify_source_access(request.user.username,
                                          data)
            if result['success']:
                message = '<div>User modified successfully!</div>'
                result['message'] = message
            return HttpResponse(json.dumps(result),
                                content_type="application/json")
        else:
            return HttpResponse(json.dumps({'form':form.as_table()}),
                                content_type="application/json")
    else:
        error = "Expected AJAX POST!"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def source_add(request):
    """
    Add a source to CRITs. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        source_form = AddSourceForm(request.POST)
        user = request.user
        if source_form.is_valid():
            if user.has_access_to(GeneralACL.ADD_NEW_SOURCE):
                result = add_new_source(source_form.cleaned_data['source'],
                                        user)
                if result:
                    msg = ('<div>Source added successfully! Add this source to '
                           'users to utilize it.</div>')
                    message = {'message': msg,
                               'success': True}
                else:
                    message = {'message': '<div>Source addition failed!</div>', 'success':
                               False}
            else:
                message = {'message': 'User does not have permission to add source.', 'success':False}

        else:
            message = {'success': False,
                       'form': source_form.as_table()}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    return render(request, "error.html", {"error" : 'Expected AJAX POST' })

@user_passes_test(user_can_view_data)
def role_add(request):
    """
    Add a role to CRITs. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        role_form = AddRoleForm(request.POST)
        user = request.user
        if role_form.is_valid():
            if user.has_access_to(GeneralACL.ADD_NEW_USER_ROLE):
                name = role_form.cleaned_data['name']
                description = role_form.cleaned_data['description']
                copy_from = role_form.cleaned_data['copy_from']
                result = add_new_role(name,
                                      copy_from,
                                      description,
                                      user)
                if result['success']:
                    url = reverse('crits-core-views-role_details',
                                  args=[result['id']])
                    message = {'message': '<div><a href="%s">Role</a> added successfully!</div>' % url,
                               'success': True}
                else:
                    message = {'message': '<div>Role addition failed!</div>',
                               'success': False}
            else:
                message = {'message': 'User does not have permission to add user role.',
                           'success': False}
        else:
            message = {'success': False,
                       'form': role_form.as_table()}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    return render(request, "error.html", {"error" : 'Expected AJAX POST'})

@user_passes_test(user_can_view_data)
def role_graph(request):
    """
    Render the role graph.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    analyst = request.user.username
    if request.method == "GET":
        start_type = request.GET.get('start_type', 'roles')
        start_node = request.GET.get('start_node', None)
        expansion_node = request.GET.get('expansion_node', None)
    if request.method == "POST" and request.is_ajax():
        start_type = request.POST.get('start_type', 'roles')
        start_node = request.POST.get('start_node', None)
        expansion_node = request.POST.get('expansion_node', None)
        result = render_role_graph(start_type,
                                start_node,
                                expansion_node,
                                analyst)
        if result:
            return HttpResponse(json.dumps(result),
                                content_type="application/json")
    return render(request, "role_graph.html",
                              {"start_type": start_type,
                              "start_node": start_node,
                              "expansion_node": expansion_node})

@user_passes_test(user_can_view_data)
def add_update_source(request, method, obj_type, obj_id):
    """
    Add/Update a source for a top-level object. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param method: Whether this is an "add" or "update".
    :type method: str
    :param obj_type: The type of top-level object.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        form = SourceForm(request.user, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = request.user
            acl = get_acl_object(obj_type)
            # check to see that this user can already see the object
            if (data['name'] in user_sources(user)):
                if method == "add":
                    date = datetime.datetime.now()
                    if user.has_access_to(acl.SOURCES_ADD):
                        result = source_add_update(obj_type,
                                                   obj_id,
                                                   method,
                                                   data['name'],
                                                   method=data['method'],
                                                   reference=data['reference'],
                                                   tlp=data['tlp'],
                                                   date=date,
                                                   user=user.username)
                    else:
                        result = {"success":False,
                                  "message":"User does not have permission to add sources to object."}
                else:
                    date = datetime.datetime.strptime(data['date'],
                                                      settings.PY_DATETIME_FORMAT)
                    if user.has_access_to(acl.SOURCES_EDIT):
                        result = source_add_update(obj_type,
                                                   obj_id,
                                                   method,
                                                   data['name'],
                                                   method=data['method'],
                                                   reference=data['reference'],
                                                   tlp=data['tlp'],
                                                   date=date,
                                                   user=user.username)
                    else:
                        result = {"success":False,
                                  "message":"User does not have permission to edit sources."}

                if 'object' in result:
                    if method == "add":
                        result['header'] = result['object'].name
                        result['data_field'] = 'name'
                        result['html'] = render_to_string('sources_header_widget.html',
                                                          {'source': result['object'],
                                                           'obj_type': obj_type,
                                                           'obj_id': obj_id},
                                                          request=request)
                    else:
                        result['html'] = render_to_string('sources_row_widget.html',
                                                          {'source': result['object'],
                                                           'instance': result['instance'],
                                                           'obj_type': obj_type,
                                                           'obj_id': obj_id},
                                                          request=request)
                return HttpResponse(json.dumps(result,
                                               default=json_handler),
                                    content_type="application/json")
            else:
                return HttpResponse(json.dumps({'success': False,
                                                'form': form.as_table()}),
                                    content_type="application/json")
        else:
            return HttpResponse(json.dumps({'success': False,
                                            'form':form.as_table()}),
                                content_type="application/json")
    return HttpResponse({})

@user_passes_test(user_can_view_data)
def remove_source(request, obj_type, obj_id):
    """
    Remove a source from a top-level object. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param obj_type: The type of top-level object.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        date = datetime.datetime.strptime(request.POST['key'],
                                            settings.PY_DATETIME_FORMAT)
        name = request.POST['name']

        user = request.user
        acl = get_acl_object(obj_type)

        if user.has_access_to(acl.SOURCES_DELETE):
            result = source_remove(obj_type,
                                    obj_id,
                                    name,
                                    date,
                                    '%s' % user.username)
        else:
            result = {"success":False,
                      "message":"User does not have permission to remove sources."}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    return HttpResponse({})

@user_passes_test(user_can_view_data)
def remove_all_source(request, obj_type, obj_id):
    """
    Remove all sources from a top-level object. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param obj_type: The type of top-level object.
    :type obj_type: str
    :param obj_id: The ObjectId to search for.
    :type obj_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        name = request.POST['key']
        result = source_remove_all(obj_type,
                                    obj_id,
                                    name, '%s' % request.user.username)
        result['last'] = True
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    return HttpResponse({})

@user_passes_test(user_can_view_data)
def bucket_promote(request):
    """
    Promote a bucket to a Campaign. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    bucket = request.GET.get("name", None)
    if not bucket:
        return render(request, "error.html", {'error': 'Need a bucket.'})
    form = CampaignForm(request.POST)
    if form.is_valid():
        analyst = request.user.username
        confidence = form.cleaned_data['confidence']
        name = form.cleaned_data['name']
        related = form.cleaned_data['related']
        description = form.cleaned_data['description']
        result = promote_bucket_list(bucket,
                                     confidence,
                                     name,
                                     related,
                                     description,
                                     analyst)
        return HttpResponse(json.dumps(result), content_type="application/json")

@user_passes_test(user_can_view_data)
def bucket_modify(request):
    """
    Modify a bucket list for a top-level object. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        tags = request.POST['tags'].split(",")
        oid = request.POST['oid']
        itype = request.POST['itype']
        user = request.user
        acl = get_acl_object(itype)
        if user.has_access_to(acl.BUCKETLIST_EDIT):
            modify_bucket_list(itype, oid, tags, request.user.username)
    return HttpResponse({})

@user_passes_test(user_can_view_data)
def bucket_list(request, option=None):
    """
    Generate the jtable data for rendering in the list template.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_bucket_csv(request)
    return generate_bucket_jtable(request, option)

@user_passes_test(user_can_view_data)
def download_object(request):
    """
    Download a top-level object.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method != "POST":
        return render(request, "error.html", {"error" : "Expecting POST."})

    form = DownloadFileForm(request.POST)
    if form.is_valid():
        total_limit = form.cleaned_data['total_limit']
        depth_limit = form.cleaned_data['depth_limit']
        rel_limit = form.cleaned_data['rel_limit']
        bin_fmt = form.cleaned_data['bin_fmt']
        rst_fmt = form.cleaned_data['rst_fmt']
        objects = form.cleaned_data['objects']
        obj_type = form.cleaned_data['obj_type']
        obj_id = form.cleaned_data['obj_id']

        crits_config = CRITsConfig.objects().first()
        total_max = getattr(crits_config, 'total_max', settings.TOTAL_MAX)
        depth_max = getattr(crits_config, 'depth_max', settings.DEPTH_MAX)
        rel_max = getattr(crits_config, 'rel_max', settings.REL_MAX)
        user = request.user

        acl = get_acl_object(obj_type)

        try:
            total_limit = int(total_limit)
            depth_limit = int(depth_limit)
            rel_limit = int(rel_limit)
            if total_limit < 0 or depth_limit < 0 or rel_limit < 0:
                raise
        except:
            return render(request, "error.html", {"error" : "Limits must be positive integers."})

        # Don't exceed the configured maximums. This is done in the view
        # so that scripts can enforce their own limmits.
        if total_limit > total_max:
            total_limit = total_max
        if depth_limit > depth_max:
            depth_limit = depth_max
        if rel_limit > rel_max:
            rel_limit = rel_max

        sources = user_sources(request.user.username)
        if not sources:
            return render(request, "error.html", {"error" : "No matching data."})

        if user.has_access_to(acl.DOWNLOAD):
            result = download_object_handler(total_limit,
                                             depth_limit,
                                             rel_limit,
                                             rst_fmt,
                                             bin_fmt,
                                             objects,
                                             [(obj_type, obj_id)],
                                             sources)
        else:
            return render(request, "error.html",
                                      {"error" : "User does not have permission to download %s" % obj_type})

        if not result['success']:
            return render(request, "error.html", {"error" : "No matching data."})

        response = HttpResponse()
        response['mimetype'] = result['mimetype']
        response['Content-Disposition'] = 'attachment; filename=%s' % result['filename']
        response.write(result['data'])
        return response
    else:
        return render(request, "error.html", {"error" : "Invalid form."})

@user_passes_test(user_can_view_data)
def timeline(request, data_type="dns"):
    """
    Render the timeline.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param data_type: The type of data to include in the timeline.
    :type data_type: str
    :returns: :class:`django.http.HttpResponse`
    """

    format = request.GET.get("format", "none")
    user = request.user
    sources = user_sources(user)
    query = {}
    params = {}
    if request.GET.get("campaign"):
        query["campaign.name"] = request.GET.get("campaign")
        params["campaign"] = query["campaign.name"]
    if request.GET.get("backdoor"):
        query["backdoor.name"] = request.GET.get("backdoor")
        params["backdoor"] = query["backdoor.name"]
    query["source.name"] = {"$in": sources}
    page_title = data_type
    if format == "json":
        timeglider = []
        tline = {}
        tline['id'] = "tline"
        tline['focus_date'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tline['initial_zoom'] = "20"
        tline['timezone'] = strftime("%z", gmtime())
        events = []

        # DNS data

        if data_type == "dns" and user.has_access_to(GeneralACL.DNS_TIMELINE_READ):
            tline['title'] = "DNS"
            events = dns_timeline(query, user, sources)
        # Email data

        elif data_type == "email" and user.has_access_to(GeneralACL.EMAILS_TIMELINE_READ):
                tline['title'] = "Emails"
                events = email_timeline(query, user, sources)
            # Indicator data

        elif data_type == "indicator" and user.has_access_to(GeneralACL.indicators_timeline_read):
                tline['title'] = "Indicators"
                tline['initial_zoom'] = "14"
                events = indicator_timeline(query, user, sources)

        if events:
            tline['events'] = events
            timeglider.append(tline)
            return HttpResponse(json.dumps(timeglider,
                                           default=json_util.default),
                                content_type="application/json")
        else:
            return HttpResponse(json.dumps({'success': False,
                                            'message': "User does not have permission to view timeline."}),
                                content_type="application/json")
    else:
        if user.has_access_to(GeneralACL.DNS_TIMELINE_READ) and data_type=="dns":
            return render(request, 'timeline.html',
                                      {'data_type': data_type,
                                       'params': json.dumps(params),
                                       'page_title': page_title})

        elif user.has_access_to(GeneralACL.EMAILS_TIMELINE_READ) and data_type=="email":
            return render(request, 'timeline.html',
                                      {'data_type': data_type,
                                       'params': json.dumps(params),
                                       'page_title': page_title})

        elif user.has_access_to(GeneralACL.indicators_timeline_read) and data_type=="indicator":
            return render(request, 'timeline.html',
                                      {'data_type': data_type,
                                       'params': json.dumps(params),
                                       'page_title': page_title})
        else:
            error = "User does not have permission to view timeline."
            return render(request, "error.html",
                                      {"error" : error })

def base_context(request):
    """
    Set of common content to include in the Response so it is always available
    to every template on every page. This is included in settings.py in the
    TEMPLATE_CONTEXT_PROCESSORS.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: dict
    """

    crits_config = CRITsConfig.objects().first()
    base_context = {}
    classification = getattr(crits_config,
                             'classification',
                             settings.CLASSIFICATION)
    instance_name = getattr(crits_config,
                            'instance_name',
                            settings.INSTANCE_NAME)
    company_name = getattr(crits_config,
                           'company_name',
                           settings.COMPANY_NAME)
    crits_version = settings.CRITS_VERSION
    enable_toasts = getattr(crits_config,
                            'enable_toasts',
                            settings.ENABLE_TOASTS)
    git_branch = getattr(crits_config,
                         'git_branch',
                         settings.GIT_BRANCH)
    git_hash = getattr(crits_config,
                       'git_hash',
                        settings.GIT_HASH)
    git_hash_long = getattr(crits_config,
                       'git_hash_long',
                        settings.GIT_HASH_LONG)
    git_repo_url = getattr(crits_config,
                            'git_repo_url',
                            settings.GIT_REPO_URL)
    hide_git_hash = getattr(crits_config,
                      'hide_git_hash',
                      settings.HIDE_GIT_HASH)
    splunk_url = getattr(crits_config,
                         'splunk_search_url',
                         settings.SPLUNK_SEARCH_URL)
    secure_cookie = getattr(crits_config,
                           'secure_cookie',
                           settings.SECURE_COOKIE)
    mongo_database = settings.MONGO_DATABASE
    base_context['crits_config'] = crits_config
    base_context['current_datetime'] = datetime.datetime.now()
    base_context['classification'] = classification.upper()
    base_context['instance_name'] = instance_name
    base_context['company_name'] = company_name
    base_context['crits_version'] = crits_version
    base_context['enable_toasts'] = enable_toasts
    if git_repo_url:
        base_context['git_repo_link'] = "<a href='"+git_repo_url+"/commit/"+git_hash_long+"'>"+git_branch+':'+git_hash+"</a>"
    else:
        base_context['git_repo_link'] = "%s:%s" % (git_branch, git_hash)
    base_context['hide_git_hash'] = hide_git_hash
    base_context['splunk_search_url'] = splunk_url
    base_context['mongo_database'] = mongo_database
    base_context['secure_cookie'] = secure_cookie
    base_context['service_nav_templates'] = settings.SERVICE_NAV_TEMPLATES
    base_context['service_cp_templates'] = settings.SERVICE_CP_TEMPLATES
    base_context['service_tab_templates'] = settings.SERVICE_TAB_TEMPLATES
    if (request.user.is_authenticated if django_version >= (1, 10) else request.user.is_authenticated()):
        user = request.user
        base_context['acl'] = ReadACL
        base_context['GeneralACL'] = GeneralACL
        # The way this is currently implemented, this must stay in base_context
        try:
            base_context['new_action'] = ActionsForm(initial={'analyst': user,
                'active': "off",
                'date': datetime.datetime.now()})
        except Exception, e:
            logger.warning("Base Context ActionsForm Error: %s" % e)

        # Other info acquired from functions
        try:
            base_context['email_notifications'] = get_user_email_notification(user.username)
        except Exception, e:
            logger.warning("Base Context get_user_email_notification Error: %s" % e)
        try:
            base_context['user_notifications'] = get_user_notifications(user.username,
                                                                        count=True)
        except Exception, e:
            logger.warning("Base Context get_user_notifications Error: %s" % e)
        try:
            base_context['user_organization'] = get_user_organization(user)
        except Exception, e:
            logger.warning("Base Context get_user_organization Error: %s" % e)
        try:
            base_context['user_source_list'] = user_sources(user)
        except Exception, e:
            logger.warning("Base Context user_sources Error: %s" % e)

        nav_template = get_nav_template(request.user.prefs.nav)
        if nav_template != None:
            base_context['nav_template'] = nav_template

        base_context['newer_notifications_location'] = request.user.prefs.toast_notifications.get('newer_notifications_location', 'top')
        base_context['initial_notifications_display'] = request.user.prefs.toast_notifications.get('initial_notifications_display', 'show')
        base_context['max_visible_notifications'] = request.user.prefs.toast_notifications.get('max_visible_notifications', 5)
        base_context['notification_anchor_location'] = request.user.prefs.toast_notifications.get('notification_anchor_location', 'bottom_right')

        base_context['nav_config'] = {'text_color': request.user.prefs.nav.get('text_color'),
                                      'background_color': request.user.prefs.nav.get('background_color'),
                                      'hover_text_color': request.user.prefs.nav.get('hover_text_color'),
                                      'hover_background_color': request.user.prefs.nav.get('hover_background_color')}

    # As said in stable-4, I do not believe that this is neccessary anymore with the current implementation
    #try:
    #    base_context['source_create'] = AddSourceForm()
    #except Exception, e:
    #    logger.warning("Base Context AddSourceForm Error: %s" % e)

    base_context['category_list'] = [
                                    {'collection': '', 'name': ''},
                                    {'collection': settings.COL_BACKDOORS,
                                        'name': 'Backdoors'},
                                    {'collection': settings.COL_CAMPAIGNS,
                                        'name': 'Campaigns'},
                                    {'collection': settings.COL_EVENT_TYPES,
                                        'name': 'Event Types'},
                                    {'collection': settings.COL_IDB_ACTIONS,
                                        'name': 'Indicator Actions'},
                                    {'collection': settings.COL_OBJECT_TYPES,
                                        'name': 'Object Types'},
                                    {'collection': settings.COL_RAW_DATA_TYPES,
                                        'name': 'Raw Data Types'},
                                    {'collection': settings.COL_RELATIONSHIP_TYPES,
                                        'name': 'Relationship Types'},
                                    {'collection': settings.COL_SOURCE_ACCESS,
                                        'name': 'Sources'},
                                    {'collection': settings.COL_SIGNATURE_TYPES,
                                        'name': 'Signature Types'},
                                    {'collection': settings.COL_SIGNATURE_DEPENDENCY,
                                        'name': 'Signature Dependency'},
                                    ]

    return base_context

def user_context(request):
    """
    Set of common content about the user to include in the Response so it is
    always available to every template on every page. This is included in
    settings.py in the TEMPLATE_CONTEXT_PROCESSORS.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: dict
    """

    context = {}
    # Get user theme
    user = CRITsUser.objects(username=request.user.username).first()
    if user:
        context['theme'] = user.get_preference('ui', 'theme', 'default')
        favorite_count = 0
        favorites = user.favorites.to_dict()
        for favorite in favorites.values():
            favorite_count += len(favorite)
        context['user_favorites'] = user.favorites.to_json()
        context['favorite_count'] = favorite_count
    return context

@user_passes_test(user_can_view_data)
def get_user_source_list(request):
    """
    Get a user's source list. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        user_source_access = user_sources('%s' % request.user.username)
        message = {'success': True,
                   'data': user_source_access}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def user_source_access(request, username=None):
    """
    Get a user's source access list. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param username: The user to get the sources for.
    :type username: str.
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        if not username:
            username = request.POST.get('username', None)
        user = get_user_info(username)
        if user:
            user = user.to_dict()
            if 'roles' not in user:
                user['roles'] = ''
        else:
            user = {'username': '',
                    'roles': '',
                    'organization': settings.COMPANY_NAME}
        form = SourceAccessForm(initial=user)
        message = {'success': True,
                   'message': form.as_table()}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def user_preference_toggle(request, section, setting):
    """
    Toggle a preference for a user. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param section: The preferences section to toggle.
    :type section: str.
    :param setting: The setting to toggle.
    :type setting: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        pref = generate_user_preference(request, section, 'toggle', setting)
        if not pref or 'toggle' not in pref:
            error = "Unexpected Preference Toggle Received in AJAX POST"
            return render(request, "error.html", {"error" : error })

        result = toggle_user_preference(request.user.username, section, setting, is_enabled=pref.get('enabled'))

        if result['success']:
            result["message"] = "(Saved)"
            if result['state']:
                result["text"] = "Enabled"
                result["title"]= "Click to Disable"
            else:
                result["text"] = "Disabled"
                result["title"]= "Click to Enable"

            if 'reload' in pref:
                result["reload"] = pref['reload']

        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def user_preference_update(request, section):
    """
    Update a user preference. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param section: The preferences section to toggle.
    :type section: str.
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        result = {}

        pref = generate_user_preference(request,section)

        if not pref or 'formclass' not in pref or not callable(pref['formclass']):
            error = "Unexpected Form Received in AJAX POST"
            return render(request, "error.html", {"error" : error })

        form = (pref['formclass'])(request, request.POST)

        if form.is_valid():
            data = form.cleaned_data

            # Incoming attributes may be flattened, e.g.
            #     option.one.sub.key = value
            # So this will unflatten them into a option: {one: a} dict
            values = unflatten( data )

            result = update_user_preference(request.user.username, section, values)
            result['values'] = values
            if result['success']:
                result["message"] = "(Saved)"
                if 'reload' in pref:
                    result["reload"] = pref['reload']

        else:
            result['success'] = False
            pref['form'] = form  # Inject our form instance with validation results
            result['html'] = render_to_string("preferences_widget.html",
                                              {'pref': pref},
                                              request=request)

        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def clear_user_notifications(request):
    """
    Clear a user's notifications.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    remove_user_notifications("%s" % request.user.username)
    return HttpResponseRedirect(reverse('crits-core-views-profile') + '#notifications_button')

@user_passes_test(user_can_view_data)
def delete_user_notification(request, type_, oid):
    """
    Delete a user notification. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param type_: The top-level object type.
    :type type_: str
    :param oid: The ObjectId.
    :type oid: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        result = remove_user_from_notification("%s" % request.user.username,
                                               oid,
                                               type_)
        message = "<p style=\"text-align: center;\">You have no new notifications!</p>"
        result['message'] = message
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def change_subscription(request, stype, oid):
    """
    Subscribe/unsubscribe a user from this top-level object. Should be an AJAX
    POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param stype: The CRITs type of the top-level object.
    :type stype: str
    :param oid: The ObjectId of the top-level object.
    :type oid: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        username = "%s" % request.user.username
        message = ""
        if is_user_subscribed(username, stype, oid):
            unsubscribe_user(username, stype, oid)
            message = ("<span class=\"ui-icon ui-icon-signal-diag subscription_link"
                       "_disable\" title=\"Subscribe\"></span>")
        else:
            subscribe_user(username, stype, oid)
            message = ("<span class=\"ui-icon ui-icon-close subscription_link"
                       "_enable\" title=\"Unsubscribe\"></span>")
        result = {'success': True,
                  'message': message}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def source_subscription(request):
    """
    Subscribe/unsubscribe a user from this source. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        username = "%s" % request.user.username
        user_source_access = user_sources(username)
        source = request.POST['source']
        if source not in user_source_access:
            error = "You do not have access to that source."
            return render(request, "error.html", {"error" : error })
        message = ""
        if is_user_subscribed_to_source(username, source):
            unsubscribe_from_source(username, source)
            message = "unsubscribed"
        else:
            subscribe_to_source(username, source)
            message = "subscribed"
        result = {'success': True, 'message': message}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

def collections(request):
    """
    Set of common content about collections to include in the Response so it is
    always available to every template on every page. This is included in
    settings.py in the TEMPLATE_CONTEXT_PROCESSORS.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: dict
    """

    colls = {}
    colls['COL_CERTIFICATES'] = settings.COL_CERTIFICATES
    colls['COL_EMAIL'] = settings.COL_EMAIL
    colls['COL_EVENTS'] = settings.COL_EVENTS
    colls['COL_DOMAINS'] = settings.COL_DOMAINS
    colls['COL_INDICATORS'] = settings.COL_INDICATORS
    colls['COL_IPS'] = settings.COL_IPS
    colls['COL_PCAPS'] = settings.COL_PCAPS
    colls['COL_RAW_DATA'] = settings.COL_RAW_DATA
    colls['COL_SAMPLES'] = settings.COL_SAMPLES
    colls['COL_SIGNATURES'] = settings.COL_SIGNATURES
    colls['COL_TARGETS'] = settings.COL_TARGETS
    return colls

@user_passes_test(user_can_view_data)
def change_password(request):
    """
    Change a user's password. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        username = request.user.username
        current_p = request.POST['current_p']
        new_p = request.POST['new_p']
        new_p_c = request.POST['new_p_c']
        result = change_user_password(username,
                                      current_p,
                                      new_p,
                                      new_p_c)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def change_totp_pin(request):
    """
    Change a user's TOTP pin. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        username = request.user.username
        new_pin = request.POST.get('new_pin', None)
        if new_pin:
            result = save_user_secret(username, new_pin, "crits", (200,200))
            if result['success']:
                result['message'] = "Secret: %s" % result['secret']
                if result['qr_img']:
                    qr_img = result['qr_img']
                    result['qr_img'] = '<br /><img src="data:image/png;base64,'
                    result['qr_img'] += '%s" />' % qr_img
            else:
                result['message'] = "Secret generation failed"
        else:
            result = {'message': "Please provide a pin"}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def control_panel(request):
    """
    Render the control panel.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    return render(request, "control_panel.html", {})

@user_passes_test(user_can_view_data)
def roles_listing(request, option=None):
    """
    Generate the jtable data for rendering in the list template.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_roles_jtable(request, option)

@user_passes_test(user_can_view_data)
def users_listing(request, option=None):
    """
    Generate the jtable data for rendering in the list template.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_users_jtable(request, option)

@user_passes_test(user_can_view_data)
def toggle_user_active(request):
    """
    Toggle a user active/inactive. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        user = request.POST.get('username', None)
        analyst = request.user.username
        if not user:
            result = {'success': False}
        else:
            toggle_active(user, analyst)
            result = {'success': True}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def item_editor(request):
    """
    Render the item editor control panel page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    counts = {}
    obj_list = [ActorThreatIdentifier,
                Campaign,
                Action,
                RawDataType,
                SignatureType,
                SignatureDependency,
                SourceAccess]
    for col_obj in obj_list:
        counts[col_obj._meta['crits_type']] = col_obj.objects().count()
    return render(request, "item_editor.html", {'counts': counts})

@user_passes_test(user_can_view_data)
def items_listing(request, itype, option=None):
    """
    Generate the jtable data for rendering in the list template.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param itype: The item type.
    :type itype: str
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_items_jtable(request, itype, option)

@user_passes_test(user_can_view_data)
def audit_listing(request, option=None):
    """
    Generate the jtable data for rendering in the list template.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'csv', 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user
    if user.has_access_to(GeneralACL.CONTROL_PANEL_AUDIT_LOG_READ):
        if option == "csv":
            return generate_audit_csv(request)
        return generate_audit_jtable(request, option)
    else:
        error = "User does not have permission to view audit listing."
        return render(request, "error.html",
                                  {"error" : error })

@user_passes_test(user_can_view_data)
def toggle_item_active(request):
    """
    Toggle an item active/inactive. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        type_ = request.POST.get('coll', None)
        oid = request.POST.get('oid', None)
        analyst = request.user.username
        if not oid or not type_:
            result = {'success': False}
        else:
            result = toggle_item_state(type_, oid, analyst)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def role_details(request, rid=None):
    """
    Generate Role details template.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param rid: The ObjectId of the Role to get details for.
    :type rid: str
    :returns: :class:`django.http.HttpResponse`
    """

    # Silly Django :(
    try:
        roles = request.POST.getlist('roles', None)
    except:
        roles = None
    analyst = request.user.username
    template = "role_detail.html"
    (new_template, args) = get_role_details(rid, roles, analyst)
    if new_template:
        template = new_template
    return render(request, template,
                              args)

@user_passes_test(user_can_view_data)
def role_value_change(request):
    """
    Change the value of a Role item. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        rid = request.POST.get('rid', None)
        name = request.POST.get('name', None)
        value = request.POST.get('value', None)
        analyst = request.user.username
        if not rid or not name:
            result = {'success': False}
        else:

            result = set_role_value(rid, name, value, analyst)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html",
                                  {"error" : error })

@user_passes_test(user_can_view_data)
def role_add_source(request):
    """
    Add a source to a Role. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        rid = request.POST.get('rid', None)
        name = request.POST.get('name', None)
        analyst = request.user.username
        if not rid or not name:
            result = {'success': False}
        else:
            result = add_role_source(rid, name, analyst)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html",
                                  {"error" : error })

@user_passes_test(user_can_view_data)
def update_role_name(request):
    """
    Update a Role name. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        rid = request.POST.get('rid', None)
        name = request.POST.get('name', None)
        old_name = request.POST.get('old_name', None)
        analyst = request.user.username
        if not rid or not name:
            result = {'success': False}
        else:
            result = edit_role_name(rid, old_name, name, analyst)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html",
                                  {"error" : error })

@user_passes_test(user_can_view_data)
def update_role_description(request):
    """
    Update a Role description. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        rid = request.POST.get('rid', None)
        description = request.POST.get('description', None)
        analyst = request.user.username
        if not rid or not description:
            result = {'success': False}
        else:
            result = edit_role_description(rid, description, analyst)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html",
                                  {"error" : error })

@user_passes_test(user_can_view_data)
def role_remove_source(request):
    """
    Remove a source from a Role. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        rid = request.POST.get('rid', None)
        name = request.POST.get('name', None)
        analyst = request.user.username
        if not rid or not name:
            result = {'success': False}
        else:
            result = remove_role_source(rid, name, analyst)
        return HttpResponse(json.dumps(result), content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html",
                                  {"error" : error })

@user_passes_test(user_can_view_data)
def download_file(request, sample_md5):
    """
    Download a file. Used mainly for situations where you are not using the
    standard download file modal form in the UI.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param sample_md5: The MD5 of the file to download.
    :type sample_md5: str
    :returns: :class:`django.http.HttpResponse`
    """

    dtype = request.GET.get("type", "sample")
    if dtype=='cert':
        tlo_type = 'Certificate'
    else:
        tlo_type = dtype

    user = request.user
    acl = get_acl_object(tlo_type)
    if user.has_access_to(acl.DOWNLOAD):
        if dtype in ('object', 'pcap', 'cert'):
            return download_grid_file(request, dtype, sample_md5)
        else:
            return render(request, 'error.html',
                                      {'data': request,
                                       'error': "Unknown Type: %s" % dtype})
    else:
        return render(request, 'error.html',
                                  {'data': request,
                                   'error': "User does not have permission to download %s" % dtype})

@user_passes_test(user_can_view_data)
def details(request, type_=None, id_=None):
    """
    Redirect to the details page. This is useful for getting to the details page
    when you know the type and ID but not the information necessary for normally
    getting to the Details page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if not type_ or not id_:
        return render(request, 'error.html', {'error': "Need a type and id to redirect to."})
    redir = details_from_id(type_, id_)
    if redir:
        return HttpResponseRedirect(redir)
    else:
        return render(request, 'error.html', {'error': "No details page exists for type %s" % type_})


@user_passes_test(user_can_view_data)
def add_update_ticket(request, method, type_=None, id_=None):
    """
    Add/update/remove a ticket for a top-level object.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param method: Whether this is an "add", "update", or "remove".
    :type method: str
    :param type_: The CRITs type of the top-level object.
    :type type_: str
    :param id_: The ObjectId to search for.
    :type id_: str
    :returns: :class:`django.http.HttpResponseRedirect`
    """
    user = request.user

    acl = get_acl_object(type_)

    if method =="remove" and request.method == "POST" and request.is_ajax():
        date = datetime.datetime.strptime(request.POST['key'],
                                            settings.PY_DATETIME_FORMAT)
        date = date.replace(microsecond=date.microsecond/1000*1000)
        if user.has_access_to(acl.TICKETS_DELETE):
            result = ticket_remove(type_, id_, date, user)
        else:
            result = {"success":False,
                      "message":"User does not have permission to delete tickets."}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")

    if request.method == "POST" and request.is_ajax():
        form = TicketForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            add = {
                    'ticket_number': data['ticket_number'],
            }
            if method == "add":
                add['date'] = datetime.datetime.now()
                if user.has_access_to(acl.TICKETS_ADD):
                    result = ticket_add(type_, id_, add, user)
                else:
                    result = {"success":False,
                              "message":"User does not have permission to add tickets."}
            else:
                date = datetime.datetime.strptime(data['date'],
                                                         settings.PY_DATETIME_FORMAT)
                date = date.replace(microsecond=date.microsecond/1000*1000)
                add['date'] = date
                if user.has_access_to(acl.TICKETS_EDIT):
                    result = ticket_update(type_, id_, add, user.username)
                else:
                    result = {"success":False,
                              "message":"User does not have permission to modify tickets."}

            crits_config = CRITsConfig.objects().first()
            if 'object' in result:
                result['html'] = render_to_string('tickets_row_widget.html',
                                                  {'ticket': result['object'],
                                                   'crits_config': crits_config,
                                                   'obj_type': type_,
                                                   'obj': class_from_id(type_, id_)},
                                                   request=request)
            return HttpResponse(json.dumps(result,
                                           default=json_handler),
                                content_type="application/json")
        else: #invalid form
            return HttpResponse(json.dumps({'success':False,
                                            'form': form.as_table()}),
                                content_type="application/json")
    else:
        result = {"success":False,
                  "message":"User does not have permission to delete tickets."}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")

    #default. Should we do anything else here?
    return HttpResponse({})

@user_passes_test(user_can_view_data)
def get_search_help(request):
    """
    Render the search help box. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    result = {'template': render_to_string('search_help.html', {})}
    return HttpResponse(json.dumps(result, default=json_handler),
                        content_type="application/json")

@user_passes_test(user_can_view_data)
def get_api_key(request):
    """
    Get an API key for a user. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        username = request.user.username
        name = request.POST.get('name', None)
        if not name:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a name.'}),
                                content_type="application/json")
        result = get_api_key_by_name(username, name)
        if result:
            return HttpResponse(json.dumps({'success': True,
                                            'message': result}),
                                content_type="application/json")
        else:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'No key for that name.'}),
                                content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def create_api_key(request):
    """
    Create an API key for a user. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        username = request.user.username
        name = request.POST.get('name', None)
        if not name:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a name.'}),
                                content_type="application/json")
        result = create_api_key_by_name(username, name)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def make_default_api_key(request):
    """
    Set an API key as default for a user. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        username = request.user.username
        name = request.POST.get('name', None)
        if not name:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a name.'}),
                                content_type="application/json")
        result = make_default_api_key_by_name(username, name)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def revoke_api_key(request):
    """
    Revoke an API key for a user. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == "POST" and request.is_ajax():
        username = request.user.username
        name = request.POST.get('name', None)
        if not name:
            return HttpResponse(json.dumps({'success': False,
                                            'message': 'Need a name.'}),
                                content_type="application/json")
        result = revoke_api_key_by_name(username, name)
        return HttpResponse(json.dumps(result),
                            content_type="application/json")
    else:
        error = "Expected AJAX POST"
        return render(request, "error.html", {"error" : error })

@user_passes_test(user_can_view_data)
def sector_modify(request):
    """
    Modify a sectors list for a top-level object. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user
        acl = get_acl_object(request.POST['itype'])
        if user.has_access_to(acl.SECTORS_EDIT):
            sectors = request.POST['sectors'].split(",")
            oid = request.POST['oid']
            itype = request.POST['itype']
            modify_sector_list(itype, oid, sectors, request.user.username)

    return HttpResponse({})

@user_passes_test(user_can_view_data)
def sector_list(request, option=None):
    """
    Generate the jtable data for rendering in the list template.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_sector_csv(request)
    return generate_sector_jtable(request, option)

@user_passes_test(user_can_view_data)
def get_available_sectors(request):
    """
    Get the available sectors to use.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        return HttpResponse(
            json.dumps(Sectors.values(sort=True), default=json_handler),
            content_type='application/json'
        )
    return HttpResponse({})

@user_passes_test(user_can_view_data)
def bucket_autocomplete(request):
    """
    Get the list of current buckets to autocomplete.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        term = request.POST.get('term', None)
        if term:
            return get_bucket_autocomplete(term)
    return HttpResponse({})

@user_passes_test(user_can_view_data)
def tlp_modify(request):
    """
    Modify the TLP for a top-level object. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        tlp = request.POST['tlp']
        oid = request.POST['oid']
        itype = request.POST['itype']
        results = modify_tlp(itype, oid, tlp, request.user.username)
        return HttpResponse(json.dumps(results), content_type="application/json")
    else:
        return render(request, "error.html",
                                  {"error" : 'Expected AJAX POST.'})

@user_passes_test(user_can_view_data)
def add_preferred_actions(request):
    """
    Add preferred actions to an indicator. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        if 'obj_type' not in request.POST and 'obj_id' not in request.POST:
            result = {'success': False, 'message': "Invalid parameters."}
        else:
            username = request.user.username
            obj_type = request.POST['obj_type']
            obj_id = request.POST['obj_id']
            result = do_add_preferred_actions(obj_type, obj_id, username)
            if 'object' in result:
                result['html'] = ''
                for obj in result['object']:
                    result['html'] += render_to_string('indicators_action_row_widget.html',
                                                       {'action': obj,
                                                        'indicator_id': obj_id})
    else:
        result = {'success': False, 'message': "Expected AJAX POST"}
    return HttpResponse(json.dumps(result, default=json_handler),
                        content_type='application/json')

@user_passes_test(user_can_view_data)
def new_action(request):
    """
    Add a new action. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        form = NewActionForm(request.POST)
        user = request.user
        if form.is_valid():
            if user.has_access_to(GeneralACL.ADD_NEW_INDICATOR_ACTION):
                result = add_new_action(form.cleaned_data['action'],
                                        form.cleaned_data['object_types'],
                                        form.cleaned_data['preferred'],
                                        user)
                if result:
                    message = {'message': '<div>Action added successfully!</div>',
                               'success': True}
                else:
                    message = {'message': '<div>Action addition failed!</div>',
                               'success': False}
            else:
                message = {'message': '<div>User does not have permission to add indicator action.</div>',
                           'success': False}
        else:
            message = {'form': form.as_table()}
        return HttpResponse(json.dumps(message),
                            content_type="application/json")
    return render(request, 'error.html',
                              {'error': 'Expected AJAX POST'})

@user_passes_test(user_can_view_data)
def add_update_action(request, method, obj_type, obj_id):
    """
    Add/update an object's action. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param method: Whether we are adding or updating.
    :type method: str ("add", "update")
    :param obj_type: The class type of the top level object.
    :type obj_id: str
    :param obj_id: The ObjectId of the top level object to update.
    :type obj_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user
        acl = get_acl_object(obj_type)
        form = ActionsForm(request.POST)
        form.is_valid()
        data = form.cleaned_data
        data['action_type'] = request.POST.get('action_type')
        add = {
            'action_type': data['action_type'],
            'begin_date': data['begin_date'] if data['begin_date'] else '',
            'end_date': data['end_date'] if data['end_date'] else '',
            'performed_date': data['performed_date'] if data['performed_date'] else '',
            'active': data['active'],
            'reason': data['reason'],
        }
        if method == "add":
            add['date'] = datetime.datetime.now()
            if user.has_access_to(acl.ACTIONS_ADD):
                result = action_add(obj_type, obj_id, add, user)
            else:
                result = {"success":False,
                          "message":"User does not have permission to add action."}
        else:
            date = datetime.datetime.strptime(data['date'],
                                                settings.PY_DATETIME_FORMAT)
            date = date.replace(microsecond=date.microsecond/1000*1000)
            add['date'] = date
            if user.has_access_to(acl.ACTIONS_EDIT):
                result = action_update(obj_type, obj_id, add, user.username)
            else:
                result = {"success":False,
                          "message":"User does not have permission to edit action."}
        if 'object' in result:
            result['html'] = render_to_string('action_row_widget.html',
                                                {'action': result['object'],
                                                'obj_type':obj_type,
                                                'obj_id':obj_id})

        return HttpResponse(json.dumps(result,
                                       default=json_handler),
                            content_type='application/json')

    return render(request, "error.html",
                              {'error': 'Expected AJAX/POST'})

@user_passes_test(user_can_view_data)
def remove_action(request, obj_type, obj_id):
    """
    Remove a TLO's action. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :param obj_type: The class type of the top level object.
    :type obj_id: str
    :param obj_id: The ObjectId of the object to remove the action from.
    :type obj_id: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        user = request.user
        if user.has_access_to(acl.ACTIONS_DELETE):
            key = request.POST['key'].split(',')
            date = datetime.datetime.strptime(key[0],
                                              settings.PY_DATETIME_FORMAT)
            date = date.replace(microsecond=date.microsecond/1000*1000)
            result = action_remove(obj_type, obj_id, date, key[1], user)

            return HttpResponse(json.dumps(result),
                                content_type="application/json")
        else:
            result = {"success":False,
                      "message":"User does not have permission to delete action."}
        return HttpResponse(json.dumps(result),
                            content_type="application/json")

    return render(request, "error.html",
                              {'error': 'Expected AJAX/POST'})


@user_passes_test(user_can_view_data)
def get_actions_for_tlo(request):
    """
    Get the actions for the specified TLO.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    type_ = request.GET.get('type', None)
    final = get_action_types_for_tlo(type_)
    return HttpResponse(json.dumps({'results': final}),
                content_type="application/json")
