import json
import urllib

from django.contrib.auth.decorators import user_passes_test
try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render

from crits.core.user_tools import user_can_view_data
from crits.core.class_mapper import class_from_value
from crits.targets.forms import TargetInfoForm
from crits.targets.handlers import upsert_target, get_target_details
from crits.targets.handlers import remove_target
from crits.targets.handlers import generate_target_jtable, generate_target_csv
from crits.targets.handlers import generate_division_jtable
from crits.vocabulary.acls import TargetACL

@user_passes_test(user_can_view_data)
def targets_listing(request,option=None):
    """
    Generate the Target listing page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', 'csv', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user

    if user.has_access_to(TargetACL.READ):
        if option == "csv":
            return generate_target_csv(request)
        return generate_target_jtable(request, option)
    else:
        return render(request, "error.html",
                                  {'error': 'User does not have permission to view Target listing.'})

@user_passes_test(user_can_view_data)
def divisions_listing(request,option=None):
    """
    Generate the Division listing page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param option: Action to take.
    :type option: str of either 'jtlist', 'jtdelete', 'csv', or 'inline'.
    :returns: :class:`django.http.HttpResponse`
    """

    return generate_division_jtable(request, option)

@user_passes_test(user_can_view_data)
def target_search(request):
    """
    Search for Targets.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponseRedirect`
    """

    query = {}
    query[request.GET.get('search_type', '')]=request.GET.get('q', '').strip()
    return HttpResponseRedirect(reverse('crits-emails-views-emails_listing') +
                                "?%s" % urllib.urlencode(query))

@user_passes_test(user_can_view_data)
def target_info(request, email_address):
    """
    Generate the Target details page.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param email_address: The email_address to get details for.
    :type email_address: str
    :returns: :class:`django.http.HttpResponse`
    """

    user = request.user
    if user.has_access_to(TargetACL.READ):
        template = "target.html"
        (new_template, args) = get_target_details(email_address, user)
        if new_template:
            template = new_template
        return render(request, template, args)
    else:
        return render(request, "error.html",
                                  {'error': 'User does not have permission to view Target details.'})


@user_passes_test(user_can_view_data)
def add_update_target(request):
    """
    Add/update a Target. Should be an AJAX POST.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST":
        email = request.POST['email_address']
        new_email = email.strip().lower()
        form = TargetInfoForm(request.user, request.POST)
        analyst = request.user.username
        if form.is_valid():
            data = form.cleaned_data
            results = upsert_target(data, analyst)
            if results['success']:
                message = '<div>Click here to view the new target: <a href='
                message += '"%s">%s</a></div>' % (reverse('crits-targets-views-target_info',
                                                          args=[new_email]),
                                                  new_email)
                result = {'message': message}
            else:
                result = results
                result['form'] = form.as_table()
        else:
            result = {'message': ['<div>Form is invalid!</div>']}
            result['form'] = form.as_table()
        if request.is_ajax():
            return HttpResponse(json.dumps(result), content_type="application/json")
        else:
            return HttpResponseRedirect(reverse('crits-targets-views-target_info',
                                                args=[email]))
    else:
        return render(request, "error.html", {"error" : "Expected AJAX POST" })

@user_passes_test(user_can_view_data)
def delete_target(request, email_address=None):
    """
    Delete a target.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param email_address: The email address of the Target to delete.
    :type email_address: str
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST":
        analyst = request.user.username
        results = remove_target(email_address, analyst)
        if not results['success']:
            error = "Error removing target: %s" % results['message']
            return render(request, "error.html", {"error" : error })
        return HttpResponseRedirect(reverse('crits-targets-views-target_details'))
    else:
        return render(request, "error.html", {"error" : "Expected POST" })

@user_passes_test(user_can_view_data)
def target_details(request, email_address=None):
    """
    Target modification form generation.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :param email_address: The email address of the Target to get details for..
    :type email_address: str
    :returns: :class:`django.http.HttpResponse`
    """

    if email_address is None:
        form = TargetInfoForm()
    else:
        target = class_from_value('Target', email_address)
        if not target:
            form = TargetInfoForm(request.user, initial={'email_address': email_address})
        else:
            form = TargetInfoForm(request.user, initial=target.to_dict())
    return render(request, 'target_form.html',
                              {'form': form})
