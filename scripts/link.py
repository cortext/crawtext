from urlparse import (
   urlparse, urljoin, urlsplit, urlunsplit, parse_qs)
from tldextract import tldextract
from filter2 import filter
import os, sys, re
import urllib2 as ul

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
	def __init__(self, url, source_url="", origin = ""):
		self.url = url
		# self.url = ul.unquote(self.url)
		self.source_url = source_url
		self.origin = origin
		self.step = "link created"
		self.msg = "Ok"
		self.parse_url(self.url)
		self.url = "".join(self.clean_url(url, source_url))
		
		print self.url_id
		
	def clean_url(self, url, source_url):
		domain = self.get_domain(url)
		domain_id = re.sub("www\.|http://", "", self.netloc)
		domain_id = re.sub("\.", "_", domain_id)

		if url.startswith('/'):
			l = self.parse_url(source_url)
			return ("http://"+l.netloc+url, domain, l.domain_id)
		else:
			return (url, domain, domain_id)

	def get_domain(self, url):
		tld_dat = tldextract.extract(url)
		return tld_dat.domain.lower()
	
	def get_subdomain(self, url):
		tld_dat = tldextract.extract(url)
		return tld_dat.subdomain.lower()
	
	def parse_url(self,url):
		'''complete info on url'''
		self.step = "parse"
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
		self.domain = tld_dat.domain.lower()
		self.domain_id = re.sub("www\.|http\.", "", self.netloc)
		if self.subdomain in ["www", "", " "]:
			self.url_id = self.domain
		else:
			self.url_id = self.subdomain+"_"+self.domain
		
		#print "Parse url domain id", self.domain_id
		self.extension =  tld_dat.suffix
		#info on page
		self.path_chunk = [x for x in self.path.split('/') if len(x) > 0]
		self.in_depth = len(self.path_chunk)


		if self.in_depth < 1:
			self.name = ""
		else:
			self.name = self.path_chunk[-1]
		return self

	def is_valid(self):
		#print "isvalid"
		self.step = "Valid"
		if self.url in ["void", ";"]:
			self.msg ='Javascript %s' % self.url
			self.status = False
			self.code = "804"
			return False
		
		if self.url is None or len(self.url) < 11:
			self.msg ='Url is too short (less than 11) %s' % self.url
			self.status = False
			self.code = "803"
			return False
		elif self.url.startswith('javascript'):
			self.msg ='Javascript %s' % self.url
			self.status = False
			self.code = "804"
			return False
			
		if self.filter_ads(self.url):
			return False
		#invalid protocol
		if check_scheme(self.scheme) is False:
			self.msg = 'wrong protocol %s' % self.scheme
			self.status = False
			self.code = "804"
			return False
		if check_path(self.path) is False:
			self.msg ='wrong path %s' % self.path
			self.status = False
			self.code = "805"
			return False

		if self.path != "" and not self.path.startswith('/'):
			self.msg = 'Invalid path for url %s' % self.path
			self.status = False
			self.code = "805"
			return False

		if self.filetype in BAD_TYPES:
			self.msg = 'Invalid webpage type %s' % self.filetype
			self.status = False
			self.code = "806"
			return False

		if self.domain in BAD_DOMAINS:
			self.msg = 'bad domain %s' % self.domain
			self.status = False
			self.code = "807"
			return False
		return True

	def filter_ads(url):
		if filter.match(url):
			self.msg = 'Blacklisted url'
			self.status = False
			self.code = "808"
			return False
		return True
		#~ match_date = re.search(DATE_REGEX, self.url)
		#~ # if we caught the verified date above, it's an article
		#~ if match_date is not None:
			#~ self.date = match_date.group()
			#~ return True

	def export(self, depth, mode="advanced"):
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
