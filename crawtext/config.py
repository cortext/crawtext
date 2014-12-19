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

MAX_DEPTH = 100
class Config(object):
	def __init__(self, name, job_type, debug=False):
		#project database manager
		self.debug = debug
		self.db = TaskDB()
		self.coll = self.db.coll
		self.name = name
		self.type = job_type
		self.msg = ""
		self.task = self.coll.find_one({"name":self.name, "type": self.type})

	
	def exists(self):	
		self.task = self.coll.find_one({"name":self.name, "type": self.type})
		if self.task is not None:
			return True
		else:
			print "No %s job %s found" %(self.type, self.name)
			return False

	def setup(self):
		if self.debug: print "Setup"
		if self.exists():
			if self.debug: print "Already exists"
			self.project_db = Database(self.task["project_name"])
			if self.type == "crawl":
				if self.debug: print "Setup Crawl"
				return self.crawl_config()
			elif self.type == "report":
				if self.debug: print "Setup Report"
				return self.report_config()
			elif self.type == "export":
				if self.debug: print "Setup Export"
				return self.report_config()
			else:
				print "Not config"
	
	def crawl_config(self):
		print "=====\nAdding parameters to configuration:"
		self.query = self.task["query"]
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
			self.max_depth = self.task["max_depth"]
		except KeyError:
			self.max_depth = MAX_DEPTH
		
		if len(error) < 3:
			return True
		else: 
			print "Error configuring sources" 
			return False
	
	def crawl_setup(self):
		print "=====\nCrawl configuration:"
		if self.exists():
			try:
				self.project_name = self.task["project_name"]
				self.project_db = Database(self.task["project_name"])
				self.project_db.set_colls()
				print "=====\nChecking configuration:"
				if self.check_sources() is False:
					return False
				
				if self.check_query() is False:
					return False

				else:
					self.check_depth()
					self.check_lang()	
					self.check_directory()
					if self.put_to_queue():
						if self.debug: print "Ok"
						return True
					else:

						return False
			except KeyError:
				self.msg = "No crawl project %s found" %(self.name)
				print self.msg
				return False
		return False
	
	def check_directory(self):
		try:
			self.directory = self.task['directory']
			if not os.path.exists(self.directory):
				os.makedirs(self.directory)
				index = os.path.join(self.directory, 'index')
				self.index_dir = os.makedirs('index')
				print "A specific directory has been created to store your projects\n Location:%s"	%(self.directory)
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
				print "A specific directory has been created to store your projects\n Location:%s"	%(self.directory)
				self.coll.update({"name": self.name, "type": self.type, "directory": self.directory})
			return True	
	
	def update_sources(self):
		print "updated sources"
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
		print "- Verifying sources:"
		self.update_sources()
		self.sources = self.project_db.use_coll("sources")
		sources_nb = self.sources.count()
		
		if sources_nb == 0:
			self.msg = "No sources in database"
			# self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config", "status": "False", "date": dt.now(), "msg": self.msg}})	
			print "No sources found\nHelp: You need at least one url into sources database to start crawl."
			return False
		else:
			# self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "True", "date": dt.now(), "msg": "Ok"}})
			print "\tx sources nb:", sources_nb
			return True

	def put_to_queue(self):
		print "Putting url to crawl"
		for item in self.project_db.sources.find():
			if item["url"] not in self.project_db.queue.distinct("url"):
				self.project_db.queue.insert(item)
			else:
				pass
		if self.project_db.queue.count() > 0:
			return True
		else:
			False

	def check_query(self):
		print "- Verifying query:"
		try:
			self.query = self.task["query"]
			self.check_directory()
			print "\tx query: %s" %self.query
			return True
		except KeyError:
			self.msg = "No query has been set. Unable to start crawl."	
			print self.msg
			return False

	def check_file(self):		
		try:
			self.file = self.task['file']
			print "-Verifying urls from file:"
			print "\tx file: %s" %self.file
			if self.add_file() is False:
				# self.msg = "Unable to add urls from file"
				# self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl: add sources from file", "status": False, "date": dt.now(), "msg": "Filename incorrect"}})
				return False
			else:
				return True
		except KeyError:
			return False	
		
	def check_bing(self):
		try:
			self.key = self.task['key']
			print "-Verifying key for Bing"
			if self.add_bing() is False:
	 			# self.msg = "Unable to add urls from search"
	 			# self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl: add sources from file", "status": False, "date": dt.now(), "msg": "API Key: Wrong credential for Search"}})
	 			return False
	 		return True
		except AttributeError, KeyError:
			return False
		
	def check_url(self):
		try:
			self.url = self.task['url']
			print "-Verifying input url:"

			if self.add_url(self.url,'manual',0):
		 		print "\tx",self.url, "added" 
		 	else:
		 		print "\tx",self.url, "updated"
		 	return True
		except KeyError:
			return False

	def check_depth(self):
		print "- Verifying defaut depth for crawl:"
		try:
			self.max_depth = self.task['max_depth']
			print "\tx maximum depth is set to:  %d" %(self.max_depth)
			
		except KeyError:
			self.max_depth = 100
			print "\tx defaut maximum depth is set to:  %d" %(self.max_depth)
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "True", "date": dt.now(), "msg": "Setting up defaut max_depth to 100"}})
			
	def check_lang(self):
		try:
			print "- Verifying language filter:"
			self.lang = self.task['lang']
			self.activ_lang = True
			print "\tx language filter is set to:", self.lang
		except KeyError:
			self.lang = 'default'
			self.activ_lang = False
			print "\tx language filter is INACTIVE"

	def reload_sources(self):
		if self.check_file() is False:
			error.append('file')
		elif self.check_bing() is False:
			error.append('bing')
		elif self.check_url() is False:
			error.append('url')
		if len(error) == 3:
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": False, "date": dt.now(), "msg": "No sources set by user"}})
			print "add url or key or file to you project:"
			print "\tpython crawtext.py %s add --url=\"yoururl.com/examples\"" %(self.project_name)
			print "\tpython crawtext.py %s add --file=\"seed_examples.txt\"" %(self.project_name)
			print "python crawtext.py %s add --key=\"3X4MPL3\""	%(self.project_name)		
			return False
		return True
	
	def add_url(self, url, origin="default", depth=0, source_url = None):
		'''Insert url into sources with its status inserted or updated'''
		self.sources = self.project_db.use_coll("sources")
		link = Link(url, source_url, depth, origin)
		exists = self.sources.find_one({"url": link.url})
		if exists is not None:
		 	print "\tx Url updated: %s \n\t\t>Status is set to %s" %(link.url, link.status)
		 	self.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(),"status": link.status, "step": link.step, "msg": link.msg}}, upsert=False)
		 	return False
		else:
			print "\tx Url added: %s \n\t\t>Status is set to %s" %(link.url, link.status)
			self.sources.insert({"url":link.url, "source_url":None, "origin": origin, "depth": 0, "date":[dt.now()], "step":["Added"], "status":[link.status], "msg":["inserted"]})
			exists = self.sources.find_one({"url": link.url})
			if exists is not None:
				self.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(),"status": link.status,"step": link.step, "msg": link.msg}}, upsert=False)
			return True
		
	def add_bing(self, nb = 50):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		import requests
		try:
			r = requests.get(
				'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
				params={
					'$format' : 'json',
					'$top' : 51,
					'Query' : '\'%s\'' %self.query,
				},	
				auth=(self.key, self.key)
				)
			
			r.raise_for_status()
			
			print "- Getting new sources from BING API Keys"
			results =  [self.add_url(e["Url"], "bing", 0) for e in r.json()['d']['results']]
			# if self.debug: print results, 

			new = [n for n in results if n is not False]
			# if self.debug: print len(new)
			# if self.debug: print status_b

			print "\tx %d urls inserted" %len(new)
			print "\tx %d urls updated" %(len(results)-len(new))
			return True
		
		except requests.exceptions.HTTPError as e:
			self.msg = "Wrong key authentication"
			return False

	def add_file(self):
		''' Method to extract url list from text file'''
		# self._log.step = "local file extraction"
		try:
			url_list = [re.sub("\n", "", n) for n in open(self.file).readlines()]
			i = 0
			y = 0
			print "-Adding urls from file"
			if len(url_list) == 0:
				print "x File %s is empty" %self.file
				return False
			
			results = [self.add_url(url, "file", 0) for url in url_list]
			new = [n for n in results if n is True]	
				
			print "\t-%d new urls has been inserted\n\t-%d urls updated" %(len(new), len(results)-len(new))
			return True
		
		except IOError, e:
			print "-Adding urls from file"
			print "x File does not exist"
			print "**********HELP***********\n"
		  	print "Please verify that your file is in the current directory."
		 	print "To set up a correct filename and add contained urls to sources database:"
		 	print "\t crawtext.py %s add --file =\"%s\"" %(self.name, self.file)
			print "Debug msg: %s" %str(e)
			print "*************************\n"
			self.msg = "File doesn't exists"
			return False

	def report_config(self):
		"Config for Report"
		pass
	def export_config(self):
		"Config for Export"
		pass