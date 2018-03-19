import logging
import sys
import traceback

from django.shortcuts import render

logger = logging.getLogger(__name__)

def custom_500(request, exception=None):
    exception, value, tb = sys.exc_info()
    ftb = traceback.format_exception(exception, value, tb)
    logger.debug(ftb)
    return render(request, "500.html",
                              {"exception": exception,
                               "value": value})

def custom_404(request, exception=None):
    return render(request, "404.html",
                              {})

def custom_403(request, exception=None):
    return render(request, "403.html",
                              {})

def custom_400(request, exception=None):
    return render(request, "400.html",
                              {})
