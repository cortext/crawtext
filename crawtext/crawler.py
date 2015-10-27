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



#defaut import
import os, sys, re
import inspect
from collections import defaultdict
from datetime import datetime as dt
import datetime

#Internal module import
from config import config
from database import Database
from database import DuplicateKeyError, WriteError, OperationFailure, ASCENDING
#from database import TaskDb

from article import Page
#from logger import logger
import q

import requests

class Crawtext(object):
    '''main crawler default config on config.json'''    
    def __init__(self, task_cfg = None):
        print task_cfg
        self.status = True
        dt1 = dt.today()
        self.date = dt1.replace(second=0, microsecond=0)
        if task_cfg is None :
            cfg = config()
            #set name
            self.name = cfg["project"]["name"]
            #set_scheduler
            self.task_db = Database(cfg["default"]["db_name"])
            
        else:
            self.name = task_cfg["name"]
            self.task_db = Database(task_cfg["db_name"])
        
        self.coll = self.task_db.use_coll("job")
        print [n for n in self.coll.find()]
        #set_task
        self.task = self.coll.find_one({"name": self.name})
        #set_project
        if bool(self.task is None):
            #creating parameters of the project
            if task_cfg is not None:
                
                sys.exit("No project found")
            else:
                self.create_dir(cfg["default"]["dir_name"])
                self.create(cfg["project"])
        else:    
            #updating parameters of the project
            if task_cfg is not None:
                self.update(self.task)
            else:
                self.update(cfg["project"])
        #load_db
        self.load()
        if self.queue.count() == 0:
            if self.check_interval(self.task["next"]):
                self.add_seeds()
            elif self.data.count({"depth":0}) == 0:
                self.add_seeds()
            self.reload_queue()
        self.run()
        

    @q
    def load(self):
        '''Load the data store of the projects from the project name'''
        self.task = self.coll.find_one({"name": self.name})
        
        self.project = Database(self.name)
        self.data = self.project.set_coll("data")
        self.queue = self.project.set_coll("queue")
        self.logs = self.project.set_coll("logs")
        print("%i urls in data" %(self.data.count()))
        print("%i queue" %(self.queue.count()))
        print("%i logs " %(self.logs.count()))
        return self

    @q    
    def add_seeds(self):
        '''adding seeds 
        initial seeds are not checked with filtering by query
        but put automatically in data store 
        executed only:
        if new project
        if last_run is more than one day 
        if queue is empty
        '''
        methods = [k for k, v in self.task.iteritems() if k in ["file", "url", "key"] and v is not False]
        if self.query is False or self.query is None or self.query == "":
            methods = [k for k in methods if k != "key"]
        if self.queue.count() == 0:
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
            self.archives_dir = os.path.join(self.project_path, 'archives')
            if not os.path.exists(self.archives_dir):
                os.makedirs(self.archives_dir)
        return self
    
        
    
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
            
        else:
            self.status = False
        return self.status
        

    @q
    def update(self, cfg_project):
        '''updated project params config return (Bool)
        False if less one day
        True if something has changed in config
        return False if no need to relaunch seeds update < 1 day
        
        '''
        #check existing task removing status_info
        #self.task = self.coll.find_one({"name":self.name})
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
            
        else:
            #no change
            self.load()
            if self.next is not False:
                if self.check_interval(self.next) is False:
                    self.add_seeds()
            else:
                if self.check_interval() is False:
                    self.add_seeds()
        self.task = self.coll.find_one({"name":self.name})
        return self.status
    
    def insert_file(self):
        path = os.path.join(self.current_dir, self.file)        
        with open(path, 'r') as f:
            for i,url in enumerate(f.readlines()):
                print("Adding source from", url_file, url)
                self.link = {"url": url, "source_url": "file:"+url_file, "depth": 0}
                self.insert_url()
            print ("%i urls added" %i)
        return True
    
    def insert_url(self):
        "insert url directly into data and next_url to seeds"
        #in case a simple url is given
        
        if type(self.url) == str:
            self.link = {"url": self.url, "source_url": "url", "depth": 0}
        page = Page(self.link, self.task)
        return
                
    def check_interval(self, interval ="day"):
        '''interval default 1 day or 1 week or 1 month'''
        try:
            task_d = self.task['history'][-1]
            today = self.date.isocalendar()
            if interval == "day":
                last_run = task_d.isocalendar()
            elif interval == "week":
                last_run = task_d.isocalendar()+datetime.timedelta(days=7)
                
            elif interval == "month":
                last_run = task_d.isocalendar()+ datetime.timedelta(days=21)
            return bool(task_d == today)
        except TypeError:
            return False
        
        
    def reload_queue(self):
        for n in self.data.find({"depth":0},{"url":1, "source_url": 1, "depth":1}):
            self.link = n
            p = Page(self.link, self.task)
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
        if self.search_nb < 50:
            print("Minimum of search results should be 50 urls")
        web_results = []
        for i in range(0,self.search_nb, 50):
            r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
                params={'$format' : 'json',
                    '$skip' : i,
                    '$top': 50,
                    'Query' : '\'%s\'' %self.query,
                    },auth=(self.key, self.key)
                    )
    
            for i, e in enumerate(r.json()['d']['results']):
                
                self.link = {"url": e['Url'], "source_url": "search", "depth": 0}
                self.insert_url()
                if i == self.search_nb-1:
                    break
        if i == 0:
            return False
        else:
            return True
        
            

    
    def run(self):
        '''the main crawler logic'''
        
        self.task = self.coll.find_one({"name": self.name})
        while self.queue.count() > 0:
            print("%i urls in process" %self.queue.count())
            print("%i sources in process" %self.queue.count({"depth":0}))
            print("%i sources stored" %self.data.count({"depth":0}))
            #self.report()
            for item in self.queue.find(no_cursor_timeout=True).sort([('depth', ASCENDING)]):
                print("%i urls in process" %self.queue.count())
                #if item["url"] not in self.logs.distinct("url"):
                page = Page(item, self.task)
                self.queue.delete_one({"url": item["url"]})
                print("%i urls in process" %self.queue.count())
                print("%i results" %self.data.count())
                print("%i logs" %self.logs.count())
               
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

    
