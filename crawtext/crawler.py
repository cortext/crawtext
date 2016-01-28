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
from config import *
from requests_futures.sessions import FuturesSession
from parser import *
import pymongo
class Crawler(object):
    def __init__(self, global_settings, project_settings):
        self.PROJECT = project_settings
        del self.PROJECT["_id"]
        self.name = self.PROJECT["name"]
        self.status = self.PROJECT["status"]
        self.date = self.PROJECT["date"][-1]
        
        self.SETTINGS = global_settings
        self.db = self.SETTINGS["db"]
        
        self.setup_db()
        
            #~ setattr(self, k, v)
        if self.status:
            #~ self.setup_db()
            self.add_seeds()
        else:
            #launch()
            pass
            
            
    def exists(self):
        if self.db["provider"] == "mongo":
            uri = 'mongodb://%s,%s:%s'%(self.db["host"], self.db["host"], self.db["port"])
            self.client =  MongoClient(uri)
            db_name  = self.client[self.name]
            return bool(self.name in self.client.database_names())
        else:
            raise NotImplementedError
       

    def setup_db(self):
        if not self.exists():
            if self.db["provider"] == "mongo":
                uri = 'mongodb://%s,%s:%s'%(self.db["host"], self.db["host"], self.db["port"])
                self.client =  MongoClient(uri)
                self.db = self.client[self.name]
                self.infos = self.db["infos"].insert(self.PROJECT)
                
                self.db["seeds"].create_index([("url", pymongo.HASHED)],unique=True, background=True, safe=True)
                
                
                
                self.db["data"].create_index("url",unique=True, background=True)
                
                
                
            elif self.db["provider"] in ["sql","sqlite"]:
                #~ import sqlite3
                #~ self.client = sqlite3.connect(self.db["db_name"])
                #~ DB = self.client.cursor()
                #~ DB.execute("""CREATE TABLE IF NOT EXISTS %s()""") %self.db["collection"]
                #~ DB.commit()
                raise NotImplementedError
            else:
                #~ import psycopg2
                #~ try:
                    #~ conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s" %(self.db["name"],self.db["user"], self.db["host"], self.db["password"]) )
                #~ except:
                    #~ print "I am unable to connect to the database"
                raise NotImplementedError
        self.seeds = self.db["seeds"]
        self.data = self.db["data"]
        self.queue = {}
        return self
                
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
                    self.add_url(url)
        print self.seeds.count()
        for n in self.seeds.find():
            print n["url"]
    def add_file(self, filename):
        #print self.SETTINGS["dir"], filename
        if filename.startswith("./"):
            filename = os.path.realpath(filename)
            print filename
        else:
            
            parent_dir = os.path.abspath(os.path.join(self.SETTINGS["dir"], os.pardir))
            #print filename
        try:
            with open(filename, "r") as f:
                seeds =  [n.replace("\n","") for n in f.readlines() if n != "\n"]
                urls_ids = [{   "date":self.date, 
                                "url": url, 
                                "url_id":get_url_id(url), 
                                "title":None, 
                                "rank":i,
                                "source_url": None, 
                                "depth":0,
                                "method": "file"
                                } for i, url in enumerate(seeds)]
                try:
                    print("Inserting %i new seeds from file") %len(seeds)
                    self.seeds.insert_many(seeds)
                except pymongo.errors.DuplicateKeyError:
                    pass
        except IOError:
            sys.exit("File not found")
    def add_url(self, url):
        print args
        try:
            self.seeds.insert({
                                "date": [self.date],
                                "url": url,
                                "url_id" : get_url_id(url),
                                "title": None,
                                "description": None,
                                "rank": 1,
                                "source_url": None,
                                "depth": 0,
                                "method": "manual"
                                }, safe = True)
                                    
        except pymongo.errors.DuplicateKeyError:
            print "Duplicate"
            pass
                    
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
                                        "date": [date],
                                        "url": url,
                                        "url_id" : get_url_id(url),
                                        "title": title,
                                        "description": description,
                                        "rank": position,
                                        "source_url": None,
                                        "depth": 0,
                                        "method": "search",
                                        "query": params["query"],
                                            }, safe = True)
                                    
                except pymongo.errors.DuplicateKeyError:
                    print "Alredy in DB"
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
                
if __name__=="__main__":
    
    t = Project()
    if t.status:
        c = Crawler(t.settings, t.PROJECT)
        
    #print t.START_DATE

