import json

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.contrib.auth.decorators import user_passes_test

from crits.core.user_tools import user_can_view_data
from crits.standards.forms import UploadStandardsForm
from crits.standards.handlers import import_standards_doc

@user_passes_test(user_can_view_data)
def upload_standards(request):
    """
    Upload a standards document.

    :param request: Django request.
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    std_form = UploadStandardsForm(request.user, request.POST, request.FILES)
    response = {
                   'form': std_form.as_table(),
                   'success': False,
                   'message': ""
                 }

    if request.method != "POST":
        response['message'] = "Must submit via POST."
        return render_to_response('file_upload_response.html',
                                  {'response': json.dumps(response)},
                                  RequestContext(request))

    if not std_form.is_valid():
        response['message'] = "Form is invalid."
        return render_to_response('file_upload_response.html',
                                  {'response': json.dumps(response)},
                                  RequestContext(request))

    data = ''
    for chunk in request.FILES['filedata']:
        data += chunk

    make_event = std_form.cleaned_data['make_event']
    source = std_form.cleaned_data['source']

    # SAB  Add reverence field
    reference = std_form.cleaned_data['reference']

    # XXX: Add reference to form and handle here?
    status = import_standards_doc(data, request.user.username, "Upload",
                                  make_event=make_event, source=source,
                                  ref=reference)

    if not status['success']:
        response['message'] = status['reason']
        return render_to_response('file_upload_response.html',
                                  {'response': json.dumps(response)},
                                  RequestContext(request))

    response['success'] = True
    response['message'] = render_to_string("import_results.html", {'failed' : status['failed'], 'imported' : status['imported']})
    return render_to_response('file_upload_response.html',
                              {'response': json.dumps(response)},
                              RequestContext(request))
