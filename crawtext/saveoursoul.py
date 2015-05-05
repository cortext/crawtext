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
	crawtext.py (<name>) [--debug]
	crawtext.py (<name>) --query=<query> --key=<key> [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug] [--repeat=(day|week|month)]
	crawtext.py (<name>) (--url=<url>| --file=<file>) [--query=<query>] [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug]
	crawtext.py (<name>) delete [--debug]
	crawtext.py (<name>) start [--debug]
	crawtext.py (<name>) restart [--debug]
	crawtext.py (<name>) export [--data=<data>] [--format=<format>] [--debug]
	crawtext.py (<name>) report [--user=<email>] [--format=<format>] [--debug]
	crawtext.py (<name>) stop [--debug]
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
		self.project_path = os.path.join(RESULT_PATH, name)
		if self.config_task(user_input) is True:
			print "COnfig from ui"
			self.load_ui(user_input)
			if self.task_exists():
				print "Update"
				self.coll.remove({"name":name})
			else:
				print "create"
			new_task = self.__dict__
			del new_task['coll']
			del new_task['task_db']
			self.coll.insert(new_task)
			self.show_project()
			sys.exit()
		else:
			if self.task_exists():
				self.dispatch()
				sys.exit()
			else:
				sys.exit("No configuration found for project")

	def config_task(self,ui):
		if len([v for v in ui.values() if v != None and v != False]) > 1:
			return True
		return False

	def task_exists(self):
		print "task exists"
		self.task_db = TaskDB()
		self.coll = self.task_db.coll
		print self.coll
		self.task = self.coll.find_one({"name":self.name})
		if self.task is None:
		 	return False
		return True

	def dispatch(self):
		if self.stop is True:
			print "stop"
			raise NotImplementedError
		elif self.restart is True:
			print "restart"
			raise NotImplementedError
		elif self.export is True:
			print "export"
			raise NotImplementedError
		elif self.report is True:
			print "report"
			raise NotImplementedError
		elif self.load_config() is not False:

			#if (self.url, self.file, self.key) != (False, False, False):
			#if (self.url != False)|(if self.file != False) | if (self.key != False):
				self.start_crawl()
				return sys.exit()
		else:
			self.show_task()
			self.show_stats()
			return sys.exit()



	def load_ui(self, ui):

		for k, v in ui.items():
			k = re.sub("--|<|>", "", k)
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
			else:
				if v is None or v is False:
					setattr(self, k, False)
				else:
					setattr(self, k, v)
		return bool(len([k for k, v in ui.items() if v is not None and v is not False])> 1)


	def load_config(self):
		self.active = True
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
			else:
				if v is None or v is False:
					setattr(self, k, False)
				else:
					setattr(self, k, v)
			return self

	def start_crawl(self):
		logging.info("start")
		self.load_project()
		if self.url is not False:
			return self.set_crawler()
		elif self.file is not False:
			return self.set_crawler()
		elif (self.query,self.key) != (False,False):
			return self.set_crawler()

	def show_task(self):
		for k, v in self.__dict__.items():
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

		return self

	def show_stats(self):
		try:
			print "********\n"
			print "SOURCES:"
			print "- Nb Sources indexées: %i" %self.sources.unique
			print "\t- pertinentes: %i" %self.sources.active_urls.nb
			print "\t- non-pertinentes: %i" %self.sources.inactive_urls.nb
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

	def load_project(self):
		self.project_db = Database(self.name)
		self.results = self.project_db.use_coll('results')
		self.sources = self.project_db.use_coll('sources')
		self.logs = self.project_db.use_coll('logs')
		self.queue = self.project_db.use_coll('queue')
		print "Mapping project DB"
		#RESULTS
		self.results.nb = self.results.count()
		self.results.urls = self.results.find().distinct("url")
		self.results.unique = len(self.results.urls)
		#self.results.list = [self.results.find_one({},{"url":url}) for url in self.results.urls]
		#print self.results.list

		#SOURCES
		self.sources.nb = self.sources.count()
		self.sources.urls = self.sources.distinct("url")
		self.sources.unique = len(self.sources.urls)
		self.sources.list = [self.sources.find_one({"url":url}) for url in self.sources.urls]
		self.sources.active = self.project_db.use_coll('info')
		self.sources.active.list = [n for n in self.sources.list if n["status"][-1] is True]

		self.sources.active.nb = len(self.sources.active.list)
		self.sources.inactive = self.project_db.use_coll('info')
		self.sources.inactive.list = [n for n in self.sources.list if n["status"][-1] is False]
		self.sources.inactive.nb = len(self.sources.inactive.list)

		# self.sources.list = self.sources.active.list
		#LOGS
		self.logs.nb = self.logs.count()
		self.logs.urls = self.logs.distinct("url")
		self.logs.unique = len(self.logs.urls)
		#self.logs.list = [self.logs.find_one({},{"url":url}) for url in self.logs.urls]
		#QUEUE
		self.queue.nb = self.queue.count()
		self.queue.urls = self.queue.distinct("url")
		self.queue.unique = len(self.queue.urls)
		self.queue.list = [self.queue.find_one({},{"url":url}) for url in self.queue.urls]
		self.queue.max_depth = self.queue.find_one(sort=[("depth", -1)])
		#self.queue.dates = self.queue.find({"date":{"$exists":"True"}})
		#print self.queue.dates
		#CRAWL INFOS
		self.crawl = self.project_db.use_coll('info')
		self.crawl.nb = self.queue.unique+self.logs.unique+self.sources.active.nb
		return self

	def set_crawler(self):
		if (self.query, self.key, self.url, self.file) == (False, False, False, False):
			#logging.info("Invalid parameters task should have at least one seed (file, url or API key for search)")
			return sys.exit("Invalid parameters task should have at least one seed (file, url or API key for search)")
		elif (self.query, self.key, self.url) == (False, False, True):
			self.upsert_url(self.url, "manual")
			return self.crawler(filter="off")

		elif (self.query, self.key, self.file) == (False, False, True):
			self.upsert_file()
			return self.crawler(filter="off")

		elif (self.query, self.key) != (False, False):
			if self.sources.unique == 0:
				self.get_seeds()
			elif self.repeat is not False:
				self.update_seeds()

			return self.crawler(filter="on")
		else:
			if self.query is False:
				sys.exit("No query provided. Please add one")
			elif self.key is False:
				sys.exit("No BING API key provided")
			else:
				sys.exit("Invalid parameters")

	def update_crawl(self):
		raise NotImplementedError

	def bing_search(self):
		web_results = []
		for i in range(0,self.nb, 50):

			#~ try:
			r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
				params={'$format' : 'json',
					'$skip' : i,
					'$top': step,
					'Query' : '\'%s\'' %self.query,
					},auth=(self.key, self.key)
					)

			#logging.info(r.status_code)

			msg = r.raise_for_status()
			if msg is None:
				for e in r.json()['d']['results']:
					print e["Url"]
					web_results.append(e["Url"])

		if len(web_results) == 0:
			return False
		return web_results

	def get_seeds(self):
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
			for i,url in enumerate(bing_sources):
					self.sources.insert({
											"url":url,
											"source_url": "search",
											"depth": 0,
											"nb":i,
											"total":total_bing_sources,
											"msg":["inserted"],
											"code": [100],
											"status": [True]
										})
			logging.info("%i urls from BING search inserted")
			return self
		else:
			logging.warning("Bing search for source failed")
			return self

	def upsert_url(self, url, source_url):
		if exists is None:
			self.project_db.sources.insert({"url":url,
											"source_url": source_url,
											"depth": 0,
											"msg":["inserted"],
											"code": [100],
											"status": [True],
											"date": [self.date]
											})
		else:
			self.project_db.sources.update({"url":exists["url"]},
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

	def crawler(self, filter="off"):
		self.queue.list = self.sources.active.list
		while self.queue.nb > 0:
			for item in self.queue.list:
				if item["url"] in self.results.urls:
					self.queue.remove(item)
				elif item["url"] in self.logs.urls:
					self.queue.remove(item)
				else:
					print "Treating", item["url"], item["depth"]
					p = Page(item["url"], item["source_url"],item["depth"], item["date"], True)
					if p.download():
						a = Article(p.url,p.html, p.source_url, p.depth,p.date, True)
						if a.extract():
							if filter == "on":
								if a.filter(self.query, self.directory):
									if a.check_depth(a.depth):
										a.fetch_links()
										if len(a.links) > 0:
											for url, domain in zip(a.links, a.domains):
												if url not in self.queue.urls:
													self.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
													if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
												self.results.insert(a.export())
									else:
										self.logs.insert(a.log())
								else:
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
									self.logs.insert(a.log())
						else:
							print "Error Extracting"
							self.logs.insert(a.log())
					else:
						print "Error Downloading"
						self.logs.insert(p.log())
					print "Removing"
					self.queue.remove(item)
					print self.queue.nb
				if self.queue.nb == 0:
					break
			if self.queue.nb == 0:
				break
			if self.results.count() > 200000:
				self.queue.drop()
				break

		return self.show_stats()


if __name__ == "crawtext":
	c = Crawtext(docopt(__doc__)["<name>"],docopt(__doc__), True)

	# if c.active:
	# 	c.show_task()
	#  	c.show_project()
	# 	c.set_crawler()
	# 	sys.exit(0)
