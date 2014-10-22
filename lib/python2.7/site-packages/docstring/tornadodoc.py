import functools

import tornado.web

from docstring import utils


def _get_helper(application,
    handlers=None,
    server_name=None,
    request=None,
    is_root=False,
    ):
    """
    @param handlers: list(RequestHandler), list of handlers to limit
    the documentation for. If not specified, documentation will be
    generated for all handlers.
    @param server_name: str, will be used as the title in the generated
    HTML.
    @param request: HTTPRequest|None
    @param is_root: bool
    @return: str
    """
    urls = application.handlers[0][1]
    classes = [h.__class__ for h in handlers] if handlers else None
    server_name = server_name or application.settings.get('server_name', "")
    endpoints = []
    for url in urls:
        if classes and not url.handler_class in classes:
            continue
        if url.handler_class.__module__.startswith('tornado.'):
            continue
        if url.handler_class.__name__ == DocHandler.__name__:
            continue
        endpoint = utils.Endpoint(
                url.handler_class.__doc__,
                url.regex.pattern,
                )
        endpoints.append(endpoint)
    return utils.get_api_doc(endpoints, server_name,
            request_url=request.full_url(),
            is_root=is_root,
            )


class DocHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        self._server_name = None
        super(DocHandler, self).__init__(*args, **kwargs)

    def initialize(self, **kwargs):
        """
        @param server_name: str, server_name to use for base handler.
        """
        self._server_name = kwargs.get('server_name')

    def get(self):
        self.write(_get_helper(
            self.application,
            request=self.request,
            server_name=self._server_name,
            is_root=True,
            ))

class document(object):
    """
    Decorator to add to the tornado get method to get documentation out
    of it.
    """
    def __init__(self, param='doc', server_name=None):
        """
        @param param: str|None, if param in the url request, return
        documentation. Otherwise, go with the normal get method. If param=None
        return documentation if there are no parameters in the request.
        @param server_name: str, server_name to use for handler.
        """
        self._param = param
        self._server_name = server_name

    def __call__(self, fn):
        @functools.wraps(fn)
        def wrapped_f(*args, **kwargs):
            handler = args[0]
            if ((self._param and handler.get_argument(self._param, None)) or
                    (not self._param and not handler.request.arguments)):
                server_name = self._server_name
                # Remove passing server_name via get_server_name method.
                # This value should just come from the decorator
                if hasattr(handler, 'get_server_name'):
                    server_name = handler.get_server_name()
                handler.write(_get_helper(handler.application,
                    handlers=[handler],
                    server_name=server_name,
                    request=handler.request,
                    ))
                return
            return fn(*args, **kwargs)
        return wrapped_f
