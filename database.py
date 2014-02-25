#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymongo
from pymongo import MongoClient
from pymongo import errors

class Database():
	def __init__(self, database_name="full_test"):
		client = MongoClient('mongodb://localhost:27017')
		self.db = client[database_name]
		#self.db.x = self.db[x]
		print self.db
		
	def create_tables(self):
		self.results = self.db['results']
		self.queue = self.db['queue'] 
		self.report = self.db['report']
		return self
		
	def select(self, coll_name):
		return self.db[str(coll_name)]
		
	def good_status(self,type, value):
		'''insert into report status true url and type url then clean queue'''
		self.report.insert({"url": value,"type":type, "status": True})
		self.queue.remove({ "url": value })
		return self
		
	def bad_status(self, type, url, error_type):
		'''insert into report url status false, url and type url then clean queue'''
		self.report.insert({"url": url, "status": False, "type":type, "error":error_type})	
		self.queue.remove({"url": url })
		return self
		
	def get_txt_report(self):
		'''generate a simple report'''
		delim = "\n***STATISTIQUES de TRAITEMENT***"
		size = "\n\tsize of DB: %d" % ((self.db.command('dbStats', 1024)['storageSize'])/1024)
		work = "\n\t-url en cours de traitement: %d " % (self.queue.count()) 
		url = "\n\t-urls traitées: %d" % (self.report.count())
		ok = "\n\t\t%d urls correctes" % (self.report.find({"status":True}).count())
		error = "\n\t\t %d urls fausses" % (self.report.find({"status":False}).count())
		delim2 = "\n***STATISTIQUES du CRAWTEXT***"
		results = "\n\t-forum: %d " % (self.results.count())
		result = [delim, size, work, url, ok, error, delim2, results]
		return "".join(result)
	
	def get_info(self, collection_name=None):
		if collection_name is not None:
			print "results doc type example:", (self.results).find_one()
		else:
			print "No collection specified"
			print self.get_txt_report()
			
	def insert_into(self, collection_name, *values):
		#~ print "inserting", type(collection_name)
		#~ self.db[collection_name].insert(*values, upsert=True, multi=True)
		if collection_name == "forum":
			return self.forum.insert(values, upsert=True, multi=True)
		elif collection_name == "category":
			return self.category.insert(values, upsert=True, multi=True)
		elif collection_name == "topic":
			return self.topic.insert(values, upsert=True, multi=True)
		elif collection_name == "post":
			return self.post.insert(values, upsert=True, multi=True)
		else:
			print "No collection specified"
			return None
			
	def find_into(self, collection_name, *values):
		self.db[str(collection_name)].find_one(values)
	
	def udpate_into(self, collection_name, value,  *query):
		self.db[str(collection_name)].udpate(value, query)	
