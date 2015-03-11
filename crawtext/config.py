#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Utilities for project configuration of a crawler
'''
import os, sys
ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
from database import TaskDB, Database
#from url import Link
from datetime import datetime as dt
from link import Link

import logging
logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="crawtext.log", format=FORMAT, level=logging.DEBUG)

MAX_DEPTH = 100
MAX_RESULTS = 1000

class Config(object):
	def __init__(self, name, job_type, debug=False):
		#project database manager
		self.debug = debug
		self.db = TaskDB()
		self.coll = self.db.coll
		self.name = name
		self.type = job_type
		self.msg = ""
		self.task = self.coll.find_one({"name":self.name, "type": self.type},timeout=False)
		self.date = dt.now()
    	# self.date = (self.date).replace(hour=0, minute=0, second=0, microsecond=0)

	def exists(self):
		self.task = self.coll.find_one({"name":self.name, "type": self.type},timeout=False)
		if self.task is not None:
			self.project_name = self.task["project_name"]
			return True
		else:
			logging.info("No %s job %s found" %(self.type, self.name))
			return False

	def setup(self):
		if self.debug: logging.info("Setup")
		if self.exists():
			if self.debug: logging.info("Already exists")
			self.project_db = Database(self.task["project_name"])
			if self.type == "crawl":
				if self.debug: logging.info("Setup Crawl")
				return self.crawl_config()
			elif self.type == "report":
				if self.debug: logging.info("Setup Report")
				return self.report_config()
			elif self.type == "export":
				if self.debug: logging.info("Setup Export")
				return self.report_config()
			else:
				logging.info("Not config")
		else:
			logging.info("No project %s found." %self.name)
			return False

	def crawl_config(self):
		'''verify if all required element are set query and key or file or url'''
		if self.exists():
			if self.debug : logging.info("Adding parameters to configuration:")
			self.query = self.task["query"]
			if self.check_query() is False:
				return False
			error = []
			try:
				self.file  = self.task["file"]
				self.check_file()
			except KeyError:
				error.append("file")
				pass
			try:
				self.key = self.task["key"]
				self.check_bing()


			except KeyError:
				error.append("bing")
				pass
			try:
				self.url = self.task["url"]
				self.check_url()
			except KeyError:
				error.append("url")
				pass
			try:
				self.max_depth = self.task["depth"]
			except KeyError:
				self.max_depth = MAX_DEPTH

			if len(error) < 3:
				return True
			else:
				logging.info("Error configuring sources")
				return False
		else:
			logging.info("No project %s found" %self.name)
			return False

	def crawl_setup(self):
		if self.debug : logging.info("=====\nCrawl configuration:")
		if self.exists():
			try:
				self.project_name = self.task["project_name"]
				self.project_db = Database(self.task["project_name"])
				self.project_db.set_colls()
				logging.info("=====\nChecking configuration:")
				if self.check_sources() is False:
					return False

				if self.check_query() is False:
					return False

				else:
					self.check_depth()
					self.check_lang()
					self.check_directory()
					if self.put_to_queue():
						if self.debug: logging.info("Ok")
						return True
					else:
						return False
			except KeyError:
				self.msg = "No crawl project %s found" %(self.name)
				if self.debug: logging.info(self.msg)
				return False
		else:
			self.msg = "No crawl project %s found" %(self.name)
			if self.debug: logging.info(self.msg)
			return False

	def check_directory(self):
		try:
			self.directory = self.task['directory']
			if not os.path.exists(self.directory):
				os.makedirs(self.directory)
				index = os.path.join(self.directory, 'index')
				self.index_dir = os.makedirs('index')
				if self.debug: logging.info("A specific directory has been created to store your projects\n Location:%s"%(self.directory))
			return True
		except KeyError:
			try:
				self.project_name = self.task["project_name"]
			except KeyError:
				self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
				self.coll.update({"name": self.name, "project_name": self.project_name})
			self.directory = os.path.join(ABSPATH, self.project_name)
			if not os.path.exists(self.directory):
				os.makedirs(self.directory)
				index = os.path.join(self.directory, 'index')
				self.index_dir = os.makedirs('index')
				logging.info("A specific directory has been created to store your projects\n Location:%s"	%(self.directory))
				self.coll.update({"name": self.name, "type": self.type, "directory": self.directory})
			return True

	def update_sources(self):
		if self.debug: logging.info("updated sources")
		try:
			self.file = self.task['file']
			self.add_file()
		except KeyError:
			pass
		try:
			self.key = self.task['key']
			self.query = self.task['query']
			self.add_bing()
		except KeyError:
			pass
		try:
			self.url = self.task['url']
			self.add_url(self.task['url'], "manual", 0)
		except KeyError:
			pass

	def check_sources(self):
		logging.info("- Verifying sources:")
		#self.update_sources()
		self.sources = self.project_db.use_coll("sources")
		sources_nb = self.sources.count()

		if sources_nb == 0:
			self.msg = "No sources in database"
			# self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config", "status": "False", "date": dt.now(), "msg": self.msg}})
			logging.info("No sources found\nHelp: You need at least one url into sources database to start crawl.")
			return False
		else:
			# self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "True", "date": dt.now(), "msg": "Ok"}})
			logging.info("\tx sources nb:", sources_nb)
			return True

	def put_to_queue(self):
		'''inserting sources to queue treatement'''
		logging.info("putting to queue")
		for item in self.project_db.sources.find():
			if self.debug : logging.info("Putting url to crawl", item["url"], item["status"][-1], item["depth"])
			if item["url"] not in self.project_db.queue.distinct("url"):
				#logging.info(item["url"])
				self.project_db.queue.insert(item)
			else:
				pass
		if self.project_db.queue.count() > 0:
			return True
		else:
			logging.info("No url to put in queue")
			return False

	def check_query(self):
		logging.info("- Verifying query:")
		try:
			self.query = self.task["query"]
			self.check_directory()
			logging.info("\tx query: %s" %self.query)
			return True
		except KeyError:
			self.msg = "No query has been set. Unable to start crawl."
			logging.info(self.msg)
			return False

	def check_file(self):
		try:
			self.file = self.task['file']
			logging.info("-Verifying urls from file:")
			logging.info("\tx file: %s" %self.file)
			if self.add_file() is False:
				self.msg = "Unable to add urls from file"
				# self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl: add sources from file", "status": False, "date": dt.now(), "msg": "Filename incorrect"}})
				return False
			else:
				return True
		except KeyError:
			return False

	def check_bing(self):
		try:
			self.key = self.task['key']
			logging.info("-Verifying key for Bing")
			if self.debug: logging.info(self.key)
			if self.add_bing() is False:
	 			self.msg = "Unable to add urls from search %s" %(self.resp)
	 			return False
	 		return True
		except AttributeError, KeyError:
			return False

	def check_url(self):
		try:
			self.url = self.task['url']
			logging.info("-Verifying input url:")

			if self.add_url(self.url,'manual',0):
		 		logging.info("\tx",self.url, "added")
		 	else:
		 		logging.info("\tx",self.url, "updated")
		 	return True
		except KeyError:
			return False

	def check_depth(self):
		logging.info("- Verifying defaut depth for crawl:")
		try:
			self.max_depth = int(self.task['depth'])
			logging.info("\tx maximum depth is set to:  %d" %(self.max_depth))

		except KeyError:
			self.max_depth = int(MAX_DEPTH)
			logging.info("\tx defaut maximum depth is set to:  %d" %(self.max_depth))
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "True", "date": self.date, "msg": "Setting up defaut max_depth to 100"}})

	def check_lang(self):
		try:
			logging.info("- Verifying language filter:")
			self.lang = self.task['lang']
			self.activ_lang = True
			logging.info("\tx language filter is set to: %s" %sself.lang)
		except KeyError:
			self.lang = 'default'
			self.activ_lang = False
			logging.info("\tx language filter is INACTIVE")

	def reload_sources(self):
		if self.check_file() is False:
			error.append('file')
		elif self.check_bing() is False:
			error.append('bing')
		elif self.check_url() is False:
			error.append('url')
		if len(error) == 3:
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": False, "date": self.date, "msg": self.msg}})
			print "add url or key or file to you project:"
			print "\tpython crawtext.py %s add --url=\"yoururl.com/examples\"" %(self.project_name)
			print "\tpython crawtext.py %s add --file=\"seed_examples.txt\"" %(self.project_name)
			print "\tpython crawtext.py %s add --key=\"3X4MPL3\"" %(self.project_name)
			return False
		return True

	def add_url(self, url, origin="default",depth=0, source_url = None, nb=0, nb_results=0):
		'''Insert url into sources with its status inserted or updated'''
		self.sources = self.project_db.use_coll("sources")
		if origin == "bing":
			exists = self.sources.find_one({"url": url})
			#~ logging.info(exists
			if exists is not None:
				self.sources.update({"_id":exists['_id']}, {"$push": {"date":self.date,"status": True, "step": "Updated", "nb": nb,"nb_results": nb_results, "msg": "Ok"}}, upsert=False)
				return False
			else:
				self.sources.insert({"url":url, "source_url":None, "origin": origin, "nb":[nb], "nb_results":[nb_results],"depth": 0, "date":[self.date], "step":["Added"], "status":[True], "msg":["Inserted"]})
				return True
		# 	pass
		else:
			link = Link(url, source_url, depth, origin)
			exists = self.sources.find_one({"url": link.url},timeout=False)
			if exists is not None:
			 	# logging.info("\tx Url updated: %s \n\t\t>Status is set to %s" %(link.url, link.status)
			 	self.sources.update({"_id":exists['_id']}, {"$push": {"date":self.date,"status": link.status, "step": link.step, "msg": link.msg}}, upsert=False)
			 	return False
			else:
				#logging.info("\tx Url added: %s \n\t\t>Status is set to %s" %(link.url, link.status)
				self.sources.insert({"url":link.url, "source_url":None, "origin": origin, "depth": 0, "date":[self.date], "step":["Added"], "status":[link.status], "msg":["inserted"]})
				# exists = self.sources.find_one({"url": link.url})
				# if exists is not None:
				# 	self.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(),"status": link.status,"step": link.step, "msg": link.msg}}, upsert=False)
				return True

	def add_bing(self, nb = MAX_RESULTS):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB '''
		import requests, time
		start = 0
		step = 50
		if nb > 1000:
			logging.info("Maximum search results is %d results." %MAX_RESULTS)
			nb = 1000


		if nb%50 != 0:
			logging.info("Nb of results must be a multiple of 50 not %d" %nb)
			nb = nb - (nb%50)
		web_results = []
		new = []
		inserted = []

		if self.debug: logging.info("Searching %i results" %nb)
		for i in range(0,nb, 50):
			r = requests.get(
					'https://api.datamarket.azure.com/Bing/Search/v1/Web',
					params={
						'$format' : 'json',
						'$skip' : i,
						'$top': step,
						'Query' : '\'%s\'' %self.query,
					},
					auth=(self.key, self.key)
					)
			# logging.info(r.status_code
			self.msg = r.raise_for_status()
			if self.msg is None:
				web_results.extend([e["Url"] for e in r.json()['d']['results']])
				results = [(x,y) for x,y in enumerate(web_results)]
				self.add_bing_results(results)
				#removing update
				# for i, url in results:
				# 	if self.add_url(url, origin="bing",depth=0, source_url = None, nb=i, nb_results=len(results)) is True:
				# 		new.append(url)
				# 	else:
				# 		inserted.append(url)
			else:
				return False
		logging.info("%i urls added"%(len(results)))
		return True

	def add_bing_results(self, results_list):
		'''simple insert into sources db'''
		self.sources = self.project_db.use_coll("sources")
		logging.info("adding bing results %d" %len(results_list))
		for i,url in enumerate(results_list):
			exists = self.sources.find_one({"url": url})
			#~ logging.info(exists
			if exists is not None:
				pass
			else:
				self.sources.insert({"url":url, "source_url":"bing.com", "origin": "bing", "nb":i, "nb_results":len(results_list),"depth": 0, "date":[self.date], "step":["Added"], "status":[True], "msg":["Inserted"]})
				return True

	def add_file(self):
		''' Method to extract url list from text file'''
		# self._log.step = "local file extraction"
		try:
			url_list = [re.sub("\n", "", n) for n in open(self.file).readlines()]
			i = 0
			y = 0
			logging.info("-Adding urls from file")
			if len(url_list) == 0:
				logging.info("x File %s is empty" %self.file)
				return False

			results = [self.add_url(url, "file", 0) for url in url_list]
			new = [n for n in results if n is True]

			logging.info("\t-%d new urls has been inserted\n\t-%d urls updated" %(len(new), len(results)-len(new)))
			return True

		except IOError, e:
			logging.info("-Adding urls from file")
			logging.info("x File does not exist")
			logging.info("**********HELP***********\n")
		  	logging.info("Please verify that your file is in the current directory.")
		 	logging.info("To set up a correct filename and add contained urls to sources database:")
		 	logging.info("\t crawtext.py %s add --file =\"%s\"" %(self.name, self.file))
			logging.info("Debug msg: %s" %str(e))
			logging.info("*************************\n")
			self.msg = "File doesn't exists"
			return False

	def report_config(self):
		"Config for Report"
		pass
	def export_config(self):
		"Config for Export"
		pass

	def flush(self):
		if self.exists():
			try:
				self.project_name = self.task["project_name"]
				self.project_db = Database(self.task["project_name"])
			except Exception:
				logging.info("No project %s found" %self.name)
				return False
		self.queue = self.project_db.use_coll("queue")
		sources_nb = self.queue.count()
		self.queue.drop()
		logging.info(sources_nb+" deleted")
		return True
