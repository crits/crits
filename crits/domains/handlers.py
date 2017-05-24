import json
import re
import datetime

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
try:
    from mongoengine.base import ValidationError
except ImportError:
    from mongoengine.errors import ValidationError

from crits.core import form_consts
from crits.core.class_mapper import class_from_id, class_from_value
from crits.core.crits_mongoengine import EmbeddedSource, EmbeddedCampaign
from crits.core.crits_mongoengine import json_handler, create_embedded_source
from crits.core.handsontable_tools import convert_handsontable_to_rows, parse_bulk_upload
from crits.core.handlers import build_jtable, jtable_ajax_list, jtable_ajax_delete
from crits.core.data_tools import convert_string_to_bool
from crits.core.handlers import csv_export
from crits.core.user_tools import user_sources, is_user_favorite
from crits.core.user_tools import is_user_subscribed
from crits.domains.domain import Domain, TLD
from crits.domains.forms import AddDomainForm
from crits.ips.ip import IP
from crits.ips.handlers import validate_and_normalize_ip
from crits.notifications.handlers import remove_user_from_notification
from crits.objects.handlers import object_array_to_dict, validate_and_add_new_handler_object
from crits.relationships.handlers import forge_relationship
from crits.services.handlers import run_triage, get_supported_services

from crits.vocabulary.relationships import RelationshipTypes
from crits.vocabulary.acls import DomainACL

def get_valid_root_domain(domain):
    """
    Validate the given domain and TLD, and if valid, parse out the root domain

    :param domain: the domain to validate and parse
    :type domain: str
    :returns: tuple: (Valid root domain, Valid FQDN, Error message)
    """

    root = fqdn = error = ""
    black_list = "/:@\ "
    domain = domain.strip()

    if any(c in black_list for c in domain):
        error = 'Domain cannot contain space or characters %s' % (black_list)
    else:
        global tld_parser
        root = tld_parser.parse(domain)
        if root == "no_tld_found_error":
            tld_parser = etld()
            root = tld_parser.parse(domain)
            if root == "no_tld_found_error":
                error = 'No valid TLD found'
                root = ""
        else:
            fqdn = domain.lower()

    return (root, fqdn, error)

def get_domain_details(domain, user):
    """
    Generate the data to render the Domain details template.

    :param domain: The name of the Domain to get details for.
    :type domain: str
    :param user: The user requesting this information.
    :type user: str
    :returns: template (str), arguments (dict)
    """

    template = None
    allowed_sources = user_sources(user)
    dmain = Domain.objects(domain=domain,
                           source__name__in=allowed_sources).first()

    if not user.check_source_tlp(dmain):
        dmain = None

    if not dmain:
        error = ("Either no data exists for this domain"
                 " or you do not have permission to view it.")
        template = "error.html"
        args = {'error': error}
        return template, args

    dmain.sanitize(username="%s" % user,
                           sources=allowed_sources)


    # remove pending notifications for user
    remove_user_from_notification("%s" % user, dmain.id, 'Domain')

    # subscription
    subscription = {
            'type': 'Domain',
            'id': dmain.id,
            'subscribed': is_user_subscribed("%s" % user,
                                             'Domain',
                                             dmain.id),
    }

    #objects
    objects = dmain.sort_objects()

    #relationships
    relationships = dmain.sort_relationships("%s" % user, meta=True)

    # relationship
    relationship = {
            'type': 'Domain',
            'value': dmain.id
    }

    #comments
    comments = {'comments': dmain.get_comments(),
                'url_key':dmain.domain}

    #screenshots
    screenshots = dmain.get_screenshots(user)

    # favorites
    favorite = is_user_favorite("%s" % user, 'Domain', dmain.id)

    # services
    service_list = get_supported_services('Domain')

    # analysis results
    service_results = dmain.get_analysis_results()

    args = {'objects': objects,
            'relationships': relationships,
            'comments': comments,
            'favorite': favorite,
            'relationship': relationship,
            'subscription': subscription,
            'screenshots': screenshots,
            'domain': dmain,
            'service_list': service_list,
            'service_results': service_results,
            'DomainACL': DomainACL}

    return template, args

def generate_domain_csv(request):
    """
    Generate a CSV file of the Domain information

    :param request: The request for this CSV.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    response = csv_export(request,Domain)
    return response

def generate_domain_jtable(request, option):
    """
    Generate the jtable data for rendering in the list template.

    :param request: The request for this jtable.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    obj_type = Domain
    type_ = "domain"
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
        'title': "Domains",
        'default_sort': mapper['default_sort'],
        'listurl': reverse('crits.%ss.views.%ss_listing' % (type_, type_),
                                                    args=('jtlist',)),
        'deleteurl': reverse('crits.%ss.views.%ss_listing' % (type_, type_),
                                                    args=('jtdelete',)),
        'searchurl': reverse(mapper['searchurl']),
        'fields': mapper['jtopts_fields'],
        'hidden_fields': mapper['hidden_fields'],
        'linked_fields': mapper['linked_fields'],
        'details_link': mapper['details_link']
    }
    jtable = build_jtable(jtopts,request)
    jtable['toolbar'] = [
        {
            'tooltip': "'All Domains'",
            'text': "'All'",
            'click': "function () {$('#domain_listing').jtable('load', {'refresh': 'yes'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'New Domains'",
            'text': "'New'",
            'click': "function () {$('#domain_listing').jtable('load', {'refresh': 'yes', 'status': 'New'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'In Progress Domains'",
            'text': "'In Progress'",
            'click': "function () {$('#domain_listing').jtable('load', {'refresh': 'yes', 'status': 'In Progress'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Analyzed Domains'",
            'text': "'Analyzed'",
            'click': "function () {$('#domain_listing').jtable('load', {'refresh': 'yes', 'status': 'Analyzed'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Deprecated Domains'",
            'text': "'Deprecated'",
            'click': "function () {$('#domain_listing').jtable('load', {'refresh': 'yes', 'status': 'Deprecated'});}",
            'cssClass': "'jtable-toolbar-center'",
        },
        {
            'tooltip': "'Add Domain'",
            'text': "'Add Domain'",
            'click': "function () {$('#new-domain').click()}",
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

def add_new_domain_via_bulk(data, rowData, request, errors,
                            is_validate_only=False, cache={}):
    """
    Wrapper for add_new_domain to pass in rowData.

    :param data: The data about the domain.
    :type data: dict
    :param rowData: Any objects that need to be added to the domain.
    :type rowData: dict
    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param errors: A list of current errors to append to.
    :type errors: list
    :param is_validate_only: Only validate the data and return any errors.
    :type is_validate_only: boolean
    :param cache: Cached data, typically for performance enhancements
                  during bulk uperations.
    :type cache: dict
    :returns: tuple
    """

    return add_new_domain(data, request, errors, rowData=rowData,
                          is_validate_only=is_validate_only, cache=cache)

def retrieve_domain(domain, cache):
    """
    Retrieves a domain by checking cache first. If not in cache
    then queries mongo for the domain.

    :param domain: The domain name.
    :type domain: str
    :param cache: Cached data, typically for performance enhancements
                  during bulk uperations.
    :type cache: dict
    :returns: :class:`crits.domains.domain.Domain`
    """
    domain_obj = None
    cached_results = cache.get(form_consts.Domain.CACHED_RESULTS)

    if cached_results:
        domain_obj = cached_results.get(domain.lower())

    if not domain_obj:
        domain_obj = Domain.objects(domain__iexact=domain).first()

    return domain_obj

def add_new_domain(data, request, errors, rowData=None, is_validate_only=False, cache={}):
    """
    Add a new domain to CRITs.

    :param data: The data about the domain.
    :type data: dict
    :param request: The Django request.
    :type request: :class:`django.http.HttpRequest`
    :param errors: A list of current errors to append to.
    :type errors: list
    :param rowData: Any objects that need to be added to the domain.
    :type rowData: dict
    :param is_validate_only: Only validate the data and return any errors.
    :type is_validate_only: boolean
    :param cache: Cached data, typically for performance enhancements
                  during bulk operations.
    :type cache: dict
    :returns: tuple (<result>, <errors>, <retVal>)
    """

    result = False
    retVal = {}
    domain = data['domain']
    add_ip = data.get('add_ip')
    ip = data.get('ip')
    ip_type = data.get('ip_type')

    if add_ip:
        error = validate_and_normalize_ip(ip, ip_type)[1]
        if error:
             errors.append(error)

    if is_validate_only:
        error = get_valid_root_domain(domain)[2]
        if error:
            errors.append(error)

        # check for duplicate domains
        fqdn_domain = retrieve_domain(domain, cache)

        if fqdn_domain:
            if isinstance(fqdn_domain, Domain):
                resp_url = reverse('crits.domains.views.domain_detail', args=[domain])
                message = ('Warning: Domain already exists: '
                                     '<a href="%s">%s</a>' % (resp_url, domain))
                retVal['message'] = message
                retVal['status'] = form_consts.Status.DUPLICATE
                retVal['warning'] = message
        else:
            result_cache = cache.get(form_consts.Domain.CACHED_RESULTS);
            result_cache[domain.lower()] = True

    elif not errors:
        user = request.user
        reference = data.get('source_reference')
        source_name = data.get('source_name')
        method = data.get('source_method')
        tlp = data.get('source_tlp')
        bucket_list = data.get(form_consts.Common.BUCKET_LIST_VARIABLE_NAME)
        ticket = data.get(form_consts.Common.TICKET_VARIABLE_NAME)
        related_id = data.get('related_id')
        related_type = data.get('related_type')
        relationship_type = data.get('relationship_type')

        if user.check_source_write(source_name):
            source = [create_embedded_source(source_name, reference=reference,
                                             method=method, tlp=tlp, analyst=user.username)]
        else:
            result =  {"success": False,
                    "message": "User does not have permission to add objects \
                    using source %s." % str(source_name)}

            return False, False, result
        if data.get('campaign') and data.get('confidence'):
            campaign = [EmbeddedCampaign(name=data.get('campaign'),
                                         confidence=data.get('confidence'),
                                         analyst=user.username)]
        else:
            campaign = []

        retVal = upsert_domain(domain, source, user.username, campaign,
                               bucket_list=bucket_list, ticket=ticket, cache=cache, related_id=related_id, related_type=related_type, relationship_type=relationship_type)

        if not retVal['success']:
            errors.append(retVal.get('message'))
            retVal['message'] = ""

        else:
            new_domain = retVal['object']
            ip_result = {}
            if add_ip:
                if data.get('same_source'):
                    ip_source = source_name
                    ip_method = method
                    ip_reference = reference
                    ip_tlp = tlp
                else:
                    ip_source = data.get('ip_source')
                    ip_method = data.get('ip_method')
                    ip_reference = data.get('ip_reference')
                    ip_tlp = data.get('ip_tlp')
                from crits.ips.handlers import ip_add_update
                ip_result = ip_add_update(ip,
                                          ip_type,
                                          source=ip_source,
                                          source_method=ip_method,
                                          source_reference=ip_reference,
                                          source_tlp=ip_tlp,
                                          campaign=campaign,
                                          user=user,
                                          bucket_list=bucket_list,
                                          ticket=ticket,
                                          cache=cache)
                if not ip_result['success']:
                    errors.append(ip_result['message'])
                else:
                    #add a relationship with the new IP address
                    new_ip = ip_result['object']
                    if new_domain and new_ip:
                        new_domain.add_relationship(new_ip,
                                                    RelationshipTypes.RESOLVED_TO,
                                                    analyst=user.username,
                                                    get_rels=False)
                        new_domain.save(username=user.username)

            #set the URL for viewing the new data
            resp_url = reverse('crits.domains.views.domain_detail', args=[domain])

            if retVal['is_domain_new'] == True:
                retVal['message'] = ('Success! Click here to view the new domain: '
                                     '<a href="%s">%s</a>' % (resp_url, domain))
            else:
                message = ('Updated existing domain: <a href="%s">%s</a>' % (resp_url, domain))
                retVal['message'] = message
                retVal[form_consts.Status.STATUS_FIELD] = form_consts.Status.DUPLICATE
                retVal['warning'] = message

            #add indicators
            if data.get('add_indicators'):
                from crits.indicators.handlers import create_indicator_from_tlo
                # If we have an IP object, add an indicator for that.
                if ip_result.get('success'):
                    ip = ip_result['object']
                    result = create_indicator_from_tlo('IP',
                                                       ip,
                                                       user,
                                                       ip_source,
                                                       source_tlp=ip_tlp,
                                                       add_domain=False)
                    ip_ind = result.get('indicator')
                    if not result['success']:
                        errors.append(result['message'])

                # Add an indicator for the domain.
                result = create_indicator_from_tlo('Domain',
                                                   new_domain,
                                                   user,
                                                   source_name,
                                                   source_tlp=tlp,
                                                   add_domain=False)

                if not result['success']:
                    errors.append(result['message'])
                elif ip_result.get('success') and ip_ind:
                    forge_relationship(class_=result['indicator'],
                                       right_class=ip_ind,
                                       rel_type=RelationshipTypes.RESOLVED_TO,
                                       user=user.username)
            result = True

    # This block validates, and may also add, objects to the Domain
    if retVal.get('success') or is_validate_only == True:
        if rowData:
            objectsData = rowData.get(form_consts.Common.OBJECTS_DATA)

            # add new objects if they exist
            if objectsData:
                objectsData = json.loads(objectsData)
                current_domain = retrieve_domain(domain, cache)
                for object_row_counter, objectData in enumerate(objectsData, 1):
                    if current_domain != None:
                        # if the domain exists then try to add objects to it
                        if isinstance(current_domain, Domain) == True:
                            objectDict = object_array_to_dict(objectData,
                                                              "Domain",
                                                              current_domain.id)
                        else:
                            objectDict = object_array_to_dict(objectData,
                                                              "Domain",
                                                              "")
                            current_domain = None;
                    else:
                        objectDict = object_array_to_dict(objectData,
                                                          "Domain",
                                                          "")

                    (obj_result,
                     errors,
                     obj_retVal) = validate_and_add_new_handler_object(
                        None, objectDict, request, errors, object_row_counter,
                        is_validate_only=is_validate_only,
                        cache=cache, obj=current_domain)
                    if not obj_result:
                        retVal['success'] = False

    return result, errors, retVal

def edit_domain_name(domain, new_domain, analyst):
    """
    Edit domain name for an entry.

    :param domain: The domain name to edit.
    :type domain: str
    :param new_domain: The new domain name.
    :type new_domain: str
    :param analyst: The user editing the domain name.
    :type analyst: str
    :returns: boolean
    """

    # validate new domain
    (root, validated_domain, error) = get_valid_root_domain(new_domain)
    if error:
        return False

    domain = Domain.objects(domain=domain).first()
    if not domain:
        return False
    try:
        domain.domain = validated_domain
        domain.save(username=analyst)
        return True
    except ValidationError:
        return False

def upsert_domain(domain, source, username=None, campaign=None,
                  confidence=None, bucket_list=None, ticket=None, cache={}, related_id=None, related_type=None, relationship_type=None):
    """
    Add or update a domain/FQDN. Campaign is assumed to be a list of campaign
    dictionary objects.

    :param domain: The domain to add/update.
    :type domain: str
    :param source: The name of the source.
    :type source: str
    :param username: The user adding/updating the domain.
    :type username: str
    :param campaign: The campaign to attribute to this domain.
    :type campaign: list, str
    :param confidence: Confidence for the campaign attribution.
    :type confidence: str
    :param bucket_list: List of buckets to add to this domain.
    :type bucket_list: list, str
    :param ticket: The ticket for this domain.
    :type ticket: str
    :param cache: Cached data, typically for performance enhancements
                  during bulk uperations.
    :type cache: dict
    :param related_id: ID of object to create relationship with
    :type related_id: str
    :param related_type: Type of object to create relationship with
    :type related_id: str
    :param relationship_type: Type of relationship to create.
    :type relationship_type: str
    :returns: dict with keys:
              "success" (boolean),
              "object" the domain that was added,
              "is_domain_new" (boolean)
    """


    # validate domain and grab root domain
    (root, domain, error) = get_valid_root_domain(domain)
    if error:
        return {'success': False, 'message': error}

    is_fqdn_domain_new = False
    is_root_domain_new = False

    if not campaign:
        campaign = []
    # assume it's a list, but check if it's a string
    elif isinstance(campaign, basestring):
        c = EmbeddedCampaign(name=campaign, confidence=confidence, analyst=username)
        campaign = [c]

    # assume it's a list, but check if it's a string
    if isinstance(source, basestring):
        s = EmbeddedSource()
        s.name = source
        instance = EmbeddedSource.SourceInstance()
        instance.reference = ''
        instance.method = ''
        instance.analyst = username
        instance.date = datetime.datetime.now()
        s.instances = [instance]
        source = [s]

    fqdn_domain = None
    root_domain = None
    cached_results = cache.get(form_consts.Domain.CACHED_RESULTS)

    if cached_results != None:
        if domain != root:
            fqdn_domain = cached_results.get(domain)
            root_domain = cached_results.get(root)
        else:
            root_domain = cached_results.get(root)
    else:
        #first find the domain(s) if it/they already exist
        root_domain = Domain.objects(domain=root).first()
        if domain != root:
            fqdn_domain = Domain.objects(domain=domain).first()

    #if they don't exist, create them
    if not root_domain:
        root_domain = Domain()
        root_domain.domain = root
        root_domain.source = []
        root_domain.record_type = 'A'
        is_root_domain_new = True

        if cached_results != None:
            cached_results[root] = root_domain
    if domain != root and not fqdn_domain:
        fqdn_domain = Domain()
        fqdn_domain.domain = domain
        fqdn_domain.source = []
        fqdn_domain.record_type = 'A'
        is_fqdn_domain_new = True

        if cached_results != None:
            cached_results[domain] = fqdn_domain

    # if new or found, append the new source(s)
    for s in source:
        if root_domain:
            root_domain.add_source(s)
        if fqdn_domain:
            fqdn_domain.add_source(s)

    #campaigns
    #both root and fqdn get campaigns updated
    for c in campaign:
        if root_domain:
            root_domain.add_campaign(c)
        if fqdn_domain:
            fqdn_domain.add_campaign(c)
    if username:
        if root_domain:
            root_domain.analyst = username
        if fqdn_domain:
            fqdn_domain.analyst = username

    if bucket_list:
        if root_domain:
            root_domain.add_bucket_list(bucket_list, username)
        if fqdn_domain:
            fqdn_domain.add_bucket_list(bucket_list, username)

    if ticket:
        if root_domain:
            root_domain.add_ticket(ticket, username)
        if fqdn_domain:
            fqdn_domain.add_ticket(ticket, username)

    related_obj = None
    if related_id:
        related_obj = class_from_id(related_type, related_id)
        if not related_obj:
            retVal['success'] = False
            retVal['message'] = 'Related Object not found.'
            return retVal

    # save
    try:
        if root_domain:
            root_domain.save(username=username)
        if fqdn_domain:
            fqdn_domain.save(username=username)
    except Exception, e:
        return {'success': False, 'message': e}

    #Add relationships between fqdn, root
    if fqdn_domain and root_domain:
        root_domain.add_relationship(fqdn_domain,
                                     RelationshipTypes.SUPRA_DOMAIN_OF,
                                     analyst=username,
                                     get_rels=False)
        root_domain.save(username=username)
        fqdn_domain.save(username=username)

    #Add relationships from object domain is being added from
    if related_obj and relationship_type:
        relationship_type=RelationshipTypes.inverse(relationship=relationship_type)
        if fqdn_domain and (related_obj != fqdn_domain):
            fqdn_domain.add_relationship(related_obj,
                                         relationship_type,
                                         analyst=username,
                                         get_rels=False)
            fqdn_domain.save(username=username)
        if root_domain and (related_obj != root_domain):
            root_domain.add_relationship(related_obj,
                                         relationship_type,
                                         analyst=username,
                                         get_rels=False)
            root_domain.save(username=username)

    # run domain triage
    if is_fqdn_domain_new:
        fqdn_domain.reload()
        run_triage(fqdn_domain, username)
    if is_root_domain_new:
        root_domain.reload()
        run_triage(root_domain, username)

    # return fqdn if they added an fqdn, or root if they added a root
    if fqdn_domain:
        return {'success': True, 'object': fqdn_domain, 'is_domain_new': is_fqdn_domain_new}
    else:
        return {'success': True, 'object': root_domain, 'is_domain_new': is_root_domain_new}

def update_tlds(data=None):
    """
    Update the TLD list in the database.

    :param data: The TLD data.
    :type data: file handle.
    :returns: dict with key "success" (boolean)
    """

    if not data:
        return {'success': False}
    line = data.readline()
    while line:
        line = line.rstrip()
        if line and not line.startswith('//'):
            line = line.replace("*.", "")
            TLD.objects(tld=line).update_one(set__tld=line, upsert=True)
        line = data.readline()

    # Update the package local tld_parser with the new domain info
    tld_parser = etld()

    return {'success': True}

class etld(object):
    """
    TLD class to assist with extracting root domains.
    """

    def __init__(self):
        self.rules = {}
        etlds = TLD.objects()
        for etld in etlds:
            tld = etld.tld.split('.')[-1]
            self.rules.setdefault(tld, [])
            self.rules[tld].append(re.compile(self.regexpize(etld.tld)))

    def regexpize(self, etld):
        """
        Generate regex for this TLD.

        :param etld: The TLD to generate regex for.
        :returns: str
        """

        etld = etld[::-1].replace('.',
                                  '\\.').replace('*',
                                                 '[^\\.]*').replace('!',
                                                                    '')
        return '^(%s)\.(.*)$' % etld

    def parse(self, hostname):
        """
        Parse the domain.

        :param hostname: The domain to parse.
        :returns: str
        """

        try:
            hostname = hostname.lower()
            tld = hostname.split('.')[-1]
            hostname = hostname[::-1]
            etld = ''
            for rule in self.rules[tld]:
                m = rule.match(hostname)
                if m and m.group(1) > etld:
                    mytld = "%s.%s" % ( m.group(2)[::-1].split(".")[-1],
                                       m.group(1)[::-1])
            if not mytld:
                return ("no_tld_found_error")
            return (mytld)
        except Exception:
            return ("no_tld_found_error")

def parse_row_to_bound_domain_form(request, rowData, cache):
    """
    Parse a row in bulk upload into form data that can be used to add a Domain.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param rowData: The objects to add for the Domain.
    :type rowData: dict
    :param cache: Cached data, typically for performance enhancements
                  during bulk uperations.
    :type cache: dict
    :returns: :class:`crits.domains.forms.AddDomainForm`
    """

    bound_domain_form = None

    # TODO Add common method to convert data to string
    domain_name = rowData.get(form_consts.Domain.DOMAIN_NAME, "").strip();
    campaign = rowData.get(form_consts.Domain.CAMPAIGN, "")
    confidence = rowData.get(form_consts.Domain.CAMPAIGN_CONFIDENCE, "")
    source = rowData.get(form_consts.Domain.DOMAIN_SOURCE, "")
    method = rowData.get(form_consts.Domain.DOMAIN_METHOD, "")
    reference = rowData.get(form_consts.Domain.DOMAIN_REFERENCE, "")
    tlp = rowData.get(form_consts.Common.SOURCE_TLP, "")
    #is_add_ip = convert_string_to_bool(rowData.get(form_consts.Domain.ADD_IP_ADDRESS, ""))
    is_add_ip = False

    ip = rowData.get(form_consts.Domain.IP_ADDRESS, "")
    ip_type = rowData.get(form_consts.Domain.IP_TYPE, "")
    created = rowData.get(form_consts.Domain.IP_DATE, "")
    #is_same_source = convert_string_to_bool(rowData.get(form_consts.Domain.SAME_SOURCE, "False"))
    is_same_source = False
    ip_source = rowData.get(form_consts.Domain.IP_SOURCE, "")
    ip_method = rowData.get(form_consts.Domain.IP_METHOD, "")
    ip_reference = rowData.get(form_consts.Domain.IP_REFERENCE, "")
    ip_tlp = rowData.get(form_consts.Domain.IP_TLP, "")
    is_add_indicators = convert_string_to_bool(rowData.get(form_consts.Domain.ADD_INDICATORS, "False"))

    bucket_list = rowData.get(form_consts.Common.BUCKET_LIST, "")
    ticket = rowData.get(form_consts.Common.TICKET, "")

    if(ip or created or ip_source or ip_method or ip_reference or ip_tlp):
        is_add_ip = True

    if is_add_ip == True:
        data = {'domain': domain_name,
                'campaign': campaign,
                'confidence': confidence,
                'source_name': source,
                'source_method': method,
                'source_reference': reference,
                'source_tlp': tlp,
                'add_ip': is_add_ip,
                'ip': ip,
                'ip_type': ip_type,
                'created': created,
                'same_source': is_same_source,
                'ip_source': ip_source,
                'ip_method': ip_method,
                'ip_reference': ip_reference,
                'ip_tlp': ip_tlp,
                'add_indicators': is_add_indicators,
                'bucket_list': bucket_list,
                'ticket': ticket}

        bound_domain_form = cache.get("domain_ip_form")

        if bound_domain_form == None:
            bound_domain_form = AddDomainForm(request.user, data)
            cache['domain_ip_form'] = bound_domain_form
        else:
            bound_domain_form.data = data
    else:
        data = {'domain': domain_name,
                'campaign': campaign,
                'confidence': confidence,
                'source_name': source,
                'source_method': method,
                'source_reference': reference,
                'source_tlp': tlp,
                'add_ip': is_add_ip,
                'bucket_list': bucket_list,
                'ticket': ticket}

        bound_domain_form = cache.get("domain_form")

        if bound_domain_form == None:
            bound_domain_form = AddDomainForm(request.user, data)
            cache['domain_form'] = bound_domain_form
        else:
            bound_domain_form.data = data

    if bound_domain_form != None:
        bound_domain_form.full_clean()

    return bound_domain_form

def process_bulk_add_domain(request, formdict):
    """
    Performs the bulk add of domains by parsing the request data. Batches
    some data into a cache object for performance by reducing large
    amounts of single database queries.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param formdict: The form representing the bulk uploaded data.
    :type formdict: dict
    :returns: :class:`django.http.HttpResponse`
    """

    domain_names = []
    ip_addresses = []
    cached_domain_results = {}
    cached_ip_results = {}

    cleanedRowsData = convert_handsontable_to_rows(request)
    for rowData in cleanedRowsData:
        if rowData != None:
            if rowData.get(form_consts.Domain.DOMAIN_NAME) != None:
                domain = rowData.get(form_consts.Domain.DOMAIN_NAME).strip().lower()
                (root_domain, full_domain, error) = get_valid_root_domain(domain)
                domain_names.append(full_domain)

                if domain != root_domain:
                    domain_names.append(root_domain)

            if rowData.get(form_consts.Domain.IP_ADDRESS) != None:
                ip_addr = rowData.get(form_consts.Domain.IP_ADDRESS)
                ip_type = rowData.get(form_consts.Domain.IP_TYPE)
                (ip_addr, error) = validate_and_normalize_ip(ip_addr, ip_type)
                ip_addresses.append(ip_addr)

    domain_results = Domain.objects(domain__in=domain_names)

    ip_results = IP.objects(ip__in=ip_addresses)


    for domain_result in domain_results:
        cached_domain_results[domain_result.domain] = domain_result

    for ip_result in ip_results:
        cached_ip_results[ip_result.ip] = ip_result

    cache = {form_consts.Domain.CACHED_RESULTS: cached_domain_results,
             form_consts.IP.CACHED_RESULTS: cached_ip_results,
             'cleaned_rows_data': cleanedRowsData}

    response = parse_bulk_upload(request, parse_row_to_bound_domain_form, add_new_domain_via_bulk, formdict, cache)

    return response

# Global definition of the TLD parser -- etld.
# This is a workaround to use a global instance because the __init__ method takes ~0.5 seconds to
# initialize. Was causing performance problems (high CPU usage) with bulk uploading of domains since
# each domain needed to create the etld() class.
# TODO investigate if updating of TLDs causes this global instance to become stale.
tld_parser = etld()
