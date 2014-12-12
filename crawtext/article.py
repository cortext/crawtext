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
import re
from bs4 import BeautifulSoup
import requests
from url import Link
from utils import encodeValue

class ArticleException(Exception):
    pass


class Article(object):
    """Article objects abstract an online news article page
    """
    def __init__(self, url, depth="", source_url=u'', debug= False):
        """The **kwargs argument may be filled with config values, which
        is added into the config object
        """
        self.debug = debug
        # if self.debug: print "Article Debug is activated"

        self.depth = depth
        if source_url == u'':
            source_url = urls.get_scheme(url) + '://' + urls.get_domain(url)

        
        self.source_url = encodeValue(source_url)

        url = encodeValue(url)
        self.url = Link(url)
        if self.url.is_valid():
            self.url = self.url.prepare_url(self.source_url)
            if self.debug: print ">>Treating", self.url
            self.title = u''
            # Body text from this article
            self.text = u''

            # This article's unchanged and raw HTML
            self.html = u''

            # Flags warning users in-case they forget to download() or parse()
            # or if they call methods out of order
            self.is_parsed = False
            self.is_downloaded = False

            self.status = True
            if url == None:
                self.status = False
            if url == "":
                self.status = False
            self.links = []
            self.keywords = []
            self.description = u''
            self.authors = []
            self.generator = None

        else:
            self.status = False
            self.msg = self.url.msg
            self.code = self.url.code
            self.url = url
            
        

    def fetch(self):
        if self.status:
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
                        self.code = req.status_code
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
                self.msg = "Requests: answer was not understood %s" %e
                self.code = 400
                self.status = False
                return False
        else:
            self.code = 300
            self.msg = "Fetch: url is invalid %s" %self.url
            self.status = False
            return False

    def extract(self):
        self.doc = BeautifulSoup(self.html)
        # self.clean_doc = copy.deepcopy(self.doc)
        self.body = self.doc.body
        self.title = (self.doc.find("title").text).encode('utf-8')
        self.get_meta()
        #print self.doc.findAll("meta")
        # self.description = self.doc.find("meta", {"name":re.compile("description", re.I)})['content']
        # self.keywords = re.split(",", self.doc.find("meta", {"name":re.compile("keywords", re.I)})['content'])
        try:
            self.metalang = self.doc.find("meta", {"http-equiv":"content-language"})['content']
        except Exception:
            self.metalang = None

        
        
        # self.links = self.fetch_links()
        
        self.text = re.sub("\s\s|\n|\t", " ", (self.doc.find("body").text)).encode('utf-8')
        self.status = True
        self.msg = "Ok"
        self.code = 200
        return True

    def get_meta(self):
        self.meta = self.doc.findAll("meta")
        self.meta = [(n["name"], n["content"]) for n in self.meta if n is not None and "content" in n and "name" in n]
        for k,v in self.meta:
            print k
            setattr(self, k,v)

    def correct_lang(self,filter_lang):
        if filter_lang is True and self.metalang is not None:
            if self.metalang == filter_lang:
                return True
            else:
                return False
        else:
            return True
    def parse(self, query):
        try:
            if self.debug: print "Parsing ..."
            
            if self.is_relevant(query):
                if self.debug :print "Relevant"
                self.outlinks = self.clean_outlinks()
                return True
            else:
                self.code = 800
                self.msg = "Article Query: not relevant"
                self.status = False
                return False
        except Exception as e:
            print e
            return False        
    def export(self):
        return {
                "url": self.url,
                "title": self.title,
                "links": self.links,
                "html": self.html,
                "text": self.text,
                "keywords": self.keywords,
                "description": self.description,
                "lang": self.metalang,
                }
    
    
    def log(self):
        if self.debug is True:
            print "Log", self.status, self.msg, self.code 
        return {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code}    
    
    def fetch_links(self):
        if self.links == []:
            self.links = [n.get('href') for n in self.doc.findAll("a")]
        return list(set(self.links))

    def clean_outlinks(self):
        if self.debug: print "Calculate next links"
        self.fetch_links()
        self.outlinks= [{"url":n, "depth":self.depth+1, "source_url": self.url} for n in self.links]  
        return self.outlinks
        
    
    def is_valid_url(self):
        """Performs a check on the url of this link to determine if article
        is a real news article or not
        """
        return urls.valid_url(self.url)

    def check_lang(self, lang):
        if self.lang is not None:
            if self.lang == self.metalang:
                return True
            else:
                return False
        return False

    def is_relevant(self,query):
        
        self.relevant = query.match({"content": self.text})
        if self.relevant and self.debug : print query.hit
        return self.relevant
        #return query.match(indexed)
    
    def json(self):
        result = {}
        values = ['title', 'date', 'depth','outlinks', 'inlinks', 'source_url']
        for k,v in self.__dict__.items():
            if k in values and v is not None:
                if type(v) == set:
                    v = list(v)
                result[k] = v
        return result
