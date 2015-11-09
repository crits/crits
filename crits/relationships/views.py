import json

from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext

from crits.core.user_tools import user_can_view_data
from crits.relationships.forms import ForgeRelationshipForm
from crits.relationships.handlers import forge_relationship, update_relationship_dates, update_relationship_confidences
from crits.relationships.handlers import update_relationship_types, delete_relationship, update_relationship_reasons

from crits.vocabulary.relationships import RelationshipTypes

@user_passes_test(user_can_view_data)
def add_new_relationship(request):
    """
    Add a new relationship. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        form = ForgeRelationshipForm(request.POST)
        choices = [(c,c) for c in RelationshipTypes.values(sort=True)]
        form.fields['forward_relationship'].choices = choices
        if form.is_valid():
            cleaned_data = form.cleaned_data;
            results = forge_relationship(type_=cleaned_data.get('forward_type'),
                                         id_=cleaned_data.get('forward_value'),
                                         right_type=cleaned_data.get('reverse_type'),
                                         right_id=cleaned_data.get('dest_id'),
                                         rel_type=cleaned_data.get('forward_relationship'),
                                         rel_date=cleaned_data.get('relationship_date'),
                                         user=request.user.username,
                                         rel_reason=cleaned_data.get('rel_reason'),
                                         rel_confidence=cleaned_data.get('rel_confidence'),
                                         get_rels=True)
            if results['success'] == True:
                relationship = {'type': cleaned_data.get('forward_type'),
                                'value': cleaned_data.get('forward_value')}
                message = render_to_string('relationships_listing_widget.html',
                                           {'relationship': relationship,
                                            'nohide': True,
                                            'relationships': results['relationships']},
                                           RequestContext(request))
                result = {'success': True, 'message': message}
            else:
                message = "Error adding relationship: %s" % results['message']
                result = {'success': False, 'message': message}
        else:
            message = "Invalid Form: %s" % form.errors
            form = form.as_table()
            result = {'success': False, 'form': form, 'message': message}
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_relationship_type(request):
    """
    Update relationship type. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        results = update_relationship_types(left_type=request.POST['my_type'],
                                            left_id=request.POST['my_value'],
                                            right_type=request.POST['reverse_type'],
                                            right_id=request.POST['dest_id'],
                                            rel_type=request.POST['forward_relationship'],
                                            rel_date=request.POST['relationship_date'],
                                            new_type=request.POST['new_relationship'],
                                            analyst=request.user.username)
        if results['success']:
            message = "Successfully updated relationship: %s" % results['message']
            result = {'success': True, 'message': message}
        else:
            message = "Error updating relationship: %s" % results['message']
            result = {'success': False, 'message': message}
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_relationship_confidence(request):
    """
    Update relationship confidence. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """
    if request.method == 'POST' and request.is_ajax():
        new_confidence = request.POST['new_confidence']
        if new_confidence not in ('unknown', 'low', 'medium', 'high'):
            result = {'success': False,
                      'message': 'Unknown confidence level.'}
            return HttpResponse(json.dumps(result), mimetype="application/json")
        else:
            results = update_relationship_confidences(left_type=request.POST['my_type'],
                                                left_id=request.POST['my_value'],
                                                right_type=request.POST['reverse_type'],
                                                right_id=request.POST['dest_id'],
                                                rel_type=request.POST['forward_relationship'],
                                                rel_date=request.POST['relationship_date'],
                                                analyst=request.user.username,
                                                new_confidence=new_confidence)

        if results['success']:
            message = "Successfully updated relationship: %s" % results['message']
            result = {'success': True, 'message': message}
        else:
            message = "Error updating relationship: %s" % results['message']
            result = {'success': False, 'message': message}
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))




@user_passes_test(user_can_view_data)
def update_relationship_reason(request):
    """
    Update relationship reason. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """
    if request.method == 'POST' and request.is_ajax():
        results = update_relationship_reasons(left_type=request.POST['my_type'],
                                            left_id=request.POST['my_value'],
                                            right_type=request.POST['reverse_type'],
                                            right_id=request.POST['dest_id'],
                                            rel_type=request.POST['forward_relationship'],
                                            rel_date=request.POST['relationship_date'],
                                            analyst=request.user.username,
                                            new_reason=request.POST['new_reason'])
        if results['success']:
            message = "Successfully updated relationship: %s" % results['message']
            result = {'success': True, 'message': message}
        else:
            message = "Error updating relationship: %s" % results['message']
            result = {'success': False, 'message': message}
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def update_relationship_date(request):
    """
    Update relationship date. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        results = update_relationship_dates(left_type=request.POST['my_type'],
                                            left_id=request.POST['my_value'],
                                            right_type=request.POST['reverse_type'],
                                            right_id=request.POST['dest_id'],
                                            rel_type=request.POST['forward_relationship'],
                                            rel_date=request.POST['relationship_date'],
                                            new_date=request.POST['new_relationship_date'],
                                            analyst=request.user.username)
        if results['success']:
            message = "Successfully updated relationship: %s" % results['message']
            result = {'success': True, 'message': message}
        else:
            message = "Error updating relationship: %s" % results['message']
            result = {'success': False, 'message': message}
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def break_relationship(request):
    """
    Remove a relationship. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST' and request.is_ajax():
        results = delete_relationship(left_type=request.POST['my_type'],
                                      left_id=request.POST['my_value'],
                                      right_type=request.POST['reverse_type'],
                                      right_id=request.POST['dest_id'],
                                      rel_type=request.POST['forward_relationship'],
                                      rel_date=request.POST['relationship_date'],
                                      analyst=request.user.username)
        if results['success']:
            relationship = {'type': request.POST['my_type'],
                            'value': request.POST['my_value']}
            message = render_to_string('relationships_listing_widget.html',
                                       {'relationship': relationship,
                                        'nohide': True,
                                        'relationships': results['relationships']},
                                       RequestContext(request))
            result = {'success': True, 'message': message}
        else:
            message = "Error deleting relationship: %s" % results['message']
            result = {'success': False, 'message': message}
        return HttpResponse(json.dumps(result), mimetype="application/json")
    else:
        error = "Expected AJAX POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))

@user_passes_test(user_can_view_data)
def get_relationship_type_dropdown(request):
    """
    Get relationship type dropdown data. Should be an AJAX POST.

    :param request: Django request object (Required)
    :type request: :class:`django.http.HttpRequest`
    :returns: :class:`django.http.HttpResponse`
    """

    if request.method == 'POST':
        if request.is_ajax():
            dd_final = {}
            for type_ in RelationshipTypes.values(sort=True):
                dd_final[type_] = type_
            result = {'types': dd_final}
            return HttpResponse(json.dumps(result), mimetype="application/json")
        else:
            error = "Expected AJAX"
            return render_to_response("error.html",
                                      {"error" : error },
                                      RequestContext(request))
    else:
        error = "Expected POST"
        return render_to_response("error.html",
                                  {"error" : error },
                                  RequestContext(request))
