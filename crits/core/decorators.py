from django.http import HttpResponseNotAllowed

def requires_post(func):
    """
    Returns an HTTP 405 error if the request method isn't POST.
    """
    def decorator(request, *args, **kwargs):
        if request.method == 'POST':
            return func(request, *args, **kwargs)
        return HttpResponseNotAllowed(['POST'])
    return decorator
