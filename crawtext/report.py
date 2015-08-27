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


ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")


class Stats(object):
    def __init__(self, name, params = None):
        self.name = name
        self.required_keys = ["format", "lang", "max_depth", "data", "date", "short_export", "user"]
        if params is None:
            for k in self.required_keys:
                setattr(self,k, False)
            
        elif type(params) == dict:
            #for debug
            self.added_keys = params.keys()
            self.required_keys = ["format", "lang", "max_depth", "data", "date", "short_export"]
            for k in self.required_keys:
                try:
                    setattr(self,k, params[k])
                except Exception as AttributeError:
                    if k == "max_depth":
                        setattr(self,k, 10)
                    setattr(self,k, False)
            
        else:
            return sys.exit("Error in calling Stats object")
        
        if self.date is False:
            self.date = datetime.now()
        elif type(self.date) == list:
            self.date = self.date[-1]
        self.date = self.date.strftime("%Y-%B-%d")
        self.project = name
        self.c = Database(name)
        self.data = self.c.set_coll("data")
        self.queue = self.c.set_coll("queue")
        
    def get_completed_level(self):
        
        if self.max_depth is False:
            self.max_depth = 10
        for n in range(0,self.max_depth):
            
            to_treat = self.queue.count({"depth":n})
            inserted = self.data.count({"depth":n})
            if to_treat != 0 and inserted != 0:
                self.completed_level = n-1
                return self.completed_level
            
        
    def build(self):
        self.count= {}
        self.results = self.data.find({"last_status":True})
        self.logs = self.data.find({"last_status":False})
        
        self.count["data"] = {"treated": self.data.count(), "results": self.results.count(), "logs": self.logs.count(), "queue": self.queue.count()}
        
        self.count["sources"] = {"results":self.data.count({"depth":0, "last_status": True}), "logs":self.data.count({"depth":0, "last_status": False}) ,"total": self.data.count({"depth":0})}
        
        if self.max_depth is False:
            self.max_depth = 10
        
        for n in range(0, self.max_depth):
            #~ 
            queue = self.queue.count({"depth":n})
            treated = self.data.count({"depth":n})
            logs = self.data.count({"depth":n, "last_status": False})
            results = self.data.count({"depth":n, "last_status": True})
            total_logs = self.data.count({"depth":{"$lte":n}, "last_status": False})
            total_results = self.data.count({"depth":{"$lte":n}, "last_status": True})
            self.count["depth_"+str(n) ] = {"queue":queue, "treated": treated, "results":results, "logs":logs, "total_logs":total_logs,"total_results":total_results, "depth":n}
            if queue == 0 and treated != 0:
                self.count["last"] = self.count["depth_"+str(n)]
            if queue != 0 and treated !=0:
                self.count["current"] = self.count["depth_"+str(n)]
                break
        
        return self.count
    
    def text(self):
        '''Showing stats of current project in shell'''
        text = []
        text.append("Stats for %s" %self.project)
        text.append("**************************")
        try:
            count = self.count
        except AttributeError:
            count = self.build()
        
        for k,v in count.items():
            
            if k == "processing":
                text.append("*"+k)
                for x,y in v.items():
                    text.append("\t - %s" %x)
                    for z,a in y.items():
                        text.append("\t\t- %s: %s"%(z, a)) 
            else:
                text.append("*"+k)
                try:
                    for x,y in v.items():
                        text.append("\t- %s:%s"%(x, y))
                except: 
                    text.append( "\t- %s" %v)
                
        text.append("**************************")
        return "\n".join(text)
        
    def show(self):
        '''Showing stats of current project in shell'''
        print self.text()
        return
    
    def report(self, format="mail"):
        '''Create canvas for report'''
        #~ try:
            #~ count = self.count.items()
        #~ except AttributeError:
        count = self.build()
        if format in ["shell", "print", "debug", "terminal"]:
            return self.show()
        elif format in ["mail", "email", "html"]:
            from jinja2 import Template
            from jinja2 import Environment, PackageLoader
            env = Environment(loader=PackageLoader('crawtext', './'))
            template = env.get_template('./template.html')
            
            html = template.render(date = self.date, name=self.name, count=self.count, project_url= "http://playlab.paris/projects/users/report")
            html = transform(html)
            text = self.text()
            if format in ["mail", "email"]:
                if self.user is False:
                    self.user = __author__
                self.send_mail(self.user, html, text)
                return True
            elif format in ["html"]:
                raise NotImplementedError
        else:
            raise NotImplementedError
            
    def send_mail(self, user, html, txt):
        from packages.format_email import createhtmlmail
        from packages.private import username, passw
        import smtplib

        fromaddrs = "crawlex@playlab.paris"
        toaddrs  = user
        subject = "PLAYERLAB - REPORT from Crawl %s" %str(self.name)
        msg = createhtmlmail(html, txt, subject, fromaddrs)
        # The actual mail send
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.starttls()
        server.login(username,passw)
        server.sendmail(fromaddrs, toaddrs, msg)
        server.quit()
        return True

    def generate_report(self):
        #~ date = dt.now()
        #~ date = date.strftime('%d-%m-%Y_%H-%M')
        #~ directory = os.path.join(directory, 'reports')
        #~ if not os.path.exists(directory):
            #~ os.makedirs(directory)
        #~ filename = "%s/%s.txt" %(directory, date)
#~ 
        #~ with open(filename, 'w') as f:
            #~ f.write("\n======PROJECT PARAMS======\n")
            #~ for k, v in task.items():
                #~ if k not in ["action", "status","msg", "date", "creation_date", "_id"]:
                    #~ if k == "date":
                        #~ v = task[k].strftime('%d-%m-%Y@%H:%M:%S')
                        #~ f.write(str(k)+": "+str(v)+"\n")
#~ 
                    #~ try:
                        #~ f.write(str(k)+": "+str(v)+"\n")
                    #~ except Exception:
                        #~ pass
#~ 
            #~ f.write(db.export_stats())
#~ 
            #~ f.write("\n\n======HISTORY OF THE PROJECT======\n")
#~ 
            #~ #date_list = [n.strftime('%d-%m-%Y %H-%M-%S') for n in task["date"]]
#~ 
            #~ # status_list = list(zip(task["status"],task["msg"]))
            #~ # for msg in status_list:
            #~ #   f.write("\n-"+str(msg))
        #~ logging.info("Your report is ready!\nCheck here: %s" %(filename))
        #~ return True
        return

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
            directory = os.path.join(RESULT_PATH, self.project_name)
                
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
    new_project = "COP21_2015_08"
    s1 = Stats(new_project)
    s1.report("mail")
    #s1.export(format="mongodb")
