#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
from pymongo import MongoClient
from pymongo import errors
import logging

class Database(object):
    '''Database creation''' 
    def __init__(self, database_name, debug=False, port=27017):
        self.debug = debug      
        self.client = MongoClient('mongodb://localhost,localhost:%s') %str(port)
        self.db_name = database_name
        self.db = getattr(self.client,database_name)

    def connect(self):
        try:
            print self.client[str(self.db_name)]
        except Exception as ex:
            print logging.Exception(ex)
            return False
        return True