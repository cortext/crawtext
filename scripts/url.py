#!/usr/bin/env python
# -*- coding: utf-8 -*-

__title__ = 'url'
__author__ = 'c24b'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014-2015, c24b'

from urlparse import (
   urlparse, urljoin, urlsplit, urlunsplit, parse_qs)
from tldextract import tldextract
from filter import Filter
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

