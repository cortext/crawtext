#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "crawtext"
__script_name__ = "saveoursoul"
__version__ = "4.3.2"
__author__= "4barbes@gmail.com"
__doc__ = '''Crawtext.

Description:
A simple crawler in command line for targeted websearch.

Usage:
	crawtext.py (<name>) show [--debug]
	crawtext.py (<name>) (create|update|add) [--query=<query>] [--file=<file>][--url=<url>][--key=<key>] [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug] [--repeat=<repeat>]
	crawtext.py (<name>) add [--query=<query>] [--file=<file>][--url=<url>][--key=<key>] [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug] [--repeat=<repeat>]
	crawtext.py (<name>) start [--debug]
	crawtext.py (<name>) restart [--debug]
	crawtext.py (<name>) stop [--debug]
	crawtext.py (<name>) export [--data=<data>] [--format=<format>] [--debug]
	crawtext.py (<name>) report [--user=<email>] [--format=<format>] [--debug]
	crawtext.py (<name>) delete [--debug]
'''

import os, sys, re
import copy
from docopt import docopt
from datetime import datetime as dt
from database import *
import datetime
#from url import Link
from report import send_mail, generate_report
import hashlib
from article import Article, Page
from crawl import crawl
import requests
from logger import *
from bson.son import SON
import pickle

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")
#search result nb from BING
MAX_RESULTS = 1000
#max depth
DEPTH = 100

class Crawtext(object):
	def __init__(self, name, user_input, debug):
		self.name = name
		self.debug = debug
		dt = datetime.datetime.today()
		self.date = dt.replace(minute=0, second=0, microsecond=0)
		self.project_path = os.path.join(RESULT_PATH, name)
		self.task_db = TaskDB()
		self.coll = self.task_db.coll
		self.task = self.coll.find_one({"name":self.name})
		self.dispatch_action(user_input)

	def dispatch_action(self,user_input):
		for k,v in user_input.items():
			if k == "debug" and self.debug is True:
				#forcing to consider first the debug of the program
				pass
			if k.startswith("<"):
				# key = re.sub("<|>", "", k)
				# setattr(self,key,v)
				pass
			elif k.startswith("--"):
				key = re.sub("--", "", k)
				if v is None:
					v = False
				setattr(self,key,v)
			else:
				if v is not False and v is not None:
					action = getattr(self, k)
		logging.debug(self.__dict__.items())
		return action()

	def create(self):
		'''create a new task with user params and store it into db'''
		if self.task is None:
			new_task = copy.copy(self.__dict__)
			logging.info(self.create.__doc__)

			del new_task['task']
			del new_task['task_db']
			del new_task['coll']
			#logging.debug(new_task.items())
			self.coll.insert(new_task)
			logging.info("Sucessfully created")

			return self.show()
		else:
			logging.info("Project already exists")
			return self.update()

	def update(self):
		'''udpating project'''
		logging.info(self.update.__doc__)
		new_task = copy.copy(self.__dict__)
		for k,v in new_task.items():
			if v is None and v is False:
				del new_task[k]
		del new_task['coll']
		del new_task['task_db']
		del new_task['task']
		self.coll.update({"name":self.task["name"]}, new_task)
		logging.info("Sucessfully updated")
		return self.show()
	def show(self):
		'''showing the task parameters'''
		self.task.find({"name": self.name})
		if self.task is None:
			sys.exit("Project doesn't exists.")
		else:
			return self.show_task()
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

	def show_project(self):
		self.load_project()
		self.load_data()
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

	def start(self):
		if self.task is None:
			sys.exit("Project doesn't exists.")
		else:
			print self.coll.find_one({"name":self.name})
			logging.info("Loading task parameters")
			self.load_task()
			self.config_crawl()
			self.crawler()
			#self.update_task()
			return self.show()




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
		self.results = self.project.use_coll('results')
		self.sources = self.project.use_coll('sources')
		self.logs = self.project.use_coll('logs')
		self.queue = self.project.use_coll('queue')

		return self.project

	def load_sources(self):
		'''loading sources data and stats'''
		#SOURCES
		logging.info("Loading sources")
		self.sources.nb = self.sources.count()
		self.sources.urls = self.sources.distinct("url")
		#self.sources.unique = db.sources.aggregate([{ $group: { _id: "$url"}  },{ $group: { _id: 1, count: { $sum: 1 } } }])
		self.sources.unique = len(self.sources.urls)
		self.sources.list = [self.sources.find_one({"url":url}) for url in self.sources.urls]

		self.sources.active = self.project.use_coll('info')
		self.sources.active.list = [n for n in self.sources.list if n["status"][-1] is True]
		self.sources.active.nb = len(self.sources.active.list)

		self.sources.inactive = self.project.use_coll('info')
		self.sources.inactive.list = [n for n in self.sources.list if n["status"][-1] is False]
		self.sources.inactive.nb = len(self.sources.inactive.list)
		return self.sources

	def load_results(self):
		self.results.nb = self.results.count()
		self.results.urls = self.results.find().distinct("url")
		self.results.unique = len(self.results.urls)
		#self.results.unique = db.results.aggregate([{ $group: { _id: "$url"}  },{ $group: { _id: 1, count: { $sum: 1 } } } ])
		self.results.list = [self.results.find_one({"url":url}) for url in self.results.urls]
		return self.results

	def load_logs(self):
		self.logs.nb = self.logs.count()
		self.logs.urls = self.logs.distinct("url")
		#self.logs.unique = self.logs.aggregate([{ $group: { _id: "$url"}  },{ $group: { _id: 1, count: { $sum: 1 } } } ])
		#self.logs.list = [self.logs.find_one({},{"url":url}) for url in self.logs.urls]
		return self.logs
	def load_queue(self):
		self.queue.nb = self.queue.count()
		self.queue.urls = self.queue.distinct("url")
		self.queue.unique = len(self.queue.urls)
		#self.queue.unique = self.sources.aggregate([{ $group: { _id: "$url"}  },{ $group: { _id: 1, count: { $sum: 1 } } } ])
		self.queue.list = [self.queue.find_one({"url":url}) for url in self.queue.urls]
		self.queue.max_depth = self.queue.find_one(sort=[("depth", -1)])
		#self.queue.dates = self.queue.find({"date":{"$exists":"True"}})
		return self.queue

	def load_data(self):
		'''loading data and mapping it into object'''
		logging.info("Loading data from project db")
		try:
			self.load_sources()

		except AttributeError as e:
			logging.warning(e)
			pass
		try:
			self.load_results()
		except AttributeError as e:
			logging.warning(e)

			pass
		try:
			self.load_queue()
		except AttributeError as e:
			logging.warning(e)

			pass

		try:
			self.load_logs()
		except AttributeError as e:
			logging.warning(e)

			pass
		try:
			self.crawl = self.project.use_coll('info')
			self.crawl.process_nb = self.queue.unique
			self.crawl.treated_nb = self.logs.unique+self.results.unique+self.sources.unique
			return self
		except AttributeError as e:
			logging.warning(e)
			return self
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

		self.load_project()
		self.load_data()

		self.target = True
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
		# if (dt.day, dt.month, dt.year) == (self.task['date'].day, self.task['date'].month, self.task['date'].year) :
		# 	logging.info("Search already done today")
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
					self.sources.insert({
											"url":url,
											"source_url": "search",
											"depth": 0,
											"nb":i,
											"total":total_bing_sources,
											"msg":["inserted"],
											"code": [100],
											"status": [True],
											"date": [self.date]
										})
			logging.info("%i urls from BING search inserted" %i)
			return self
		else:
			logging.warning("Bing search for source failed.")
			return self
	def push_to_queue(self):
		for n in self.sources.active.list:
			if self.queue.find_one({"url": n["url"]}) is None:
				self.queue.insert(n)

		return self.queue

	def upsert_url(self, url, source_url):
		if exists is None:

			self.project.sources.insert({"url":url,
											"source_url": source_url,
											"depth": 0,
											"msg":["inserted"],
											"code": [100],
											"status": [True],
											"date": [self.date],
											})
		else:
			self.project.sources.update({"url":exists["url"]},
											{"$push":{
													"msg":"updated",
													"code": 100,
													"status": True,
													"date": self.date
													}})

			return False
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

		logging.info("Begin crawl with %i active urls"%self.sources.active.nb)
		self.push_to_queue()

		logging.info("Processing %i urls"%self.queue.nb)



		#print self.queue.list

		while self.queue.count() > 0:
			for item in self.queue.list:
				if item["url"] in self.results.find({"url": url}):
					logging.info("in results")
					self.queue.remove(item)

				elif item["url"] in self.logs.find({"url": url}):
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
												if url not in self.queue.find({"url": url}) and url not in self.results.find({"url": url}):
													self.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
													if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
												if a.url not in self.results.find({"url": url}):
													self.results.insert(a.export())
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
											if url not in self.queue.urls:
												self.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
												if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
											self.results.insert(a.export())
								else:
									logging.debug("Depth exceeded")
									self.logs.insert(a.log())
						else:
							logging.debug("Error Extracting")
							self.logs.insert(a.log())
					else:
						logging.debug("Error Downloading")
						self.logs.insert(p.log())

					self.queue.remove(item)
					logging.info("Processing %i urls"%self.queue.nb)
				if self.queue.nb == 0:
					break
			if self.queue.nb == 0:
				break
			if self.results.count() > 200000:
				self.queue.drop()
				break

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
		      '''
				if self.exists():

				try:
		              self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"stop crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
		          except Exception, e:
		              self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"start crawl", "status": False, "date": date, "msg": e}})
				'''
		      os.kill(pid, signal.SIGKILL)
		'''
	      if self.exists():
	          self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"stop crawl", "status": False, "date": dt.now(), "msg": "No running project found"}})
	          print "No running project %s found" %self.name
	          return False
	      else:
	          print "No crawl job %s found" %self.name
	          return False
		'''
	def report(self):
		logging.info("Report")
		self.load_project()
		self.load_data()
		self.create_dir()
		if self.user is None or self.user is False:
			self.user = __author__
		data = self.show_project()
		if send_mail(self.user, data) is True:
			logging.info("A report email has been sent to %s\nCheck your mailbox!" %self.user)
			#self.coll.update({"name": self.task['name']}, {"$push": {"action":"report: mail", "status":True, "date": self.date, "msg": "Ok"}})
		else:
			logging.info("Impossible to send mail to %s\nCheck your email!" %self.user)
			#self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":False, "date": self.date, "msg": "Error while sending the mail"}})
		if generate_report(self.task, self.project, self.directory):
			#self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": True, "date": self.date, "msg": "Ok"}})
			logging.info("Report sent and stored!")
			return sys.exit(0)
		else:
			#self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": False, "date": self.date, "msg": "Unable to create report document"}})
			return sys.exit("Report failed")
	def export(self):
		self.load_project()
		self.create_dir()
		self.load_project()
		logging.info("Export")
		from export import generate
		if generate(self.name, self.data, self.format, self.directory):
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"export", "status": True, "date":dt.now(), "msg": "Exported"}})
			logging.info("Export done!")
			return sys.exit()
		else:
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"export", "status": False, "date": dt.now(), "msg": "Error while exporting"}})
			return sys.exit("Failed to export")

if __name__ == "crawtext":
	c = Crawtext(docopt(__doc__)["<name>"],docopt(__doc__), True)

	# if c.active:
	# 	c.show_task()
	#  	c.show_project()
	# 	c.set_crawler()
	# 	sys.exit(0)
