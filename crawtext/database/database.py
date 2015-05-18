#!/usr/bin/env python
# -*- coding: utf-8 -*-
__name__ == "mongodb"
import pymongo
import logging
logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="mongodb.log", format=FORMAT, level=logging.INFO)

import re
from datetime import datetime
from copy import copy
TASK_MANAGER_NAME = "crawtext_jobs"
TASK_COLL = "job"


class Database(object):
	'''Database creation'''
	def __init__(self, database_name, debug=False):
		self.debug = debug
		self.client = pymongo.MongoClient('mongodb://localhost,localhost:27017')
		#connection = pymongo.Connection()
		self.version = self.client.server_info()['version']
		self.t_version = tuple(self.version.split("."))
		self.db_name = database_name
		self.db = getattr(self.client,database_name)
		self.date = datetime.now()
		logging.debug("MongoDB Version :"+self.version)


		#serverVersion = tuple(connection.server_info()['version'].split('.'))
		#requiredVersion = tuple("1.3.3".split("."))
	def set_colls(self, colls=[]):
		if len(coll) == 0:
			self.colls = ["sources", "logs", "results", "queue"]
		else:
			self.colls = colls
		for i in self.colls:
			setattr(self, str(i), self.db[str(i)])
		return self

	def use_db(self, database_name):
		return self.client[str(database_name)]

	def create_db(self, database_name):
		logging.info("Configuring Database %s" %database_name)
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
		logging.debug("Configure collections")
		if len(coll_names) > 0:
			self.colls = ["results","sources", "logs", "queue"]
		else:
			self.colls = coll_names
		for n in self.colls:
			setattr(self, n, self.db[str(n)])
			try:
				self.__dict__[n].create_index("url", unique=True)
			except pymongo.errors.DuplicateKeyError:
				pass
		return self.colls

	def load_sources(self):
		logging.info("Loading sources")
		'''
		pipeline = [
		          #On déroule les status
		          {"$unwind": "$status"},
		          #On les groupes par dernières occurences
		          {"$group": {"_id":
									{"url": "$url",
									"source_url": "$source_url",
									"depth": "$depth",
									"date": "$date",
									"msg": "$msg" ,
									"_id": "$_id",
									},

								"status": {"$last": "$status"}
							}},
		          #ON vérifie que le dernier est valide
		          {"$match": { "status": True }},
		          #On conserve l\'ordre du  tri
		          {"$sort": { "_id._id": 1 }}
		          ]
		#self.sources.active = self.sources.aggregate(pipeline)
		self.sources.active = self.sources.aggregate(pipeline, useCursor=False)

		self.sources.nb = len([n for n in self.sources.actives])
		logging.info("%i url actives",self.sources.nb)


		pipeline2 = [
		          #On déroule les status
		          {"$unwind": "$status"},
		          #On les groupes par dernières occurences
		          {"$group": {"_id":
									{"url": "$url",
									"source_url": "$source_url",
									"depth": "$depth",
									"date": "$date",
									"msg": "$msg" ,
									"_id": "$_id",
									},

								"status": {"$last": "$status"}
							}},
		          #ON vérifie que le dernier est valide
		          {"$match": { "status": False }},
		          #On conserve l\'ordre du  tri
		          {"$sort": { "_id": 1 }}
		          ]

		self.sources.inactive = self.sources.aggregate(pipeline2)
		self.sources.inactive.nb = len([ n for n in self.sources.inactive])
		print self.sources.inactive_nb
		'''
		for n in self.sources.find():
			if n["status"][-1] is False:
				try:
					self.sources.inactive.insert_one(n)
				except pymongo.errors.DuplicateKeyError:
					pass
			else:
				try:
					self.sources.active.insert_one(n)
				except pymongo.errors.DuplicateKeyError:
					pass
		logging.info("%i sources", self.sources.count())
		logging.info("%i active sources", self.sources.active.count())
		logging.info("%i inactive sources", self.sources.inactive.count())
		return self.sources

	def load_logs(self):
		logging.info("%i logs", self.logs.count())
		return self.logs

	def load_queue(self):
		logging.info("%i candidate nodes", self.queue.count())
		return self.queue

	def load_results(self):
		logging.info("%i results", self.results.count())
		return self.results

	def load_data(self):
		self.load_sources()
		self.load_queue()
		self.load_logs()
		self.load_results()
		return self

	def show_coll(self):
		try:
			print ("using collection %s in DB : %s") %(self.coll_name, self.db_name)
			return self.coll_name
		except AttributeError:
			return False

	def show_coll_items(self, coll_name):
		return [n for n in self.db[str(coll_name)].find()]

	def create_index(key, coll):
		 return coll.create_index([(key, pymongo.DESCENDING,True,True)])

	def drop_dups(self, key, coll):
		#logger.DEBUG(coll.count())
		coll = getattr(self, coll)
		if self.t_version[0] > 2:
			print coll.aggregate([{
							"$group": {"_id": { "url": "$url"},
									"uniqueIds": { "$addToSet": "$_id" },
									"count": { "$sum": 1 }}},
									{ "$match": {
										"count": { "$gt": 1 }
										}
									}
							])

			# print coll.count()
			# pipeline = [{ $group: { _id: "url"}  },{ $group: { _id: 1, count: { $sum: 1 } } } ]
			# print self.db.command(db.str(coll).aggregate(pipeline))


			#self.project.sources.aggregate
			# complete = [coll.find_one({"url":n}) for n in coll.distinct("url")]
			# for n in coll.find():
			# 	if n[""] not in coll.
			# 	if n["url"] not in complete:
			# 		coll.remove(n)
			# print coll.count()


			pass
		else:
			coll.ensure_index({url: 1}, {unique:true, dropDups: true})
			print coll.count()
			#coll.ensure_index("url", unique=True)
			#logger.DEBUG(coll.count())
			return

	'''
	def drop_dups(self):
        #only available for < Mongo 2
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
			# Python syntax?
			# self.sources.ensure_index("url", unique=True)
			# self.results.ensure_index("url", unique=True)
			# self.queue.ensure_index("url", unique=True)

		return self
	'''

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
		# "\t-result updated"
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
