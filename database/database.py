#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymongo
from pymongo import MongoClient
from pymongo import errors
import re
from datetime import datetime

TASK_MANAGER_NAME = "crawtext_jobs"
TASK_COLL = "job"

class Database(object):
	'''Database creation''' 
	def __init__(self, database_name):		
		self.client = MongoClient('mongodb://localhost,localhost:27017')
		self.db_name = database_name
		self.db = getattr(self.client,database_name)
		
	def use_db(self, database_name):
		return self.client[str(database_name)]

	def use_coll(self, coll_name):
		return self.db[coll_name]

	def show_dbs(self):
		return self.client.database_names()

	def create_coll(self, coll_name):
		setattr(self, str(coll_name), self.db[str(coll_name)])
		#print ("coll : %s has been created in db:%s ") %(self.__dict__[str(coll_name)], self.db_name)
		#return self.__dict__[str(coll_name)]
		return self

	def create_colls(self, coll_names=["results","sources", "log", "queue"]):
		for n in coll_names:
			setattr(self, n, self.db[str(n)])
		# self.queue = self.db['queue'] 
		# self.log = self.db['log']
		# self.sources = self.db['sources']
		# #print ("Creating coll",  [n for n in self.db.collection_names()])
		return [n for n in self.db.collection_names()]
			
	def show_coll(self):
		try:
			print ("using collection %s in DB : %s") %(self.coll_name, self.db_name)
			return self.coll_name
		except AttributeError:
			return False
		
	def show_coll_items(self, coll_name):
		return [n for n in self.db[str(coll_name)].find()]	

	def drop(self, type, name):
		if type == "collection":
			return self.db[str(name)].drop()
		elif type == "database":
			return self.client.drop_database(str(name))
		else:
			print ("Unknown Type")
			return False
	
	def drop_db(self):
		return self.client.drop_database(str(self.db_name))

	def drop_all_dbs(self):
		'''remove EVERY SINGLE MONGO DATABASE'''
		for n in self.show_dbs():
			#if n not in ["projects", "tasks"]:
			self.use_db(n)
			self.drop("database", n)
	'''
	def get_error_list(self):
		for n in self.db.logs.find():
			print n['code'], n['msg'], n['url']
	'''
	
	def insert_log(self,url, log):
		del log["url"]
		try:
			del log['html']
		except KeyError:
			pass
		# print "insert into log %s" %url
		if url not in self.db.sources.distinct("url"):
			print "url is not a source"
			if url not in self.db.logs.distinct("url"):
				print "url is already in logs"
				self.db.logs.insert({"url":url,"msg":[log["msg"]], "status":[log["status"]], "code": [log["code"]]})
			else:
				exists = self.db.logs.find_one({"url":url})
				if exists is not None:
					print "updating log %s" %",".join(log.keys())
					self.db.logs.update({"_id":exists["_id"]}, {"$push": log})
		else:
			print "url is a source"
			exists = self.db.sources.find_one({"url":url})	
			if exists is not None:
				print "updating sources %s" %",".join(log.keys())
				self.db.sources.update({"_id":exists["_id"]}, {"$push": log})
	
	def insert_result(self, log):
		return self.db.results.insert(log)
	
	def sources_stats(self):
		self.show_stats()
		return self.template[3]
	def results_stats(self):
		self.show_stats()
		return self.template[1]
	def results_stats(self):
		self.show_stats()
		return self.template[2]	
	def show_stats(self):
		'''Output the current stats of database in Terminal'''
		self.stats()
		date = datetime.now()
		date = date.strftime("- %d/%M/%Y at %H:%M -")
		title = "==== Project: %s ====\n%s" %(str(self.db_name).capitalize(), date)
		results = "#Results:\n-Total:%d\n-Unique urls:%d"%(self.results_nb, self.uniq_results_nb)
		errors = "#Errors:\n-Total:%d\n-Unique:%d"%(self.logs_nb, self.uniq_logs_nb)
		sources = "#Sources:\n-Total:%d\n-Unique:%d\n-Valid:%d\n-Invalid:%d\nCollected methods:\n-From search:%d\n-From file:%d\n-Manual:%d\n-Automatic:%d"%(self.sources_nb, self.uniq_sources_nb,self.active_sources_nb, self.inactive_sources_nb, self.bing_sources, self.file_sources, self.manual_sources, self.expanded_sources)
		other = "#Other:\nName of the database: %s\nSize of the database: %d MB" %(self.db_name, (self.db.command('dbStats', 1024)['storageSize'])/1024/1024.)
		self.template = [title, results, errors, sources, other]
		return "\n".join(self.template)
	
	def stats(self):
		#sources
		self.sources_nb = self.db.sources.count()
		self.uniq_sources_nb = len(self.db.sources.distinct("url"))
		
		#self.active_sources_nb = self.db.sources.find({"status":True}, { "status": {"$slice": -1 } } ).count()
		self.inactive_sources_nb = self.db.sources.find({"status":False}, { "status": {"$slice": -1 } } ).count()
		self.active_sources_nb = self.sources_nb - self.inactive_sources_nb
		self.bing_sources = self.db.sources.find({"origin":"bing"}).count()
		self.file_sources = self.db.sources.find({"origin":"file"}).count()
		self.manual_sources = self.db.sources.find({"origin":"manual"}).count()
		self.expanded_sources = self.db.sources.find({"origin":"automatic"}).count()

		#results
		self.results_nb = self.db.results.count()
		self.uniq_results_nb = len(self.db.results.distinct("url"))
		#logs
		self.logs_nb = self.db.logs.count()
		self.uniq_logs_nb = len(self.db.logs.distinct("url"))
		self.non_pertinent_nb = self.db.logs.find({"code":800}, { "code": {"$slice": -1 } } ).count()
		#treated
		self.treated_nb = int(int(self.db.results.count()) + int(self.db.logs.count()))
		return self

	def mail_report(self):
		self.show_stats()	
		title = "Report for project %s" %(str(self.db_name))
		
		template = [title]
		
		template.append("<ul>")
		for n in self.template:
			chunk = n.split("\n")

			for c in chunk:
				if c.startswith("#"):
					c = "<h3>%s</h3>"%str(c)
				elif c.startswith("="):
					c = "<h2>%s</h2>"%str(c)
				else:
					c = "<li>%s</li>"%str(c)
				template.append(c)
		
		template.append("</ul>")
		return "".join(template)
		#return "\n".join(self.result) 
	
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
	# 	print ("source; target")
	# 	for n in self.db.results.find():
	# 		for o in n["outlinks"]:
	# 			if o is not None:
	# 				print n['url']+";"+o
	# 			else:
	# 				print n["url"]+";None"
	# 	return
	# def export_backlinks(self):
	# 	print ("source;target")
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

class TaskDB(Database):
	def __init__(self):
		Database.__init__(self, TASK_MANAGER_NAME)
		self.coll = self.db[str(TASK_COLL)]
	
	def get(self):
		return self.coll

if __name__== "__main":
	print "Database"