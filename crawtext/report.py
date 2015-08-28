#!/usr/bin/env python
# -*- coding: utf-8 -*-


__script_name__ = "stats"
__version__ = "4.4.4"
__author__= "4barbes@gmail.com"
__doc__ = '''Crawtext.'''

#defaut import
import os, sys, re
import inspect
import collections
from collections import defaultdict
from datetime import datetime as dt
import datetime
import hashlib
import subprocess

#requirements
import pymongo #3.0.3
from premailer import transform
from database import *
from jinja2 import Template
from jinja2 import Environment, PackageLoader

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")


class Stats(object):
    def __init__(self, name, params = None):
        self.name = name
        self.data_info = None
        self.c = Database(name)
        self.data = self.c.set_coll("data")
        self.queue = self.c.set_coll("queue")
        
        self.date = datetime.now()
        self.project = name
        if params is not None and type(params) is dict:
            self.params = params
        self.get_task()
        
    def get_task(self):
        ''' here the parameters of the project'''
        #loading the parameters
        db = TaskDB()
        task = db.coll.find_one({"name":self.project})
        params_values = []
        if task is None:
            return sys.exit("No Project found")
        for k, v in task.items():
            if type(v) == list:
                try:
                    if type(v[-1]) == datetime:
                        setattr(self, "last_date", v[-1].strftime("%d %B %Y %H:%M"))
                    else:
                        setattr(self, "last_"+k, v[-1])
                    params_values.append("last_"+k)
                except IndexError:
                    pass
            elif k == "data":
                continue
            else:
                setattr(self, k, v)
                params_values.append(k)
        try:
            setattr(self, "created_at", task["date"][0].strftime("%d %B %Y %H:%M"))
            setattr(self, "now",self.date.strftime("%d %B %Y %H:%M"))
            params_values.extend(["created_at", "now"])
            return params_values
        except IndexError:
            return params_values
        except KeyError:
            return params_values
            
    def get_sources(self):
        #here bizarrerie
        return {"results":self.data.count({"depth":0, "last_status": True}), "logs":self.data.count({"depth":0, "last_status": False}) ,"total": self.data.count({"depth":0})}
    
    def get_total(self):
        self.results = self.data.find({"last_status":True})
        self.logs = self.data.find({"last_status":False})
        return {"treated": self.data.count(), "results": self.results.count(), "logs": self.logs.count(), "queue": self.queue.count()}
            
    def get_completed_level(self):
        if self.max_depth is False:
            self.max_depth = 10
        for n in range(0,int(self.max_depth)):
            to_treat = self.queue.count({"depth":n})
            
            inserted = self.data.count({"depth":n})
            if (to_treat,inserted) != (0,0):
                self.cur = n
                self.completed_level = n-1
                
                return self.completed_level
        return n
        
    def get_depth(self, n):
        queue = self.queue.count({"depth":n})
        treated = self.data.count({"depth":n})
        logs = self.data.count({"depth":n, "last_status": False})
        results = self.data.count({"depth":n, "last_status": True})
        cumul_logs = self.data.count({"depth":{"$lte":n}, "last_status": False})
        cumul_results = self.data.count({"depth":{"$lte":n}, "last_status": True})
        return {"queue":queue, "treated": treated, "results":results, "logs":logs, "cumul_logs":cumul_logs,"cumul_results":cumul_results, "depth":n}
        
    def get_process(self):
        process = []
        if self.max_depth is False:
            self.max_depth = 10
        current = self.get_completed_level()        
        if current <= 0:
            process.append({0: self.get_depth(0)})
            return process
        else:
            for i in range(0, current):
                process.append({i: self.get_depth(i)})
        return process
    
    def get_short_stats(self):
        ''' here the stats of the crawl '''
        stats = {}
        for k in  self.get_params():
            if self.__dict__[k] is not False:
                stats["params"] = {k:v}
        stats["sources"] = self.get_sources()
        stats["total"] = self.get_total()
        return stats
        
    def get_full_stats(self):
        ''' here the stats of the crawl '''
        stats = {}
        stats["process"] = self.get_process()
        stats["total"] = self.get_total()
        return  stats
        
    
    def text(self):
        '''Showing stats of current project in shell'''
        
        text = []
        sources = self.get_sources()
        total = self.get_total()
        
        text.append("Stats for %s" %self.project)
        text.append("**************************")
        text.append("**SOURCES**")
        
        for k, v in sources.items():
            text.append("\t- %s: %s" %(k,v))
        text.append("**TOTAL**")
        for k, v in total.items():
            text.append("\t- %s: %s" %(k,v))
        text.append("**************************")
        return "\n".join(text)
        
    def show(self):
        '''Showing stats of current project in shell'''
        print self.text()
        return
    
    def report(self, type=["crawl","action"], format="mail",):
        '''Create canvas for report'''
        if self.data is None:
            self.build()
            
        if format in ["shell", "print", "debug", "terminal"]:
            return self.show()
        elif format in ["mail", "email", "html"]:
            if format in ["mail", "email"]:
                for t in type:
                    if t == "crawl":
                        if self.user is False:
                            send_mail(__author__, "crawl", self.data)
                        else:
                            send_mail([self.user,__author__], "crawl", self.data)
                    else:
                        if self.user is False:
                            
                            send_mail(__author__, "action", self.data.update({"params":self.params_report()}))
                        else:
                            send_mail([self.user,__author__], "action", self.data.update({"params":self.params_report()}))
                            
            elif format in ["html"]:
                raise NotImplementedError
        else:
            raise NotImplementedError
    
    def report_start(self, format = "mail"):
        db = TaskDB()
        task = db.coll.find_one({"name":self.project})
        
        if task is None:
            return self.report()
        
        try:
            count = self.count.items()
        except AttributeError:
            count = self.build()
        
        env = Environment(loader=PackageLoader('crawtext', './'))
        template = env.get_template('./start_report.html')
        html = template.render(date = self.date, project_name=self.name, count=count, params=task, project_url= "http://playlab.paris/projects/users/report")
        html = transform(html)
        text = self.text()
        if format in ["mail", "email"]:
            if self.user is False:
                self.user = __author__
            self.send_mail(self.user, html, text)
            return True
        else:
            raise NotImplementedError
    
    def report(self, type=["crawl", "action"]):
        for n in type:
            if n == "crawl":
                if self.user is None:
                    send_mail(__author__, n, self.get_full_stats())
                else:
                    send_mail(self.user, n, self.get_full_stats())
            else:
                if self.user is None:
                    send_mail(__author__, n, self.get_short_stats())
                else:
                    send_mail(self.user, n, self.get_short_stats())
                        
    
        
    

    def export(self, format ="json", directory="", depth_limit = None):
        
        if self.format is False:
            self.format = format
        
        if self.format not in ["json", "csv", "sql", "mongodb", "mongo"]:
            sys.exit("Wrong export format")
        
        
        
        if depth_limit is not None:
            completed_depth = depth_limit
            
        else:
            completed_depth = self.get_completed_level()
            print completed_depth
        if directory is None:
            directory = os.path.join(RESULT_PATH, self.project)
                
        query_str = '{last_status:true,depth:{$lte:%i}}, {\"_id\": 0, \"last_cited_links_ids\":1, \"last_title\":1, \"last_text\":1, \"last_status\":1, \"last_date\":1, \"depth\":1, \"url\":1, \"url_id\":1}' %completed_depth
        query, projection = {"last_status":True,"depth":{"$lte":completed_depth}},{"_id": 0, "last_cited_links_ids":1, "last_title":1, "last_text":1, "last_status":1, "last_date":1, "depth":1, "url":1, "url_id":1}
        
        
        outfile = os.path.join(directory, "results_export"+self.date+"."+str(format))
        
        if self.format == "json":
            query = "\'"+query+"\'"
            cmds = ["mongoexport", "--db",self.project,"--collection","data","--query",query_str, "--out",outfile]
            print " ".join(cmds)
            subprocess.call(" ".join(cmds), shell=True)
            count = ["cat", outfile, "|", "wc", "-l"]
            results_nb = subprocess.call(count, shell=False)
            logging.info("Exported %s records into %s" %(results_nb, outfile))
            return 
        elif self.format == "csv":
            raise NotImplementedError
        elif format == "sql":
            raise NotImplementedError
        elif str(self.format).startswith("mongo"):
            try:
                self.results = self.c.set_coll("results", "url")
            except pymongo.errors.DuplicateKeyError:
                self.c.drop_coll("results")
                self.results = self.c.set_coll("results", "url")
            res = self.data.find({"last_status":True,"depth":{"$lte":completed_depth}}, {"_id": 0, "last_cited_links_ids":1, "last_title":1, "last_text":1, "last_status":1, "last_date":1, "depth":1, "url":1, "url_id":1})
            for n in res:
                try:
                    self.results.insert_one(n)
                except pymongo.errors.DuplicateKeyError:
                    pass
                
            
            try: 
                self.logs = self.c.set_coll("logs", "urls")
            except pymongo.errors.DuplicateKeyError:
                self.c.drop_coll("logs")
                self.logs = self.c.set_coll("logs", "url")
            log = self.data.find({"last_status":False,"depth":{"$lte":completed_depth}}, {"_id": 0, "last_msg":1, "last_date":1, "depth":1, "url":1, "url_id":1})
            for n in log:
                try:
                    self.logs.insert_one(n)
                except pymongo.errors.DuplicateKeyError:
                    pass
            logging.info("Exported %i records into %s and %i into %s collections of %s db for %i steps" %(self.logs.count(),"logs", self.results.count(),"results",  self.project, completed_depth))
            return True
        else:
            sys.exit("Unknown export format")

if __name__=="__main__":
    #test
    new_project = "RRI"
    s1 = Stats(new_project)
    print s1.get_full_stats()
    #~ if queue == 0 and treated != 0:
                #~ self.data_info["last"] = self.data_info["depth_"+str(n)]
                #~ 
            #~ elif queue != 0 and treated !=0:
                #~ self.data_info["current"] = self.data_info["depth_"+str(n)]
                #~ break
            #~ else:
                #~ self.data_info["current"] = {"queue":queue, "treated": total_results, "logs":total_logs,"depth":n}
                #~ self.data_info["last"] = {"queue":queue, "treated": total_results, "logs":total_logs,"depth":n}
                #~ continue
            #~ 
    
    #s1.export(format="mongodb")
    pass
