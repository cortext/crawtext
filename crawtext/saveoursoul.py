#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "crawtext"
__script_name__ = "saveoursoul"
__version__ = "4.3.1"
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

		#RESULTS
		self.results.nb = self.results.count()
		self.results.urls = self.results.distinct("url")
		# self.results.unique = len(self.results.urls)
		self.results.list = [self.results.find_one({"url":url}) for url in self.results.urls]

		#SOURCES
		self.sources.nb = self.sources.count()
		self.sources.urls = self.sources.distinct("url")
		# self.sources.unique = len(self.sources.urls)
		# self.sources.active_urls = [url for url in self.sources.urls if self.sources.find_one({"url":url})["status"][-1] is True]
		# self.sources.inactive_urls = [url for url in self.sources.urls if self.sources.find_one({"url":url})["status"][-1] is False]
		# self.sources.errors = [self.sources.find_one({"url":url})["msg"][-1] for url in self.sources.inactive_urls]
		self.sources.list = [self.sources.find_one({"url":url}) for url in self.sources.urls]


		#LOGS
		self.logs.nb = self.logs.count()
		self.logs.urls = self.logs.distinct("url")
		#self.logs.unique = len(self.logs.urls)

		# self.logs.errors = [self.logs.find_one({"url":url}) for url in self.logs.unique]
		#QUEUE
		self.queue.nb = self.queue.count()
		self.queue.urls = self.queue.distinct("url")
		#self.queue.unique = len(self.queue.urls)
		#self.queue.max_depth = max([self.queue.find_one({"url":url})["depth"] for url in self.queue.urls])
		self.queue.list = [self.queue.find_one({"url":url}) for url in self.queue.urls]
		#CRAWL INFOS
		self.crawl = self.project_db.use_coll('info')
		self.crawl.nb = len(self.sources.find_one({"url":self.sources.urls[-1]})["status"])
		# self.crawl.dates = [date[0].strftime("%d-%m-%Y@%H:%M:%S") for date in self.sources.find_one({"url":self.sources.urls[-1]})["date"]]
		# self.crawl.last_date = self.crawl.dates[-1]
		# self.crawl.first_date = self.crawl.dates[0]
		#self.crawl.max_depth = max([self.results.find_one({"url":url})["depth"] for url in self.results.urls])
		return self

if __name__ == "crawtext":
	print "Running"
	an = Analyzor(docopt(__doc__)["<name>"], True)
	if an.active:
		an.show_task()
		an.show_project()
		print "RRI_11"
	else:
		sys.exit()
	while an.queue.nb > 0:
		for item in an.queue.list:
			print item
			if item["url"] in an.results.urls:
				an.queue.remove(item)
			elif item["url"] in an.logs.urls:
				an.queue.remove(item)
			else:
				print "Treating", item["url"]
				p = Page(item["url"], item["source_url"],item["depth"], item["date"], True)
				if p.download():
					a = Article(p.url,p.html, p.source_url, p.depth,p.date, True)
					if a.extract():
						#if option == "filter":
						if a.filter(an.query, an.directory):
							if a.check_depth(a.depth):
								a.fetch_links()
								if len(a.links) > 0:
									for url, domain in zip(a.links, a.domains):
										if url not in an.queue.urls:
											an.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
											if an.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
										an.results.insert(a.export())

					else:
						print "Error Extracting"
						an.logs.insert(a.log())
				else:
					print "Error Downloading"
					an.logs.insert(p.log())
			print "Removing"
			an.queue.remove(item)
			print an.queue.nb
		if an.queue.nb == 0:
			break
		if an.results.count() > 200000:
			an.queue.drop()
			break
