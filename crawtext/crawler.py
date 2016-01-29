#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Usage: crawtext.py [(config|run <task-db>)] ...

Options:
    run     run the scheduled crawtext project
    config  create a new crawtext project based on the config.json file
"""
__script__ = "crawtext"
__version__ = "6.0.0"
__author_username__= "c24b"
__author_email__= "4barbes@gmail.com"
__author__= "Constance de Quatrebarbes"
from config import Project
from requests_futures.sessions import FuturesSession
from parser import *
 
import pymongo
from pymongo import MongoClient
import os, sys, lxml, re
from bs4 import BeautifulSoup as bs
from readability.readability import Document
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("readability").setLevel(logging.WARNING)


class Crawler(object):
    def __init__(self):
        print "xxxxxxxxxxxxxxxxxxxxxx"
        p = Project()
        self.PROJECT = p.get()
        
        #print self.PROJECT
        DB = p.get_config()["db"]
        
        self.name = self.PROJECT["name"]
        self.directory = self.PROJECT["directory"]
        self.status = self.PROJECT["status"]
        self.date = self.PROJECT["date"][-1]
        #Global config
        self.setup(DB)
        self.load_filters()
        if self.PROJECT["reload"] and self.PROJECT["status"]:
            self.add_seeds()
        self.get_seeds()
        
    def load_default(self):
        filters = {k: self.params["seeds"][k]["active"] for k in self.PROJECT["seeds"].keys()}
        seeds_options = [k for k, v in filters.items() if v is True]
        
            
    def exists(self):
        return bool(self.name in self.DB['client'].database_names())
        
    def setup(self, config):
        self.DB = {}
        self.DB["uri"] = '%sdb://%s,%s:%s'%(config["provider"], config["host"], config["host"], config["port"])
        self.DB["client"] =  MongoClient(self.DB["uri"])
        
        self.db = self.DB["client"][self.name]
        if not self.exists():
            del self.PROJECT["_id"]
            self.infos = self.db["infos"].insert_one(self.PROJECT)
            self.db["seeds"].create_index("url",unique=True, background=True, safe=True)
            self.db["data"].create_index("url",unique=True, background=True)
        
        self.seeds = self.db["seeds"]
        self.data = self.db["data"]
        self.queue = {}
        
        return self
    def load_filters(self):
        filters = {k: self.PROJECT["filters"][k]["active"] for k in self.PROJECT["filters"].keys()}
        self.filters = {}
        self.values = {}
        for k,v in filters.items():
            if v is True:
                
                setattr(self, k, self.PROJECT["filters"][k][k])
            else:
                self.filters[k] = v
        return self.filters
        
    def add_seeds(self):
        #~ print self.PROJECT.keys()
        filters = {k: self.PROJECT["seeds"][k]["active"] for k in self.PROJECT["seeds"].keys()}
        seeds_options = [k for k,v in filters.items() if v is True]
        for n in seeds_options:
            
            if n == "search":
                params = self.PROJECT["seeds"][n]
                params["query"] = self.PROJECT["filters"]["query"]["query"]
                self.search(params)
            else:
                params = self.PROJECT["seeds"][n]
                if n == "file":
                    self.add_file(params[n])
                elif n == "url":
                    self.add_url(params[n])
        return
    def add_file(self, filename):
        #print self.SETTINGS["dir"], filename
        if filename.startswith("./"):
            filename = os.path.realpath(filename)
            #print filename
        else:
            
            parent_dir = os.path.abspath(os.path.join(self.SETTINGS["dir"], os.pardir))
            #print filename
        try:
            with open(filename, "r") as f:
                seeds =  [n.replace("\n","") for n in f.readlines() if n != "\n"]
                for r, url in enumerate(seeds):
                    self.add_url(url, r, "file")
            return self
        except IOError:
            sys.exit("File not found")
    
    def add_url(self, url, rank=0, method="url"):
        
        try:
            self.seeds.insert_one({
                                "date": [self.date],
                                "url": url,
                                "url_id" : get_url_id(url),
                                "title": None,
                                "description": None,
                                "rank": rank,
                                "source_url": None,
                                "depth": 0,
                                "method": method
                                })
                                    
        except pymongo.errors.DuplicateKeyError:
            print "Duplicate"
        return self
    def search(self, params):
        session = FuturesSession()
        def get_req(future):
            response = future.result()
            results = response.json()['d']['results']
            
            for res in results:
                position = int(res['__metadata']['uri'].split("&$")[1].split("=")[1])+1
                url, description, title = res["Url"], res["Description"], res["Title"]
                try:
                    self.seeds.insert({
                                        "date": [self.date],
                                        "url": url,
                                        "url_id" : get_url_id(url),
                                        "title": title,
                                        "description": description,
                                        "rank": position,
                                        "source_url": None,
                                        "depth": 0,
                                        "method": "search",
                                        "query": params["query"],
                                            })
                                    
                except pymongo.errors.DuplicateKeyError:
                    #print "Alredy in DB"
                    pass
            
        for i in range(0,params["nb"]+50, 50):
            
            future = session.get(
                        'https://api.datamarket.azure.com/Bing/Search/v1/Web',
                        params={    '$format' : 'json',
                                    '$skip' : i,
                                    '$top': 50,
                                    'Query' : '\'%s\'' %params["query"],},
                        auth=(params["key"], params["key"]),
                        headers = { 'User-agent': 'Mozilla/5.0',
                                    'Connection': 'close'}
                    )
            try:
                future.add_done_callback(get_req)
            except:
                pass
        return self
    
    def check_depth(self, depth):
        if self.depth is not False:
            return (depth<=self.depth)
        else:
            return True
    
    def check_lang(self, text):
        self.data["lang"] 
        if self.lang is not False:
            try:
                self.data["lang"] = langdetect(text)
                return (self.lang == self.data["lang"])
            except Exception as e:
                print e
                return True
        else:
            return True
    
    def check_query(self, text):
        if self.query is not False:
            q = Query(self.query, self.directory)
            doc = {"content": text}
            return (q.match(doc))
        else:
            return True
    
    def extract_text(self, html, url):
        print lxml_cleaner(html, url)
        #~ print extract_article(html, url)
        #~ print 
    def extract_outlinks(self, html):
        pass
    
    def extract_meta(self,html):
        pass
        
    def check_status(self, reponse):
         return (reponse not in range(400,520))
    
        
    def get_seeds(self):
        '''download url'''
        filters = False
        session = FuturesSession()
        def get_req(future):
            #print filters
            response = future.result()
            if self.check_status(response.status_code):
                if "text/html" in response.headers['content-type']:
                    html = response.text
                    encoding = response.encoding.lower()
                    print encoding
                    fname = url.url_id.replace(".", "_")+"_VERSION_"+self.date.strftime("%d_%m_%Y_%H_%M")
                    f = os.path.join(self.directory, fname)
                    with open(f, "w") as f:
                        html = (html).encode("utf-8")
                        f.write(html)
                    #text = self.extract_text(html)
                    article = lxml_extractor(html, response.url)
                    #~ print article[0:500]
                    fname = url.url_id.replace(".", "_")+"_VERSION_"+self.date.strftime("%d_%m_%Y_%H_%M")+".txt"
                    f = os.path.join(self.directory, fname)
                    with open(f, "w") as f:
                        f.write(article.encode("utf-8"))
                elif "pdf" in response.header["content-type"] or "pdf" or url.filetype:
                    print "PDF!"
                    
            #print(response.url, response.status_code)
            
        for x in self.seeds.find({},{"url":1, "depth":1, "_id":0}):
            url = Url(x["url"])
            url.clean_url()
            
            future = session.get(url.url)
            try:
                future.add_done_callback(get_req)
            except:
                pass
            break
            sys.exit()
    
            
if __name__=="__main__":
    c = Crawler()
    
