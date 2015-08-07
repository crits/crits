import urllib
import json

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms.util import ErrorList

from crits.core import form_consts
from crits.core.data_tools import json_handler
from crits.core.handsontable_tools import form_to_dict
from crits.core.user_tools import user_can_view_data
from crits.domains.forms import TLDUpdateForm, AddDomainForm
from crits.domains.handlers import edit_domain_name
from crits.domains.handlers import add_new_domain, get_domain_details
from crits.domains.handlers import update_tlds, generate_domain_jtable
from crits.domains.handlers import generate_domain_csv, process_bulk_add_domain
from crits.objects.forms import AddObjectForm


@user_passes_test(user_can_view_data)
def domain_detail(request, domain):
    """
    Generate the Domain details page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param domain: The domain to get details for.
    :type domain: str
    :returns: :class:`django.http.HttpResponse`
    """

    template = "domain_detail.html"
    (new_template, args) = get_domain_details(domain,
                                              request.user.username)
    if new_template:
        template = new_template
    return render_to_response(template,
                              args,
                              RequestContext(request))

@user_passes_test(user_can_view_data)
def bulk_add_domain(request):
    """
    Bulk add domains via a bulk upload form.

    Args:
        request: The Django context which contains information about the
            session and key/value pairs for the bulk add domains request

    Returns:
        If the request is not a POST and not a Ajax call then:
            Returns a rendered HTML form for a bulk add of domains
        If the request is a POST and a Ajax call then:
            Returns a response that contains information about the
            status of the bulk uploaded domains. This may include information
            such as domains that failed or successfully added. This may
            also contain helpful status messages about each operation.
    """

    formdict = form_to_dict(AddDomainForm(request.user))

    if request.method == "POST" and request.is_ajax():
        response = process_bulk_add_domain(request, formdict);

        return HttpResponse(json.dumps(response,
                            default=json_handler),
                            mimetype='application/json')
    else:
        objectformdict = form_to_dict(AddObjectForm(request.user))

        return render_to_response('bulk_add_default.html',
                                 {'formdict': formdict,
                                  'objectformdict': objectformdict,
                                  'title': "Bulk Add Domains",
                                  'table_name': 'domain',
                                  'local_validate_columns': [form_consts.Domain.DOMAIN_NAME],
                                  'custom_js': "domain_handsontable.js",
                                  'is_bulk_add_objects': True},
                                  RequestContext(request));

@user_passes_test(user_can_view_data)
def domains_listing(request,option=None):
    """
    Generate the Domain listing page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', 'csv', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    if option == "csv":
        return generate_domain_csv(request)
    return generate_domain_jtable(request, option)

@user_passes_test(user_can_view_data)
def add_domain(request):
    """
    Add a domain. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.is_ajax() and request.method == "POST":
        add_form = AddDomainForm(request.user, request.POST)
        result = False
        retVal = {}
        errors = []
        if add_form.is_valid():
            errors = []
            data = add_form.cleaned_data
            (result, errors, retVal) = add_new_domain(data,
                                                      request,
                                                      errors)
        if errors:
            if not 'message' in retVal:
                retVal['message'] = ""
            elif not isinstance(retVal['message'], str):
                retVal['message'] = str(retVal['message'])
            for e in errors:
                if 'Domain' in e or 'TLD' in e:
                    dom_form_error = add_form._errors.setdefault("domain",
                                                                 ErrorList())
                    dom_form_error.append('Invalid Domain')
                elif 'IP' in e:
                    ip_form_error = add_form._errors.setdefault("ip",
                                                                ErrorList())
                    ip_form_error.append('Invalid IP')
                retVal['message'] += '<div>' + str(e) + '</div>'
        if not result:
            retVal['form'] = add_form.as_table()
        retVal['success'] = result
        return HttpResponse(json.dumps(retVal,
                                       default=json_handler),
                            mimetype="application/json")
    else:
        return render_to_response("error.html",
                                  {"error" : 'Expected POST' },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def edit_domain(request, domain):
    """
    Edit a domain. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param domain: The domain to edit.
    :type domain: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        new_name = request.POST.get('value')
        analyst = request.user.username
        if edit_domain_name(domain, new_name, analyst):
            return HttpResponse(new_name)
        else:
            return HttpResponse(domain)
    else:
        return render_to_response("error.html",
                                  {"error" : 'Expected AJAX POST' },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def domain_search(request):
    """
    Search for domains.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    query = {}
    query[request.GET.get('search_type', '')]=request.GET.get('q', '').strip()
    #return render_to_response('error.html', {'error': query})
    return HttpResponseRedirect(reverse('crits.domains.views.domains_listing')
                                + "?%s" % urllib.urlencode(query))

@user_passes_test(user_can_view_data)
def tld_update(request):
    """
    Update TLDs. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    if request.method == 'POST':
        form = TLDUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            filedata = request.FILES['filedata']
            result = update_tlds(filedata)
            if result['success']:
                response = {'success': True,
                            'message': 'Success! <a href="%s">Go to Domains.</a>'
                            % reverse('crits.domains.views.domains_listing')}
            else:
                response = {'success': False, 'form': form.as_table()}
        else:
            response = {'success': False, 'form': form.as_table()}
        return render_to_response('file_upload_response.html',
                                  {'response': json.dumps(response)},
            RequestContext(request))
    else:
        return render_to_response('error.html',
                                  {'error': 'Expected POST'},
                                  RequestContext(request))
