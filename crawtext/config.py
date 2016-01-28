#usr/bin python env
# coding: utf-8
import os, sys
import simplejson as json
import yaml
import crypt
from pymongo import MongoClient

import datetime
from datetime import datetime as dt
#import requests


import logging
logging.basicConfig()

class Setup(object):
    def __init__(self, global_settings=None):
        '''setting global environnement'''
        self.get_settings(global_settings)
        self.USER, self.password = self.settings["user"], crypt.crypt(self.settings["password"],"22")
        #~ os.system("useradd -p "+self.password+" "+self.user)
        self.db = self.settings["db"]
        if not self.db_exists():
            self.setup_db()
        
        self.DB = self.client[self.db["db_name"]]
        self.COLL = self.DB[self.db["collection"]]
        self.DIR = self.create_env()
        self.GLOBAL_SETTINGS = {"db": self.db, "user": self.USER, "dir": self.DIR}
        self.LOCAL_SETTINGS = {"user":self.USER,"db":self.DB,"coll": self.COLL,"dir": self.DIR}
        
    def get_settings(self, cfg):
        #loading default setup
        if cfg is None:
            afile = os.path.realpath("./config/settings.json")
            self.settings = json_config(afile)
            return self.settings
        #loading from a simple dict
        elif isinstance(cfg, dict):
            self.settings = cfg
            return self.settings
        #loading from file
        else:
            afile = os.path.realpath(cfg)
            
            try:
                if afile.endswith(".json"):
                    self.settings = json_config(afile)
                elif afile.endswith(".yml"):
                    self.settings = yml_config(afile)
                else:
                    sys.exit("SETUP error: config input MUST be a dict, a JSON or a YAML file")
            except IOError:
                self.settings = json_config(afile)
                sys.exit("SETUP error: no config file found")
            return self.settings
    
    

    def db_exists(self):
        uri = 'mongodb://%s,%s:%s'%(self.db["host"], self.db["host"], self.db["port"])
        self.client =  MongoClient(uri)
        return bool(self.db["db_name"] in self.client.database_names())
   
    def create_env(self):
        '''create the default store directory'''
        self.DIR = os.path.join(os.getcwd(), self.USER)
        if not os.path.exists(self.DIR):
            os.makedirs(self.DIR)
        return self.DIR
    
    def delete_env(self):
        import shutil
        
        if os.path.exists(self.DIR):
            shutil.rmtree(self.DIR)
            #logger.debug("Directory %s: %s sucessfully deleted"    %(self.name,directory))
            return True
        else:
            #logger.debug("No directory found for crawl project %s" %(str(self.name)))
            return False

    def delete_db(self):
        return self.DB.drop_db()
        
    def list_projects(self):
        for n in self.COLL.find():
            print n
        return 
        
class Project(object):
    def __init__(self, project = None, global_settings = None):
        '''config project and task'''
        s = Setup(global_settings)
        
        self.settings = s.GLOBAL_SETTINGS
        for k, v in s.LOCAL_SETTINGS.items():
            #print k.upper(), v
            setattr(self, k.upper(),v)
            #~ 
        self.PROJECT = None
        self.get_params(project)
        self.status = self.setup_project()
        #TEST
        self.status = True
        self.PROJECT["status"] = self.status 
        
    def get_params(self, cfg):
        '''indexig parameters from file'''
        #loading default setup
        if cfg is None:
            print "Loading demo"
            afile = os.path.realpath("./config/example.json")
            self.params = json_config(afile)
        #loading from a simple dict
        elif isinstance(cfg, dict):
            self.params = cfg
        #loading from file
        else:
            afile = os.path.realpath(cfg)
            try:
                if afile.endswith(".json"):
                    self.params = json_config(afile)
                elif afile.endswith(".yml"):
                    self.params = yml_config(afile)
                else:
                    sys.exit("SETUP error: config input MUST be a dict, a JSON or a YAML file")
            except IOError:
                self.params = json_config(afile)
                sys.exit("SETUP error: no config file found")
        return self.params
        
    def setup_project(self):
        if self.exists():
            return self.update_project()
        return self.create_project()

    def exists(self):
        self.NAME = self.params["name"]
        #self.USER is in SETUP
        
        self.PROJECT = self.COLL.find_one({"user":self.USER, "name": self.NAME})
        return bool(self.PROJECT is not None)
        
    def create_project(self):
        '''creating a new project'''
        print self.create_project.__doc__
        date = dt.today()
        self.START_DATE = date.replace(second=0, microsecond=0)
        self.params["date"] = [self.START_DATE]
        self.params["history"] = ["created"]
        self.params["user"] = self.USER
        #self.SCHEDULE = self.params["scheduler"]
        #~ if self.SCHEDULE["active"]:
            #~ print self.SCHEDULE["days"]
        
        if self.check_config():
            self.project_id = self.COLL.insert(self.params)
            if self.exists():
                print "Project %s has been sucessfully created" %self.PROJECT["name"]
                return True
            else:
                return False
        else:
            print "Error in config file. Aborting"
            return False
        
    def update_project(self):
        '''updating project configuration'''
        print self.update_project.__doc__
        
        self.START_DATE = self.PROJECT["date"][-1]
        date = dt.today()
        self.UPDATED_DATE = date.replace(second=0, microsecond=0)
        time_elapsed = self.START_DATE - self.UPDATED_DATE
        
        scheduler = self.PROJECT["scheduler"], self.params["scheduler"]
        if self.has_changed(scheduler):
            self.COLL.update({"_id": self.PROJECT["_id"]}, {'$set':{"scheduler": self.params["scheduler"]}})
            self.PROJECT["scheduler"] = self.params["scheduler"]
            self.COLL.update({"_id": self.PROJECT["_id"]}, {'$push':{"date": self.UPDATED_DATE}})
            self.COLL.update({"_id": self.PROJECT["_id"]}, {'$push':{"history": "update sccheduler"}})
        reload_seeds = False
        histories = []
        for n in ["seeds", "filters"]:
            seeds = zip(self.PROJECT[n].keys(), self.PROJECT[n].values(), self.params[n].values())
            values = []
            for k, dic1, dic2 in seeds:
                params = zip(dic1.keys(), dic1.values(), dic2.values())
                for item in params:
                    if item[1] != item[2]:
                        
                        self.COLL.update({"_id": self.PROJECT["_id"]}, {"$set":{n+"."+k+"."+item[0]: item[2]}})
                        self.PROJECT[n][k][item[0]] = item[2]
                        msg = n+" "+k+" "+item[0]+"has been updated to: "+ str(item[2])
                        histories.append(msg)
                        if n == "seeds":
                            reload_seeds = True
                        if item[0] == "query" or item[0] == "key":
                            reload_seeds = True
        if len(histories) > 0:
            self.COLL.update({"_id": self.PROJECT["_id"]}, {'$push':{"date": self.UPDATED_DATE}})
            self.COLL.update({"_id": self.PROJECT["_id"]}, {'$push':{"history": " ".join(histories)}})
        if self.check_config():
            return reload_seeds
        else:
            return False
    
        
    def check_config(self):
        '''Verifying configuration from self.params'''
        def test_value(value):
            if value is None or len(value) == 0:
                #print "parameter is empty"
                return False
            if type(value) not in [unicode, str]:
                #print "%s is not text" %value
                return False
            return True
            
        filters = {k: self.params["seeds"][k]["active"] for k in self.params["seeds"].keys()}
        seeds_options = [k for k, v in filters.items() if v is True]
        
        status = True
        #verifier que au moins une option de seeds est activée
        print ".............................."
        print "CONFIGURATION CHECK"
        print " * Checking seeds options:"
        if any(filters.values()):
            
            for f in seeds_options:
                #vérifier les parametres pour le search
                if f == "search":
                    print "\t Search option has been activated"
                    print "\t - Checking search options"
                    
                    #verifier qu'il y a une requete
                    status = test_value(self.params["filters"]["query"]["query"])
                    if status is False:
                        err = "! wrong format, cannot be None or empty"
                        print "\t\t Query:"+err
                        print err
                    else:
                        print "\t\t Query:"+"Ok"
                    
                    #verifier que la clé d'API est OK
                    if test_value(self.params["seeds"]["search"]["key"]):
                        
                        if len(self.params["seeds"]["search"]["key"]) != 43:
                            err = "! must be composed by 43 caracters"
                            print "\t\t API Key:"+err
                            status = False
                        else:
                            print "\t\t API Key:"+ "OK"
                    else:
                        status =  False
                        err = "!  wrong format, cannot be None or empty"
                        print "\t\t API Key:"+err
                    
                    if self.params["seeds"]["search"]["nb"] not in range(50,1100):
                        status =  False
                        err = "! Search nb has to be <=1000 and >=50"
                        print "\t\t Search nb:"+err
                    else:
                        #print "\t\t Search nb: Ok"
                        pass
                    if self.params["seeds"]["search"]["nb"] %50 != 0:
                        status =  False
                        err = "! Search nb has to be a multiple of 50"
                        print "\t\t Search nb:"+err
                    else:
                        print "\t\t Search nb: Ok"
                        
                else:
                    
                    print "\t %s option has been activated" %f.title()
                    
                    if test_value(self.params["seeds"][f][f]):
                        print "\t - %s parameter: OK" %f
                        
                    else:
                        err = "! Wrong format \n%s cannot be empty or Null and has to be a string" %f
                        print "\t -"+ f +" parameter: "+err
                        status = False
                        
                        
                        
        else:
            err = '''\t ! No seed option has been activated: 
            Activate at least one option inside your config file to launch the crawler:
                - url
                - file
                - search
                '''
            
            print err
            status = False
        if status is True:
            print "Configuration is Ok"
            print "..............................."
        return status
       
            
    def has_changed(self, params):
        return any([n[0]!=n[1] for n in zip(params[0].values(),params[1].values())])
    
    def delete_project(self):
        if self.exists():
            print self.COLL.remove({"name":self.PROJECT["name"], "user":self.PROJECT["user"]})
            return True
        return False
    
                        
def yml_config(afile):
    with open(afile, 'r') as ymlfile:
        
        config = yaml.load(ymlfile.read())
        return config

def json_config(afile):
    with open(afile, 'r') as jsonfile:
        try:
            config = json.load(jsonfile)
            return config    
        except ValueError as e:
            sys.exit("Error parsing %s file: %s" %(afile, e))
