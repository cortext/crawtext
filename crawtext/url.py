#from url_filter import *

from urlparse import urlparse
from urlparse import urljoin
from urlparse import urlunparse
import json
import tldextract
from extractor import bs
import logging
logging.basicConfig()
logging.getLogger("tldextract").setLevel(logging.CRITICAL)
ACCEPTED_PROTOCOL = ['http', 'https']
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
    'css', 'pdf', 'exe', 'bin', 'rss','dtd', 'js', 'torrent',
]
ALLOWED_TYPES = ['html', 'htm', 'md', 'rst', 'aspx', 'jsp', 'rhtml', 'cgi',
                'xhtml', 'jhtml', 'asp', 'php', None, 'aspx', '']

BAD_DOMAINS = ['amazon', 'doubleclick', 'twitter', 'facebook', 'streaming', 'stream', "proxy"]
BAD_SUBDOMAINS = ['www', 'ww1', 'ww2', 'ww3', 'ww4', 'ww5', 'ww6', 'ww7', 'ww8', 'ww9', 'ww10', 
                'www1', 'www2', 'www3', 'www4', 'www5', 'www6', 'www7', 'www8', 'www9', 'www10']
BAD_PATHS = ['mailto', "share="]

BAD_QUERY = ["mailto", "share"]

from adblockparser import AdblockRules
import os

PKG_DIR = os.path.realpath('packages')
#PKG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'packages')
class Filter(object):
    '''Filter url with adblockparser'''
    def __init__(self, filename):
        self.rules = []
        with open(filename, "r") as blacklist:
            for line in blacklist.xreadlines():
                if line.startswith('!'):
                    continue
                if '##' in line: # HTML rule
                    continue
                else:
                    self.rules.append(line)
        #, supported_options=['script', 'domain']
        self.adblock = AdblockRules(self.rules, supported_options=['script', 'domain'])
        
    def match(self, url, options=None):
        return self.adblock.should_block(url)
    
url_filter = Filter(os.path.join(PKG_DIR, "complete-list.txt"))

class Url(object):    
    def __init__(self, url, source_url=None):
        self.url = url
        self.source_url = source_url
        self.parse()
        self.check()
        
        #~ self.clean_url()
        
    def get_url_id(self):
        try:
            ext= tldextract.extract(self.url)
            subdomain = ".".join([x for x in ext.subdomain.split(".") if x not in BAD_SUBDOMAINS])
            if len(subdomain) > 0 :
                return ".".join([subdomain,ext.domain, ext.suffix])
            else:
                return ".".join([ext.domain, ext.suffix])
        except TypeError:
            return self.url
    
    def parse(self):
        
        self.url_id = self.get_url_id()
        self.sheme = "http"
        try:
            parsed_url = urlparse(self.url)
            for k in ["scheme", "netloc", "path", "params", "query", "fragment"]:
                setattr(self,k, getattr(parsed_url,k))
            
        except AttributeError:
            logging.warning("Unable to parse url %s" %self.url)
            
        try:
            ext = tldextract.extract(self.url)
            self.domain = ext.domain
            self.subdomain = ext.subdomain
            self.suffix = ext.suffix
            self.filetype = self.netloc.split(".")[-1]
            self.internal_depth = len([n for n in self.path.split('/') if len(n) > 0])
        except TypeError: 
            logging.warning("EXTRACT TLD error on %s" %self.url)
         
        self.make_absolute()
        return self
        
    def make_absolute(self):
        if bool(self.netloc):
            
            if self.source_url is not None:
                self.url = urljoin(self.source_url, self.url)
                self.url_id = self.get_url_id(self.url)
            else:
                #~ try:
                    #~ print self.sheme+self.url
                #~ except
                try:
                    
                    if self.sheme is None:
                    #rebuilding
                        self.url = urljoin("http://www", self.url)
                        self.parse()
                except AttributeError:
                    self.url = urljoin("http://www", self.url)
                    self.parse()
        return self
        
    def is_wrong_domain(self):
        #print self.subdomain
        return bool(self.domain  in BAD_DOMAINS)
    
    def is_wrong_protocol(self):
        return bool(self.scheme not in ACCEPTED_PROTOCOL)
    
    def is_wrong_filetype(self):
        try:
            return bool(self.filetype in BAD_TYPES)
        except ValueError, AttributeError:
            return False
            
    #~ def is_wrong_subdomain(self):
        #~ try:
            #~ return bool(self.subdomain in BAD_SUBDOMAINS)
        #~ except ValueError, AttributeError:
            #~ return False
            
    def is_wrong_query(self):
        try:
            return bool(self.query in BAD_QUERY)
        except ValueError, AttributeError:
            return False
        
    def is_wrong_path(self):
        try:
            return bool(self.path in BAD_PATHS)
        except ValueError, AttributeError:
            return False
        
    def is_wrong_url(self):
        '''adblock url'''
        return url_filter.match(self.url)
        
    def is_wrong_source(self):
        '''check if same than the source_url'''
        if self.source_url is not None:
            return bool(self.url == self.source_url)
            
    def export(self):
        return self.__dict__
    def check(self):
        check_f = [n for n in dir(Url) if n.startswith("is_wrong")]
        check_m = [getattr(self, f) for f in check_f]
        list_function = [(f[0], f[1]()) for f in zip(check_f, check_m)]
        #f_name = [f[0] for f in list_functions]
        f_test = [f[0]  for f in list_function if f[1] is True]
        if len(f_test) > 0:
            self.msg = "Invalid url"+ " ".join(f_test)
            self.status = False
            return False
        self.status = True
        return True
            
def get_outlinks(html, url):
    '''absolute link parser with beautifulsoup'''
    soup = bs(html, "lxml")
    urls = [tag.get('href') for tag in soup.findAll('a', href=True)]
    urls=  [Url(url) for url in set(urls) if url is not None or len(url)<=0]
    urls = [url for url in urls if url.status is True]
    return urls
    
