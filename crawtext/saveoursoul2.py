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
	def __init__(self, name):
		self.name = name
		self.task_db = TaskDB()
		self.coll = self.task_db.coll
		self.task = self.coll.find_one({"name":name})
		delattr(self, "task_db")
		delattr(self, "coll")

	def show_task(self):
		for k, v in self.task.items():

			if type(v) == list:
				print "*", k,":"
				for item in v:
					print "\t-", item

			else:
				print "*", k,":", v

	def show_project(self):

		self.project_db = Database(self.name)
		self.results = self.project_db.use_coll('results')
		self.sources = self.project_db.use_coll('sources')
		self.logs = self.project_db.use_coll('logs')
		self.queue = self.project_db.use_coll('queue')

		#RESULTS
		self.results.nb = self.results.count()
		self.results.urls = self.results.distinct("url")
		self.results.unique = len(self.results.urls)
		#SOURCES
		self.sources.nb = self.sources.count()
		self.sources.urls = self.sources.distinct("url")
		self.sources.unique = len(self.sources.urls)
		self.sources.active_urls = [url for url in self.sources.urls if self.sources.find_one({"url":url})["status"][-1] is True]
		self.sources.inactive_urls = [url for url in self.sources.urls if self.sources.find_one({"url":url})["status"][-1] is False]
		self.sources.errors = 
		#LOGS
		self.logs.nb = self.logs.count()
		self.logs.urls = self.logs.distinct("url")
		self.logs.unique = len(self.logs.urls)
		#QUEUE
		self.queue.nb = self.queue.count()
		self.queue.urls = self.queue.distinct("url")
		self.queue.unique = len(self.queue.urls)
		#CRAWL INFOS
		self.crawl = self.results
		self.crawl.nb = len(self.sources.find_one({"url":self.sources.urls[-1]})["status"])
		self.crawl.dates = [date[0].strftime("%d-%m-%Y@%H:%M:%S") for date in self.sources.find_one({"url":self.sources.urls[-1]})["date"]]
		self.crawl.last_date = self.crawl.dates[-1]
		self.crawl.first_date = self.crawl.dates[0]

if __name__ == "crawtext":
	a = Analyzor("RRI_10_ET_05")
	a.show_task()
	a.show_project()
