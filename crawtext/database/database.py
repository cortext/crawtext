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
	def __init__(self, database_name, debug=False):
		self.debug = debug
		self.client = MongoClient('mongodb://localhost,localhost:27017')
		connection = pymongo.Connection()
		self.version = connection.server_info()['version']
		self.t_version = tuple(self.version.split("."))
		self.db_name = database_name
		self.db = getattr(self.client,database_name)
		self.date = datetime.now()
		#print self.t_version[0]

		#serverVersion = tuple(connection.server_info()['version'].split('.'))
		#requiredVersion = tuple("1.3.3".split("."))
	def set_colls(self):
		self.sources = self.db["sources"]
		self.logs = self.db["logs"]
		self.results = self.db["results"]
		self.queue = self.db["queue"]
		return self

	def use_db(self, database_name):
		return self.client[str(database_name)]

	def create_db(self, database_name):
		self.db = self.client[str(database_name)]
		self.create_colls()
		return self

	def use_coll(self, coll_name):
		return self.db[coll_name]

	def show_dbs(self):
		return self.client.database_names()

	def create_coll(self, coll_name):
		setattr(self, str(coll_name), self.db[str(coll_name)])
		#print ("coll : %s has been created in db:%s ") %(self.__dict__[str(coll_name)], self.db_name)
		#return self.__dict__[str(coll_name)]
		return self

	def create_colls(self, coll_names=["results","sources", "logs", "queue"]):
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

	def drop_dups(self):
        ''' only available for < Mongo 2'''
		if self.t_version[0] > 2:
			#self.project.sources.aggregate
			raise NotImplementedError
		else:
	        self.results.create_index([("url", pymongo.DESCENDING, "background"=True, "unique"= True)
			self.queue.create_index([("url", pymongo.DESCENDING, "background"=True, "unique"=True)
			self.sources.create_index([("url", pymongo.DESCENDING, "background"=True, "unique"=True)
			self.queue.ensure_index({url: 1}, {unique:true, dropDups: true})
			self.sources.ensure_index({url: 1}, {unique:true, dropDups: true})
			self.queue.ensure_index({url: 1}, {unique:true, dropDups: true})
			self.project.sources.ensure_index("url", unique=True)
			self.project.results.ensure_index("url", unique=True)
			self.project.queue.ensure_index("url", unique=True)
			self.queue.ensure_index({url: 1}, {unique:true, dropDups: true})
		return self

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

	def insert_logs(self, log_list):
		for log in log_list:
			self.insert_log(self, log)

	def insert_log(self, log):
		# if self.debug: print "insert log", log["msg"]
		url = log["url"]
		try:
			del log['html']
		except KeyError:
			pass
		if url in self.db.sources.distinct("url"):
			if self.debug: print "Source updated"
			exists = self.db.sources.find_one({"url":url})
			if exists is not None:
				del log["url"]
				try:
					self.db.sources.update({"_id":exists["_id"]}, {"$push": log})
					return True
				except:
					self.db.sources.update({"url":url}, {"$push": log})
					return True
		else:
			if url not in self.db.logs.distinct("url"):
				self.db.logs.insert({"url":url,"msg":log["msg"], "status":log["status"], "code": log["code"], "date": [datetime.now()]})
				return True
			else:
				exists = self.db.logs.find_one({"url": url})
				self.db.sources.update({"_id":exists["_id"]}, {"$push": log})
				return True
	def insert_results(self,results):
		for log in results:
			self.insert_result(self, log)
		return True

	def insert_result(self, log):
		self.debug = True
		result = self.db.results.find_one({"url":log['url']})
		source = self.db.sources.find_one({"url":log['url']})
		if source is not None:
			if self.debug: print "\t- sources udpated"
			self.db.sources.update({"_id":source["_id"]}, {"$push": {"date": log["date"], "status": True, "msg": "Result stored"}})
		if result is not None:
			return self.update_result(log)

		else:
			if self.debug: print "\t-page inserted"
			self.db.results.insert(log)
			return True


	def update_result(self, log):
		"\t-result updated"
		try:
			result = self.db.results.find_one({"url":log['url']})
			updated = self.db.results.update({"_id":result["_id"]},{"$push": {"date": log["date"], "status": True, "msg": "Result stored"}})
			# print updated
			try:
				incremented = self.db.results.update({"_id":result["_id"]},{"$set": {"crawl_nb":result["crawl_nb"]+1}})
			except:
				incremented = self.db.results.update({"_id":result["_id"]},{"$set": {"crawl_nb":1}})
			# print incremented
			return True
		except Exception:
			print "No url provided"
			return False

	def insert_queue(self, log):
		if self.debug: print "insert queue", log["url"]
		if log["url"] not in self.db.queue.distinct("url"):
			self.db.queue.insert(log)
			return True

	def remove_queue(self, log):
		self.db.queue.remove({"url":log["url"]})
		return True

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
		results = "#Results:\n\t-Total:%d\n\t-Unique urls:%d"%(self.results_nb, self.uniq_results_nb)
		errors = "#Errors:\n\t-Total:%d\n\t-Unique:%d"%(self.logs_nb, self.uniq_logs_nb)
		sources = "#Sources:\n\t-Total: %d\n-Unique: %d\n\t-Valid: %d\n\t-Invalid: %d\nCollected methods:\n\t-From search:%d\n\t-From file:%d\n\t-Manual:%d\n\t-Automatic:%d"%(self.sources_nb, self.uniq_sources_nb,self.active_sources_nb, self.inactive_sources_nb, self.bing_sources, self.file_sources, self.manual_sources, self.expanded_sources)
		process = "#Process:\n\t-Total: %d\n\t-Unique: %d\n\t-Treated: %d" %(self.queue_nb, self.uniq_queue_nb, self.treated_nb)
		other = "#Other:\n\tName of the database: %s\n\tSize of the database: %d MB" %(self.db_name, (self.db.command('dbStats', 1024)['storageSize'])/1024/1024.)
		self.template = [title, results, errors, sources, process, other]
		return "\n".join(self.template)

	def stats(self):
		#sources
		self.sources_nb = self.db.sources.count()
		self.uniq_sources_nb = len(self.db.sources.distinct("url"))

		#self.active_sources_nb = self.db.sources.find({"status":True}, { "status": {"$slice": -1 } } ).count()
		self.inactive_sources_nb = self.db.sources.find({"status":False}, { "status": {"$slice": -1 } },timeout=False ).count()
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
		self.non_pertinent_nb = self.db.logs.find({"code":800}, { "code": {"$slice": -1 } }, timeout=False ).count()
		#treated
		self.treated_nb = int(int(self.db.results.count()) + int(self.db.logs.count()))
		self.queue_nb = self.db.queue.count()
		self.uniq_queue_nb = len(self.db.queue.distinct("url"))
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
class TaskDB(Database):
	def __init__(self):
		Database.__init__(self, TASK_MANAGER_NAME)
		self.coll = self.db[str(TASK_COLL)]

	def get(self):
		return self.coll

def main():
	import sys
	print "MAINNNN"
	db = Database('test10')
	db.drop_all_dbs()
	print "Hop Foututualapoubelle"
	sys.exit()

if __name__== "__main__":
	main()
