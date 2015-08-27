#!/usr/bin/env python
# -*- coding: utf-8 -*-


__script_name__ = "crawtext"
__version__ = "4.4.4"
__author__= "4barbes@gmail.com"
__doc__ = '''Crawtext.'''

#defaut import
import os, sys, re
import inspect
from collections import defaultdict
#from docopt import docopt
from datetime import datetime as dt
import datetime
import hashlib
#requirements

import pymongo #3.0.3
import requests
#internal import
#from report import send_mail, generate_report
from database import *
from article import Page
from logger import *


ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")
#search result nb from BING
MAX_RESULTS = 1000
#max depth
DEPTH = 100


class Crawtext(object):
    def __init__(self, name):
        #logger.debug("_init_")
        self.name = name
        dt1 = dt.today()
        self.date = dt1.replace(minute=0, second=0, microsecond=0)
        self.task_db = TaskDB()
        self.coll = self.task_db.coll
        
        
                
    def start(self, user_input=None):
        if type(user_input) != dict :
             sys.exit("Wrong format args")
        
        self.task = self.coll.find_one({"name": self.name})
        if self.task is None:
            #Project doesn't exits
            logger.info("No project %s found. Creating the project" %self.name)
            if self.create(user_input) is False:
                sys.exit("Fail to create a new project")
            
        else:
            logger.info("Project %s found. Udpating the project" %self.name)
            if self.update(user_input) is False:
                logger.info("No parameters to update")
                
        if self.add_seeds() is False:
            sys.exit("No seeds found ")
        
        if self.queue.count() > 0:
            self.global_crawl()
            return True
        else:
            sys.exit("All urls has been treated")
        
        
    def load_data(self):
        logger.info("Loading data from project db")
        self.project = Database(self.name)
        self.data = self.project.set_coll("data", "url")
        self.queue = self.project.set_coll("queue", "url")
        print "%i urls in data" %(self.data.count())
        print "%i urls to treat" %(self.queue.count())
        return self
        
    def add_seeds(self):
        self.load_data()
        self.sources_nb = self.data.count({"depth":0})
        self.logs = self.data.find({"type":"log"})
        self.results = self.data.find({"type": "page"})
        
        print "Sources nb", self.sources_nb
        #Si pas de sources
        
        if self.sources_nb == 0:
            logger.info("No sources found ")
            params = [k for k, v in self.task.items() if k in ["file", "url", "key"] and v is not False]
            #ajouter
            self.add_sources(params)
        
        
        if self.queue == 0:
            logger.info("No url awaiting  to be crawled")
            logger.info("Adding %i sources to queue" %self.sources_nb)
            for doc in self.data.find({"depth":0}):
                #print doc["status"][-1]
                if doc["status"][-1] is True:
                    try:
                        self.queue.insert_one(doc)
                    except pymongo.errors.DuplicateKeyError:
                        pass
            
        
        if self.queue.count() == 0:
            logger.warning("No source to crawl")
            return False
        else:
            logger.warning("%i sources url to crawl" %self.queue.count())
            return True
            
    def load_defaut_config(self):
        """
        Load a defaut dict of params 
        configuring params the crawl (set to False):
        - name: project name given (str)
        - query: a query for filtering content (regex or XPR/False)
        - file: a file that contains urls as seeds (file_name)
        - url: an url as seed (url)
        - key: an api key to search seeds on BING (key/False)
        - search_nb: max results of seeds while searching on BING (set to 1000)
        - filter_lang: a lang for filtering only content of this langage
        - user: an email for sending report
        - max_depth: stopping crawl after x steps (set to 100)
        - repeat: repeat the task every day, week, month or year
        - data: specific collection to export
        - format: specific format to export csv/json/mysql/mongo
        - project_path: the dedicated directory for this path
        - next: ["month", "week", "day", "year"]
        - short_export: a short version of results without sources (True/False)
        """
        #logger.debug("Load default project")
        #params
        params = {"name": self.name}
        for k in ["query", "file", "url", "key", "search_nb", "filter_lang", "user", "max_depth", "repeat", "data", "format", "short_export", "next"]:
            params[k] = False
        
        #loading defaut
        params["max_depth"] = 100
        params["search_nb"] = 1000
        
        params["directory"]= self.create_dir()
        for n in ["status", "msg", "action", "date", "error"]:
            params[n] = []
        return params
    
    def create_dir(self):
        self.directory = os.path.join(RESULT_PATH, self.name)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
            index = os.path.join(self.directory, 'index')
            try:
                self.index_dir = os.makedirs('index')
            except:
                pass
            #logger.debug("A specific directory has been created to store your projects\n Location:%s"   %(self.directory))
        return self.directory    
    
        
        
    def create(self, user_input):
        logger.debug("Create project %s" %self.name)
        default_project = self.load_defaut_config()
        #check if some parameters are given by the user
        keys2add = set(default_project.keys()) & set(user_input.keys())
        params = {}
        for k in keys2add:
            if user_input[k] != default_project[k]:
                default_project[k] = user_input[k]
                params[k] = user_input[k]
        
        if len(params.items()) == 0:
            logger.debug("Project %s has no parameters.Please add some parameters to activate the crawl" %self.name)
            return False
        else:
            if default_project["query"] is not False:
                default_project["filter"] = True
        updated_values = " & ".join(params.keys())
        self.coll.insert_one(default_project)
        #logger.debug("Project %s has been created with the specified parameters: %s" %(self.name, updated_values))
        self.coll.update_one({"name": self.name}, {"$push": {"status": True, "code":100, "msg": "created", "date": self.date}})
        self.task = self.coll.find_one({"name": self.name})
        #params = [k for k,v in self.task.items() if v is not False and k in ["file", "url", "key"]]
        self.add_seeds()
        return True
    
    def update(self, user_input):
        '''updated project params config'''
        logger.debug("Update")
        params = {}
        default_project = self.load_defaut_config()
        for k,v in user_input.items():
           if k in default_project.keys():
                if user_input[k] != self.task[k]:
                    self.task[k] = user_input[k]
                    params[k] = user_input[k]
        
        if len(params.items()) == 0:
            logger.debug("No change in project %s" %self.name)
            self.task = self.coll.find_one({"name":self.name})
            return False
        else:
            if default_project["query"] is not False:
                default_project["filter"] = True
            self.coll.update_one({"name":self.name}, {"$set":params, "$push": {"status": True, "code":100, "msg": "updated", "date": self.date}})
            self.task = self.coll.find_one({"name":self.name})
            params = [k for k,v in params.items() if v is not False and k in ["file", "url", "key"]]
            if len(params) != 0:
                self.add_sources(params)
            elif params["repeat"] is not False:
                params = [k for k,v in self.task.items() if v is not False and k in ["file", "url", "key"]]
                self.add_sources(params)
            else:
                pass
            
            return True
        
    
    def insert_url(self,url):
        "insert url directly into data and next_url to seeds"
        info = Page({"url": url, "source_url": "url", "depth": 0}, self.task)
        info.process(False)
        try:
            self.data.insert_one(info.set_data())
        except pymongo.errors.DuplicateKeyError:
            date = self.date.replace(hour=0)
            p_date = (info.date[-1]).replace(hour=0)
            if p_date == date:
                print "Already in processing queue today. No need to update then!"
                #self.queue.delete_one({"url":info.url})
                #return self.queue
                pass
            else:
                self.data.update_one({"url":url, "depth":0}, {"$push":info.add_data()})
        self.data.update_one({"url":url}, {"$inc":{"crawl_nb":1}})
        self.data.update_one({"url":url}, {"$set":{"type":"source"}})
        if info.status:
            for link in info.outlinks:
                
                try:
                    self.queue.insert_one(link)
                except pymongo.errors.DuplicateKeyError:
                    continue
        return self.queue
                
                            
        
    def add_sources(self, to_update):
        
        for k in to_update:
            
            if k == "url":
                print "Adding source from", k, self.task[k]
                #logger.debug("Adding url %s from manual insert" %self.task[k])
                url = self.task[k]
                self.insert_url(url)
                    
            elif k == "file":
                if self.task["directory"] is not False:
                    url_file = os.path.join(self.task["directory"],self.task[k])
                else:
                    url_file = self.task[k]
                    
                #logger.debug("Adding url from file %s" %url_file)
                with open(url_file, 'r') as f:
                    for url in f.readlines():
                        print "Adding source from", url_file, url
                        self.insert_url(url)
            else:
                if self.task["query"] is False:
                    logger.warning("Please add a query to activate search")
                    continue
                else:
                    print "Adding source from search with query", self.task['query']
                    web_results = self.search(self.task["key"], self.task["query"], self.task["search_nb"])
                    logger.debug("\t> inserting %s urls from search on %s " %(len(web_results), self.task["query"]))
                    for nb,url in enumerate(web_results):
                        self.insert_url(url)
        
        return self
        
        
    def search(self, key, query, nb):
        
        #logger.debug("Bing is searching %s urls" %nb)
        if nb > 1000:
            #logger.warning("Maximum of search results is 1000 urls")
            nb = 1000
        
        web_results = []
        for i in range(0,nb, 50):

            #~ try:
            r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
                params={'$format' : 'json',
                    '$skip' : i,
                    '$top': 50,
                    'Query' : '\'%s\'' %query,
                    },auth=(key, key)
                    )

            ##logger.debug(r.status_code)

            #msg = r.raise_for_status()
            #if msg is None:
                
            for e in r.json()['d']['results']:
                #print e["Url"]
                web_results.append(e["Url"])

        if len(web_results) == 0:
            return False
        #resultats capés pour éviter les variations de résultats
        if nb == 1000:
            return web_results[:900]
        else:
            
            return web_results
        
            

    
    def global_crawl(self):
        logger.debug("***************CRAWL********")
        while self.queue.count() > 0:
            print "%i urls in process" %self.queue.count()
            print "in which %i sources in process" %self.queue.count({"depth":0})
            for item in self.queue.find({"depth":{"$gt":0}}).sort([('depth', pymongo.ASCENDING), ('crawl_nb', pymongo.ASCENDING)]):
                
                print "%i urls in process" %self.queue.count()
                
                #~ #Once a day
                #~ if self.task["repeat"] is False:
                    #~ date = self.date.replace(hour=0)
                    #~ p_date = p.date[-1].replace(hour=0)
                    #~ if p_date == date:
                        #~ print "Already treated today"
                        #~ self.queue.delete_one({"url":p.url})
                        #~ continue
                  
                #si c'est une source
                #~ if item["depth"] == 0:
                    #~ print "is source"
                    #~ self.queue.delete_one({"url": item["url"]})
                    #~ continue
                #~ else:
                
                    
                page = Page(item, self.task)
                #pertinence
                status = page.process()                    
                try:
                    
                    #on cree et insere la page
                    self.data.insert_one(page.set_data())
                    self.data.update_one({"url":item["url"]}, {"$set":page.set_last(), "$inc":{"crawl_nb":1}})
                    
                    if page.status:
                        cpt = 0
                        if page.depth+1 < page.max_depth:
                            for outlink in page.outlinks:
                                if outlink["url"] not in self.data.distinct("url"):
                                    try:
                                       cpt = cpt+1
                                       self.queue.insert_one(outlink)
                                    except pymongo.errors.DuplicateKeyError:
                                        continue
                                else: continue
                            print "adding %i new urls in queue  with depth %i" %(cpt, page.depth+1)
                        #self.data.update_one({"url":item["url"]}, {"$set":{"type":"page"}})
                    #else:
                        #self.data.update_one({"url":item["url"]}, {"$set":{"type":"log"}})
                    self.queue.delete_one({"url": item["url"]})
                    continue
                    
                except pymongo.errors.DuplicateKeyError:
                    self.queue.delete_one({"url": item["url"]})
                    continue
                    #check_last_modif
                    #####################"
                    #check_last_crawl
                    ########################
                    #~ date = self.date.replace(hour=0)
                    #~ p_date = page.date[-1]
                    #~ p_date = (p_date).replace(hour=0, day=p_date.day+1)
                    #~ print p_date, date
                    #~ if p_date == date:
                        #~ print "Already treated today"
                        #~ self.queue.delete_one({"url":item['url']})
                        #~ continue
                    #~ else:
                        #check_last_modif
                        #####################"
                        #~ #if self.has_modification():
                            #~ if page.status:
                                #diff btw page.outlinks and last_page.outlinks
                            
                                #~ for outlink in page.outlinks:
                                    #~ try:
                                        #~ self.queue.insert_one(outlink)
                                    #~ except pymongo.errors.DuplicateKeyError:
                                        #~ continue
                            
                            #~ self.data.update_one({"url":item["url"]}, {"$push": page.add_info(),"$set":page.set_last(), "$inc":{"crawl_nb":1}})
                        #~ else:
                           #~ pass
                        #~ self.data.update_one({"url":item["url"]}, {"$push": page.add_data(), "$inc":{"crawl_nb":1}})
                        #~ self.queue.delete_one({"url": item["url"]})
                        #~ continue
                #~ except Exception as e:
                    #~ self.data.update_one({"url":item["url"]}, {"$push": {"msg":str(e), "status":False, "code":909, "date": self.date }})
                    #~ self.queue.delete_one({"url": item["url"]})
                    #~ continue
        logger.debug("***************END********")
        #s = Stats(self.name)
        s.show(self)
        return True
        
                    
    def has_modification(self, url, page):
        #~ ref = self.data.find_one({"url":url})
        #~ if page.status is True and ref["status"][-1] is False:
            #~ print "status has been relevant", ref["msg"][-1]
            #~ return True
        #~ elif page.status is False and ref["status"][-1] is True:
            #~ print "status is not  relevant anymore", ref["msg"][-1]
            #~ return True
        #~ if ref["text"][-1] == page.text:
            #~ return False
        #~ elif set(ref[
        raise NotImplementedError
        
    def stop(self):
        import subprocess, signal
        p = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
        out, err = p.communicate()
        cmd = "crawtext.py %s start" %self.name
        for line in out.splitlines():
            if cmd in line:
                pid = int([n for n in line.split(" ") if n != ""][0])
                #pid = int(line.split(" ")[0])
                #logger.warning("Current crawl project %s killed" %self.name)
                os.kill(pid, signal.SIGKILL)
        try:
            self.update_status(self.task["name"], "stop")
        except pymongo.errors.OperationFailure:
            pass
                    
    def report(self):
        #logger.debug("Report")
        self.load_project()
        #self.load_data()
        self.create_dir()
        if self.user is False:
            self.user = __author__
        #data = self.show_project()
        if send_mail(self.user, self.project) is True:
            #logger.debug("A report email has been sent to %s\nCheck your mailbox!" %self.user)
            try:
                self.update_status(self.task['name'], "report : mail")
            except pymongo.errors.OperationFailure:
                pass
        else:
            #logger.debug("Impossible to send mail to %s\nCheck your email!" %self.user)
            try:
                self.update_status(self.task['name'], "report : mail", False)
            except pymongo.errors.OperationFailure:
                pass
            
        if generate_report(self.task, self.project, self.directory):
            #self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": True, "date": self.date, "msg": "Ok"}})
            try:
                self.update_status(self.task['name'], "report : doc")
            except pymongo.errors.OperationFailure:
                pass
            #logger.debug("Report sent and stored!")
            return sys.exit(0)
        else:
            #self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": False, "date": self.date, "msg": "Unable to create report document"}})
            try:
                self.update_status(self.task['name'], "report : doc", False)
            except pymongo.errors.OperationFailure:
                pass
            return sys.exit("Report failed")
    
    '''def export(self):
        self.load_project()
        self.create_dir()

        #logger.debug("Export")
        from export import generate
        if generate(self.name, self.data, self.format, self.directory):
            try:
                self.update_status(self.task['name'], "export")
            except pymongo.errors.OperationFailure:
                pass
            #logger.debug("Export done!")
            return sys.exit()
        else:
            try:
                self.update_status(self.task['name'], "export", False)
            except pymongo.errors.OperationFailure:
                pass
            return sys.exit("Failed to export")
    '''
    
    def delete(self, with_dir=False):
        self.task = self.coll.find_one({"name": self.name})
        if self.task is None:
            sys.exit("Project %s doesn't exist" %self.name)
        else:       
            self.delete_db()
            if with_dir:
                self.delete_dir()
            self.coll.remove({"_id": self.task['_id']})
            #logger.debug("Project %s: sucessfully deleted"%(self.name))
            sys.exit()
       

    def delete_dir(self):
        import shutil
        directory = os.path.join(RESULT_PATH, self.name)
        if os.path.exists(directory):
            shutil.rmtree(directory)
            #logger.debug("Directory %s: %s sucessfully deleted"    %(self.name,directory))
            return True
        else:
            #logger.debug("No directory found for crawl project %s" %(str(self.name)))
            return False

    def delete_db(self):
        db = Database(self.name)
        db.drop_db()
        #logger.debug("Database %s: sucessfully deleted" %self.name)
        return True
        
    def list_projects(self):
        for n in self.coll.find():
            try:
                print "-", n["name"]
            except KeyError:
                self.coll.remove(n)
        return sys.exit(0)

    def list_projects(self):
        for n in self.coll.find():
            try:
                print "-", n["name"]
            except KeyError:
                self.coll.remove(n)
        return sys.exit(0)



if __name__ == "__main__":
    pass
    
