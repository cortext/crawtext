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
#import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
import requests
from requests_futures.sessions import FuturesSession
requests.packages.urllib3.disable_warnings()
from extractor import *
from parser import *
from url import Url, get_outlinks
import pymongo
from pymongo import MongoClient
from pymongo import DeleteOne, InsertOne
import os, sys, bson
#from pymongo import bson
from logger import logger


#~ logging.getLogger("requests").setLevel(logging.WARNING)




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
        print self.PROJECT["history"]
        self.status = self.PROJECT["status"]
        self.date = self.PROJECT["date"][-1]
        #Global config
        self.setup(DB)
        self.load_filters()
        
        
    
    def start(self):
        #debug
        #~ self.get_seeds
        if self.PROJECT["reload"]:
            self.add_seeds()
        if self.status:
            self.add_seeds()
            
        if self.db.seeds.count() == 0:
            self.add_seeds()
            
        if self.db.queue.count() > 0:
            self.get_seeds()
        
        
        self.crawl()
        #queue = {e.submit(self.get_seeds())}
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
            self.db["seeds"].create_index("url",unique=True, safe=True)
            self.db["data"].create_index("url",unique=True, safe=True)
            self.db["queue"].create_index("url", unique=True,safe=True)
        #~ self.seeds = self.db["seeds"]
        #~ self.data = self.db["data"]
        #~ self.queue = self.db["queue"]
        return self
        
    def load_filters(self):
        '''load filters by default and mapping to Objet'''
        self.filters = {k: self.PROJECT["filters"][k]["active"] for k in self.PROJECT["filters"].keys()}
        #~ for n in filter(lambda x: (self.filters[x] is True), self.filters):
            #~ self.filters[n] = self.PROJECT["filters"][n][n]
        for k, v in self.filters.items():
            if v is not False:
                setattr(self, k, self.PROJECT["filters"][k][k])
                self.filters[k] = self.PROJECT["filters"][k][k]
            else:
                setattr(self, k, False)
        return self
        
    def add_seeds(self):
        print "addings seeds"
        #~ print self.PROJECT.keys()
        filters = {k: self.PROJECT["seeds"][k]["active"] for k in self.PROJECT["seeds"].keys()}
        seeds_options = [k for k,v in filters.items() if v is True]
        for n in seeds_options:
            print "from", n
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
        url = Url(url)
        try:
            self.db.seeds.insert_one({
                                "date": [self.date],
                                "url": url.url,
                                "url_id" : url.url_id,
                                "url_info": url.export(),
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
        #~ session = FuturesSession()
        #~ def get_req(future):
            #~ response = future.result()
            #~ results = response.json()['d']['results']
            #~ 
            #~ for res in results:
                #~ position = int(res['__metadata']['uri'].split("&$")[1].split("=")[1])+1
                #~ url, description, title = res["Url"], res["Description"], res["Title"]
                #~ url = Url(url)
                #~ try:
                    #~ self.db.seeds.insert({
                                        #~ "date": [self.date],
                                        #~ "url": url.url,
                                        #~ "url_id" : url.url_id,
                                        #~ "title": title,
                                        #~ "description": description,
                                        #~ "rank": position,
                                        #~ "source_url": None,
                                        #~ "depth": 0,
                                        #~ "method": "search",
                                        #~ "query": params["query"],
                                            #~ })
                                    #~ 
                #~ except pymongo.errors.DuplicateKeyError:
                    #~ #print "Alredy in DB"
                    #~ self.db.seeds.update({"url": url.url}, {'$push': {"date": self.date}})
            #~ 
            #~ 
        for i in range(0,params["nb"], 50):
            
            r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
                params={'$format' : 'json',
                    '$skip' : i,
                    '$top': 50,
                    'Query' : '\'%s\'' %params["query"],
                    },auth=(params["key"], params["key"]),
                    verify=False)
            #~ s = requests.Session('https://api.datamarket.azure.com/Bing/Search/v1/Web')
            #~ future = requests.get(
                        #~ 'https://api.datamarket.azure.com/Bing/Search/v1/Web',
                        #~ params={    '$format' : 'json',
                                    #~ '$skip' : i,
                                    #~ '$top': 50,
                                    #~ 'Query' : '\'%s\'' %params["query"],},
                        #~ auth=(params["key"], params["key"]),
                        #~ headers = { 'User-agent': 'Mozilla/5.0',
                                    #~ 'Connection': 'close'}
                    #~ )
            results = r.json()['d']['results']
            for res in results:
                position = int(res['__metadata']['uri'].split("&$")[1].split("=")[1])+1
                url, description, title = res["Url"], res["Description"], res["Title"]
                url = Url(url)
                try:
                    self.db.seeds.insert({
                                        "date": [self.date],
                                        "url": url.url,
                                        "url_id" : url.url_id,
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
                    #self.db.seeds.update({"url": url.url}, {'$push': {"date": self.date}})
                    pass
        return self
    
    def check_depth(self, depth):
        if self.depth is not False:
            return (depth<=self.depth)
        else:
            return True
    
    def check_lang(self, text):
        '''check if filter lang is activated and match'''
        try:
            self.page_lang = langdetect(text)
        except Exception as e:
            logger.warning("Check_lang Error", e)
            return True
        if self.lang is not False:
            return bool(self.lang == self.page_lang)
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

    def extract_outlinks(self, html, url, depth):
        '''extract links on page'''
        outlinks = []
        for u in get_outlinks(html, url):
            doc = {"url":u.url, "url_id": u.url_id, "url_info": u.export(), "depth": depth+1}
            outlinks.append(doc)
        return outlinks
    
    def extract_title(self, html):
        try:
            return bs(html, "lxml").title.text
        except AttributeError: 
            return bs(html, "lxml").head.title.text
            
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
                    meta[re.sub("og:|DC.|.|:", "", name)] = content
                #~ 
            if prop is not None:
                meta[re.sub("og:|DC.|.|:", "", prop)] = content
        
        return meta
    
    def store_file(self, url_id, data, fmt="txt"):
        if fmt is None:
            fname = url_id.replace(".", "_")+"_VERSION_"+self.date.strftime("%d_%m_%Y")
        else:    
            fname = url_id.replace(".", "_")+"_VERSION_"+self.date.strftime("%d_%m_%Y")+"."+fmt
        
        fname = os.path.join(self.directory, fname)
        try:
            with open(fname, "w") as f:
                data = (data).encode("utf-8")
                f.write(data)
            return self
    def show(self, article):
        return {"$set":{k: v for k, v in article.items() if k not in ["date", "url", "outlinks"]}}
    def extract(self, response, depth=0, filters=True):
        article = {}
        html = response.text
        url = response.url
        url = Url(url)
        article["url"] = url.url
        article["url_info"] = url.export()
        article["url_id"] = url.url_id
        article["depth"] = depth
        article["type"] = response.headers['content-type']
        article["date"] = self.date
        article["encoding"] = response.encoding.lower()
        
        article["status"] = True
        if url.status:
            article_txt = lxml_extractor(html, url)
            article["title"] = self.extract_title(html)
            article["meta"] = self.extract_meta(html)
            article["keywords"] = self.extract_keywords(article["meta"])
            if filters:
                if self.check_lang(article_txt):
                    if self.check_query(article_txt):
                        article["html_file"] = self.store_file(article["url_id"], html, fmt="html")
                        article["txt_file"] = self.store_file(article["url_id"], article_txt, fmt="txt")
                        outlinks = self.extract_outlinks(html, url, depth)
                        article["citeds_url"] = [n["url"] for n in outlinks]
                        article["cited_url_ids"] = [n["url_id"] for n in outlinks]
                        article["outlinks"] =  outlinks
                        article["lang"] = self.page_lang
                        return article
                        
                    else:
                        if self.check_query(article["title"]):                            
                            article["html_file"] = self.store_file(article["url_id"], html, fmt="html")
                            article["txt_file"] = self.store_file(article["url_id"], article_txt, fmt="txt")
                            outlinks = self.extract_outlinks(html, url, depth)
                            article["cited_urls"] = [n["url"] for n in outlinks]
                            article["cited_url_ids"] = [n["url_id"] for n in outlinks]
                            article["outlinks"] =  outlinks
                            article["lang"] = self.page_lang
                            article = self.extract_page(article, article_txt, html)
                            article["lang"] = self.page_lang
                            return article
                        else:
                            article["status"] = False
                            article["status_code"] = 900
                            article["msg"] = "Search expression not found"
                            return article
                else:
                    if self.check_lang(article["title"]):                        
                        article["html_file"] = self.store_file(article["url_id"], html, fmt="html")
                        article["txt_file"] = self.store_file(article["url_id"], article_txt, fmt="txt")
                        outlinks = self.extract_outlinks(html, url, depth)
                        article["cited_urls"] = [n["url"] for n in outlinks]
                        article["cited_url_ids"] = [n["url_id"] for n in outlinks]
                        article["outlinks"] =  outlinks
                        article["lang"] = self.page_lang
                        return article
                    else:
                        article["status"] = False
                        article["status_code"] = 1000
                        article["msg"] = "Lang is invalid"
                        article["lang"] = self.page_lang
                        return article
            else:
                self.check_lang(article_txt)
                article["html_file"] = self.store_file(article["url_id"], html, fmt="html")
                article["txt_file"] = self.store_file(article["url_id"], article_txt, fmt="txt")
                outlinks = self.extract_outlinks(html, url, depth)
                article["cited_urls"] = [n["url"] for n in outlinks]
                article["cited_url_ids"] = [n["url_id"] for n in outlinks]
                article["outlinks"] =  outlinks
                article["lang"] = self.page_lang
                return article
        else:
            article["status"] = False
            article["error"] = "Invalid url"
            article["status_code"] = 800
            return article
        
    def get_seeds(self):
        '''download and store seeds'''
        session = FuturesSession()
        def get_req(future):
            response = future.result()
            if response.status_code not in range(400,520):
                if "text/html" in response.headers['content-type']:
                    article = self.extract(response, depth=0, filters=False)
                    if article["status"]:
                        outlinks = article["outlinks"]
                        del article["outlinks"]
                        
                        try:
                            #~ print article
                            self.db.data.insert_one(article)
                            
                            try:
                                ex = [n["_id"] for n in self.db.seeds.find({"url":article["url"]},{"_id":1})]
                                
                                self.db.seeds.find_one_and_update({"url":article["url"]}, self.show(article))
                            except Exception as e:
                                pass
                                
                                #self.db.seeds.update(article)
                            for n in outlinks:
                                #bulk = [InsertOne(x for x in outlinks if x["url"] not in self.db.data.distinct("url") and x["url"] not in self.db.queue.distinct("url"))]
                                if self.db.queue.count({"url":n["url"]}) > 0:
                                    pass
                                if self.db.data.count({"url":n["url"]}) > 0:
                                    pass
                                else:
                                    try:
                                        self.db.queue.insert_one(n)
                                    except pymongo.errors.DuplicateKeyError:
                                        #print "Already in queue"
                                        pass
                            return True
                            
                        except pymongo.errors.DuplicateKeyError:
                            #~ print "Article is already in DB outlinks not put in Queue"
                            try:
                                self.db.seeds.find_one_and_update({"url":article["url"]}, self.show(article))
                            except Exception as e:
                                pass
                            return True
                            #~ self.db.data.update({"url":article_url}, {"$set":json.dumps(article)})
                        
                        
                    else:
                        try:
                            self.db.seeds.find_one_and_update({"url":article["url"]}, self.show(article))
                        except Exception as e:
                            pass
                        return False
                else:
                    status_code = 406
                    msg = "Format de la page non supporté: %s" %response.headers['content-type']
                    self.db.seeds.find_one_and_update({"url":response.url}, {"$set":{"status": False, "status_code": status_code, "msg": msg}})
                    return False
            else:
                status_code = response.status_code
                msg = "Page indisponible"
                self.db.seeds.find_one_and_update({"url":response.url}, {"$set":{"status": False, "status_code": status_code, "msg": msg}})
                return False
                
        
        for x in self.db.seeds.find({},{"url":1, "depth":1, "_id":0,"status":1}):
            url = Url(x["url"])
            #headers = {"User-agent": "Mozilla/5.0","Connection": "close"}
            future = session.get(url.url, verify=False)
            depth = 0
            try:
                future.add_done_callback(get_req)
                
            except Exception as e:
                logger.critical(e)
        
        
        return bool(self.db.queue.count() > 0)
    
    def crawl(self):
        '''main crawl'''
        self.load_filters()
        def get_page(future):
            response = future.result()
            if response.status_code not in range(400,520):
                if "text/html" in response.headers['content-type']:
                    article = self.extract(response, depth=0, filters=False)
                    if article["status"]:
                        outlinks = article["outlinks"]
                        del article["outlinks"]
                        try:
                            #~ print article
                            self.db.data.insert_one(article)
                            #self.db.seeds.update({"url":article["url"]}, {"$set":article})
                            for n in outlinks:
                                #bulk = [InsertOne(x for x in outlinks if x["url"] not in self.db.data.distinct("url") and x["url"] not in self.db.queue.distinct("url"))]
                                if self.db.queue.count({"url":n["url"]}) > 0:
                                    pass
                                if self.db.data.count({"url":n["url"]}) > 0:
                                    pass
                                else:
                                    try:
                                        self.db.queue.insert_one(n)
                                    except pymongo.errors.DuplicateKeyError:
                                        pass
                            self.db.queue.delete_many({"url":article["url"]})
                            return True
                            
                        except pymongo.errors.DuplicateKeyError:
                            print "Article is already in DB outlinks not put in Queue"
                            for n in outlinks:
                                #bulk = [InsertOne(x for x in outlinks if x["url"] not in self.db.data.distinct("url") and x["url"] not in self.db.queue.distinct("url"))]
                                try:
                                    self.db.queue.insert_one(n)
                                except pymongo.errors.DuplicateKeyError:

                                    if self.db.data.count({"url":n["url"]}) > 0:
                                        self.db.queue.delete_many({"url":n["url"]})
                            self.db.queue.delete_many({"url":article["url"]})
                            return True
                    else:
                        self.db.logs.update({"url":article["url"]}, {"$set":article})
                        self.db.queue.delete_many({"url":article["url"]})
                        return False
                else:
                    status_code = 406
                    msg = "Format de la page non supporté: %s" %response.headers['content-type']
                    self.db.logs.update({"url":response.url}, {"$set":{"status": False, "status_code": status_code, "msg": msg}})
                    self.db.queue.delete_many({"url":response.url})
                    return False
            else:
                status_code = response.status_code
                msg = "Page indisponible"
                self.db.logs.update({"url":response.url}, {"$set":{"status": False, "status_code": status_code, "msg": msg}})
                self.db.queue.delete_many({"url":response.url})
                return False
                
        if self.status is False:
            #means nothing in queue
            #~ self.add_seeds()
            #~ self.get_seeds()
            #reload
            pass
        #~ else:
        session = FuturesSession(executor=ProcessPoolExecutor(max_workers=5))
        
        print "Waiting url", self.db.queue.count()
        while self.db.queue.count() > 0:
            
            for x in self.db.queue.find().sort('depth', pymongo.DESCENDING):
                url = Url(x["url"])
                
                depth = x['depth']
                if self.depth is not False:
                    if depth >= self.depth:
                        self.db.queue.delete_one({"url": url.url})
                        #results = self.db.queue.drop({"depth":{"$gt":self.depth})
                        pass
                    else:
                        #headers = {"User-agent": "Mozilla/5.0","Connection": "close"}
                        future = session.get(url.url, verify=False)
                        try:
                            future.add_done_callback(get_page)
                        except Exception as e:
                            #print logger.critical(e)
                            pass
                            
                if self.db.queue.count() == 0:
                    break
                if self.depth is not False:
                    results = self.db.queue.delete_many({"depth":{"$gt":self.depth}})
                    if results.deleted_count > 0:
                        break
            print "Url in queue", self.db.queue.count()
        self.status = True
        #self.COLL.find_and_update({"name": self.NAME, "user":
        sys.exit()
        
if __name__=="__main__":
    
    c = Crawler()
    c.start()
