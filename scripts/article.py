#!/usr/bin/env python
# -*- coding: utf-8 -*-

__title__ = 'crawtext'
__author__ = 'c24b'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014-2015, c24b'

import copy
import os
import glob
import re
from bs4 import BeautifulSoup
from readability.readability import Document
import requests
import errno

import signal

#from url import Link
#from utils import encodeValue

from datetime import datetime as dt
from query import Query
from cleaners import *
from langdetect import detect


from filter import filter
from url_filter import *

import logging
logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="quickanddirty.log", format=FORMAT, level=logging.DEBUG)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("readability").setLevel(logging.WARNING)

def check_status(f):
    def wrapper(*args):
        if args[0].status is not False:
            return f(*args)
        
    return wrapper        
def debug(f):
    def wrapper(*args):
        print f.__name__
        print f.__doc__
        return f(*args)
    return wrapper    
class Page(object):
    """
        Basic Page
    """
    def __init__(self, item, config):
        """
        Mapping item and config
        """
        for k, v in item.items():
            if k in ["url", "source_url", "depth", "type"]:
                setattr(self, k, v) 
        
        
        for k, v in config.items():
            if k in ['filter_lang','max_depth', "query", "directory", "filter", "short_export", "date"]:
                setattr(self, k, v) 
            
        ##logger.debug("Page Init")
        
        self.status = True
        self.load_default()
        
        
    
    
    def load_default(self):
        self.msg = ""
        self.code = 100
        self.status = True
        return self

        
    
    def process(self, filter_text=True):
        
        self.check_depth()
        
        self.valid_url()
        
        self.fetch()
        
        self.clean_article()
        
        self.extract()
        
        self.check_lang()
        
        if filter_text:
            if self.filter is not False:
                self.filter_text()
        return self.status
        
    @check_status
    #@debug
    def check_depth(self):
        '''checking depth'''
        if self.depth is False or self.depth is None:
            self.depth = 0
            
        #logger.debug("Page check depth")
        if self.depth > self.max_depth:
            self.code = "102"
            self.msg = "Depth exceed max_depth for page" %(self.max_depth)
            self.status = False
            return self.status
        else:
            return self
    
    @check_status
    #@debug
    def valid_url(self):
        '''checking url format and validity'''
        for k, v in self.parse_link(self.url).items():
            if k is None:
                continue
            if v is None or v == "":
                setattr(self, k, "")
            else:
                setattr(self, k, v)
                
        
        try:
            if self.scheme not in ACCEPTED_PROTOCOL:
                self.msg = 'URL: Wrong protocol %s' % self.scheme
                self.status = False
                self.code = 804
                return self.status
        except Exception as e:
            logging.warning("%s" %str(e))
            pass
        try:
            if self.filetype in BAD_TYPES:
                self.msg = 'URL: Invalid webpage type %s' % self.filetype
                self.status = False
                self.code = 806
                return self.status
        except Exception as e:
            pass
        try:
            if self.domain in BAD_DOMAINS:
                self.msg = 'URL: Bad domain %s' % self.domain
                self.status = False
                self.code = 807
                return self.status
        except Exception as e:
            logging.warning("%s" %str(e))
            pass
        try:
            if self.subdomain in BAD_DOMAINS:
                self.msg = 'URL: Bad subdomain %s' % self.subdomain
                self.status = False
                self.code = 807
                return self.status
        except Exception as e:
            logging.warning("%s" %str(e))
            pass
        
        if filter.match(self.url):
            self.msg = 'URL: Blacklisted url'
            self.status = False
            self.code = 808
            return self.status

        return self
        
    
    @check_status
    def fetch(self):
        '''downloading page'''
        try:
            req = requests.get(self.url, allow_redirects=True, timeout=3)
            req.raise_for_status()
            try:
                self.html = req.text
                self.content_type = req.headers['content-type']
                if 'text/html' not in self.content_type:
                    self.msg ="Control: Content type is not TEXT/HTML"
                    self.code = 404
                    self.status = False
                    return self.status
            #Error on ressource or on server
                elif req.status_code in range(400,520):
                    self.code = int(req.status_code)
                    self.msg = "Control: Request error on connexion no ressources or not able to reach server"
                    self.status = False
                    return self.status
                else:
                    if self.html == "" or self.html is None:
                        self.msg = "Error loading HTML from request"
                        self.code = 405
                        self.status = False
                        return self.status
                    try:
                        self.html = self.html
                        self.tree = lxml.html.document_fromstring(self.html)
                        #cleaning with lxml it's fun!
                        self.tree = cleaner.clean_html(self.tree)
                        self.tree.make_links_absolute(self.url)
                        self.doc = lxml.html.tostring(self.tree)
                        self.doc = (self.doc).replace(unichr(160), " ")
                        self.doc = re.sub(re.compile("\r+|\n+|\t+|\s+")," ",self.doc)
                        if self.doc == "" or self.doc is None:
                            self.msg = "Error loading HTML from request"
                            self.code = 405
                            self.status = False
                            return self.status
                        else:
                            return self
                        
                    except Exception as e:
                        self.msg = "Error loading HTML: "+str(e)
                        self.code = 405
                        self.status = False
                        return self.status

            except Exception as e:
                self.msg = "Requests: answer was not understood %s" %e
                self.code = 400
                self.status = False
                return self.status
                
        except Exception as e:
            #logger.warning(e)
            self.msg = "Incorrect link url"
            try:
                self.code = req.status_code
                self.status = False
                return self.status
            except Exception as e:
                self.code = 400
                self.status = False
                return self.status
    @check_status
    def clean_article(self):
        
        try:
            self.clean_doc = Document(self.doc,url = self.url, positive_keywords= "entry-content,post,main,content,container,blog,article*,post,entry", negative_keywords="like*,ad*,comment.*,comments,comment-body,about,access,navigation, sidebar.*?,share.*?,relat.*?,widget.*?")
            self.article = self.clean_doc.summary()
            self.text = re.sub("  |\t", " ",bs(self.article).get_text())
            self.title = self.clean_doc.short_title()
            if self.text == "" or self.text == u'':
                self.msg = "Error extracting Article and cleaning it"
                self.code = 700
                self.status = False
                return self.status
            if self.title == '':
                self.title = u''
            return self
        except AttributeError as e:
            self.msg = "Error loading HTML: %s" %str(e)
            self.code = 400
            self.status = False
            return self.status
        
    @check_status
    #@debug
    def extract(self):
        '''extracting info from page'''
        if self.doc is not None:
            
            links = list(set([n.get('href') for n in bs(self.article).find_all("a")]))
            links = [n for n in links if n != self.url]
            #get links, cited_links, cited_links_ids, cited_domains
            self.outlinks = self.parse_outlinks(links)
            self.get_meta()
            return self
        else:
            #~ #self.msg = str(#logger.debug("ParserError"))
            self.msg = "Extract Error"
            self.code = 701
            self.status = False
            return self.status
    
    def parse_link(self, url):
        '''parsing link info'''
        link = {"url":url}
        
        parsed_url = urlparse(url)
        for k in ["scheme", "netloc", "path", "params", "query", "fragment"]:
            if k == "query":
                link["url_query"] = getattr(parsed_url,k)
            else:
                link[k] = getattr(parsed_url,k)
                
        tld_dat = tldextract.extract(url)
        for k in ["domain", "subdomain", "suffix"]:
            link[k] = getattr(tld_dat,k)
        #~ link["subdomain"] = tld_dat.subdomain
        #~ link["domain"] = tld_dat.domain.lower()
        if link["subdomain"] not in ["www", "ww1", "ww2", ""]:
            link["url_id"] = link["subdomain"]+"_"+link["domain"]
        else:
            link["url_id"] = link["domain"]
            
        link["extension"] =  link["suffix"]
        del link["suffix"]
        link["chunks"] = [x for x in link["path"].split('/') if len(x) > 0]
        link["internal_depth"] = len(link["chunks"])
        link["filetype"] = re.split(".", link['netloc'])[-1]                
        return link
        
    
    def parse_outlinks(self, links):
        '''creating outlinks from page'''
        self.links = [self.parse_link(url) for url in set(links) if url is not None and url != ""]
        
        self.cited_links = [n["url"] for n in self.links]
        self.cited_links_ids = [n["url_id"] for n in self.links]
        self.cited_domains = [n["domain"] for n in self.links]
        self.outlinks = [{"url": n["url"], "url_id":n["url_id"], "source_url": self.url, "depth": self.depth+1, "type":"page"} for n in self.links]
        return self.outlinks
        
    def get_meta(self):
        self.generators = []
        self.meta = {}
        for n in bs(self.doc).find_all("meta"): 
            name = n.get("name")
            prop = n.get("property")
            content = n.get("content")
            if name is not None and name not in ["type", "viewport"]:
                if name.lower() in ["generator"]:
                    self.generators.append(content)
                else:
                    self.meta[re.sub("og:|DC.", "", name)] = content
                #~ 
            if prop is not None:
                self.meta[re.sub("og:|DC.", "", prop)] = content
        try:
            self.keywords = self.meta["keywords"]
        except KeyError:
            self.keywords = [""]
        return self.meta 
    
    

    @check_status
    #@debug
    def check_lang(self):
        '''checking lang'''
        try:
            self.lang = detect(self.text)
        except Exception as e:
            logging.warning("No lang detected in article")
            try:
                self.lang = detect(self.title)
            except Exception as e:
                logging.warning("No lang detected in title")
                self.lang = None
                
        if self.filter_lang is not False:
            if self.lang == self.filter_lang:
                return self
            else:
                self.status = False
                return self.status

    
    @check_status
    #@debug
    def filter_text(self):
        '''filter_text: checking relevancy'''
        
        q = Query(self.query, self.directory)
        #print "Debug query", q.query
                
        doc = {"content": self.text, "title": self.title}
        
        relevant = q.match(doc)
        
        if relevant is False:
        
            self.code = 800
            self.msg = "Article Query Filter: text not relevant"
            self.status = False
            return self.status
        else:
            self.status = True
            return self
    
    def format_export(self):
        '''format export'''
        #for n in ["url_id","url", "cited_links", "cited_links_ids","source_url", "cited_domains", "title", "text", "keywords", "generators", "extension", "filetype", "depth", "crawl_nb", "status", "msg", "date", "code", "nb", "total"]:
        pass
    #@debug
    def set_data(self):
        '''Set data : creating default page info'''
        data = {}
        for n in ["url", "url_id","url", "cited_links", "cited_links_ids","source_url", "cited_domains", "title", "text", "keywords", "generators", "extension", "filetype", "depth", "crawl_nb", "status", "msg", "date", "code", "lang"]:
            #unique info
            if n in ["url_id","url","extension", "filetype", "depth", "crawl_nb", "source_url", "type", "lang"]:
                if n in ["type"]:
                    if self.depth == "0":
                        data["type"] = "source"
                    else:
                        if self.status is True:
                            data["type"] = "page"
                        else:
                            data["type"] = "log"
                else:        
                    try:
                        data[n] = unicode(self.__dict__[n])
                    except KeyError:
                        if n in ["crawl_nb", "depth"]:
                            data[n] = 0
                        else:
                            data[n] = None
            #multiple info
            else:
                try:
                    data[n] = [self.__dict__[n]]
                    
                except KeyError:
                    data[n] = [None]
        #meta_data
        #~ for k, v in self.meta.items():
            #~ data["meta_"+k] = v
        return data
    #@debug
    def add_data(self):
        '''Add data : updating values of page_info adding contextual info to existing'''
        data = {}
        for n in ["cited_links", "cited_links_ids", "cited_domains", "title", "text", "keywords", "generators", "status", "code", "msg", "date"]:
            try:
                data[n] = self.__dict__[n]
            except KeyError:
                data[n] = None
            
        return data
        
    def set_last(self):
        data = {}
        for n in ["cited_links_ids", "title", "text", "status", "code", "msg", "date"]:
            try:
                data["last_"+n] = self.__dict__[n]
            except KeyError:
                data["last_"+n] = None
        return data
        
                
    def get_status(self):
        data = {}
        for k in ["status", "date", "code", "msg"]:
            try:
                data[k] = self.__dict__[k]
            except KeyError:
                data[k] = None
        return data
        
                
    
    
        

    

    
if __name__ == "__main__":
    #test
    #~ item = {"url":"http://www.ifpeb.fr/", "source_url":"", "depth":0, "type":"source"}
    #~ config = {'filter_lang':"fr","max_depth":10, "query": "(COP 21) OR (COP21)", "filter":True, "directory":"./projects/COP21/"}
    #~ a = Page(item, config)
    #~ a.process()
    #~ print a.get_status()
    pass
