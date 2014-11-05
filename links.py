#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import datetime
import logging
import re, os, sys

from urlparse import (
    urlparse, urljoin, urlsplit, urlunsplit, parse_qs)

from packages.tldextract import tldextract

import posixpath, sys, os
import six
from six.moves.urllib.parse import ParseResult, urlunparse, urldefrag, urlparse
import urllib
import cgi

# scrapy.utils.url was moved to w3lib.url and import * ensures this move doesn't break old code
from w3lib.url import *
from packages.encoding import unicode_to_str


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
        self.status = self.is_valid()

