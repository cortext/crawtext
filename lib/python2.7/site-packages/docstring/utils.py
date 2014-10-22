import os
import re
import urllib
from urlparse import urlparse
from urlparse import urlunparse

def _parse_params(url):
    """
    Given a url, return params as dict

    @param url: str
    @return dict(str,str)
    """
    url_parts = list(urlparse(url))
    params = (dict([part.split('=') for part in url_parts[4].split('&')]) if
             url_parts[4] else {})
    return params

def _append_params(url, params):
    """
    Append parameters to an existing url. The appended parameters will be
    properly urlencoded. It wont append a parameter if it already exists

    Ideally, params should be list of tuples, but the method accepts dict
    for legacy reasons.

    @param url: str
    @param params: dict(str,str)|list(tuple), parameters to append
    @return str: url with the parameters appended
    """
    assert(isinstance(params, dict) or isinstance(params, list))

    if isinstance(params, dict):
        params = params.items()

    url_parts = list(urlparse(url))
    query = ([part.split('=') for part in url_parts[4].split('&')] if
             url_parts[4] else [])
    params = query + params
    to_append = []
    for key, value in params:
        if type(value) == unicode:
            value = value.encode('utf-8')

        if not key in [k for (k, _) in to_append]:
            to_append.append((key, value))

    url_parts[4] = urllib.urlencode(to_append)
    to_return = urlunparse(url_parts)
    return to_return

class Endpoint(object):
    def __init__(self, docstring, mount_regex):
        """
        @param pydoc: str
        @param path: str
        """
        self._docstring = docstring
        self._mount_regex = mount_regex

    def _get_path(self, request_path=None, clean=False, params=None):
        """
        @param request_path: str, this should just be path, with no parameters
        @param clean: bool
        @param params: dict|None
        """
        params = params or {}
        match = re.search("(%s)" % self._mount_regex, request_path)
        use_relative = bool(match)
        if use_relative:
            return _append_params('./', params) if not clean else './'

        # Remove the regex pieces in the mount path. This is quite hacky
        # to do, but no other option. In essence, we are trying to find a
        # path that matches the given regex.
        path = (self._mount_regex.
                replace('$', '').
                replace('.*?', '').
                replace('.*', '')
                )
        if path.startswith('/'):
            path = path[1:]
        path = './' + path
        if not clean:
            path = _append_params(path, params)
        return path

    def get_link_path(self, request_path, clean=False, params=None):
        """
        @param request_path: str
        @param params: dict|None
        @return: str
        """
        params = params or {}
        link_path = self._get_path(
                request_path=request_path,
                clean=clean,
                params=params,
                )
        return link_path

    def get_display_path(self, request_path, clean=False, params=None):
        """
        @param request_path: str
        @param params: dict|None
        @return: str
        """
        params = params or {}
        display_path = self._get_path(
                request_path=request_path,
                clean=clean,
                params=params,
                )
        return display_path

    def get_description(self):
        """
        @return: str
        """
        docstring = self._docstring.strip()
        pattern = re.compile(r'([^@]*)', re.MULTILINE)
        match = re.search(pattern, docstring)
        if not match:
            return ''
        # Hack for now. Ideally we should not need any Example:
        description = match.group(1)
        description = description.replace('Examples:', '')
        return description.strip()

    def get_params(self):
        """
        @return: str
        """
        docstring = self._docstring.strip()
        doc = docstring.replace('\n', '<br/>\n')
        pattern = re.compile(r'@param ([^:]+?):([^@]*)', re.MULTILINE)
        matches = re.findall(pattern, doc)
        doc = ''
        for m in matches:
            doc += "<span class='param'>%s</span>:%s" % (m[0], m[1])
        return doc

    def get_example_url(self, request_path):
        """
        @param request_path: str
        @return: str
        """
        pattern = r'@see: ([^\n]+)<br/>'
        doc = self._docstring.strip().replace('\n', '<br/>\n')
        match = re.search(pattern, doc)
        if not match:
            return ''
        example_params = _parse_params(match.group(1))
        display_path = self.get_display_path(request_path, clean=False)
        link_path = self.get_link_path(request_path, clean=False)
        link_path = _append_params(link_path, example_params)
        display_path = _append_params(display_path, example_params)
        return "<span><a href='%s'>%s</a></span><br/>" % (link_path, display_path)

    def get_doc(self, request_path, request_params):
        """
        @param request_path: str
        @param request_parmams: dict
        @return: str
        """
        if not self._docstring:
            return ''
        link_path = self.get_link_path(
                request_path,
                params=dict(
                    request_params,
                    doc=1,
                    ),
                )
        display_path = self.get_display_path(request_path)
        doc = '<tr>'
        doc += '<td><a href="%s">%s</a></td>' % (link_path, display_path)
        doc += "<td>%s</td>" % self.get_description()
        doc += "<td>%s</td>" % self.get_params()
        doc += "<td>%s</td>" % self.get_example_url(request_path)
        doc += '</tr>'
        return doc

def get_api_doc(endpoints, title, request_url, is_root=False):
    """
    @param endpoints: list(Endpoint)
    @param title: str
    @param request_url: path
    @return: str
    """
    request_params = _parse_params(request_url)
    request_path = urlparse(request_url)[2]
    out = []
    fname = os.path.join(os.path.dirname(__file__), 'base.html')
    style_fname = os.path.join(os.path.dirname(__file__), 'style.css')
    base_template = open(fname).read()
    style = open(style_fname).read()
    rows = []
    for endpoint in endpoints:
        rows.append(endpoint.get_doc(request_path, request_params))
    rows = ('\n'.join(rows))
    back = ''
    if not is_root:
        back = "<a href='../?doc=1' class='back'>(back)</a>"
    out = base_template % {
        'title': title or 'no title',
        'rows': rows,
        'style': style,
        'back': back,
        }
    return out

