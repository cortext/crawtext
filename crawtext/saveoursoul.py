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
	crawtext.py (<name>)
	crawtext.py <name> --query=<query> --key=<key> [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug]
	crawtext.py <name> (--url=<url>| --file=<file>) [--query=<query>] [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug]
	crawtext.py (<name>) delete
	crawtext.py (<name>) start
	crawtext.py (<name>) restart
	crawtext.py (<name>) export [--data=<data>] [--format=<format>]
	crawtext.py (<name>) report [--user=<email>] [--format=<format>]
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

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")
#search result nb from BING
MAX_RESULTS = 1000
#max depth
DEPTH = 100

class Analyzor(object):
	def __init__(self, name, debug):
		self.name = name
		self.debug = debug
		self.task_db = TaskDB()
		self.coll = self.task_db.coll
		self.task = self.coll.find_one({"name":name})
		if self.task is None:
			self.active = False
		else:
			self.active = True

		delattr(self, "task_db")
		delattr(self, "coll")

	def show_task(self):
		for k, v in self.task.items():
			if k == "date":
				pass
			elif type(v) == list:
				print "*", k,":"
				for item in v:
					if type(item) == list:
						for n in item:
							print "\t\t-", n
					else:
						print "\t", item

			else:
				print "*", k,":", v
				setattr(self, k, v)


	def show_project(self):
		self.project_db = Database(self.name)
		self.results = self.project_db.use_coll('results')
		self.sources = self.project_db.use_coll('sources')
		self.logs = self.project_db.use_coll('logs')
		self.queue = self.project_db.use_coll('queue')
		print "Mapping project DB"
		#RESULTS
		self.results.nb = self.results.count()
		self.results.urls = self.results.distinct("url")

		# self.results.unique = len(self.results.urls)
		#self.results.list = [self.results.find_one({"url":url}) for url in self.results.urls]

		#SOURCES
		#self.sources.nb = self.sources.count()
		self.sources.urls = self.sources.distinct("url")
		#self.sources.unique = len(self.sources.urls)
		self.sources.active_urls = [url for url in self.sources.urls if self.sources.find_one({"url":url})["status"][-1] is True]
		#self.sources.inactive_urls = [url for url in self.sources.urls if self.sources.find_one({"url":url})["status"][-1] is False]
		#self.sources.errors = [self.sources.find_one({"url":url})["msg"][-1] for url in self.sources.inactive_urls]
		self.sources.list = [self.sources.find_one({"url":url}) for url in self.sources.active_urls]


		#LOGS
		#self.logs.nb = self.logs.count()
		self.logs.urls = self.logs.distinct("url")
		#self.logs.unique = len(self.logs.urls)

		#self.logs.errors = [self.logs.find_one({"url":url}) for url in self.logs.urls]
		#QUEUE
		#self.queue.nb = self.queue.count()
		self.queue.urls = self.queue.distinct("url")
		#self.queue.unique = len(self.queue.urls)
		# try:
		# 	self.queue.max_depth = max([self.queue.find_one({"url":url})["depth"] for url in self.queue.urls])
		# except ValueError:
		# 	pass
		#self.queue.list = [self.queue.find_one({"url":url}) for url in self.queue.urls]
		#CRAWL INFOS
		self.crawl = self.project_db.use_coll('info')
		#self.crawl.nb = len(self.sources.find_one({"url":self.sources.urls[-1]})["status"])
		#self.crawl.dates = [date[0].strftime("%d-%m-%Y@%H:%M:%S") for date in self.sources.find_one({"url":self.sources.urls[-1]})["date"]]
		#self.crawl.last_date = self.crawl.dates[-1]
		#self.crawl.first_date = self.crawl.dates[0]
		#self.crawl.max_depth = max([self.results.find_one({"url":url})["depth"] for url in self.results.urls])

		for url in self.results.urls:
			item = self.results.find_one({"url":url})
			if item["depth"] <=2:
				self.results_max_depth2.append(item["depth"])

		return self

	def set_crawler(self):
		if (self.query, self.key, self.url, self.file) == (False, False, False, False):
			logging.info("Invalid parameters task should have at least one seed (file, url or API key for search)")
			return sys.exit(1)
		elif (self.query, self.key, self.url) == (False, False, True):
			self.crawl_type = "open_crawl"
			return self
		elif (self.query, self.key, self.file) == (False, False, True):
			self.crawl_type = "open_crawl"
			return self
		elif (self.query, self.key) == (True, True):
			self.crawl_type = "targeted_crawl"
			return self
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
		if self.query is False:
			logging.info("No query provided")
			sys.exit(1)
		elif self.key is False:
			logging.info("No key provided")
			sys.exit(1)

		elif self.query is not False and self.key is not False:
			if self.nb is False:
				self.nb = MAX_RESULTS

			if self.nb > MAX_RESULTS:
				logging.warning("Maximum search results is %d results." %MAX_RESULTS)
				self.nb = MAX_RESULTS

			if self.nb%50 != 0:
				self.nb = self.nb - (self.nb%50)

			bing_sources =  self.bing_search()
			if bing_sources is not False:
				total_bing_sources = len(bing_sources)
				for i,url in enumerate(bing_sources):
					self.sources.insert({"url":url,
													"source_url": "search",
													"depth": 0,
													"nb":i,
													"total":total_bing_sources,
													"msg":["inserted"],
													"code": [100],
													"status": [True]})
				logging.info("%i urls from BING search inserted")


	def crawler(self):
		self.queue.list = self.sources.list
		while self.queue.nb > 0:
			for item in self.queue.list:
				print item
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
							#if option == "filter":
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
									a.msg = "Depth exceed"
									self.logs.insert(a.log())
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
			if self.results.count() > 200000:
				self.queue.drop()
				break


if __name__ == "crawtext":
	an = Analyzor(docopt(__doc__)["<name>"], True)
	print docopt(__doc__)["<name>"]
	# if an.active:
	# 	an.show_project()
	an.show_project()
	an.crawler()

	# print an.crawl.max_depth
	# print an.queue.max_depth
	sys.exit()
