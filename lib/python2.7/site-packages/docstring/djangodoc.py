from django.core.urlresolvers import resolve
from django.http import HttpResponse
import functools

from docstring import utils

def get_api_doc(request):
    """
    @param request: HttpRequest
    @return: str, html
    """
    f, args, kwars = resolve(request.path)
    endpoint = utils.Endpoint(f.__doc__, request.path)

    doc = utils.get_api_doc([endpoint], request.path, request.path)
    return doc

class document(object):
    """
    Decorator to add documentation response
    """
    def __init__(self, param='doc'):
        """
        @param param: str|None, if param in the url request, return
        documentation. Otherwise, go with the normal get method. If param=None
        return documentation if there are no parameters in the request.
        """
        self._param = param

    def __call__(self, fn):
        @functools.wraps(fn)
        def wrapped_f(*args, **kwargs):
            request = args[0]
            if ((self._param and request.GET.get(self._param, None)) or
                    not self._param and not request.GET.keys()):
                return HttpResponse(get_api_doc(request))
            return fn(*args, **kwargs)
        return wrapped_f
