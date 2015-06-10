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
import os, sys

	

class Database(object):
	'''Database creation'''
	def __init__(self, database_name, uri="mongodb://localhost:27017", debug=False):
		if uri is None and uri != "tcp://localhost:27017":
			try:
				uri = os.environ["MONGO-SRV_PORT"]
			except KeyError:
				try:
					addr = os.environ["MONGO-SRV_PORT_27017_TCP_ADDR"]
				except KeyError:
					pass
				try:
					port = int(os.environ["MONGO-SRV_PORT_27017_TCP_PORT"])
				except KeyError:
					pass		
				uri = "tcp://"+addr+":"+str(port)
		
		try:
			self.client = pymongo.MongoClient(uri)
		except pymongo.errors.ConnectionFailure:
			logging.warning("Unable to connect to database. Switching to defaut db @localhost:27017")
			try:
				self.client = pymongo.MongoClient("localhost", 27017)
			except pymongo.errors.ConnectionFailure:
				sys.exit("Unable to connect to MongoDB")
		except pymongo.errors.InvalidURI:
			try:
				self.client = pymongo.MongoClient("localhost", 27017)
			except pymongo.errors.ConnectionFailure:
				sys.exit("Unable to connect to MongoDB")
		
		self.version = self.client.server_info()['version']
		self.t_version = tuple(self.version.split("."))
		
		self.db_name = database_name
		self.db = getattr(self.client,database_name)
		
		self.date = datetime.now()
		


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
		
		result = self.db.results.find_one({"url":log['url']})
		source = self.db.sources.find_one({"url":log['url']})
		if source is not None:
			self.db.sources.update({"_id":source["_id"]}, {"$push": {"date": log["date"], "status": True, "msg": "Result stored"}})
		if result is not None:
			return self.update_result(log)

		else:
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
		if log["url"] not in self.db.queue.distinct("url"):
			self.db.queue.insert(log)
			return True

	def remove_queue(self, log):
		self.db.queue.remove({"url":log["url"]})
		return True
	#STATS
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
		'''
		#self.sources.aggregate(pipeline)
		self.sources = self.db.sources
		self.sources.active = self.use_coll("active_sources")
		self.sources.inactive = self.use_coll("inactive_sources")
		self.sources.nb = self.sources.count()
		try:
			self.sources.max_depth = max(self.sources.distinct("depth"))
		except:
			self.sources.max_depth = 0
		for n in self.sources.find({},{ "status": {"$slice": -1} }):
			if n["status"][0] == True:
				try:
					print self.sources.active.insert(n)
				except pymongo.errors.DuplicateKeyError:
					pass 
			else:
				try:
					print self.sources.inactive.insert_one(n)
				except pymongo.errors.DuplicateKeyError:
					pass 
		#origin
		self.sources.bing = self.sources.find({"origin":"bing"}).count()
		self.sources.file = self.sources.find({"origin":"file"}).count()
		self.sources.manual = self.db.sources.find({"origin":"manual"}).count()
		self.sources.automatic = self.db.sources.find({"origin":"automatic"}).count()
				
		logging.info("%i sources", self.sources.count())
		logging.info("%i active sources", self.sources.active.count())
		logging.info("%i inactive sources", self.sources.inactive.count())
		return self.sources
	
	
	def load_logs(self):
		self.logs = self.db.logs
		self.logs.nb = self.db.logs.count()
		try:
			self.logs.max_depth = max(self.logs.distinct("depth"))
		except:
			self.logs.max_depth = 0
			
		logging.info("%i logs", self.logs.count())
		#classified err
		#self.netw_err = range(400, 520)
		#self.spe_err =  [100, 101, 102, 404, 700, 800]
		#self.all_err = self.spe_err + self.netw_err
		for code in self.logs.distinct("code"):
			self.logs.errors = [{"code": k[0], "nb":k[1], "msg" :k[2]} for k in zip(
										self.logs.distinct("code"),
										[self.logs.find({"code":code}).count() for code in self.logs.distinct("code")],
										[self.logs.find_one({"code":code})['msg'] for code in self.logs.distinct("code")]
										)]
								
		return self.logs

	def load_queue(self):
		self.queue = self.db.queue
		self.queue.nb = self.queue.count()
		try:
			self.queue.max_depth = max(self.queue.distinct("depth"))
		except:
			self.queue.max_depth = 0
		logging.info("%i candidate nodes", self.queue.count())
		return self.queue

	def load_results(self):
		self.results = self.db.results
		self.results.nb = self.results.count()
		logging.info("%i results", self.results.count())
		try:
			self.results.max_depth = max(self.results.distinct("depth"))
		except:
			self.results.max_depth = 0
		
		return self.results

	def load_data(self):
		self.load_sources()
		self.load_queue()
		self.load_logs()
		self.load_results()
		return self
		
	def sources_stats(self):
		self.export_stats()
		return self.report[3]

	def results_stats(self):
		self.export_stats()
		return self.report[1]

	def logs_stats(self):
		self.export_stats()
		return self.report[2]
	
	def dump_obj(self):
		pass
		
	def build_stats(self):
		from collections import defaultdict
		self.load_data()
		#print dict.fromkeys(["results", "sources", "logs", "queue"])
		self.stats = dict.fromkeys(["results", "sources", "logs", "queue"], {})
		for k,v in self.__dict__.items():
			if k in self.stats.keys():
				self.stats[k]["nb"] = v.count()
				self.stats[k]["depth"] = [{"depth_"+str(z) : v.find({"depth": z}).count()} for z in v.distinct("depth")]
				data = getattr(self,k)
				
				for i,j in data.__dict__.items():
					if not i.startswith("_"):
						value = getattr(data, i)
						if type(value) == pymongo.collection.Collection:
							self.stats[k][i] = {}
							subvalue = getattr(value, i) 
							self.stats[k][i]["nb"] = subvalue.count()
							self.stats[k][i]["depth"] = [{"depth_"+str(z) : j.find({"depth": z}).count()} for z in j.distinct("depth")]
							try:
								self.stats[k][i]["max_depth"] = max(subvalue.distinct("depth"))
							except:
								self.stats[k][i]["max_depth"] = 0
							
						else:
							self.stats[k][i] = value
		return self.stats
	
	def export_stats(self):
		import json				
		
		self.stats = self.build_stats()
		date = datetime.now()
		self.report = []
		self.report.append("==== Project: %s ====\n%s" %(str(self.db_name).capitalize(), date))
		self.report.append(date.strftime("- %d/%M/%Y at %H:%M -"))
		
		for k in self.stats.keys():
			self.report.append("#%s:\n%s" %(k.title(), json.dumps(self.stats[k], sort_keys=False,indent=4, separators=(',', ': '))))
		self.report.append("#Monitoring:\n\tName of the database: %s\n\tSize of the database: %d MB" %(self.db_name, (self.db.command('dbStats', 1024)['storageSize'])/1024/1024.))
		return "\n".join(self.report)
		
	
	
	def mail_report(self):
		self.export_stats()
		title = "Report for project %s" %(str(self.db_name))

		template = [title]

		template.append("<ul>")
		for n in self.report:
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
		try:
			Database.__init__(self, TASK_MANAGER_NAME,os.environ["MONGO-SRV_PORT"])
		except KeyError:	
			Database.__init__(self, TASK_MANAGER_NAME)
		
		
		self.coll = self.db[str(TASK_COLL)]

	def get(self):
		return self.coll

def test():
	tk = TaskDB()
	for n in tk.coll.find():
		db = Database(n["name"])
		db.mail_report()
		
		
		
if __name__ == "__main__":
	test()
