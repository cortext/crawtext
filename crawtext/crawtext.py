#!/usr/bin/env python
# -*- coding: utf-8 -*-
__script__ = "crawtext"
__name__ = "crawtext"
__version__ = "5.0.2"
__author_username__= "c24b"
__author_email__= "4barbes@gmail.com"
__author__= "Constance de Quatrebarbes"



#defaut import
import os, sys, re
import inspect
from collections import defaultdict
from datetime import datetime as dt
import datetime

#Internal module import
from config import config
from database import Database
from database import DuplicateKeyError, WriteError, OperationFailure


from article import Page
#from logger import logger
import q
#Pas2stats#from report imore
import requests

class Crawtext(object):
    '''main crawler'''
    
    def __init__(self):
        dt1 = dt.today()
        self.date = dt1.replace(second=0, microsecond=0)
        cfg = config()
        #set name
        self.name = cfg["project"]["name"]
        #set_scheduler
        self.task_db = Database(cfg["default"]["db_name"])
        self.coll = self.task_db.use_coll("job")
        #set_task
        self.task = self.coll.find_one({"name": self.name})
        #set_project
        self.create_dir(cfg["default"]["dir_name"])
        if bool(self.task is not None):
            #updating parameters of the project
            self.update(cfg["project"])
        else:
            #creating parameteres of the project
            self.create(cfg["project"])
        if self.queue.count() == 0:
            self.reload_queue()
        self.run()
            
            
    @q
    def load(self):
        '''Load the data store of the projects from the project name'''
        self.project = Database(self.name)
        self.data = self.project.set_coll("data")
        self.queue = self.project.set_coll("queue")
        self.logs = self.project.set_coll("logs")
        print("%i urls in data" %(self.data.count()))
        print("%i urls to treat" %(self.queue.count()))
        print("%i logs " %(self.logs.count()))
        return self
    
        
            
    @q    
    def add_seeds(self):
        '''adding seeds 
        initial seeds are not checked with filetr_query 
        put automatically in data store
        if last_run is more than one day if queue is empty
        add seeds
        '''
        self.task = self.coll.find_one({"name":self.name})
        methods = [k for k, v in self.task.iteritems() if k in ["file", "url", "key"] and v is not False]
            
        if self.query is False or self.query is None or self.query == "":
            methods = [k for k in methods if k != "key"]
        if self.check_interval() is True and self.queue.count() ==0:
            for k in methods:
                getattr(self, 'insert_%s' % k)()
            return True
        elif self.queue.count() == 0:
            for k in methods:
                getattr(self, 'insert_%s' % k)()
            return True
        elif self.check_interval() is False and self.repeat is True:
            for k in methods:
                getattr(self, 'insert_%s' % k)()
            return True
        elif self.data.count({"depth":0}) == 0:
            for k in methods:
                getattr(self, 'insert_%s' % k)()
            return True
        else:    
            return False
    @q
    def create_dir(self, dirname):
        '''create the default store directory'''
        curr_dir = os.getcwd()
        self.directory = os.path.join(curr_dir, dirname)
        self.project_path = os.path.join(self.directory,re.sub(r'[^\w]',"_", self.name))
        if not os.path.exists(self.directory):
            print("creating directory to store project %s" %self.directory)
            os.makedirs(self.directory)
        if not os.path.exists(self.project_path):
            print("A specific directory has been created to store your projects\n Location:%s" %(self.project_path))
            os.makedirs(self.project_path)
            index = os.path.join(self.project_path, 'index')
            if not os.path.exists(index):
                #print("Creating the index")
                os.makedirs(index)
        return   
    
        
    
    def create(self, cfg_project):
        '''create a project inserting the parameters into the TaskDB scheduler'''
        for k,v in cfg_project.items():
            setattr(self, k, v)
        
        if self.query is not False:
            self.filter = True
            
        project = {k:v for k,v in self.__dict__.iteritems() if k not in ['coll', 'db', 'database','task_db']}
        f_name = sys._getframe().f_code.co_name
        project["status"], project["msg"], project["step"], project["history"] = [True], ["ok"], [f_name], [self.date]        
        self.coll.insert_one(project)
        self.task = self.coll.find_one({"name":self.name})
        if self.task is not None:
            self.load()
            self.add_seeds()
            return True
        return False
        

    @q
    def update(self, cfg_project):
        '''updated project params config return (Bool)
        False if less one day
        True if something has changed in config
        return False if no need to relaunch seeds update < 1 day
        
        '''
        #check existing task removing status_info
        self.task = self.coll.find_one({"name":self.name})
        task = {k:v for k,v in self.task.iteritems() if type(v) != list}
        for k,v in task.items():
            setattr(self,k,v)
        
        
        
        #~ project = {k:v for k,v in self.task.items() if k is not None and k not in ['coll', 'db', 'database','task_db']}
        status = False
        for k,v in cfg_project.iteritems():
            try:
                if v != task[k]:
                    self.coll.update({"_id":task["_id"]},{"$set":{k: v}})
                    status = True
            except KeyError:
                self.coll.update({"_id":task["_id"]},{"$set":{k: v}})
                status = True
        if status:
            f_name = sys._getframe().f_code.co_name
            self.coll.update({"_id": task["_id"]}, 
                        {"$push":
                            {"status":True,
                            "msg":"ok",
                            "step": f_name,
                            "history": self.date}
                        #"$position":0}
                        }
                        )
            self.task = self.coll.find_one({"name":self.name})
        else:
            self.load()
            self.add_seeds()
        return status
    
    def insert_file(self):
        path = os.path.join(self.current_dir, self.file)        
        with open(path, 'r') as f:
            for i,url in enumerate(f.readlines()):
                print("Adding source from", url_file, url)
                self.url = url
                self.insert_url()
            print ("%i urls added" %i)
        
        return True
        
    def insert_url(self):
        "insert url directly into data and next_url to seeds"
        print("Insert url", self.url)
        p = Page({"url": self.url, "source_url": "url", "depth": 0}, self.task)
        p.process(False)
        if p.status:
            try:
                self.data.insert_one(p.set_data())
            except DuplicateKeyError:
                pass
                #~ if self.task["repeat"]:
                    #~ self.data.update_one({"url":url, "depth":0}, {"$inc":{"crawl_nb": 1},'$push':{"history":self.date}, "$set":p.status})
            for link in p.outlinks:
                if link not in self.logs.distinct("url"):
                    try:
                        self.queue.insert_one({"url":link, "source_url":p.url, "depth":1})
                    except DuplicateKeyError:
                        continue
                    except WriteError:
                        self.logs.insert_one({"url":link, "source_url":p.url, "depth":1})
                        
                        pass
        else:
            self.logs.insert_one({"url":p.url})
        return
                
    def check_interval(self):
        task_d = self.task['history'][-1]
        last_run = (task_d.day,task_d.month, task_d.year)
        today = (self.date.day, self.date.month, self.date.year)
        return bool(task_d == today)
        
        
    def reload_queue(self):
        for n in self.data.find({"depth":0},{"url":1, "source_url": 1, "depth":1}):
            p = Page(n, self.task)
            p.process(False)
            if p.status:                
                for link in p.outlinks:
                    try:
                        self.queue.insert_one({"url":link, "source_url":p.url, "depth":1})
                    except DuplicateKeyError:
                        continue
                    except WriteError:
                        self.logs.insert_one({"url":link, "source_url":p.url, "depth":1, })
                        
        return

        
        
    def insert_key(self):
        if self.query is None or self.query is False or self.query == "":
            return False
        if self.key is False or self.key == "":
            return False
        if self.search_nb > 1000:
            print("Maximum of search results is 1000 urls so set to 1000 urls")
            self.search_nb = 1000
        
        web_results = []
        for i in range(0,self.search_nb, 50):
            r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
                params={'$format' : 'json',
                    '$skip' : i,
                    '$top': 50,
                    'Query' : '\'%s\'' %self.query,
                    },auth=(self.key, self.key)
                    )
    
            for i,e in enumerate(r.json()['d']['results']):
                self.url = e['Url']
                self.insert_url()
        if i == 0:
            return False
        else:
            return True
        
            

    
    def run(self):
        '''the main crawler logic'''
        
        while self.queue.count() > 0:
            print("%i urls in process" %self.queue.count())
            print("in which %i sources in process" %self.queue.count({"depth":0}))
            #self.report()
            for item in self.queue.find(no_cursor_timeout=True).sort([('depth', pymongo.ASCENDING)]):
                print("%i urls in process" %self.queue.count())
                if item["url"] not in self.logs.distinct("url"):
                    page = Page(item, self.task)
                    #pertinence
                    status = page.process()
                    if status is True:
                        
                        try:                   
                        
                        #on cree et insere la page
                            self.data.insert_one(page.set_data())
                            if page.status:
                                cpt = 0
                                if page.depth+1 < page.max_depth:
                                    for outlink in page.outlinks:
                                        if outlink["url"] not in self.data.distinct("url"):
                                            try:
                                               cpt = cpt+1
                                               self.queue.insert_one(outlink)
                                            except DuplicateKeyError:
                                                continue
                                        else: continue
                                    print("adding %i new urls in queue  with depth %i" %(cpt, page.depth+1))
                                    #self.data.update_one({"url":item["url"]}, {"$set":{"type": "page"}})
                            else:
                                self.logs.insert_one({"url":item["url"]})
                            
                            #~ self.data.update_one({"url":item["url"]}, {"$set":page.set_data()})
                            self.queue.delete_one({"url": item["url"]})
                            continue
                        
                        except DuplicateKeyError:
                            self.queue.delete_one({"url": item["url"]})
                            continue
                    else:
                        self.logs.insert_one({"url": p.url})
            
        
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
                os.kill(pid, signal.SIGKILL)
        try:
            self.update_status(self.task["name"], {"$set":"stop"})
        except OperationFailure:
            pass
                    
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
                print("-", n["name"])
            except KeyError:
                self.coll.remove(n)
        return sys.exit(0)
    
    def report(self, type=["crawl","action"], format="mail",):
        s = Stats(self.name)
        return s.report(type, format)

c = Crawtext()
