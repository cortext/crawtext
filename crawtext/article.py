#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import os, sys
import glob
import re
from bs4 import BeautifulSoup as bs
from readability.readability import Document
import requests
import errno
from collections import defaultdict


#from url import Link
#from utils import encodeValue

from datetime import datetime as dt
from query import Query
from cleaners import *
from langdetect import detect
from database import Database, WriteError

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
    def __init__(self, item, config):
        for k, v in item.items():
            
            setattr(self, k, v) 
        
        
        
        for k, v in config.items():
            if k != "url":
                setattr(self, k, v) 
        self.status = True
        self.load_db()
        #already somewhere in DB
        if self.exists():
            self.status = self.updated()
        else:
            self.status = self.created()
        #self.queue.delete({"url": self.url})
    @check_status
    def created(self):
        ''' '''
        if self.depth == 0:
            if self.process(False):
                try:
                    self._id = self.data.insert(self.set_data())
                except WriteError:
                    sys.exit("A former DB already exits with this name %s" %self.name)
                
                if len(self.outlinks) > 0:
                    self.queue.insert_many(self.outlinks)
            #is_source?
            else:
                try:
                    self.logs.insert(self.set_status())
                except DuplicateKeyError:
                    pass
            return True
            #should exists
        else:
            return False
    
    def download(self):
        html_archive = str(self._id)+"_"+self.date.strftime("%Y-%m-%d")+".html"
        txt_archive = str(self._id)+"_"+self.date.strftime("%Y-%m-%d")+".txt"
        hfile = os.path.join(self.project_path, html_archive)
        tfile = os.path.join(self.project_path, txt_archive)
        with open(hfile, "w") as f:
            try:
                f.write((self.html).encode("utf-8"))
            except AttributeError:
                hfile = False
        with open(tfile, "w") as f:
            try:
                f.write((self.text).encode("utf-8"))
            except AttributeError:
                tfile = False
                
        return (hfile, tfile)
    
    @check_status
    def updated(self):
        ''' general treatment if queue send to log or data 
            if already in data or log detect change
        '''
        self.set_page_type()
        if self.page_type == "queue":
            #normal case queue >>> process >>> True: result >>> False: log
            if self.process():
                try:
                    self.data.insert(self.set_data())
                except DuplicateKeyError:
                    pass
                self._id = self.get_id()
                for n in self.outlinks:
                    if n["url"] not in self.queue.distinct("url"): 
                        if n["url"] not in self.data.distinct("url"):
                            if n["url"] not in self.logs.distinct("url"):
                                self.queue.insert_one(n)
            else:
                self.logs.insert(self.set_data())
            return True
                    
        elif self.page_type == "log":
            print "log", self.set_status()
            
                    
            #depends on the status if blocked in text
            #should just run a part of the process
            #such as parse outlinks to check changes
            return False
            #previous status was false
            #if self.fetch():
            #    if self.extract():
                    #compare_outlinks only
            #    else:
                #has changed
            #else:
                #has changed
                    #compare_outlinks
            #if self.process():
                #and now true
            #    print("has changed")
                
            #else:
                #no change
            
            #    pass
        else:
            
            #depends on the status of changeif blocked in text
            #should just run a part of the process
            #such as parse outlinks to check changes
            return False
            #previous status was true
            #if self.process():
                #no change
            #    pass
            #else:
                #print self.get_status()
                #and now false
                #print("has changed")
    
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
            self.msg = "Depth %i exceed max_depth for page" %(self.max_depth)
            self.status = False
            return self.status
        else:
            return self
    
    @check_status
    #@debug
    def valid_url(self):
        '''checking url format and validity'''
            
        for k, v in self.parse_link().items():
            if k is None:
                continue
            if v is None or v == "":
                setattr(self, k, "")
            else:
                try:
                    setattr(self, k, str(v))
                except UnicodeEncodeError:
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
        try:
            if self.path in BAD_PATHS:
                self.msg = 'URL: Bad path %s' % self.path
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
            self.text = re.sub("  |\t", " ",bs(self.article, "lxml").get_text())
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
        if self.doc is not None and self.doc != "":
            
            links = list(set([n.get('href') for n in bs(self.article, "lxml").find_all("a")]))
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
    
    def parse_link(self, url=None):
        '''parsing link info'''
        if url is None:
        #just in case url is a simple link
            if type(self.url) == str or type(self.url) == unicode:
                self.link = {"url": self.url}
            else:
                self.link = self.url
        else:
            self.link = {"url": url}
        
        parsed_url = urlparse(self.url)
        for k in ["scheme", "netloc", "path", "params", "query", "fragment"]:
            if k == "query":
                self.link["url_query"] = getattr(parsed_url,k)
            else:
                self.link[k] = getattr(parsed_url,k)
                
        tld_dat = tldextract.extract(self.link["url"])
        for k in ["domain", "subdomain", "suffix"]:
            self.link[k] = getattr(tld_dat,k)
        #~ link["subdomain"] = tld_dat.subdomain
        #~ link["domain"] = tld_dat.domain.lower()
        
        if self.link["subdomain"] not in ["www", "ww1", "ww2", "", None]:
            self.link["url_id"] = self.link["subdomain"]+"_"+self.link["domain"]
        else:
            self.link["url_id"] = self.link["domain"]
        
        self.link["extension"] =  self.link["suffix"]
        del self.link["suffix"]
        self.link["id"] = self.link["url_id"]+"_"+self.link["extension"]
        self.link["chunks"] = [x for x in self.link["path"].split('/') if len(x) > 0]
        self.link["internal_depth"] = len(self.link["chunks"])
        self.link["filetype"] = re.split(".", self.link['netloc'])[-1]                
        return self.link
        
    
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
        for n in bs(self.doc, "lxml").find_all("meta"): 
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
    
        
    #@debug
    def set_data(self):
        '''Add data : updating values of page_info'''
        #data = {}
        data = defaultdict.fromkeys(["cited_links", "cited_links_ids", "cited_domains", "title", "text","html", "keywords", "generators", "status", "code", "msg", "date", "link"], None)
        try:
            for k,v in self.link.items():
                data[k] = v
        except AttributeError:
            pass
            
        for k in data.keys():
            try:
                if k not in ["html", "txt"]:
                    data[k] = self.__dict__[k]
                
                    
            except KeyError:
                pass
            except AttributeError:
                pass
                
        data["html"], data["text"] = self.download()
        return data
    
    def set_status(self):
        
        data = defaultdict.fromkeys(["status", "code", "msg", "date", "history"], None)
        try:
            for k,v in self.link.items():
                data[k] = v
        except:
            pass
        data["url"] = self.url
        for k in ["status", "date", "code", "msg", "link"]:
            try:
                data[k] = self.__dict__[k]
            except KeyError:
                data[k] = None
        return data
    def load_db(self):
        self.db = Database(self.name)
        self.data = self.db.use_coll("data")
        self.logs = self.db.use_coll("logs")
        self.queue = self.db.use_coll("queue")

    def get_id(self):
        doc = self.data.find_one({"url": self.url})
        if doc is not None:
            self._id = doc["_id"]
            print doc["_id"]
            return self._id
    def is_result(self):
        doc = self.data.find_one({"url": self.url})
        return bool(doc is not None)
    
    def is_log(self):
        doc = self.logs.find_one({"url": self.url})
        return bool(doc is not None)
    
    def is_queued(self):
        doc = self.queue.find_one({"url": self.url})
        return bool(doc is not None)
    def is_source(self):
        doc = self.queue.find_one({"url": self.url, "depth":0})
        return bool(doc is not None)
        
    def exists(self):
        return any([self.is_result(),self.is_log(), self.is_queued()])
    
    def set_page_type(self):
        types =[("result",self.is_result()), ("log",self.is_log()), ("queue",self.is_queued())]
        try:
            page_type = [t[0] for t in types if t[1] is True]
            if len(page_type) == 1:
                self.page_type = page_type[0]
            else:
                self.page_type = page_type
                print self.page_type
            
        except IndexError:
            self.page_type = None
        return self.page_type
     
     
if __name__ == "__main__":
    pass
    #test
    #~ item = {"url":"http://www.cop21.gouv.f/en", "source_url":"search", "depth":0}
    #~ from config import config
    #~ cfg = config()
    #~ name = cfg["project"]["name"]
    #~ task_db = Database(cfg["default"]["db_name"])
    #~ coll = task_db.use_coll("job")
    #~ task = coll.find_one({"name":name})
    #~ a = Page(item, task)
    #~ print a.status
    #~ if a.status is True:
    #if a.exists():
    #    print a.set_page_type()
        #~ a.set_data()
    #~ else:
        #~ print a.set_status()
    #a.add_data()
    #~ pass
    
    
