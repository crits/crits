import logging
import sys
import traceback

from django.shortcuts import render_to_response
from django.template import RequestContext

logger = logging.getLogger(__name__)

def custom_500(request):
    exception, value, tb = sys.exc_info()
    ftb = traceback.format_exception(exception, value, tb)
    logger.debug(ftb)
    return render_to_response("500.html",
                              {"exception": exception,
                               "value": value},
                              RequestContext(request))

def custom_404(request):
    return render_to_response("404.html",
                              {},
                              RequestContext(request))

def custom_403(request):
    return render_to_response("403.html",
                              {},
                              RequestContext(request))

def custom_400(request):
    return render_to_response("400.html",
                              {},
                              RequestContext(request))
