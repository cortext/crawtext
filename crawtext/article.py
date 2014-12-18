#!/usr/bin/env python
# -*- coding: utf-8 -*-

__title__ = 'crawtext'
__author__ = 'c24b'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014-2015, c24b'

import logging
import copy
import os
import glob
from bs4 import BeautifulSoup
import requests
#from url import Link
from utils import encodeValue
from text import clean_text
from query import Query
from link import Link

class Page(object):
    """Article objects abstract an online news article page
    """
    def __init__(self, url, source_url= None, depth = "",  debug= False):
        """The **kwargs argument may be filled with config values, which
        is added into the config object
        """

        self.debug = debug
        self.depth = depth
        self.url = url
        self.source_url = source_url
        self.html = u''
        self.status = True

    def is_valid(self, max_depth):
        url = Link(self.url, self.source_url, self.debug)
        if self.depth > max_depth :
            if self.debug: print "depth for this page is %d and max is set to %d" %(self.depth,max_depth)
            self.step = "Validating url"
            self.code = "102"
            self.msg = "Depth of this page is > %d" %self.depth
            self.status = False

        if url.is_valid():
            self.url = url.url
            return True
        else:
            self.msg = url.msg
            self.code = "100"
            self.step = "Validating page"
            self.status = False
            return False

    def fetch(self):
        try:
            # req = requests.get((self.url), headers = headers ,allow_redirects=True, proxies=None, timeout=5)
            req = requests.get(self.url, allow_redirects=True, timeout=5)
            req.raise_for_status()
            try:
                self.html = req.text
                self.msg = "Ok"
                self.code = 200
                self.status = True
                if 'text/html' not in req.headers['content-type']:
                    self.msg ="Control: Content type is not TEXT/HTML"
                    self.code = 404
                    self.status = False
                    return False
            #Error on ressource or on server
                elif req.status_code in range(400,520):
                    self.code = int(req.status_code)
                    self.msg = "Control: Request error on connexion no ressources or not able to reach server"
                    self.status = False
                    return False
                else:
                    return True

            except Exception as e:
                self.msg = "Requests: answer was not understood %s" %e
                self.code = 400
                self.status = False
                return False
        except Exception as e:
                self.msg = str(e)
                try:
                    self.code = req.status_code
                except Exception:
                    self.code = 400
                self.status = False
                return False
    def log(self):
        if self.debug is True:
            print "Log", self.status, self.msg, self.code 
        return {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code}    
    def export(self):
        return {"url":self.url, "source_url": self.source_url, "depth": self.depth, "html": self.html}

class Article(object):
    def __init__(self, url, html, source_url=u'', depth="",  debug= False):
        self.url = url
        self.html = html
        self.source_url = source_url
        self.depth = depth
        self.debug = debug
        self.keywords = []
        self.description = u''
        self.metalang = ""
        self.meta = None
        self.status = True

    def extract(self):
        self.doc = BeautifulSoup(self.html)
        self.text = clean_text(self.html)
        if self.doc is not None:
            try:
                self.title = (self.doc.find("title").text).encode('utf-8')
                self.get_meta()
                return True
            except Exception as ex:
                self.status = False
                self.msg = str(ex)
                self.code = "700"
                return False
        else:
            self.status = False
            self.msg = "No html loaded"
            self.code = "700"
            return False
    def get_meta(self):
        self.meta = self.doc.findAll("meta")
        self.meta = [(n["name"], n["content"]) for n in self.meta if n is not None and "content" in n and "name" in n]
        return self.meta

    def correct_lang(self,filter_lang):
        if filter_lang is True and self.metalang is not None:
            if self.metalang == filter_lang:
                return True
            else:
                return False
        else:
            return True
    
    def check_link(self, url, source_url):
        url = Link(url, source_url)
        if url.is_valid():
            return url.url
        else:
            return None

    def format_outlink(self, linklist):
        for link in linklist:
            yield {"url":link, "depth":self.depth+1, "source_url": self.url}
        
    def fetch_links(self):
        links = []
        
        for n in self.doc.findAll("a"):
            if n is not None:
                try:
                    url = self.check_link(n.get('href'), self.source_url)
                    if url is not None:
                        links.append(url)
                except Exception as ex:
                    pass
        self.links = list(set(links))
        return self.links

    def get_outlinks(self):
        self.fetch_links()
        self.outlinks= [n for n in self.format_outlink(self.links)]
        return self.outlinks
        

    def check_lang(self, lang):
        if self.lang is not None:
            if self.lang == self.metalang:
                return True
            else:
                return False
        return False

    def filter(self, query, directory):
        if self.is_relevant(query, directory):
            return True
        else:
            self.code = 800
            self.msg = "Article Query: not relevant"
            self.status = False
            return False

    def export(self):
        l = Link(self.url,self.source_url)
        l = l.parse_url(self.url)

        return {
                "url": self.url,
                "subdomain": l.subdomain,
                "extension": l.extension,
                "dt": l.filetype,
                "source": self.source_url,
                "title": self.title,
                "links": self.links,
                "html": self.html,
                "text": self.text,
                "keywords": self.keywords,
                "description": self.description,
                "meta": self.meta,
                "lang": self.metalang,
                }
        
    
    def is_relevant(self, query, directory):
        q = Query(query, directory)
        return q.match({"content": encodeValue(self.text)})
    def log(self):
        if self.debug is True:
            print "Log sent", {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code}
        return {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code}    

    # def json(self):
    #     result = {}
    #     values = ['title', 'date', 'depth','outlinks', 'inlinks', 'source_url']
    #     for k,v in self.__dict__.items():
    #         if k in values and v is not None:
    #             if type(v) == set:
    #                 v = list(v)
    #             result[k] = v
    #     return result
