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
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor, as_completed
 
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
        print self.name
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
            self.db["data"].create_index("url",unique=True, background=True, safe=True)
            self.db["queue"].create_index("url", unique=True, background=True)
        self.seeds = self.db["seeds"]
        self.data = self.db["data"]
        self.queue = self.db["queue"]
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
        return self
        
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
            pass
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
                    self.seeds.update({"url": url}, {'$push': {"date": self.date}})
            
            
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
    def check_url(self, url):
        try:
            url = url.__dict__
        except ValueError, AttributeError:
            pass
        '''check the validity of the url'''
        if url["scheme"] not in ACCEPTED_PROTOCOL:
            self.msg = "Bad scheme"
            return False
        if url["filetype"] in BAD_TYPES:
            self.msg = "Bad filetype"
            return False
        if url["domain"] in BAD_DOMAINS:
            self.msg = "Bad domain"
            return False
        if url["subdomain"] in BAD_SUBDOMAINS:
            self.msg = "Bad domain"
            return False
        if url["path"] in BAD_PATHS:
            self.msg = "Bad domain"
            return False
        if filter.match(url["url"]):
            return False
        else:
            return True
    
    def check_lang(self, text):
        '''check if filter lang is activated and match'''
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
        '''check if filter query is activated and match on a given text'''
        if self.query is not False:
            q = Query(self.query, self.directory)
            doc = {"content": text}
            return (q.match(doc))
        else:
            return True

    def extract_outlinks(self, html, url):
        '''extract links on page'''
        soup = bs(html, "lxml")
        outlinks = []
        _urls = set([u.get("href") for u in soup.findAll("a") if u.get("href") is not None and u.get("href") != "" and u.get("href") != url.url])
        for u in _urls:
            u = Url(u)
            if not u.is_absolute():
                u.make_absolute(url.url)
            u.clean_url()
            if bool(u.url != url.url):
                
                if self.check_url(u):                    
                    doc = {"url":u.url, "url_id": u.url_id, "url_info": u.export()}
                    outlinks.append(doc)
        
        return outlinks
    
    def extract_keywords(self, meta):
        return meta["keywords"]
        
    def extract_meta(self,html):
        '''extraire les balises meta de la page'''
        
        meta = {"generators": [],
                "keywords":[]
                    }
        for n in bs(html, "lxml").find_all("meta"): 
            name = n.get("name")
            prop = n.get("property")
            content = n.get("content")
            if name is not None and name not in ["type", "viewport"]:
                if name.lower() in ["generator"]:
                    meta["generators"].append(content)
                else:
                    meta[re.sub("og:|DC.", "", name)] = content
                #~ 
            if prop is not None:
                meta[re.sub("og:|DC.", "", prop)] = content
        
        return meta
    
    def store_file(self, url_id, data, fmt="txt"):
        if fmt is None:
            fname = url_id.replace(".", "_")+"_VERSION_"+self.date.strftime("%d_%m_%Y_%H_%M")
        else:    
            fname = url_id.replace(".", "_")+"_VERSION_"+self.date.strftime("%d_%m_%Y_%H_%M")+"."+fmt
        fname = os.path.join(self.directory, fname)
        with open(fname, "w") as f:
            data = (data).encode("utf-8")
            f.write(data)
        return fname

    def extract_article(self, response, depth=0):
        article = {}
        html = response.text
        
        url = response.url
        url = Url(url)
        article["url"] = url.url
        article["url_id"] = url.url_id
        
        article_txt = lxml_extractor(html, url)
        article["html_file"] = self.store_file(url.url_id, article_txt)
        article["txt_file"] = self.store_file(url.url_id, article_txt, fmt="txt")
        article["depth"] = depth
        article["url_info"] = url.export()
        article["type"] = response.headers['content-type']
        article["encoding"] = response.encoding.lower()
        article["outlinks"] = self.extract_outlinks(html, url)
        return article
    
    def get_seeds(self):
        '''download and store seeds'''
        filters = False
        session = FuturesSession()
        def get_req(future):
            response = future.result()
            if response.status_code not in range(400,520):
                if "text/html" in response.headers['content-type']:
                    article = self.extract_article(response)
                    article["status"] = True
                    article["depth"] = 0
                    article_url = article["url"]
                    
                    try:
                        self.db.data.insert_one(article)
                        
                    except pymongo.errors.DuplicateKeyError:
                        #update
                        
                        #self.db.seeds.update_one({"url":article_url]}, {"$set":article})
                        pass
                    
                    self.db.seed.update_one({"url":article_url}, {"$set":article})
                    for n in article["outlinks"]:
                        n["depth"] = 1
                        
                        try:
                            self.queue.insert_one(n)
                        except pymongo.errors.DuplicateKeyError:
                            pass                    
                else:
                    status_code = 406
                    msg = "Format de la page non supporté: %s" %response.headers['content-type']
                    self.db.seeds.insert_one({"url": response.url}, {"$set":{"status": False, "status_code": status_code, "msg": msg}}, upsert=False)
            else:
                status_code = response.status_code
                msg = "Page indisponible"
                self.db.seeds.insert_one({"url": response.url}, {"$set":{"status": False, "status_code": status_code, "msg": msg}})
        
        for x in self.seeds.find({},{"url":1, "depth":1, "_id":0,"status":1}):
            url = Url(x["url"])
            url.clean_url()
            future = session.get(url.url)
            try:
                future.add_done_callback(get_req)
                
            except Exception as e:
                print e
                pass
        print self.queue.count()
    
    def crawl(self):
        '''main crawl'''
        URLS = self.queue.find()
        def load_url(self, article):
            if self.check_depth(article["depth"]):
                
                response = request.get(article["url"])
                if response.status_code not in range(400,520):
                    if "text/html" in response.headers['content-type']:
                        a = self.extract_info(response, depth)
                        
                    else:
                        status_code = 406
                        msg = "Format de la page non supporté: %s" %response.headers['content-type']
                        try:
                            self.db.data.insert_one({"url": response.url}, {"$set":{"status": False, "status_code": status_code, "msg": msg}}, upsert=False)
                        except:
                            pass
                else:
                    status_code = response.status_code
                    msg = "Page indisponible"
                    try:
                        self.db.data.insert_one({"url": response.url}, {"$set":{"status": False, "status_code": status_code, "msg": msg}})
                    except:
                        pass
            else:
                try:
                    self.db.data.insert_one({"url": response.url}, {"$set":{"status": False, "status_code": 501, "msg": "Depth exceeded"}})
                except:
                    pass
            
            
            
    
            
if __name__=="__main__":
    c = Crawler()
    
