#usr/bin python env
# coding: utf-8
import os, sys
import simplejson as json
import yaml

import crypt
from pymongo import MongoClient
from collections import namedtuple
import datetime
from datetime import datetime as dt

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
        self.SETTINGS = {"user":self.USER,"db":self.DB,"coll": self.COLL,"dir": self.DIR}
        
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
    
    def setup_db(self):
        uri = 'mongodb://%s,%s:%s'%(self.db["host"], self.db["host"], self.db["port"])
        self.client =  MongoClient(uri)
        DB = self.client[self.db["db_name"]]
        COLL = DB[self.db["collection"]]
        return self.client
    
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
        
class Project(object):
    def __init__(self, project = None, global_settings = None):
        '''config project and task'''
        s = Setup(global_settings)
        for k, v in s.SETTINGS.items():
            #print k.upper(), v
            setattr(self, k.upper(),v)
            
        self.PROJECT = None
        self.get_params(project)
        self.setup_project()
    def get_params(self, cfg):
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
        if not self.exists():
            self.create_project()
            self.add_seeds()
        else:
            self.update_project()
            self.add_seeds()
        return self
    def exists(self):
        self.NAME = self.params["name"]
        self.PROJECT = self.COLL.find_one({"user":self.USER, "name": self.NAME})
        return bool(self.PROJECT is not None)
        
    def create_projet(self):
        date = dt.today()
        self.START_DATE = date.replace(second=0, microsecond=0)
        self.params["user"] = self.USER
        self.params["date"] = [self.START_DATE]
        self.SCHEDULE = self.params["scheduler"]
        if self.SCHEDULE["activated"]:
            print self.SCHEDULE["days"]
        
        self._id = self.COLL.insert(self.params)
        self.PROJECT = self.COLL.find_one({"_id":self._id})
        return self.PROJECT
        
    def update_project(self):
        self.START_DATE = self.PROJECT["date"][-1]
        date = dt.today()
        self.UPDATED_DATE = date.replace(second=0, microsecond=0)
        time_elapsed = self.START_DATE - self.UPDATED_DATE
        return self
    
    def delete_project():
        pass
    def add_seeds(self):
        for k, v in self.PROJECT["seeds"].items():
            
            if v["activated"]:
                print k, v
                if k == "from_search":
                    if self.PROJECT["filters"]["query_filter"]["activated"]:
                        print self.PROJECT["filters"]["query_filter"]["query"]
                        #~ if g["activated"]:
                            #~ print f, g
        pass
    def delete_seeds():
        pass
    def update_seeds():
        pass
    def delete_env(self):
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
        

if __name__=="__main__":
    t = Project()
    print t.START_DATE
