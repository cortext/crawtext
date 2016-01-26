#usr/bin python env
# coding: utf-8
import os, sys
import simplejson as json
import yaml

import crypt
from pymongo import MongoClient
from collections import namedtuple

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
        
class Config(object):
    def __init__(self, project = None, global_settings = None):
        if global_settings is None:
            s = Setup()
            SETTINGS = {"user":s.USER,"db":s.DB,"coll": s.COLL,"dir": s.DIR)
        else:
            s = Setup(global_settings)
            SETTINGS = {"user":s.USER,"db":s.DB,"coll": s.COLL,"dir": s.DIR)
            
    def get_settings(self, cfg):
        #loading default setup
        if cfg is None:
            print "Loading demo"
            afile = os.path.realpath("./config/default.json")
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
    def setup_project(self, cfg):
        '''reading setup info db, user'''
        if cfg is None:
            afile = os.path.realpath("./config/default_settings.json")
            self.settings = json_config(afile)
            print self.settings
        #loading from a simple dict
        
        elif isinstance(cfg, dict):
            self.settings = cfg
            return self.settings
        #loading from file
        
        else:
            afile = os.path.join(os.getcwd(), cfg)
            print afile
            try:
                if afile.endswith(".json"):
                    self.settings = json_config(afile)
                elif afile.endswith(".yml"):
                    self.settings = yml_config(afile)
                else:
                    sys.exit("CONFIG error: config input MUST be a dict, a JSON or a YAML file")
            except IOError:
                self.settings = json_config(afile)
                sys.exit("CONFIG error: no config file found")
            return self.settings
            
            
    def check_format(self):
        '''check if default settings are correctly setup'''
        setup_params = [bool(self.params.haskey(n)) for n in ["user", "db"]]
        print setup_params
        print self.params.keys()
        #~ if any(bool(self.params.haskey("user")), bool:
            #~ print "ok"
        
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
        


