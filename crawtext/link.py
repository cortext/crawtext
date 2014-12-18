from urlparse import (
   urlparse, urljoin, urlsplit, urlunsplit, parse_qs)
from tldextract import tldextract
from filter import Filter
import os, sys, re

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
DATE_REGEX = r'([\./\-_]{0,1}(19|20)\d{2})[\./\-_]{0,1}(([0-3]{0,1}[0-9][\./\-_])|(\w{3,5}[\./\-_]))([0-3]{0,1}[0-9][\./\-]{0,1})?'

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
    'css', 'pdf', 'exe', 'bin', 'rss','dtd', 'asp', 'js', 'torrent',
]
ALLOWED_TYPES = ['html', 'htm', 'md', 'rst', 'aspx', 'jsp', 'rhtml', 'cgi',
                'xhtml', 'jhtml', 'asp', 'php', None]


BAD_DOMAINS = ['amazon', 'doubleclick', 'twitter', 'facebook']

class Link(object):
    def __init__(self, url, source_url, debug=False):
        self.url = url
        self.source_url = source_url
        self.debug = debug
    
    def parse_url(self,url):
        '''complete info on url'''
        parsed_url = urlparse(url)
        self.scheme = parsed_url.scheme
        self.netloc = parsed_url.netloc
        self.path = parsed_url.path
        self.params = parsed_url.params
        self.query = parsed_url.query
        self.fragment = parsed_url.fragment
        #filetype:
        self.filetype = url_to_filetype(self.path)
        #subdomain and tld
        tld_dat = tldextract.extract(url)
        self.subdomain = tld_dat.subdomain
        self.tld = tld_dat.domain.lower()

        self.extension =  tld_dat.suffix
        #info on page
        self.path_chunk = [x for x in self.path.split('/') if len(x) > 0]
        self.indepth = len(self.path_chunk)
        return self    

    def relative2abs(self):
        
        self.parse_url(self.url)
        
        self.source = parse_url(self.source_url)
        if self.netloc == "":
            if self.path.startswith("."):
                self.path = re.sub(".", "", self.path)
            self.url = "http://"+self.source["netloc"]+self.path
        return self
    
    def is_valid(self):
        
        self.relative2abs()

        if self.url in ["void", ";"]:
            self.msg ='Javascript %s' % self.url
            return False

        if self.url is None or len(self.url) < 11:
            self.msg ='Url is too short (less than 11) %s' % self.url
            return False
        elif self.url.startswith('javascript'):
            self.msg ='Javascript %s' % self.url
            return False
        #invalid protocol
        if check_scheme(self.scheme) is False:
            self.msg = 'wrong protocol %s' % self.scheme
            return False
        if check_path(self.path) is False:
            self.msg ='wrong path %s' % self.path
            return False

        if not self.path.startswith('/'):
            self.msg = 'Invalid path for url %s' % self.path
            return False
    
        if self.filetype in BAD_TYPES:
            self.msg = 'Invalid webpage type %s' % self.filetype
            return False
        if self.tld in BAD_DOMAINS:
            self.msg = 'bad domain %s' % self.tld
            return False
        return True

    def filter_ads(url):
        adblock = Filter(file(ABSPATH+'/ressources/easylist.txt'), is_local=True)
        if len(adblock.match(self.url)) != 0:
            self.msg = 'Adblock url'
            return False

        match_date = re.search(DATE_REGEX, self.url)
        # if we caught the verified date above, it's an article
        if match_date is not None:
            self.date = match_date.group()
        return True
    
    def export(self, depth, mode="simple"):
        if mode == "simple":
            if self.is_valid():
                return {"url":self.url, "source_url":self.source_url, "depth": depth}
            else: return None
        else:
            if self.is_valid():
                self.data = self.__dict__()
                del self.data["source"]
                return self.data
            else:
                return None




def parse_url(url):
    info = {}
    info['url'] = url
    parsed_url = urlparse(url)
    info['scheme'] = parsed_url.scheme
    info['netloc'] = parsed_url.netloc
    info['path'] = parsed_url.path
    info['params'] = parsed_url.params
    info['query'] = parsed_url.query
    info['fragment']= parsed_url.fragment
    #filetype:
    info["filetype"] = url_to_filetype(info["path"])
    #subdomain and tld
    tld_dat = tldextract.extract(url)
    
    info['subdomain'] = tld_dat.subdomain
    info['tld'] = tld_dat.domain.lower()
    info['extension'] =  tld_dat.suffix
    #info on page
    info['path_chunk'] = [x for x in info['path'].split('/') if len(x) > 0]
    info['depth'] = len(info['path_chunk'])
    return info

def relative2abs(url, source_url):
    info = parse_url(url)
    if source_url is None:
        source = parse_url(url)
    source = parse_url(source_url)
    if info["netloc"] == "":
        info["url"] = source['scheme']+"://"+urljoin(source["netloc"], info["path"])
    info["source"] = source
    return info

def url_to_filetype(path):
    """
    Input a URL and output the filetype of the file
    specified by the url. Returns None for no filetype.
    'http://blahblah/images/car.jpg' -> 'jpg'
    'http://yahoo.com'               -> None
    """
    path = ""
    # path = urlparse(self.url).path
    # Eliminate the trailing '/', we are extracting the file
    if path.endswith('/'):
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

def check_scheme(scheme):
    if scheme in ["mailto", "ftp", "magnet", "javascript"]:
        return False
def check_path(path):
    if path in ["#", "/", "?"]:
        return False
def remove_args():
    pass

def is_valid(url, source_url):
    
    info =relative2abs(url, source_url)
    info['step'] = "Validating url"
    info['code'] = 100
    
    if info['url'] is None or len(info['url']) < 11:
        info['msg'] ='Url is too short (less than 11) %s' % info["url"]
        return (False, info)
    elif info["url"].startswith('javascript'):
        info['msg'] ='Javascript %s' % url
        return (False, info)
    #invalid protocol
    if check_scheme(info["scheme"]) is False:
        info['msg'] = 'wrong protocol %s' % info["scheme"]
        return (False, info)
    
    if check_path(info["path"]) is False:
        info['msg'] = 'wrong path %s' % info["path"]
        return (False, info)

    if not info["path"].startswith('/'):
        info['msg'] = 'Invalid path for url %s' % info["path"]
        return (False, info)
    
    if info['filetype'] in BAD_TYPES:
        info['msg'] = 'Invalid webpage type %s' % info["filetype"]
        return (False, info)
    if info["tld"] in BAD_DOMAINS:
        info['msg'] = 'bad domain %s' % info["tld"]
        return (False, info)
    else:
        return (True, info)

def filter_ads(url):
    info = {}
    info["url"] = url
    adblock = Filter(file(ABSPATH+'/ressources/easylist.txt'), is_local=True)
    if len(adblock.match(url)) != 0:
        info['msg'] = 'Adblock url'
        return (False, info)

    match_date = re.search(DATE_REGEX, url)
    # if we caught the verified date above, it's an article
    if match_date is not None:
        info["date"] = match_date.group()
        info['msg'] = 'verified for date: %s' % info["date"]
        return (True, info)
    else:
        return (True, info)

def check_url(url, source_url):
    check, info = is_valid(url, source_url)
    if check is True:
        resp, data = filter_ads(info['url'])
        if resp is True:
            return (True, data['url'])
        else:    
            return (False, data["msg"])
    else:
        return (False, info['msg'])
