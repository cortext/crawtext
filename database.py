#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo
from pymongo import MongoClient
from pymongo import errors

class Database():
	def __init__(self, database_name="full_test"):
		client = MongoClient('mongodb://localhost,localhost:27017')
		self.db = client.database_name
		#self.db.x = self.db[x]
		print self.db
		
	def create_tables(self):
		self.results = self.db['results']
		self.queue = self.db['queue'] 
		self.report = self.db['report']
		return self
		
	def select(self, coll_name):
		return self.db[str(coll_name)]
		
	def bad_status(self, url, error_code, error_type):
		'''insert into report url status false, url and type url then clean queue'''
		self.report.insert{'url':url,'error_code':error_code, 'error_type': error_type}) 
		self.queue.remove({"url": url })
		return self
		
	def get_txt_report(self):
		'''generate a simple report'''
		delim = "\n***STATISTIQUES de TRAITEMENT***"
		size = "\n\tsize of DB: %d" % ((self.db.command('dbStats', 1024)['storageSize'])/1024)
		work = "\n\t-url en cours de traitement: %d " % (self.queue.count()) 
		url = "\n\t-urls traitées: %d" % (self.report.count())
		error = "\n\t\t %d urls erronées" % (self.report.count())
		delim2 = "\n***STATISTIQUES du CRAWTEXT***"
		results = "\n\t-Nombre de liens indexés: %d " % (self.results.count())
		result = [delim, size, work, url, ok, error, delim2, results]
		return "".join(result)
	
	def get_info(self, collection_name=None):
		if collection_name is not None:
			print "results doc type example:", (self.results).find_one()
		else:
			print "No collection specified. \n====>Displaying full stats..."
			print self.get_txt_report()
				def find_into(self, collection_name, *values):
		self.db[str(collection_name)].find_one(values)
	
	def udpate_into(self, collection_name, value,  *query):
		self.db[str(collection_name)].udpate(value, query)	
