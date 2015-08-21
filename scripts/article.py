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
import requests

#from url import Link
from utils import encodeValue

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
#logging.getLogger("requests").setLevel(logging.WARNING)

def check_status(f):
    def wrapper(*args):
        if args[0].status:
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

        
    
    def process(self, filter=True):
        
        self.check_depth()
        self.valid_url()
        self.fetch()
        self.extract()
        self.check_lang()
        if filter:
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
            self.step = "Validating url"
            self.code = "102"
            self.msg = "Depth of this page is %d and > %d" %(self.depth, self.max_depth)
            self.status = False
        return self.status
    
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

        return self.status
        
    
    @check_status
    #@debug
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
                    
                    try:
                        #Parsing HTML
                        #~ parser = etree.HTMLParser()
                        #~ tree   = etree.parse(StringIO(self.html), parser)
                        #self.tree = etree.HTML(self.html)
                        
                        self.tree = lxml.html.document_fromstring(self.html)
                        #Not working :(
                        #~ try:
                            #~ self.tree = autolink_html(self.tree)
                        #~ except Exception as e:
                            #~ #logger.debug(str(e))
                            #~ pass
                        self.tree = cleaner.clean_html(self.tree)
                        self.tree.make_links_absolute(self.url)
                        self.doc = lxml.html.tostring(self.tree)
                        self.parser = "lxml"
                        return self.status
                    except Exception as e:
                        logging.warning("Error parsing request answer with LXML %s" %str(e))
                        try:
                            self.parser = "bs"
                            self.doc = bs(self.html)
                            logging.warning("Activate beautifulSoup %s" %str(e))
                        except Exception as e:
                            self.msg = "Error parsing request answer with BeautifulSoup: "+str(e)
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
    #@debug
    def extract(self):
        '''extracting info from page'''
        if self.doc is not None:
            if self.parser == "lxml":
            #~ try:
                self.doc = bs(str(self.doc))
                self.full_doc = bs(self.html)
                self.text = re.sub(notalpha, " ", self.doc.find("body").text)
                links = list(set([n.get('href') for n in self.doc.find_all("a")]))
            else:
                
                self.full_doc = self.doc
                self.doc = clean_html(self.doc)
                links = make_links_absolute(self.doc, self.url)
            try:
                self.text = self.doc.get_text()
            except AttributeError:
                self.text = get_text(self.doc)
                
            self.title = get_title(self.full_doc)
            
            #get links, cited_links, cited_links_ids, cited_domains
            self.outlinks = self.parse_outlinks(links)
            
            self.generators = []
            self.meta = {}
            for n in self.doc.find_all("meta"): 
                name = n.get("name")
                prop = n.get("property")
                content = n.get("content")
                if name is not None and name not in ["type", "viewport"]:
                    if name == "Generator" or name == "generator":
                        self.generators.append(content)
                    else:
                        
                        self.meta[re.sub("og:|DC.", "", name)] = content
                    
                if prop is not None:
                    self.meta[re.sub("og:|DC.", "", prop)] = content
            try:
                self.keywords = self.meta["keywords"]
            except KeyError:
                self.keywords = ""
            
            return self.status
        else:
            #self.msg = str(#logger.debug("ParserError"))
            self.msg = "Parser Error"
            self.code = 700
            self.status = False
            return self.status
    
    def parse_link(self, url):
        '''parsing link info'''
        link = {"url":url}
        
        parsed_url = urlparse(url)
        for k in ["scheme", "netloc", "path", "params", "query", "fragment"]:
            link[k] = getattr(parsed_url,k)
                
        tld_dat = tldextract.extract(url)
        for k in ["domain", "subdomain", "suffix"]:
            link[k] = getattr(tld_dat,k)
        #~ link["subdomain"] = tld_dat.subdomain
        #~ link["domain"] = tld_dat.domain.lower()
        link["url_id"] = link["subdomain"]+"_"+link["domain"]
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
        self.outlinks = [{"url": n["url"], "source_url": self.url, "depth": self.depth+1, "type":"page"} for n in self.links]
        return self.outlinks
        
    

    
    

    @check_status
    #@debug
    def check_lang(self):
        '''checking lang'''
        try:
            self.lang = detect(self.text)
            if self.filter_lang is not False:
                if self.lang == self.filter_lang:
                    return self.status
                else:
                    self.status = False
                    return self.status
        except Exception as e:
            logging.warning("No lang detected")
            try:
                self.lang = detect(self.title)
                if self.filter_lang is not False:
                    if self.lang == self.filter_lang:
                        
                        return self.status
                    else:
                        self.status = False
                        return self.status
            except Exception as e:
                logging.warning("No lang detected using title %s" %str(e))
                print "lang_detect", e
                if self.extension in ["fr", "en", "es", "de", "nl"]:
                    self.lang = self.extension
                    if self.filter_lang is not False:
                        if self.lang == self.filter_lang:
                            return self.status
                        else:
                            self.status = False
                
        return self.status
    
    @check_status
    #@debug
    def filter_text(self):
        '''filter_text: checking relevancy'''
        q = Query(self.query, self.directory)
        #print "Debug query", q.query
        url = self.chunks.extend([self.domain, self.subdomain])
        doc = {"content": encodeValue(self.text), "title": encodeValue(self.title)}
        
        relevant = q.match(doc)
        
        if not relevant:
        
            self.code = 800
            self.msg = "Article Query Filter: text not relevant"
            self.status = False
        
        else:
            self._match = relevant
            self.status = True
        return self.status
    
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
                        if self.status:
                            data["type"] = "page"
                        else:
                            data["type"] = "log"
                else:        
                    try:
                        data[n] = self.__dict__[n]
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
        
                
    def get_status(self):
        data = {}
        for k in ["status", "date", "code", "msg"]:
            data[k] = self.__dict__[k]
            
        return data
        
                
    
    
        

    

    
if __name__ == "__main__":
    pass    
