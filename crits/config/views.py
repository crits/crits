import json

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.config.config import CRITsConfig
from crits.config.forms import ConfigForm
from crits.config.handlers import modify_configuration
from crits.core.user_tools import user_is_admin

@user_passes_test(user_is_admin)
def crits_config(request):
    """
    Generate the CRITs Configuration template.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    crits_config = CRITsConfig.objects().first()
    if crits_config:
        crits_config = crits_config.to_dict()
        crits_config['allowed_hosts'] = ", ".join(crits_config['allowed_hosts'])
        crits_config['service_dirs'] = ", ".join(crits_config['service_dirs'])
        config_form = ConfigForm(initial=crits_config)
    else:
        config_form = ConfigForm()
    return render_to_response('config.html',
                              {'config_form': config_form},
                              RequestContext(request))

@user_passes_test(user_is_admin)
def modify_config(request):
    """
    Modify the CRITs Configuration. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == "POST" and request.is_ajax():
        config_form = ConfigForm(request.POST)
        analyst = request.user.username
        if config_form.is_valid():
            result = modify_configuration(config_form, analyst)
            message = {'message': result['message']}
        else:
            message = {'message': "Invalid Form"}
        return HttpResponse(json.dumps(message), mimetype="application/json")
    else:
        return render_to_response('error.html',
                                  {'error': 'Expected AJAX POST'},
                                  RequestContext(request))
