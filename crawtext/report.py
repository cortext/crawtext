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
from collections import defaultdict, OrderedDict
from datetime import datetime as dt
import datetime
import hashlib
import subprocess
from packages import templates as template
#requirements
import pymongo #3.0.3
from database import *
from packages import send_mail

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
        self.task = self.get_task()
        self.stats = None
        
    def get_task(self):
        ''' here mapping the parameters of the project'''
        #loading the parameters
        db = TaskDB()
        task = db.coll.find_one({"name":self.project})
        params_values = []
        if task is None:
            print "No Project found"
            return None
        else:
            task["now"] = self.date.strftime("%d %B %Y %H:%M")
            task["project_name"] = self.name
            return task
            
    def get_sources(self):
        return {"results":self.data.count({"depth":0, "status.0": True}), "logs":self.data.count({"depth":0, "status.0": False}) ,"total": self.data.count({"depth":0})}
    
    def get_total(self):
        self.results = self.data.find({"status.0":True})
        self.logs = self.data.find({"status.0":False})
        return {"treated": self.data.count(), "results": self.results.count(), "logs": self.logs.count(), "queue": self.queue.count()}

    def current_level(self):        
        max_queue_d = self.queue.aggregate([{"$group":{"_id": "$item", "maxDepth": { "$max": "$depth" }}}])
        return [n for n in max_queue_d][0]["maxDepth"]
        
    def get_process(self):
        #max_depth of the queue:
        self.process = {"level_"+str(d):self.get_depth(d) for d in range(0, self.current_level()+1) }
        return self.process
        
    def get_depth(self, n):
        queue = self.queue.count({"depth":n})
        treated = self.data.count({"depth":n})
        logs = self.data.count({"depth":n, "status.0": False})
        results = self.data.count({"depth":n, "status.0": True})
        cumul_logs = self.data.count({"depth":{"$lte":n}, "last_status": False})
        cumul_results = self.data.count({"depth":{"$lte":n}, "last_status": True})
        return {"queue":queue, "treated": treated, "results":results, "logs":logs, "cumul_logs":cumul_logs,"cumul_results":cumul_results, "depth":n}
        
    
    def get_short_stats(self):
        ''' here the stats of the crawl '''
        self.stats = {}
        for k in  self.get_params():
            if self.__dict__[k] is not False:
                self.stats["params"] = {k:v}
        self.stats["sources"] = self.get_sources()
        self.stats["total"] = self.get_total()
        return self.stats
        
    def get_full_stats(self):
        ''' here the stats of the crawl '''
        stats = {}
        stats["process"] = self.get_process()
        stats["total"] = self.get_total()
        stats["sources"] = self.get_sources()
        return stats
        
    
    def text(self):
        '''Showing stats of current project in shell'''
        
        text = []
        sources = self.get_sources()
        total = self.get_total()
        process = self.get_process()
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
        #~ if self.stats is None:
            #~ self.stats = self.get_full_stats()
            
        if format in ["shell", "print", "debug", "terminal"]:
            return self.show()
        elif format in ["mail", "email", "html"]:
            if format in ["mail", "email"]:
                for t in type:
                    if t == "crawl":
                        stats = self.get_full_stats()
                        stats["project_name"] = self.name
                        if task is None or task["user"] is False:                            
                            send_mail(__author__, "crawl.html", stats, self.text())
                        else:
                            send_mail(task["user"], "crawl.html",stats, self.text())
                    #~ else:
                        #~ if self.user is False:
                            #~ 
                            #~ send_mail(__author__, "action", self.data.update({"params":self.params_report()}))
                        #~ else:
                            #~ send_mail([self.user,__author__], "report.html", self.data.update({"params":self.params_report()}))
                    else:
                        stats = self.get_task()
                        if stats is not None:
                            stats["action"] = t
                            stats["project_name"] = self.name
                            send_mail(__author__, "info.html", stats, "\n".join(stats))
                        else:
                            pass
                            
            elif format in ["html"]:
                raise NotImplementedError
        else:
            raise NotImplementedError
    
    
    def export(self, file_format ="json", directory=None, depth_limit = None):
        
        if self.task["format"] is False:
            self.format = file_format
        else:
            self.format = task["format"]
        if self.format not in ["json", "csv", "sql", "mongodb", "mongo"]:
            sys.exit("Wrong export format")
        
        
        
        if depth_limit is not None:
            completed_depth = depth_limit
            
        else:
            try:
                completed_depth = int(self.current_level() - 1)
            except IndexError:
                completed_depth = 2
        if directory is None:
            directory = os.path.join(RESULT_PATH, self.project)
        results_fields = defaultdict.fromkeys([u'cited_domains', u'extension', u'title', u'url', u'source_url', u'date', u'depth', u'url_id', u'cited_links', u'cited_links_ids',u'crawl_nb'], 1)
        for n in self.data.find({"status.0":True},{"_id":1}):
            print(n.findOne({"_id": n["_id"]},results_fields))
            

            break
        #query_str = '{last_status:true, depth:{$lte:%i}}, {\"_id\": 0, \"last_cited_links_ids\":1, \"last_title\":1, \"last_text\":1, \"last_status\":1, \"last_date\":1, \"depth\":1, \"url\":1, \"url_id\":1}' %completed_depth
        #query, projection = {"last_status":True,"depth":{"$lte":completed_depth}},{"_id": 0, "last_cited_links_ids":1, "last_title":1, "last_text":1, "last_status":1, "last_date":1, "depth":1, "url":1, "url_id":1}
        
        
        outfile = os.path.join(directory, "results_export"+self.date.strftime("%d%m%Y_%H-%M")+"."+str(format))
        
        #~ if self.format == "json":
            #~ query_str = "\""+str(query)+"\""
            #~ cmds = ["mongoexport", "--db",self.project,"--collection","data","--query", query_str, "--out",outfile]
            #~ print " ".join(cmds)
            #~ subprocess.call(" ".join(cmds), shell=True)
            #~ count = ["cat", outfile, "|", "wc", "-l"]
            #~ results_nb = subprocess.call(count, shell=False)
            #~ logging.info("Exported %s records into %s" %(results_nb, outfile))
            #~ return 
        #~ elif self.format == "csv":
            #~ raise NotImplementedError
        #~ elif format == "sql":
            #~ raise NotImplementedError
        #~ elif str(self.format).startswith("mongo"):
            #~ try:
                #~ self.results = self.c.set_coll("results", "url")
            #~ except pymongo.errors.DuplicateKeyError:
                #~ self.c.drop_coll("results")
                #~ self.results = self.c.set_coll("results", "url")
            #~ res = self.data.find({"last_status":True,"depth":{"$lte":completed_depth}}, {"_id": 0, "last_cited_links_ids":1, "last_title":1, "last_text":1, "last_status":1, "last_date":1, "depth":1, "url":1, "url_id":1})
            #~ for n in res:
                #~ try:
                    #~ self.results.insert_one(n)
                #~ except pymongo.errors.DuplicateKeyError:
                    #~ pass
                #~ 
            #~ 
            #~ try: 
                #~ self.logs = self.c.set_coll("logs", "urls")
            #~ except pymongo.errors.DuplicateKeyError:
                #~ self.c.drop_coll("logs")
                #~ self.logs = self.c.set_coll("logs", "url")
            #~ log = self.data.find({"last_status":False,"depth":{"$lte":completed_depth}}, {"_id": 0, "last_msg":1, "last_date":1, "depth":1, "url":1, "url_id":1})
            #~ for n in log:
                #~ try:
                    #~ self.logs.insert_one(n)
                #~ except pymongo.errors.DuplicateKeyError:
                    #~ pass
            #~ logging.info("Exported %i records into %s and %i into %s collections of %s db for %i steps" %(self.logs.count(),"logs", self.results.count(),"results",  self.project, completed_depth))
            #~ return True
        #~ else:
            #~ sys.exit("Unknown export format")

#~ if __name__=="__main__":
    
    #test
    #~ new_project = "COP_24_test"
    #~ s1 = Stats(new_project)
    #~ 
    #~ s1.report(["created"])
    #~ pass
