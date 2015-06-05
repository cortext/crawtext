#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "corbot"
__script_name__ = "corbot"
__version__ = "4.4.1"
__author__= "4barbes@gmail.com"

#defaut import
import os, sys, re
from copy import copy
from collections import defaultdict
from datetime import datetime as dt
import datetime
import hashlib
#requirements
import requests
import pymongo

#internal import
from report import send_mail, generate_report
from database import *
from article import Article, Page
from logger import *


ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")
#search result nb from BING
MAX_RESULTS = 1000
#max depth
DEPTH = 100


class Crawtext(object):
	def __init__(self, name, user_input, debug=False):
		self.name = name
		self.debug = debug
		dt1 = dt.today()
		self.date = dt1.replace(minute=0, second=0, microsecond=0)
		self.task_db = TaskDB()
		self.coll = self.task_db.coll
		self.task = self.coll.find_one({"name":self.name})
		
		if self.name is not None:
			self.project_path = os.path.join(RESULT_PATH, name)
			self.dispatch_action(user_input)
		else:
			self.list_projects()

	def dispatch_action(self,user_input):
		for k,v in user_input.items():
			if k == "debug" and self.debug is True:
				#forcing to consider first the debug of the program
				pass
			else:	
				if v is not False and v is not None:
					if k == "action":
						action = getattr(self, v)
					else:
						setattr(self, k, v)
				else:
					setattr(self, k, False)
		logging.debug(self.__dict__.items())
		return action()

	def create(self):
		'''create a new task with user params and store it into db'''
		if self.task is None:
			new_task = copy(self.__dict__)
			logging.info(self.create.__doc__)
			#contextual action for update
			new_task["status"] = []
			new_task["date"] = []
			new_task["msg"] = []
			new_task["action"] = []
			del new_task['task']
			del new_task['task_db']
			del new_task['coll']
			self.coll.insert(new_task)
			self.task =  self.coll.find_one({"name": new_task["name"]})
			logging.info("Sucessfully created")
			return self.update_status(new_task["name"], "created", True,"Ok")
		else:
			logging.info("Project already exists")
			return self.update()

	def update(self):
		'''udpating parameters of the project'''
		logging.info(self.update.__doc__)
		new_task = copy(self.__dict__)
		self.task  = self.coll.find_one({"name": self.name})
		print self.name
		updated = []
		for k,v in new_task.items():
			try:
				if v is None and v is False:
					pass
				elif k == "date": 
					del new_task[k]
				elif self.task[k] == v:
					pass
				else:
					print "Updating", k
					updated.append("%s:%s"%(k,v))
					
			except KeyError:
				del new_task[k]
				
			except TypeError:
				del new_task[k]
		
		if len(updated) > 0:
			self.coll.update({"name":self.task["name"]}, new_task, upsert=True)
			self.update_status(self.task["name"], "updated : %s" %(",".join(updated)))
			logging.info("Sucessfully updated %s" %self.task["name"])
			sys.exit(0)
		else:
			logging.info("No parameters has been changed")
			return self.show()
	
	def update_status(self, name, action, status=True, msg="Ok"):
		'''updating status for task'''
		u_task = {}
		u_task["status"] = status
		u_task["date"] = self.date
		u_task["msg"] = msg
		u_task["action"] = action
		print self.coll.update({"name":name}, {"$push":u_task})
		self.task = self.coll.find_one({"name":name})
		for k,v in self.task.items():
			if type(v) == list:
				print k
				for item in v:
					print "\t-", item
		
		
	def show(self):
		'''showing the task parameters'''
		self.task = self.coll.find_one({"name": self.name})
		if self.task is None:
			sys.exit("Project doesn't exists.")
		else:
			self.show_task()
			self.show_project()
			sys.exit(0)

	def show_task(self):
		logging.info("Show current parameters stored for task")
		self.task = self.coll.find_one({"name": self.name})
		for k, v in self.task.items():
			if type(v) == list:
				print "*", k,":"
				for item in v:
					if type(item) == list:
						for n in item:
							print "\t\t-", n
					else:
						print "\t", item
			else:
				print "*", k,":", v
		return
	'''
	def show_project(self):
		self.load_project()

		try:
			print "********\n"
			print "SOURCES:"
			print "- Nb Sources indexées: %i" %self.sources.unique
			print "\t- pertinentes: %i" %self.sources.active.nb
			print "\t- non-pertinentes: %i" %self.sources.inactive.nb
			print "RESULTS:"
			print "- Nb Pages indexées: %i" %self.results.unique
			print "ERRORS:"
			print "- Nb Pages non-indexées: %i" %self.logs.unique
			print "PROCESSING"
			print "- Nb Pages en cours de traitement: %i" %self.queue.unique
			print "********\n"
			return self
		except AttributeError:
			print "********\n"
			print "No data loaded into project"
			print "********\n"
			return self
			'''

	def start(self):
		if self.task is None:
			sys.exit("Project doesn't exists.")
		else:
			print self.coll.find_one({"name":self.name})
			logging.info("Loading task parameters")
			self.load_task()
			self.update_status(self.task["name"], "loaded")
			self.config_crawl()
			self.update_status(self.task["name"], "configured")
			self.crawler()
			self.update_status(self.task["name"], "executed")
			sys.exit()




	def mapp_ui(self, ui):
		'''Mapping user parameters'''
		logging.info(self.load_ui.__doc__)
		for k, v in ui.items():
			k = re.sub("--|<|>", "", k)

			if type(v) == list:
				for item in v:
					if type(item) == list:
						#if it's a list we just map the last value
						if item[-1] is not None:
							setattr(self, k, item[-1])
						else:
							setattr(self, k, False)
					else:
						if item is None:
							setattr(self, k, False)
						else:
							setattr(self, k, item)
			else:
				if v is None or v is False:
					setattr(self, k, False)
				else:
					setattr(self, k, v)
		return self
	def load_task(self):
		logging.info("Loading task from TaskDB")
		for k, v in self.task.items():
			if k == "debug" and self.debug is True:
				#forcing to consider first the debug of the program
				pass

			if type(v) == list:
				for item in v:
					if type(item) == list:
						#if it's a list we just map the last value
						if item[-1] is not None:
							setattr(self, k, item[-1])
						else:
							setattr(self, k, False)
					else:
						if item is None:
							setattr(self, k, False)
						else:
							setattr(self, k, item)
			elif v is None:
				setattr(self, k, False)
			elif v is False:
				setattr(self, k, False)
			else:
				setattr(self, k, v)
		return self

	def load_project(self):
		logging.info("Loading Project DB")
		self.project = Database(self.name)
		for n in self.project.create_colls(["results", "sources", "logs", "queue"]):
			setattr(self, str(n), self.project.use_coll(str(n)))
			logging.info("\t- %s: %i" %(n,self.__dict__[n].count()))
		return self
	
	def show_project(self):
		self.load_project()
		self.project.load_data()
		self.project_stats = self.stats()
		for k,v in self.project_stats.items():
			print k.upper()
			print "=" *len(k)
			for i,j in sorted(v.items()):

				if type(j) != list:
					print "\t-", i, j
					pass
				else:
					for err in j:
						for l,m in err[0].items():
							print "\t\t#",l,":", m

	def create_dir(self):
		try:
			self.directory = getattr(self,"directory")
		except AttributeError:
			self.directory = os.path.join(RESULT_PATH, self.name)
			if not os.path.exists(self.directory):
				os.makedirs(self.directory)
				index = os.path.join(self.directory, 'index')
				try:
					self.index_dir = os.makedirs('index')
				except:
					pass
				logging.info("A specific directory has been created to store your projects\n Location:%s"	%(self.directory))
		return self.directory

	def filter_last_items(self, field="status", filter="True"):
		filter_active = [
		  {"$unwind": "$"+filter},
		  {"$group": {
		    "_id": '$_id',
		    "url" : { "$first": '$url' },
		    "source_url" : { "$first": '$source_url' },
		    "depth" : { "$first": '$depth' },
		   	field :  { "$last": "$"+field },
		    "date" :  { "$last": '$date' },
		    }},
		  {"$match": { field: filter }},
		  ]

		return filter_active

	def config_crawl(self):
		''' set configuration for crawler: filter with the query or open
		if project has no query and at least one seed (file or url)
			then the filter is off
			and the crawl insert the seed into sources
		elif the project has a query:
			then the filter is on
			and the crawl insert the seed into sources
		'''
		logging.info("Set crawler: Activating parameters and adding seeds to sources")
		self.create_dir()

		if any([self.key, self.url, self.file]) is False:
			#logging.info("Invalid parameters task should have at least one seed (file, url or API key for search)")
			return sys.exit("Invalid parameters task should have at least one seed (file, url or API key for search)")

		elif self.query is False:
			self.target = False
			if self.key is True:
				logging.warning("Search for seeds with an API key will not work unless you provide a query")
				return sys.exit("Please provide a query")
		else:
			#mapping project values
			self.load_project()
			#Attention un petit hack en cas de pb avec le srv mongo

			self.target = True
			if len(self.queue.distinct("url")) > 0:
				#do not update sources
				return self
			if self.url is not False:
				print "Adding url"
				self.upsert_url(self.url, "manual")
			if self.file is not False:
				print "Adding urls in file"
				self.upsert_file()
			if self.key is not False:
				print "Adding urls from search"
				self.get_seeds()
				#if self.sources.unique == 0:
				#	self.get_seeds()
				# elif self.repeat is not False:
				# 	self.update_seeds()
			return self
	def update_crawl(self):
		raise NotImplementedError

	def bing_search(self):
		# dt = datetime.datetime.now()
		#petit hack pour éviter les projets qui ont l'historique activé et cexu qui ne l'ont pas avant de le réimplémenter
		if type(self.task["date"]) == list:
			self.task["date"] = self.task["date"][-1]
		if (dt.day, dt.month, dt.year, dt.hour) == (self.task['date'].day, self.task['date'].month, self.task['date'].year, self.task['date'].hour) :
			logging.info("Search already done today in less than 1h ")
		# 	return False
		logging.info("bing is searching %s urls" %self.nb)
		web_results = []
		for i in range(0,self.nb, 50):

			#~ try:
			r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
				params={'$format' : 'json',
					'$skip' : i,
					'$top': 50,
					'Query' : '\'%s\'' %self.query,
					},auth=(self.key, self.key)
					)

			#logging.info(r.status_code)

			msg = r.raise_for_status()
			if msg is None:
				for e in r.json()['d']['results']:
					#print e["Url"]
					web_results.append(e["Url"])

		if len(web_results) == 0:
			return False
		return web_results

	def get_seeds(self):
		logging.info("Get_seeds")
		try:
			if self.nb is False:
				self.nb = MAX_RESULTS
		except AttributeError:
			self.nb = MAX_RESULTS

		if self.nb > MAX_RESULTS:
			logging.warning("Maximum search results is %d results." %MAX_RESULTS)
			self.nb = MAX_RESULTS
			logging.warning("Maximum search results has been set to %d results." %MAX_RESULTS)

		if self.nb%50 != 0:
			logging.warning("Maximum search results has to be a multiple of 50 ")
			self.nb = self.nb - (self.nb%50)
			logging.warning("Maximum search results has been set to %d results." %self.nb)

		bing_sources =  self.bing_search()
		if bing_sources is not False:
			total_bing_sources = len(bing_sources)
			logging.info("Search into Bing got %i results" %total_bing_sources)
			for i,url in enumerate(bing_sources):
					try:
						self.sources.insert({
											"url":url,
											"source_url": "search",
											"depth": 0,
											"nb":[i],
											"total":[total_bing_sources],
											"msg":["inserted"],
											"code": [100],
											"status": [True],
											"date": [self.date]
										})
					except pymongo.errors.DuplicateKeyError:
						self.sources.update({
											"url":url},
											{"$push":
											{"nb":i,
											"total":total_bing_sources,
											"msg":"updated",
											"code": 101,
											"status": True,
											"date": self.date
											}})
			logging.info("%i urls from BING search inserted" %i)
			return self
		else:
			logging.warning("Bing search for source failed.")
			return self

	def push_to_queue(self):
		for n in self.sources.find():
			if n['status'][-1] == True:
				try:
					self.queue.insert(n)
				except pymongo.errors.DuplicateKeyError:
					pass
		return self.queue

	def upsert_url(self, url, source_url):
		try:
			self.sources.insert({"url":url,
											"source_url": source_url,
											"depth": 0,
											"msg":["inserted"],
											"code": [100],
											"status": [True],
											"date": [self.date],
											})
		except pymongo.errors.DuplicateKeyError:
			self.sources.update({"url":url},
											{"$push":{
													"msg":"updated",
													"code": 100,
													"status": True,
													"date": self.date
													}})

			return
	def upsert_file(self):
		try:
			if self.directory is not False:
				filepath = os.path.join(self.directory, self.file)
			else:
				filepath = os.path.join(self.project_path, self.file)
		except AttributeError:
			filepath = os.path.join(PROJECT_PATH, self.file)

		nb = []
		with open(filepath, 'r') as f:
			for url in f.readlines():
				self.upsert_url(url, "file %s") %self.file
		return self

	def crawler(self):
		logging.info("Crawler activated with query filter %s" %self.target)
		# if self.sources.nb == 0:
		# 	sys.exit("Error: no sources found in the project.")
		try:
			self.project.load_sources()
			self.project.load_queue()
			self.project.load_logs()
		except AttributeError:
			self.load_project()





		#logging.info("Begin crawl with %i active urls"%self.sources.active_nb)
		self.push_to_queue()
		logging.info("Processing %i urls"%self.queue.count())
		if self.queue.count() == 0:
			self.update_status(self.task["name"], "running", False, "no pending url")
			self.config_crawl()
			return sys.exit("No pending url to process")

		#print self.queue.list

		while self.queue.count() > 0:
			try:
				for item in self.queue.find().sort([("depth", 1)]):
					self.update_status(self.task["name"], "running")
					if item["url"] in self.results.distinct("url"):
						logging.info("in results")
						self.queue.remove(item)

					elif item["url"] in self.logs.distinct("url"):
						logging.info("in logs")
						self.queue.remove(item)
					else:
						#print "Treating", item["url"], item["depth"]
						try:
							p = Page(item["url"], item["source_url"],item["depth"], item["date"], True)
						except KeyError:
							p = Page(item["url"], item["source_url"],item["depth"], self.date, True)
						if p.download():
							a = Article(p.url,p.html, p.source_url, p.depth,p.date, True)
							if a.extract():
								#Targeted crawk filtering for pertinency
								if self.target:
									if a.filter(self.query, self.directory):
										if a.check_depth(a.depth):
											a.fetch_links()
											if len(a.links) > 0:
												for url, domain in zip(a.links, a.domains):
													if url not in self.queue.distinct("url") and url not in self.results.distinct("url"):
														self.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
														if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
													try:
														self.results.insert(a.export())
													except pymongo.errors.DuplicateKeyError:
														#self.results.update(a.export())
														pass

										else:
											logging.debug("depth exceeded")
											self.logs.insert(a.log())
									else:
										logging.debug("Not relevant")
										self.logs.insert(a.log())
								else:
									if a.check_depth(a.depth):
										a.fetch_links()
										if len(a.links) > 0:
											for url, domain in zip(a.links, a.domains):
												try:
													self.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
												except pymongo.errors.DuplicateKeyError:
													pass
													if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
												try:
													self.results.insert(a.export())
												except pymongo.errors.DuplicateKeyError:
													pass
									else:
										logging.debug("Depth exceeded")
										try:
											self.logs.insert(a.log())
										except pymongo.errors.DuplicateKeyError:
											self.logs.update({"url":a.url}, {"$push":{"msg": a.msg}})

							else:
								logging.debug("Error Extracting")
								try:
									self.logs.insert(a.log())
								except pymongo.errors.DuplicateKeyError:
									self.logs.update({"url":a.url}, {"$push":{"msg": a.msg}})
						else:
							logging.debug("Error Downloading")
							self.logs.insert(p.log())

						self.queue.remove(item)
						logging.info("Processing %i urls"%self.queue.count())
					if self.queue.nb == 0:
						break
				if self.queue.nb == 0:
					break
				if self.results.count() > 200000:
					self.queue.drop()
					break
			except Exception as e:
				self.update_status(self.task["name"], "running", False, str(e))
		return sys.exit(1)

	def stop(self):
		import subprocess, signal
		p = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
		out, err = p.communicate()
		cmd = "crawtext.py %s start" %self.name
		for line in out.splitlines():
			if cmd in line:
				pid = int([n for n in line.split(" ") if n != ""][0])
				#pid = int(line.split(" ")[0])
				logging.warning("Current crawl project %s killed" %self.name)
				os.kill(pid, signal.SIGKILL)
				self.update_status(self.task["name"], "stop")
		      		
	def report(self):
		logging.info("Report")
		self.load_project()
		#self.load_data()
		self.create_dir()
		if self.user is None or self.user is False:
			self.user = __author__
		#data = self.show_project()
		if send_mail(self.user, self.project) is True:
			logging.info("A report email has been sent to %s\nCheck your mailbox!" %self.user)
			self.update_status(self.task['name'], "report : mail")
		else:
			logging.info("Impossible to send mail to %s\nCheck your email!" %self.user)
			self.update_status(self.task['name'], "report : mail", False)
			
		if generate_report(self.task, self.project, self.directory):
			#self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": True, "date": self.date, "msg": "Ok"}})
			self.update_status(self.task['name'], "report : doc")
			logging.info("Report sent and stored!")
			return sys.exit(0)
		else:
			#self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": False, "date": self.date, "msg": "Unable to create report document"}})
			self.update_status(self.task['name'], "report : doc", False)
			return sys.exit("Report failed")
	
	def export(self):
		self.load_project()
		self.create_dir()

		logging.info("Export")
		from export import generate
		if generate(self.name, self.data, self.format, self.directory):
			self.update_status(self.task['name'], "export")
			logging.info("Export done!")
			return sys.exit()
		else:
			self.update_status(self.task['name'], "export", False)
			return sys.exit("Failed to export")
	def delete(self):
		self.task = self.coll.find_one({"name": self.name})
		if self.task is None:
			sys.exit("Project %s doesn't exist" %self.name)
		else:       
			self.delete_db()
			self.delete_dir()
			self.coll.remove({"_id": self.task['_id']})
			logging.info("Project %s: sucessfully deleted"%(self.name))
			sys.exit()
	   

	def delete_dir(self):
		import shutil
		directory = os.path.join(RESULT_PATH, self.name)
		if os.path.exists(directory):
			shutil.rmtree(directory)
			logging.info("Directory %s: %s sucessfully deleted"    %(self.name,directory))
			return True
		else:
			logging.info("No directory found for crawl project %s" %(str(self.name)))
			return False

	def delete_db(self):
		db = Database(self.name)
		db.drop_db()
		logging.info("Database %s: sucessfully deleted" %self.name)
		return True
		
	def list_projects(self):
		for n in self.coll.find():
			try:
				print "-", n["name"]
			except KeyError:
				self.coll.remove(n)
		return sys.exit(0)

		
	def list_projects(self):
		for n in self.coll.find():
			try:
				print "-", n["name"]
			except KeyError:
				self.coll.remove(n)
		return sys.exit(0)




