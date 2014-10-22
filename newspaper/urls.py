# -*- coding: utf-8 -*-
"""
Newspaper treats urls for news articles as critical components.
Hence, we have an entire module dedicated to them.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import re

from urlparse import (
    urlparse, urljoin, urlsplit, urlunsplit, parse_qs)

from packages.tldextract import tldextract

log = logging.getLogger(__name__)
import posixpath, sys, os
from packages import six
from six.moves.urllib.parse import ParseResult, urlunparse, urldefrag, urlparse
import urllib
import cgi

# scrapy.utils.url was moved to w3lib.url and import * ensures this move doesn't break old code

from w3lib.url import *
from utils.encoding import unicode_to_str
from .filter import Filter


MAX_FILE_MEMO = 20000

DATE_REGEX = r'([\./\-_]{0,1}(19|20)\d{2})[\./\-_]{0,1}(([0-3]{0,1}[0-9][\./\-_])|(\w{3,5}[\./\-_]))([0-3]{0,1}[0-9][\./\-]{0,1})?'

ALLOWED_TYPES = ['html', 'htm', 'md', 'rst', 'aspx', 'jsp', 'rhtml', 'cgi',
                'xhtml', 'jhtml', 'asp']

GOOD_PATHS = ['story', 'article', 'feature', 'featured', 'slides',
              'slideshow', 'gallery', 'news', 'video', 'media',
              'v', 'radio', 'press']

BAD_CHUNKS = ['careers', 'contact', 'about', 'faq', 'terms', 'privacy',
              'advert', 'preferences', 'feedback', 'info', 'browse', 'howto',
              'account', 'subscribe', 'donate', 'shop', 'admin']

BAD_DOMAINS = ['amazon', 'doubleclick', 'twitter']

def remove_args(url, keep_params=(), frags=False):
    """
    Remove all param arguments from a url.
    """
    parsed = urlsplit(url)
    filtered_query= '&'.join(
        qry_item for qry_item in parsed.query.split('&')
            if qry_item.startswith(keep_params)
    )
    if frags:
        frag = parsed[4:]
    else:
        frag = ('',)

    return urlunsplit(parsed[:3] + (filtered_query,) + frag)

def redirect_back(url, source_domain):
    """
    Some sites like Pinterest have api's that cause news
    args to direct to their site with the real news url as a
    GET param. This method catches that and returns our param.
    """
    parse_data = urlparse(url)
    domain = parse_data.netloc
    query = parse_data.query

    # If our url is even from a remotely similar domain or
    # sub domain, we don't need to redirect.
    if source_domain in domain or domain in source_domain:
        return url

    query_item = parse_qs(query)
    if query_item.get('url'):
        # log.debug('caught redirect %s into %s' % (url, query_item['url'][0]))
        return query_item['url'][0]

    return url

def prepare_url(url, source_url=None):
    """
    Operations that purify a url, removes arguments,
    redirects, and merges relatives with absolutes.
    """
    try:
        if source_url is not None:
            source_domain = urlparse(source_url).netloc
            proper_url = urljoin(source_url, url)
            proper_url = redirect_back(proper_url, source_domain)
            proper_url = remove_args(proper_url)
        else:
            proper_url = remove_args(url)
    except ValueError, e:
        log.critical('url %s failed on err %s' % (url, str(e)))
        # print 'url %s failed on err %s' % (url, str(e))
        proper_url = u''

    return proper_url

def valid_url(url, verbose=False, test=False):
    """
    Is this URL a valid news-article url?

    Perform a regex check on an absolute url.

    First, perform a few basic checks like making sure the format of the url
    is right, (scheme, domain, tld).

    Second, make sure that the url isn't some static resource, check the
    file type.

    Then, search of a YYYY/MM/DD pattern in the url. News sites
    love to use this pattern, this is a very safe bet.

    Separators can be [\.-/_]. Years can be 2 or 4 digits, must
    have proper digits 1900-2099. Months and days can be
    ambiguous 2 digit numbers, one is even optional, some sites are
    liberal with their formatting also matches snippets of GET
    queries with keywords inside them. ex: asdf.php?topic_id=blahlbah
    We permit alphanumeric, _ and -.

    Our next check makes sure that a keyword is within one of the
    separators in a url (subdomain or early path separator).
    cnn.com/story/blah-blah-blah would pass due to "story".

    We filter out articles in this stage by aggressively checking to
    see if any resemblance of the source& domain's name or tld is
    present within the article title. If it is, that's bad. It must
    be a company link, like 'cnn is hiring new interns'.

    We also filter out articles with a subdomain or first degree path
    on a registered bad keyword.
    """
    # If we are testing this method in the testing suite, we actually
    # need to preprocess the url like we do in the article's constructor!
    if test:
        url = prepare_url(url)

    # 11 chars is shortest valid url length, eg: http://x.co
    if url is None or len(url) < 11:
        if verbose: print '\t%s rejected because len of url is less than 11' % url
        return False

    r1 = ('mailto:' in url) # TODO not sure if these rules are redundant
    r2 = ('http://' not in url) and ('https://' not in url)

    if r1 or r2:
        if verbose: print '\t%s rejected because len of url structure' % url
        return False

    path = urlparse(url).path

    # input url is not in valid form (scheme, netloc, tld)
    if not path.startswith('/'):
        return False

    # the '/' which may exist at the end of the url provides us no information
    if path.endswith('/'):
        path = path[:-1]

    # '/story/cnn/blahblah/index.html' --> ['story', 'cnn', 'blahblah', 'index.html']
    path_chunks = [x for x in path.split('/') if len(x) > 0]

    # siphon out the file type. eg: .html, .htm, .md
    if len(path_chunks) > 0:
        file_type = url_to_filetype(url)

        # if the file type is a media type, reject instantly
        if file_type and file_type not in ALLOWED_TYPES:
            if verbose: print '\t%s rejected due to bad filetype' % url
            return False

        last_chunk = path_chunks[-1].split('.')
        # the file type is not of use to use anymore, remove from url
        if len(last_chunk) > 1:
            path_chunks[-1] = last_chunk[-2]

    # Index gives us no information
    if 'index' in path_chunks:
        path_chunks.remove('index')

    # extract the tld (top level domain)
    tld_dat = tldextract.extract(url)
    subd = tld_dat.subdomain
    tld = tld_dat.domain.lower()

    url_slug = path_chunks[-1] if path_chunks else u''

    if tld in BAD_DOMAINS:
        if verbose: print '%s caught for a bad tld' % url
        return False

    if len(path_chunks) == 0:
        dash_count, underscore_count = 0, 0
    else:
        dash_count = url_slug.count('-')
        underscore_count = url_slug.count('_')

    # If the url has a news slug title
    if url_slug and (dash_count > 4 or underscore_count > 4):

        if dash_count >= underscore_count:
            if tld not in [ x.lower() for x in url_slug.split('-') ]:
                if verbose: print '%s verified for being a slug' % url
                return True

        if underscore_count > dash_count:
            if tld not in [ x.lower() for x in url_slug.split('_') ]:
                if verbose: print '%s verified for being a slug' % url
                return True

    # There must be at least 2 subpaths
    if len(path_chunks) <= 1:
        if verbose: print '%s caught for path chunks too small' % url
        return False

    # Check for subdomain & path red flags
    # Eg: http://cnn.com/careers.html or careers.cnn.com --> BAD
    for b in BAD_CHUNKS:
        if b in path_chunks or b == subd:
            if verbose: print '%s caught for bad chunks' % url
            return False

    match_date = re.search(DATE_REGEX, url)

    # if we caught the verified date above, it's an article
    if match_date is not None:
        if verbose: print '%s verified for date' % url
        return True

    for GOOD in GOOD_PATHS:
        if GOOD.lower() in [p.lower() for p in path_chunks]:
            if verbose: print '%s verified for good path' % url
            return True

    if verbose: print '%s caught for default false' % url
    return False

def url_to_filetype(abs_url):
    """
    Input a URL and output the filetype of the file
    specified by the url. Returns None for no filetype.
    'http://blahblah/images/car.jpg' -> 'jpg'
    'http://yahoo.com'               -> None
    """
    path = urlparse(abs_url).path
    # Eliminate the trailing '/', we are extracting the file
    if path.endswith('/'):
        path = path[:-1]
    path_chunks = [x for x in path.split('/') if len(x) > 0]
    last_chunk = path_chunks[-1].split('.')  # last chunk == file usually
    file_type = last_chunk[-1] if len(last_chunk) >= 2 else None
    return file_type or None

def get_domain(abs_url, **kwargs):
    """
    returns a url's domain, this method exists to
    encapsulate all url code into this file
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).netloc

def get_scheme(abs_url, **kwargs):
    """
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).scheme

def get_path(abs_url, **kwargs):
    """
    """
    if abs_url is None:
        return None
    return urlparse(abs_url, **kwargs).path

def is_abs_url(url):
    """
    this regex was brought to you by django!
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://'                                                                 # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'                                                                         # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'                                                # ...or ipv4
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'                                                        # ...or ipv6
        r'(?::\d+)?'                                                                          # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    c_regex = re.compile(regex)
    return (c_regex.search(url) != None)
"""
My own version
"""

#from crawtext import ABSPATH
#adblocklist of unwanted domain

#IGNORED_DOMAINS = adblock.get_list()

# common scheme that are not followed if they occur in links
#IGNORED_PROTOCOL = ['ftp', 'sftp', 'mailto', 'magnet', 'javascript']
ACCEPTED_PROTOCOL = ['http', 'https']

# common file extensions that are not followed if they occur in links
IGNORED_EXTENSIONS = [

    # images
    'mng', 'pct', 'bmp', 'gif', 'jpg', 'jpeg', 'png', 'pst', 'psp', 'tif',
    'tiff', 'ai', 'drw', 'dxf', 'eps', 'ps', 'svg','gif', 'ico', 'svg',

    # audio
    'mp3', 'wma', 'ogg', 'wav', 'ra', 'aac', 'mid', 'au', 'aiff',

    # video
    '3gp', 'asf', 'asx', 'avi', 'mov', 'mp4', 'mpg', 'qt', 'rm', 'swf', 'wmv',
    'm4a',

    # office suites
    'xls', 'xlsx', 'ppt', 'pptx', 'doc', 'docx', 'odt', 'ods', 'odg', 'odp',
    
    #compressed doc
    'zip', 'rar', 'gz', 'bz2', 'torrent', 'tar',
     
    # other
    'css', 'pdf', 'exe', 'bin', 'rss','dtd', 'asp', 'js', 'torrent',
]

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
IGNORED_DOMAINS = Filter(file(str(ABSPATH+'/utils/easylist.txt')))

def check_url(url):
    '''Bool: check the format of the curr url'''
    if url is None or len(url) <= 1 or url == "\n":
        error_type = "Url is empty"
        status = False
        status_code = 406
        
    elif url_has_any_extension(url, IGNORED_EXTENSIONS) is True :
        error_type="Url has not a supported extension (PDF, ZIP, etc...)"
        status = False
        status_code = 406.1
        
    elif url_is_from_any_domain(url, IGNORED_DOMAINS) is True:
        error_type="Url refers to an advertissement listed in Adblock"
        status = False
        status_code = 406.2
    
    else:
        scheme = urlparse(url).scheme
        if scheme == "" or scheme is None:
            url = "http://"+escape_anchor(escape_ajax(url))
            status = True
            status_code = 200
            error_type = None
            
        elif scheme not in ACCEPTED_PROTOCOL:
            error_type="Protocol is not http or https"
            status = False
            status_code = 406.2 
        else:
            status = True
            status_code = 200
            error_type = None
            url = escape_anchor(escape_ajax(url))
    return (status, status_code, error_type, url)
            

def url_has_any_protocol(url, protocols):
    """Return True if the url belongs to any of the given protocol"""
    scheme = parse_url(url).scheme.lower()
    if scheme:
        return any(((scheme == d.scheme()) for d in protocols))     
    else:
        return False
    
def url_is_from_any_domain(url, domains):
    """Return True if the url belongs to any of the given domains"""
    if len( domains.match(url) ) > 0:
        return True
    else:
        return False


def url_is_from_spider(url, spider):
    """Return True if the url belongs to the given spider"""
    return url_is_from_any_domain(url,
        [spider.name] + list(getattr(spider, 'allowed_domains', [])))

def url_has_any_protocol(url, protocols):
    print protocols
    return (parse_url(url).scheme).lower() in protocols
    
def url_has_any_extension(url, extensions):
    return posixpath.splitext(parse_url(url).netloc)[1].lower() in extensions


def is_relative_url(url):
    netloc = urlparse(url).netloc
    if netloc is None or netloc == "":
        return True
    #~ if urlparse(url).path == "/" or urlparse(url).path == "../":
        #~ return True
    else:
        return False
            
def from_rel_to_absolute_url(url,root_url):
    try:
        scheme, netloc, path, params, query, fragment = urlparse(url)
        if is_relative_url(url):
            scheme = urlparse(root_url).scheme
            netloc = urlparse(root_url).netloc
            return urlunparse((scheme, netloc.lower(), path, params, query, fragment))
        else:
            return url
    except AttributeError:
        return url
        
def check_scheme(url):
    scheme = urlparse(url).scheme
    print scheme
    if scheme in ["mailto", "ftp", "magnet"]:
        return False
    
        
        
def canonicalize_url(url,keep_blank_values=True, keep_fragments=False,
        encoding=None):
    """Canonicalize the given url by applying the following procedures:

    - sort query arguments, first by key, then by value
    - percent encode paths and query arguments. non-ASCII characters are
      percent-encoded using UTF-8 (RFC-3986)
    - normalize all spaces (in query arguments) '+' (plus symbol)
    - normalize percent encodings case (%2f -> %2F)
    - remove query arguments with blank values (unless keep_blank_values is True)
    - remove fragments (unless keep_fragments is True)

    The url passed can be a str or unicode, while the url returned is always a
    str.

    For examples see the tests in tests/test_utils_url.py
    """
    scheme, netloc, path, params, query, fragment = parse_url(url)
        
    keyvals = cgi.parse_qsl(query, keep_blank_values)
    keyvals.sort()
    query = urllib.urlencode(keyvals)
    path = safe_url_string(_unquotepath(path)) or '/'
    fragment = '' if not keep_fragments else fragment
    return urlunparse((scheme, netloc.lower(), path, params, query, fragment))


def _unquotepath(path):
    for reserved in ('2f', '2F', '3f', '3F'):
        path = path.replace('%' + reserved, '%25' + reserved.upper())
    return urllib.unquote(path)


def parse_url(url, encoding=None):
    """Return urlparsed url from the given argument (which could be an already
    parsed url)
    """
    return url if isinstance(url, ParseResult) else \
        urlparse(unicode_to_str(url, encoding))

def escape_anchor(url):
    '''escape_anchor("www.example.com/ajax.html#!key=value")'''
    url = re.split("#", url)
    return url[0]
            
def escape_ajax(url):
    """
    Return the crawleable url according to:
    http://code.google.com/web/ajaxcrawling/docs/getting-started.html

    >>> escape_ajax("www.example.com/ajax.html#!key=value")
    'www.example.com/ajax.html?_escaped_fragment_=key%3Dvalue'
    >>> escape_ajax("www.example.com/ajax.html?k1=v1&k2=v2#!key=value")
    'www.example.com/ajax.html?k1=v1&k2=v2&_escaped_fragment_=key%3Dvalue'
    >>> escape_ajax("www.example.com/ajax.html?#!key=value")
    'www.example.com/ajax.html?_escaped_fragment_=key%3Dvalue'
    >>> escape_ajax("www.example.com/ajax.html#!")
    'www.example.com/ajax.html?_escaped_fragment_='

    URLs that are not "AJAX crawlable" (according to Google) returned as-is:

    >>> escape_ajax("www.example.com/ajax.html#key=value")
    'www.example.com/ajax.html#key=value'
    >>> escape_ajax("www.example.com/ajax.html#")
    'www.example.com/ajax.html#'
    >>> escape_ajax("www.example.com/ajax.html")
    'www.example.com/ajax.html'
    """
    defrag, frag = urldefrag(url)
    if not frag.startswith('!'):
        return url
    return add_or_replace_parameter(defrag, '_escaped_fragment_', frag[1:])