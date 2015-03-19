#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "crawtext"
__version__ = "4.3.1"
__author__= "constance@cortext.net"
__doc__ = '''Crawtext.

Description:
A simple crawler in command line for targeted websearch.

Usage:
	crawtext.py (<name>)
	crawtext.py <name> --query=<query> --key=<key> [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug]
	crawtext.py <name> (--url=<url>| --file=<file>) [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug]
	crawtext.py (<name>) delete
	crawtext.py (<name>) start
	crawtext.py (<name>) export
	crawtext.py (<name>) report [--user=<email>]
'''
import os, sys, re
import copy
from docopt import docopt
from datetime import datetime as dt
from database import *
from random import choice
import datetime
#from url import Link
from report import send_mail, generate_report
import hashlib
from article import Article, Page
from config_qd import *
from crawl import crawl


ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")
import logging
logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="crawtext.log", format=FORMAT, level=logging.DEBUG)
#search result nb from BING
MAX_RESULTS = 1000
#max depth
DEPTH = 100

class Worker(object):
	def __init__(self,user_input,debug=False):
		'''Job main config'''
		self.debug = debug
		logging.info("Init worker")
		self.name = user_input["<name>"]
		logging.info("Connecting to TaskDB")
		self.db = TaskDB()
		self.coll = self.db.coll
		if self.__exists__():
			logging.info("Updating?")
			if self.__parse_task__() is False:
				logging.info("Invalid parameters")
				sys.exit(__doc__)
			else:
				self.__parse__(user_input)
				self.__parse_task__()
				self.__activate__()	
		else:
			if self.__parse__(user_input):
				self.__create__()
				self.__exists__()
				self.__activate__()	
			else:
				logging.info("Invalid parameters")
				sys.exit(__doc__)			
		
				
	def __activate__(self):
		'''if action : activate the job else show the current project'''
		self.__create_directory__()
		self.__create_db__()
		print self.start
		if self.delete is True:
			'''delete project'''
			self.delete_project()
			return False

		elif self.export is True:
			'''export projects'''
			#return self.__export__()
			logging.info("Export... ")
			
			return False

		elif self.report is True:
			''' report project'''
			logging.info("Report... ")
			if self.user is not False:
				return self.report(self.user)
			else:
				return self.report(__author__)

		elif self.start is True:
			'''starting project'''
			logging.info("Running... ")
			sys.exit("Start")
			return self.__run__()
		else:
			return self.__show__()

	def __mapp__(self,user_input):
		''' mapping user_input into Object and returns the number of false XOR empty parameters'''
		for k, v in user_input.items():
			if v is None or v is False:
				setattr(self, re.sub("--|<|>", "", k), False)

			else:
				setattr(self, re.sub("--|<|>", "", k), v)
				#setting all empty attributes to False
		return len([v for v in user_input.values() if v is not None and v is not False])

	def __parse__(self, user_input):
		'''parsing user input for options and actions'''
		# logging.info(__doc__)
		print self.__mapp__(user_input)
		if self.name is not False:
			self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		else:
			logging.warning("Invalid parameters Please provide a name to your project")
		if self.__mapp__(user_input) > 1:
			return True
			'''
			if self.query is False:
				logging.info("No query activate open crawl?")
				if self.file is False and self.url is False:
					logging.warning("Invalid parameters: needs at leat a seed")
					return sys.exit("Invalid parameters: needs at leat a seed")
				else:
					self.type = "open_crawl"
					logging.info("Open crawl")
			else:
				if self.key is False or self.file is False or self.url is False:
					logging.warning("Invalid parameters need at least a seed .Please provide an (url, file or key)")
					sys.exit("Invalid parameters need at least a seed .Please provide an (url, file or key)")
				else:
					self.type = "crawl"
					logging.info("Normal crawl")
			return self.__config_crawl__()
			'''
		return False

	def __config_crawl__(self):
		#~ print self.user
		#~ self.report = bool(self.user)

		if self.nb is False or self.nb is None:
			self.nb = MAX_RESULTS
		if self.depth is False or self.depth is None:
			self.depth = DEPTH
		self.date = dt.now()
		return True

	def __parse_task__(self):
		'''mapping params from TASKDB'''
		if self.task is not None:
			for k, v in self.task.items():
				setattr(self, k, v)
			return self
		else:
			return False


	def __create_directory__(self):
		self.directory = os.path.join(RESULT_PATH, self.project_name)
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
			index = os.path.join(self.directory, 'index')
			try:
				self.index_dir = os.makedirs('index')
			except:
				pass
			logging.info("A specific directory has been created to store your projects\n Location:%s"	%(self.directory))

		return self.directory

	def __create_db__(self):
		self.project_db = Database(self.project_name)
		self.project_db.create_colls(["results", "logs", "sources", "queue"])
		return self.project_db

	def __create__(self):
		logging.info("creating a new task")
		new_task = self.__dict__.items()
		task = {}
		for k, v in new_task:
			logging.info("Creating from dict %s:%s" %(k,v))
			if k not in ["db", "coll"]:
				task[k] = v
		try:
			task["status"] = [True]
			task["msg"] = ["Sucessfully created"]
			task["date"] = [self.date]
			task["directory"] = self.__create_directory__(task["project_name"])
			self.coll.insert(task)
			logging.info("Task successfully created")
			self.task = self.coll.find_one({"name": self.name})
			return True

		except Exception as e:
			logging.warning("Task not created")
			logging.warning(e)
			return False

	def __update__(self):
		if self.__parse_task__() is not False:
			if self.query is not False and self.key is not False:
				self.update_sources()

	def __run__(self):
		print "Run!"
		#~ 
		#~ if self.type == "crawl":
			#~ logging.info("Hihi")
			#~ # crawl()
		#~ elif self.type =="open_crawl":
			#~ logging.info("Into the wild")
			#~ # wild_crawl()
#~ 
		#~ else:
			#~ logging.info("No idea")
		# self._report()
		# self.export()
		return
		''''
		if self.__exists__():
			self.key = self.task["key"]
			self.query = self.task["query"]
			self.project_name = self.task["project_name"]
			try:
				bool(self.project_db.sources.count() == 0)
			except AttributeError:
				self.__create_db__(self.task["project_name"])
				print self.project_db.sources.count()
			#update
			#~ if (self.task["date"][-1].day,self.task["date"][-1].month, self.task["date"][-1].year)  == (self.date.day, self.date.month, self.date.year):
				#~ self.__update__()
			print self.key
			print self.query
			if self.query is not False and self.key is not False:
				#put bing to sources and nexts urls to crawl
				check, results = self.get_bing_results( self.query, self.key, self.nb)
				if check:
					treated = self.push_to_queue()
					logging.info("%d urls put into queue" %len(treated))
					self.crawl(treated)
				else:
					logging.warning("Invalid credential")
					sys.exit()
			else:
				logging.warning("Invalid parameter check your key and your query")
				sys.exit()

		else:
			logging.info("Project doesn't exist yet. Create a new one!")
			sys.exit()
		'''

	def update_sources(self):
		'''updating sources'''
		self.__parse__(self.task)
		check, bing_sources = self.get_bing_results(self.query, self.key, self.nb)
		logging.info(check)
		if check is True:
			total_bing_sources = len(bing_sources)
			logging.info("%d sources i n BING" %total_bing_sources)
			logging.info("Inserting %d into sources" %total_bing_sources)
			for i,url in enumerate(bing_sources):
				exists = self.project_db.sources.find_one({"url":url})
				if exists is None:
					self.project_db.sources.insert({"url":url,
													"source_url": "https://api.datamarket.azure.com",
													"depth": 0,
													"nb":[i],
													"total":[total_bing_sources],
													"msg":["inserted"],
													"code": [100],
													"status": [True],
													"date": [self.date]
													})
				else:
					self.project_db.sources.udpate({"url":exists["url"]},
													{"$push":{"nb": i,
													"total":total_bing_sources,
													"msg":"udpated",
													"code": 100,
													"status": True,
													"date": self.date
													}})

		else:
			logging.info(bing_sources)
			return False

	def insert_into_sources(self):
		'''Bing results insert'''
		if self.project_db.sources.count() == 0:
			self.__create_db__()
		check, bing_sources = self.get_bing_results(self.query, self.key, self.nb)
		logging.info(check)
		if check is True:

			total_bing_sources = len(bing_sources)
			logging.info("%d sources i n BING" %total_bing_sources)
			logging.info("Inserting %d into sources" %total_bing_sources)
			for i,url in enumerate(bing_sources):
				self.project_db.sources.insert({"url":url,
												"source_url": "https://api.datamarket.azure.com",
												"depth": 0,
												"nb":i,
												"total":total_bing_sources,
												"msg":["inserted"],
												"code": [100],
												"status": [True]})
				return True
		else:
			logging.info(bing_sources)
			return False
	def wild_crawl(self, treated):
		crawl(self, treated, option=None)


	def crawl(self,treated, option="filter"):
		logging.info("Starting Crawl")
		self.__create__()
		while self.project_db.queue.count() > 0:
			for item in self.project_db.queue.find(timeout=False):
				if item["url"] not in treated and self.project_db.logs.find_one({"url":item["url"]}) is None and self.project_db.results.find_one({"url":item["url"]}) is None:
					p = Page(item["url"], item["source_url"],item["depth"], item["date"], self.debug)
					if p.download():
						a = Article(p.url,p.html, p.source_url, p.depth,p.date, self.debug)

						if a.extract():
							if option == "filter":
								if a.filter(self.query, self.directory):
									if a.check_depth(self.depth):
										a.fetch_links()
									if len(a.links) > 0:
										for url, domain in zip(a.links, a.domains):
											print url, domain
											self.project_db.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
									if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
									self.project_db.insert_result(a.export())
							else:
								if a.check_depth(self.depth):
									a.fetch_links()
								if len(a.links) > 0:
									for url, domain in zip(a.links, a.domains):
										print url, domain
										self.project_db.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
								if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
								self.project_db.insert_result(a.export())
						else:
							self.project_db.insert_log(a.log())
					else:
						self.project_db.insert_log(p.log())
					treated.append(item["url"])
				self.project_db.queue.remove({"url":item["url"]})
				if self.project_db.queue.count() == 0:
					break
				if self.project_db.results.count() > 200000:
					for n in self.project_db.results.find({"depth":max(self.project_db.results.distinct("depth"))}, timeout=False):
						self.project_db.results.remove({"_id":n["_id"]})
					logging.info("Max results exceeeded %d results now" %self.project_db.results.count())
					self.project_db.queue.drop()
					break
			if self.project_db.queue.count() == 0:
				break
		return True

	def push_to_queue(self):
		treated = []
		#put bing urls to crawl
		for item in self.project_db.sources.find():
			logging.info(item["url"])
			if item["url"] not in treated:
				p = Page(item["url"], item["source_url"],item["depth"], self.date, self.debug)
				if p.fetch():
					a = Article(p.url,p.html, p.source_url, p.depth,p.date, self.debug)
					if a.extract():
						a.fetch_links()
						for url, domain in zip(a.links, a.domains):
							if url not in treated:
								self.project_db.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
						print "\t-inserted %d nexts urls into queue" %len(a.links)
						self.project_db.insert_result(a.export())
						self.project_db.sources.update({"_id":item["_id"]}, {"$push":{"status": True, "msg":"Ok", "code": 100}})
					else:
						self.project_db.sources.update({"_id":item["_id"]}, {"$push":{"status": False, "msg":a.msg, "code": a.code}})
				else:
					self.project_db.sources.update({"_id":item["_id"]}, {"$push":{"status": False, "msg":p.msg, "code": p.code}})
				treated.append(item["url"])
		return treated

	def __exists__(self):
		self.task = self.coll.find_one({"name":self.name})
		if self.task is not None:
			logging.info("\nProject %s exists" %self.name)
			return True
		else:
			logging.info("\nProject %s doesn't exist" %self.name)
			return False

	def __show__(self,name=None):
		if name is not None:
			self.name = name
		self.task = self.coll.find_one({"name":self.name})
		if self.task is not None:
			print "\n===== Project : %s =====\n" %(self.name).capitalize()
			print "* Parameters"
			print "------------"
			for k, v in self.task.items():

				print k, ":", v
			print "\nProject database stats:"
			print "-Sources nb:", self.project_db.sources.count()
			print "-Queue nb:", self.project_db.queue.count()
			print "-Results nb:", self.project_db.results.count()
			if (self.project_db.sources.count(), self.project_db.queue.count(), self.project_db.results.count()) == (0,0,0):
				logging.info("Project has never been started up.\n Please launch start option")
				print "\n* Last Status"
				print "------------"
				print "- created but not started"
			#print "\n* Last Status"
			#print "------------"
			#print self.task["action"][-1], self.task["status"][-1],self.task["msg"][-1], dt.strftime(self.task["date"][-1], "%d/%m/%y %H:%M:%S")
			return
		else:
			logging.warning("No project found")
			sys.exit("No project found!")

	def get_bing_results(self, query, key, nb):
		''' Method to extract results from BING API (Limited to 5000 req/month) return a list of url'''
		try:
			count_results = self.project_db.sources.find()
		except AttributeError:
			self.__create_db__(self.task["project_name"])
			logging.info(self.project_db.sources.count())
		logging.info("Test database")
		print "Sources nb:", self.project_db.sources.count()
		print "Queue nb:", self.project_db.queue.count()
		print "Results nb:", self.project_db.results.count()
		start = 0
		step = 50
		if nb > MAX_RESULTS:
			logging.warning("Maximum search results is %d results." %MAX_RESULTS)
			nb = MAX_RESULTS

		if nb%50 != 0:
			nb = nb - (nb%50)
		web_results = []
		new = []
		inserted = []

		for i in range(0,nb, 50):

			try:
				r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
					params={'$format' : 'json',
						'$skip' : i,
						'$top': step,
						'Query' : '\'%s\'' %query,
						},auth=(key, key)
						)
				# logging.info(r.status_code)
				msg = r.raise_for_status()
				if msg is None:
					for e in r.json()['d']['results']:
						url = e["Url"]
						exists = self.project_db.sources.find_one({"url": e["Url"]})

						if exists is None:
							self.project_db.sources.insert({"url":e["Url"],
													"source_url": "https://api.datamarket.azure.com",
													"depth": 0,
													"msg":["inserted"],
													"code": [100],
													"status": [True],
													"date": [self.date]
													})
						else:
							self.project_db.sources.update({"url":exists["url"]},
													{"$push":{
													"msg":"udpated",
													"code": 100,
													"status": True,
													"date": self.date
													}})

					logging.info(self.project_db.sources.count())
				else:
					logging.warning("Req :"+msg)
			except Exception as e:
				logging.warning("Exception: "+str(e))
				return (False, str(e))
		return (True, web_results)
	
	def _report(self):
		logging.info("Report")
		# raise NotImplementedError
		return False
	def _export(self):
		logging.info("Export")
		# raise NotImplementedError
		return False

	def delete_project(self):
		if self.__exists__():
			self.delete_db()
			self.delete_dir()
			self.coll.remove({"_id": self.task['_id']})
			print "Project %s: sucessfully deleted"%(self.name)
			return True
		else:
			print "No crawl job %s found" %self.name
			return False

	def delete_dir(self):
		import shutil
		directory = os.path.join(RESULT_PATH, self.project_name)
		if os.path.exists(directory):

			print "We will delete this directory now!"

			shutil.rmtree(directory)
			print "Directory %s: %s sucessfully deleted"    %(self.name,directory)
			return True
		else:
			print "No directory found for crawl project %s" %(str(self.name))
			return False

	def delete_db(self):
		db = Database(self.project_name)
		db.drop_db()
		logging.info("Database %s: sucessfully deleted" %self.project_name)
		return True

def uniq(seq):
	checked = []
	for e in seq:
		if e not in checked:
			checked.append(e)
	logging.info("remove duplicate %d" %len(duplicate))
	return checked

w = Worker(docopt(__doc__))
