#!/usr/bin/env python
# -*- coding: utf-8 -*-
__name__ == "database"
import pymongo
import logging

import re
from datetime import datetime
from copy import copy
import os, sys


    
    
    

class Database(object):
    '''Database creation'''
    def __init__(self, database_name, local=False, debug=False):
        try:
            addr = os.environ["MONGO-SRV_PORT_27017_TCP_ADDR"]      
        except KeyError:
            addr = "localhost"
        try:
            port = int(os.environ["MONGO-SRV_PORT_27017_TCP_PORT"])
        except KeyError:
            port = 27017
        uri = addr+":"+str(port)
        
        try:
        
            self.client = pymongo.MongoClient(uri)
        
        except pymongo.errors.ConnectionFailure:
            logging.warning("Unable to connect using uri %s" %uri)
            try:
                self.client = pymongo.MongoClient(addr, port)
            except:
                sys.exit("ConnectionFailure : Unable to connect to MongoDB with url %s:%s" %(addr,port))
            
        except pymongo.errors.InvalidURI:
            try:
                self.client = pymongo.MongoClient(addr, port)
            except pymongo.errors.ConnectionFailure:
                sys.exit("InvalidUri : Unable to connect to MongoDB with url %s:%s" %(addr,port))
        
        self.version = self.client.server_info()['version']
        self.t_version = tuple(self.version.split("."))
        
        self.db_name = database_name
        self.db = getattr(self.client,database_name)
        self.date = datetime.now()
        


        #serverVersion = tuple(connection.server_info()['version'].split('.'))
        #requiredVersion = tuple("1.3.3".split("."))
    def show_dbs(self):
        return self.client.database_names()
        
    def use_db(self, database_name):
        return self.client[str(database_name)]

    def create_db(self, database_name):
        logging.info("Configuring Database %s" %database_name)
        self.db = self.client[str(database_name)]
        self.create_colls()
        return self
    
    def set_coll(self,coll, index = None):
        setattr(self, str(coll), self.db[str(coll)])
        if index is not None:
            self.__dict__[coll].create_index(index, unique=True)
        return self.__dict__[coll]
        
    def set_colls(self, colls=[]):
        if len(colls) == 0:
            self.colls = ["data","queue"]
        else:
            self.colls = colls
        for i in self.colls:
            setattr(self, str(i), self.db[str(i)])
        return self.colls

    def use_coll(self, coll_name):
        self.coll = self.db[coll_name]
        return self.coll

    

    def create_coll(self, coll_name):
        setattr(self, str(coll_name), self.db[str(coll_name)])
        self.__dict__[coll_name].create_index("url", unique=True)
        #print ("coll : %s has been created in db:%s ") %(self.__dict__[str(coll_name)], self.db_name)
        #return self.__dict__[str(coll_name)]
        return self.db[str(coll_name)]

    def create_colls(self, coll_names=["data", "queue"], index=None):
        logging.debug("Configure collections")
        self.colls = []
        if len(coll_names) > 0:
            colls = ["data", "queue"]
        else:
            self.colls = coll_names
        for n in colls:
            self.colls.append(self.set_coll(n, index))
            
        return self.colls

    
    def show_coll(self):
        try:
            print("using current collection %s in DB : %s") %(self.coll_name, self.db_name)
            return self.coll_name
        except AttributeError:
            return False

    def show_coll_items(self, coll_name):
        return [n for n in self.db[str(coll_name)].find()]

    def create_index(key, coll):
         return coll.create_index([(key, pymongo.DESCENDING,True,True)])

    

    def drop(self, type, name):
        if type == "collection":
            return self.drop_coll(name)
        elif type == "database":
            return self.drop_db(n)
        else:
            print("Unknown Type")
            return False
    def drop_all_dbs(self):
        '''remove EVERY SINGLE MONGO DATABASE'''
        for n in self.show_dbs():
            #if n not in ["projects", "tasks"]:
            self.drop_db(n)
            
    def drop_db(self, db=None):
        if db is not None:
            print("Drop db %s" %db)
            return self.client.drop_database(str(db))

    def drop_coll(self, coll):
        return self.db[str(coll)].drop()
    
    def insert_queue(self, log):
        if log["url"] not in self.db.queue.distinct("url"):
            self.db.queue.insert_one(log)
            return True

    def remove_queue(self, log):
        self.db.queue.remove({"url":log["url"]})
        return True
        
if __name__ == "__main__":
    pass
