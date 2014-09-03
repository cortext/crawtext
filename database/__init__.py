#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
from pymongo import MongoClient
from pymongo import errors
import re


TASK_MANAGER_NAME = "crawtext_jobs"
TASK_COLL = "job"

class Database(object):
	'''Database creation''' 
	def __init__(self, database_name):
		self.client = MongoClient('mongodb://localhost,localhost:27017')
		self.db_name = database_name
		self.db = self.client[self.db_name]
		#self.jobs = self.client[self.db_name].jobs
		#self.results = self.db['results']
		#self.queue = self.db['queue'] 
		#self.log = self.db['log']
		#self.sources = self.db['sources']
		#self.jobs = self.db['jobs']
		#self.db.x = self.db[x]
		
	# def __repr__(self, database_name):	
	# 	print "Using database: %s" %self.client[database_name]
	# 	return self.db

	def use_db(self, database_name):
		return self.client[str(database_name)]

	def use_coll(self, coll_name):
		return self.db[coll_name]

	def show_dbs(self):
		return self.client.database_names()

	def create_coll(self, coll_name):
		setattr(self, str(coll_name), self.db[str(coll_name)])
		#print "coll : %s has been created in db:%s " %(self.__dict__[str(coll_name)], self.db_name)
		return self.__dict__[str(coll_name)]

	def create_colls(self, coll_names=["results","sources", "log", "queue"]):
		for n in coll_names:
			setattr(self, n, self.db[str(n)])
		# self.queue = self.db['queue'] 
		# self.log = self.db['log']
		# self.sources = self.db['sources']
		# #print "Creating coll",  [n for n in self.db.collection_names()]
		return [n for n in self.db.collection_names()]
			
	def show_coll(self):
		try:
			print "using collection %s in DB : %s" %(self.coll_name, self.db_name)
			return self.coll_name
		except AttributeError:
			return False
		

		#return self.db.collection_names()
	def show_coll_items(self, coll_name):
		return [n for n in self.db[str(coll_name)].find()]	

	# def count(self, coll_name):
	# 	self.db_coll = self.db[str(coll_name)]
	# 	return self.db_coll.count()

	
	
	def drop(self, type, name):
		if type == "collection":
			return self.db[str(name)].drop()
		elif type == "database":
			return self.client.drop_database(str(name))
		else:
			print "Unknown Type"
			return False

	def drop_all_dbs(self):
		'''remove EVERY SINGLE MONGO DATABASE'''
		for n in self.show_dbs():
			#if n not in ["projects", "tasks"]:
			self.use_db(n)
			self.drop("database", n)

	def stats(self):
		'''Output the current stats of database in Terminal'''
		title = "===STATS===\n"
		date = datetime.now()
		date = date.strftime("%d/%M/%Y at %H:%M:%s")
		name ="Stored results in Mongo Database: %s \n" %(self.db_name)
		res = "\t-Nombre de resultats dans la base: %d\n" % (self.db.results.count())
		h2 = "#Sources\n"
		sources = "\t-Nombre de seeds: %d\n" % len(self.db.sources.distinct('url')) 
		from_bing="* Sources ajoutées depuis une recherche bing: %d" %len([n for n in self.db.sources.find({"origin":"bing"})])
		from_file="* Sources ajoutées depuis une fichier: %d" %len([n for n in self.db.sources.find({"origin":"file"})])
		manual="* Sources ajoutées par l'utilisateur: %d" %len([n for n in self.db.sources.find({"origin":"defaut"})])
		automatic ="* Sources ajoutées depuis les  résultats: %d" %len([n for n in self.db.sources.find({"origin":"automatic"})])
		
		url = "\t-urls en cours de traitement: %d\n" % (self.db.queue.count())
		url2 = "\t-urls traitees: %d\n" % (len(self.db.results.count())+ len(self.db.logs.count()))
		url3 = "\t-urls erronees: %d\n" % (self.db.logs.count())
		url4 = "\t-urls non pertinentes: %d\n" %(self.db.logs.find({"code": -1, "msg": "Not Relevant"}).count())
		size = "\t-Size of the database %s: %d MB\n" % (self.db_name, (self.db.command('dbStats', 1024)['storageSize'])/1024/1024.)
		result = [title, date,  name, res, h2, sources, from_bing, from_file, automatic, manual, url, url2, url3, url4, size]
		return "".join(result)
	
	def report(self):
		''' Output the currents of database for Email Report'''
		res = "<li>Nombre de resultats dans la base: %d</li>" % (self.db.results.count())
		sources = "<li>Nombre de sources: %d</li>" % len(self.db.sources.distinct('url')) 
		url = "<li>urls en cours de traitement: %d\n</li>" % (self.db.queue.count())
		url2 = "<li>urls traitees: %d</li>" % (self.db.results.count()+ self.db.log.count())
		size = "<li>Size of the database %s: %d MB</li>" % (self.db_name, (self.db.command('dbStats', 1024)['storageSize'])/1024/1024.)
		result = [res, sources, url, 	url2, size]
		return "".join(result)
	
	# Define export gephi inside report option
	# def create_node(self):
	# 	label = ["url", "outlink", "backlink"]
	# 	urllist = [n for n in self.db.results.distinct("url")]
	# 	# outlist = [u for u in n['outlinks'] for n in self.db.results.find() if u not in outlist]
	# 	# backlist = [u["url"] for u in n['backlinks'] for n in self.db.results.find() if u["url"] not in backlist]
	# 	outlist = []
	# 	backlist = []
	# 	print len(urllist)
	# 	for n in self.db.results.find():
	# 		if n["outlinks"] is None:
	# 	 		pass
	# 		for o in n["outlinks"]:
	# 			if o is not None:
	# 				outlist.append([o["url"], "backlink"])
	# 	for n in self.db.results.find():
	# 	 	if n != []:
	# 			for o in n["backlinks"]:
	# 	 			if o is not None:
	# 					backlist.append([o["url"], "backlink"])

	# 	return 
	# def export_outlinks(self):
	# 	'''Output url : outlink'''
	# 	print "source; target"
	# 	for n in self.db.results.find():
	# 		for o in n["outlinks"]:
	# 			if o is not None:
	# 				print n['url']+";"+o
	# 			else:
	# 				print n["url"]+";None"
	# 	return
	# def export_backlinks(self):
	# 	print "source;target"
	# 	for n in self.db.results.find():
	# 		if n != []:
	# 			for u in n["backlinks"]:
	# 				print n["url"]+";"+u["url"]
	# 		# for o in n["backlinks"]:
	# 		# 		if o is not None:
	# 		# 			print n['url']+";"+o
	# 		# 		else:
	# 		# 			print n["url"]+";None"
	# 	return
# if __name__ == "__main__":
#  	db = Database('test')
#  	db.drop_all_dbs()
