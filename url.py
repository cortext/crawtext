#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import datetime
import re, os, sys

from urlparse import (
     urlparse, urljoin, urlsplit, urlunsplit, parse_qs)



import posixpath
import six
from six.moves.urllib.parse import ParseResult, urlunparse, urldefrag, urlparse
import urllib
import cgi
<<<<<<< HEAD

=======
from filter import Filter
>>>>>>> logs_job
# scrapy.utils.url was moved to w3lib.url and import * ensures this move doesn't break old code

from w3lib.url import *

from encoding import unicode_to_str

from tldextract import tldextract


ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))



MAX_FILE_MEMO = 20000

DATE_REGEX = r'([\./\-_]{0,1}(19|20)\d{2})[\./\-_]{0,1}(([0-3]{0,1}[0-9][\./\-_])|(\w{3,5}[\./\-_]))([0-3]{0,1}[0-9][\./\-]{0,1})?'

ACCEPTED_PROTOCOL = ['http', 'https']

ALLOWED_TYPES = ['html', 'htm', 'md', 'rst', 'aspx', 'jsp', 'rhtml', 'cgi',
                'xhtml', 'jhtml', 'asp', 'php']

# common file extensions that are not followed if they occur in links
BAD_TYPES = [

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

GOOD_PATHS = ['story', 'article', 'feature', 'featured', 'slides',
              'slideshow', 'gallery', 'news', 'video', 'media',
              'v', 'radio', 'press']

BAD_CHUNKS = ['careers', 'contact', 'about', 'faq', 'terms', 'privacy',
              'advert', 'preferences', 'feedback', 'info', 'browse', 'howto',
              'account', 'subscribe', 'donate', 'shop', 'admin']


BAD_DOMAINS = ['amazon', 'doubleclick', 'twitter']

class Link(object):
    def __init__(self, url, origin="", depth = 0, source_url= None):
        self.url = url
        self.origin = origin
        self.depth = depth
        self.source_url = source_url
        self.msg = "Ok"
        self.parse()
        self.set_source_url()
        self.abs_url()
<<<<<<< HEAD
        self.is_valid()
=======
        self.status = self.is_valid()
>>>>>>> logs_job
        
    def set_source_url(self):
        if self.source_url is None:
            if self.scheme != "" and self.netloc != "":
                self.source_url  = self.scheme + "://" + self.netloc
            elif self.scheme == "" and self.netloc != "":
                self.source_url  = "http://" + self.netloc
            else:
                self.source_url = self.url

    def parse(self):
        #components of the url
<<<<<<< HEAD
        print "Parsing"
        self.url = self.prepare_url()
        parsed_url = urlparse(self.url)
        self.scheme = parsed_url.scheme
        print "self.scheme %s" self.sheme
=======
        self.url = self.prepare_url()
        parsed_url = urlparse(self.url)

        self.scheme = parsed_url.scheme
>>>>>>> logs_job
        self.netloc = parsed_url.netloc
        self.path = parsed_url.path
        self.params = parsed_url.params
        self.query = parsed_url.query
        self.fragment= parsed_url.fragment
        
        #filetype
<<<<<<< HEAD
        self.file_type = url_to_filetype(self.url)
=======
        self.file_type = self.url_to_filetype()
>>>>>>> logs_job
        #subdomain and tld
        tld_dat = tldextract.extract(self.url)
        self.subdomain = tld_dat.subdomain
        self.tld = tld_dat.domain.lower()
        self.extension =  tld_dat.suffix
        #info on page
        self.path_chunk = [x for x in self.path.split('/') if len(x) > 0]
        self.depth = len(self.path_chunk)
        

    def abs_url(self):
        self.relative = False
        if self.netloc != "" and self.path != "":
            self.relative = True
        

<<<<<<< HEAD
    def prepare_url(self):
        """
        Operations that purify a url, removes arguments,
        redirects, and merges relatives with absolutes.
        """
        try:
            if self.source_url is not None:
                self.source_domain = urlparse(self.source_url).netloc
                proper_url = urljoin(self.source_url, self.url)
                proper_url = redirect_back(proper_url, self.source_domain)
                self.proper_url = remove_args(proper_url)
            else:
                self.proper_url = remove_args(self.url)
        except ValueError, e:
            self._log.msg = 'url %s failed on err %s' % (url, str(e))
            self.proper_url = u''
        return self.proper_url
=======
    # def prepare_url(self):
    #     """
    #     Operations that purify a url, removes arguments,
    #     redirects, and merges relatives with absolutes.
    #     """
    #     try:
    #         if self.source_url is not None:
    #             self.source_domain = urlparse(self.source_url).netloc
    #             proper_url = urljoin(self.source_url, self.url)
    #             proper_url = redirect_back(proper_url, self.source_domain)
    #             self.proper_url = remove_args(proper_url)
    #         else:
    #             self.proper_url = remove_args(self.url)
    #     except ValueError, e:
    #         self.msg = 'url %s failed on err %s' % (url, str(e))
    #         self.proper_url = self.url
    #     return self.proper_url
>>>>>>> logs_job
    
    def is_valid(self):
        self.step = "Validating url"
        self.code = "100"
        if self.url is None or len(self.url) < 11:
<<<<<<< HEAD
            self.msg ='\t%s : len of url is less than 11' % self.url
            return False
        #invalid protocol
        if self.scheme not in ['http','https']:
            self.msg = '\t%s : wrong protocol not http or https' % self.url
            return False
        if not self.path.startswith('/'):
            self.msg = '\t%s : url is not valid' % self.url
            return False
        
        if self.file_type is not None and self.file_type not in ALLOWED_TYPES:
            self.msg = '\t%s : invalid webpage type (pdf, zip, etc..)' % self.url
            return False

        
        if len(adblock.match(self.url)) != 0:
            self.msg = '%s : adblock url' % self.url
            return False

        if self.tld in BAD_DOMAINS:
            self.msg = '%s : bad domain' % self.url
            return False
        
        match_date = re.search(DATE_REGEX, self.url)
        # if we caught the verified date above, it's an article
        if match_date is not None:
            self.msg = '%s verified for date' % self.url
            self.date = match_date
            return True
=======
            self.msg ='Url is too short (less than 11) %s' % self.url
            return False
        #invalid protocol
        if self.check_scheme() is False:
            self.msg = 'wrong protocol %s' % self.scheme
            return False
        if not self.path.startswith('/'):
            self.msg = 'Invalid path for url %s' % self.path
            return False
        
        if self.file_type is not None and self.file_type not in ALLOWED_TYPES:
            self.msg = 'invalid webpage type %s' % self.file_type
            return False
        if self.tld in BAD_DOMAINS:
            self.msg = 'bad domain %s' % self.tld
            return False
        
        
        adblock = Filter(file(ABSPATH+'/ressources/easylist.txt'), is_local=True)
        if len(adblock.match(self.url)) != 0:
            self.msg = 'Adblock url'
            return False

        match_date = re.search(DATE_REGEX, self.url)
        # if we caught the verified date above, it's an article
        if match_date is not None:
            self.date = match_date.group()
            self.msg = 'verified for date: %s' % self.date
            return True
        
>>>>>>> logs_job
        return True
    
    def json(self):
        link = {}
<<<<<<< HEAD
        keys = ["url", "scheme", "netloc", "path", "file_type", "tld", "extension", "depth", "source_url", "proper_url", "relative", "depth", "origin"]
=======
        keys = ["url", "scheme", "netloc", "path", "file_type", "tld", "extension", "depth", "source_url", "relative", "depth", "origin"]
>>>>>>> logs_job
        for k in keys:
            link[k] =  self.__dict__[k]
        link['status'] = [self.__dict__['status']]
        link['date'] = [datetime.now()]
        link['msg'] = [self.msg]
        return link

<<<<<<< HEAD
    def remove_args(url, keep_params=(), frags=False):
        """
        Remove all param arguments from a url.
        """
        parsed = urlsplit(url)
=======
    def remove_args(self, url, keep_params=(), frags=False):
        """
        Remove all param arguments from a url.
        """
        
        parsed = urlsplit(self.url)
>>>>>>> logs_job
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

<<<<<<< HEAD
    def prepare_url(url, source_url=None):
=======
    def prepare_url(self, source_url=None):
>>>>>>> logs_job
        """

        Operations that purify a url, removes arguments,
        redirects, and merges relatives with absolutes.
        """
        try:
            if source_url is not None:
                source_domain = urlparse(source_url).netloc
<<<<<<< HEAD
                proper_url = urljoin(source_url, url)
                proper_url = redirect_back(proper_url, source_domain)
                proper_url = remove_args(proper_url)
            else:
                proper_url = remove_args(url)
        except ValueError, e:
            self._log.msg = 'url %s failed on err %s' % (url, str(e))
            # print 'url %s failed on err %s' % (url, str(e))
=======
                proper_url = urljoin(source_url, self.url)
                proper_url = redirect_back(proper_url, source_domain)
                proper_url = self.remove_args(proper_url)
            else:
                proper_url = self.remove_args(self.url)
        except ValueError, e:
            self.msg = 'url %s failed on err %s' % (self.url, str(e))
            print 'url %s failed on err %s' % (url, str(e))
>>>>>>> logs_job
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
        
        # url = prepare_url(url)

        # 11 chars is shortest valid url length, eg: http://x.co
        if url is None or len(url) < 11:
            self.msg ='\t%s : len of url is less than 11' % url
            #Link exception
            return False
        # parsed_url = urlparse(url)
        # scheme = parsed_url.scheme
        # netloc = parsed_url.netloc
        # path = parsed_url.path
        

        if self.scheme not in ['http','https']:
            self.msg = '\t%s : scheme is not http or https' % url
            
            return False

        
        
        # input url is not in valid form (scheme, netloc, tld)
        if not path.startswith('/'):
            self.msg = '\t%s : path is not valid' % url
            return False

        
        # '/story/cnn/blahblah/index.html' --> ['story', 'cnn', 'blahblah', 'index.html']
        path_chunks = [x for x in path.split('/') if len(x) > 0]
        
        # siphon out the file type. eg: .html, .htm, .md
        if len(path_chunks) > 1:

            file_type = url_to_filetype(url)
            # if the file type is a media type, reject instantly
            if file_type not in ALLOWED_TYPES:
                self.msg = '\t%s : filetype is not valid' % url
                
                return False
        
        # extract the tld (top level domain)
        tld_dat = tldextract.extract(url)
        subd = tld_dat.subdomain
        tld = tld_dat.domain.lower()
        
        url_slug = path_chunks[-1] if path_chunks else u''
<<<<<<< HEAD
        pdb.set_trace()
        from packages.filter import Filter
        pdb.set_trace()
        adblock = Filter(file(ABSPATH+'/ressources/easylist.txt'), is_local=True)
        if len(adblock.match(url)) != 0:
            self.msg = '%s : adblock url' % url
=======
        
        
        adblock = Filter(file(ABSPATH+'/ressources/easylist.txt'), is_local=True)
        
        if len(adblock.match(url)) != 0:
            self.msg = 'adblock url'
>>>>>>> logs_job
            return False

        if tld in BAD_DOMAINS:
            self.msg = '%s : bad domain' % url
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
                    self.msg = '%s verified for being a slug' % url
                    return True

            if underscore_count > dash_count:
                if tld not in [ x.lower() for x in url_slug.split('_') ]:
                    self.msg = '%s verified for being a slug' % url
                    return True

        
        match_date = re.search(DATE_REGEX, url)

        # if we caught the verified date above, it's an article
        if match_date is not None:
            self.msg = '%s verified for date' % url
            return True

        for GOOD in GOOD_PATHS:
            if GOOD.lower() in [p.lower() for p in path_chunks]:
                self.msg = '%s verified for good path' % url
                return True

        
        return True

<<<<<<< HEAD
    def url_to_filetype(abs_url):
=======
    def url_to_filetype(self):
>>>>>>> logs_job
        """
        Input a URL and output the filetype of the file
        specified by the url. Returns None for no filetype.
        'http://blahblah/images/car.jpg' -> 'jpg'
        'http://yahoo.com'               -> None
        """
<<<<<<< HEAD
        path = urlparse(abs_url).path
        # Eliminate the trailing '/', we are extracting the file
        if path.endswith('/'):
=======
        path = ""
        # path = urlparse(self.url).path
        # Eliminate the trailing '/', we are extracting the file
        if self.path.endswith('/'):
>>>>>>> logs_job
            path = path[:-1]
        path_chunks = [x for x in path.split('/') if len(x) > 0]
        try:
            last_chunk = path_chunks[-1].split('.')  # last chunk == file usually
            if len(last_chunk) >= 2:
                file_type = last_chunk[-1]
                return file_type
            return None
        except IndexError:
            return None
        

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
        return posixpath.splitext(urlparse(url).netloc)[1].lower() in extensions


    def is_relative_url(url):
        netloc = urlparse(url).netloc
        if netloc is None or netloc == "":
            return True
        #~ if urlparse(url).path == "/" or urlparse(url).path == "../":
            #~ return True
        else:
            return False

<<<<<<< HEAD
    def check_scheme(url):
        scheme = urlparse(url).scheme
        print scheme
        if scheme in ["mailto", "ftp", "magnet", "javascript"]:
=======
    def check_scheme(self):
        if self.scheme in ["mailto", "ftp", "magnet", "javascript"]:
>>>>>>> logs_job
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



