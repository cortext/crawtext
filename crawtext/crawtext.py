#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "crawtext"
__version__ = "4.2.0b1"
__doc__ = '''Crawtext.
Description:
A simple crawler in command line.

Usage:
	crawtext.py (<name>)
	crawtext.py (<name>) (--query=<query>) (--key=<key> |--file=<file> [--nb=<nb>] |--url=<url>) [--mode=(hard|soft)] [--user=<email>] [--r=<repeat>] [--depth=<depth>]
	crawtext.py <name> add [--url=<url>] [--file=<file>] [--key=<key>] [--user=<email>] [--r=<repeat>] [--option=<expand>] [--depth=<depth>] [--nb=<nb>]
	crawtext.py <name> delete [-q] [-k] [-f] [--url=<url>] [-u] [-r] [-d]
	crawtext.py (<name>) report [-email] [--user=<email>] [--r=<repeat>]
	crawtext.py (<name>) export [--format=(csv|json)] [--r=<repeat>]
	crawtext.py (<name>) start [--maxdepth=<depth>]
	crawtext.py (<name>) stop
	crawtext.py (<name>) toobig
	crawtext.py (-h | --help)	
'''

import os, sys, re
from docopt import docopt
from datetime import datetime as dt
from database import *
from random import choice
import datetime
from url import Link
from report import send_mail, generate_report
import hashlib
DEBUG = False


ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")

class Worker(object):
	def __init__(self,user_input,debug=False):
		'''Job main config'''
		self.debug = debug
		if self.debug:
			print "self.debug init"
		self.db = TaskDB()
		self.coll = self.db.coll
		self.user_input = user_input
		self.name = self.user_input['<name>']
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		del self.user_input['<name>']
		if not os.path.exists(RESULT_PATH):
			os.makedirs(RESULT_PATH)
			print "Directory created to store your projects\n Location:%s"	%(RESULT_PATH)
			
		
	def dispatch(self):
		params = dict()
		action = None
		for k,v in self.user_input.items():
			if v is not None and v is not False:
				if k.startswith("-"):
					params[k] = v
				else:
					action = k
		del self.user_input

		if action is None:
			if len(params) == 0:
				return self.show()
			else:
				return self.create(params)
		else:
			if self.debug is True:
				print "dispatch", action, params
			job = getattr(self, str(action))
			return job(params)
				
	def exists(self):
		self.task = self.coll.find_one({"name":self.name})
		if self.task is not None:
			return True
		else:
			return False

	def clean_params(self, params):
		p = dict()
		for k,v in params.items():
			k = re.sub("--", "", k)
			p[k] = v
		return p

	def clean_options(self, options):
		opt = {"-q":"query","-k":"key","-f":"file","-u":"user","-r":"repeat", "--url":"url", "-d":"depth", "--mode": "mode"}
		for k,v in options.items():
			if k in opt.keys():
				del options[k]
				if v is True:
					options[opt[k]] = ""
				else:
					options[opt[k]] = v
		return options

	def show(self):
		if self.exists():
			print "\n===== Project : %s =====\n" %(self.name).capitalize()
			print "* Parameters"
			print "------------"
			for k, v in self.task.items():
				if k not in ['status', 'msg', 'action', 'date', '_id']:
					print k, ":", v 
			print "\n* Last Status"
			print "------------"
			print self.task["action"][-1], self.task["status"][-1],self.task["msg"][-1], dt.strftime(self.task["date"][-1], "%d/%m/%y %H:%M:%S")
			return True	
		else:
			print "No crawl job %s found" %self.name
			return False	

	def report(self, params):
		if self.exists():
			db = Database(self.task['project_name'])
			params = self.clean_params(params)
			if len(params)!= 0:
				self.coll.update({"_id":self.task["_id"]},{"$set":params})
			else:
				try:
					format = self.task['format']
				except KeyError:
					format = "email"
					
				if format == "email":
					try:
						user = self.task['user']
						if send_mail(user, db) is True:
							print "A report email has been sent to %s\nCheck your mailbox!" %user
							self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":True, "date": dt.now(), "msg": "Ok"}})
								
						else:
							self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":False, "date": dt.now(), "msg": "Error while sending the mail"}})
					except KeyError:
						print "No user has been set: \ndeclare a user email for your project to receive it by mail."
						self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":False, "date": dt.now(), "msg": "User email unset, unable to send mail"}})
						
				if generate_report(self.task, db):
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": True, "date": dt.now(), "msg": "Ok"}})
					return True
				else:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": False, "date": dt.now(), "msg": "Unable to create report document"}})
					return False
		else:
			print "No crawl job %s found" %self.name
		return False

	def export(self,params):
		from export import generate
		if self.exists():
			self.directory = self.create_dir()
			for k,v in params.items():
				params[re.sub("--", "", k)] = v
			print generate(self.name, params, self.directory)	
			return True
		else:
			print "No crawl job %s found" %self.name
			return False

	def create_dir(self):
		
		self.directory = os.path.join(RESULT_PATH, self.project_name)
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
			print "Directory for %s created\n Location:%s"	%(self.name, self.directory)
		return self.directory

	def create(self, params):

		if self.exists():
			print "Crawl project %s already exists:" %self.name
		else:
			params = self.clean_params(params)
			params["name"] = self.name
			params["project_name"] = self.project_name
			params["type"] = "crawl"
			params["action"] = ["create"]
			params["directory"] = self.create_dir()
			params["creation_date"] = dt.now()
			params["depth"] = 10
			params["date"] = [dt.now()]
			params["status"] = ["True"]
			params["msg"] = ['Ok']
			self.coll.insert(params)
			if self.exists():
				self.query = params["query"]
				try:
					self.file  = params["file"]
					self.check_file()
				except KeyError:
					pass
				try:
					self.key = params["key"]
					self.check_bing()
				except KeyError:
					pass
				try:
					self.url = params["url"]
					self.check_url()
				except KeyError:
					pass			
				print "Created a new crawl job called %s" %self.name
		return self.show()

	def add(self, params):
		if self.exists():
			if len(params) != 0:
				params = self.clean_params(params)
				action = "add: %s" %(",".join(params.keys()))
				date = dt.now()
				status = True
				try:
					self.coll.update({"_id": self.task['_id']}, {"$set": params})
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":action, "status": status, "date": date, "msg":'Ok'}})	
					print "Sucessfully added parameters %s from %s crawl job" %(",".join(params.keys()), self.name)
					self.update_sources(params)
					
				except Exception, e:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":action, "status": False, "date": date, "msg": str(e)}})	
			else:
				print "Nothing to add to crawl job %s" %self.name
				
			return self.show()
		else:
			print "No crawl job %s found" %self.name
			return False

	def update_sources(self, params):
		update = [n for n in params.keys() if n in ["file", "url", "key"]]
		if len(update) != 0:
			for n in update:		
				if n == "file":
					if self.check_file() is False:
						print "Error no url from file %s has been added to sources" %params[n]
				elif n == "url":
					if self.check_url() is False:
						print "Error no url has been added"
				else:
					self.query = self.task["query"]
					if self.check_bing() is False:
						print "Error no url from search result has been added"
		return

	def delete(self, params):
		if self.exists():	
			if len(params) != 0:
				params = self.clean_options(params)
				values = ",".join(params.keys())
				self.coll.update({"_id": self.task['_id']}, {"$unset": params})
				try:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":str("delete: "+ values), "status": True, "date": dt.now(), "msg": "Ok"}})	
					print "Sucessfully deleted parameters %s from %s crawl job" %(values, self.name)
				except Exception, e:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":action, "status": False, "date": date, "msg": e}})	
				return self.show()
			else:
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
			print "Directory %s: %s sucessfully deleted"	%(self.name,directory)
			return True
		else:
		 	print "No directory found for crawl project %s" %(str(self.name))
			return False

	def delete_db(self):
		db = Database(self.project_name)
		db.drop_db()
		print "Database %s: sucessfully deleted" %self.project_name
		return True
			
	def start(self, params):
		if self.exists():
			print "Starting project"
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"start crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
			print "Config"
			if self.config() is False:
				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": False, "date": dt.now(), "msg": "Ok"}})
				return
			else:
				self.check_mode()
				if self.crawl(self.mode):
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"run crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
				else:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"run crawl", "status": False, "date": dt.now(), "msg": "Ok"}})
				return
		else:
			print "No crawl job %s found" %self.name
			return
				
	def check_query(self):
		print "- Verifying query:"
		try:
			self.query = self.task["query"]
			print "- query: %s" %self.query
			return True
		except KeyError:
			print "No query has been set. Unable to start crawl."	
			return False
	
	def check_file(self):
		try:
			self.file = self.task['file']
			print "Adding urls from file: %s " %self.file
			if self.add_file() is False:
				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl: add sources from file", "status": False, "date": dt.now(), "msg": "Filename incorrect"}})
				return False
		except KeyError:
			return False	
		
	def check_bing(self):
		try:
			self.key = self.task['key']
		except AttributeError, KeyError:
			return False
		print "Adding sources from search results on : %s" %self.query
		if self.add_bing() is False:
	 		self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl: add sources from file", "status": False, "date": dt.now(), "msg": "API Key: Wrong credential for Search"}})
	 		return False
	 	return True
		
	def check_url(self):
		try:
			self.url = self.task['url']
			print "Adding source from the given url: %s" %self.url
			if self.add_url(self.url,'manual',0):
		 		print "\t- inserted" 
		 	else:
		 		print "\t- updated"
		except KeyError:
			return False
	
	def check_depth(self):
		try:
			self.max_depth = self.task['max_depth']
			print "Adding depth %d for user params" %(self.max_depth)
			return False
		except KeyError:
			self.max_depth = 10
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "True", "date": dt.now(), "msg": "Setting up defaut max_depth to 10"}})
			return True 

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
			print "\tpython crawtext.py %s add --url=\"yoururl.com/examples\""
			print "\tpython crawtext.py %s add --file=\"seed_examples.txt\""
			print "python crawtext.py %s add --key=\"3X4MPL3\""			
			return False
	def check_mode(self):
		try:
			self.mode = self.task["mode"]	
		except KeyError:
			self.mode = "soft"	
		return self.mode	
	
	def config(self):
		print "Checking configuration:"
		if self.check_query() is False:
			return False
		else:
			self.check_depth()
			print "- Verifying sources:"
			db = Database(self.project_name)
			sources = db.use_coll("sources")
			sources_nb = sources.count()
			print sources_nb, "sources in config"
			if sources_nb == 0:			
				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "False", "date": dt.now(), "msg": "No sources from db"}})	
				print "No sources found\nHelp: You need at least one url into sources database to start crawl."
				return False
			else:
				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "True", "date": dt.now(), "msg": "Ok"}})
				
				#print db.show_stats()
				return True
		
	def add_url(self, url, origin="default", depth=0, source_url = None):
		'''Insert url into sources with its status inserted or updated'''
		db = Database(self.project_name)
		db.create_colls(["sources"])
		link = Link(url, origin, depth, source_url)
		print link.url
		exists = db.sources.find_one({"url": link.url})
		if exists is not None:
		 	db.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(),"status": link.status, "step": link.step, "msg": link.msg}}, upsert=False)
		 	return False
		else:
			db.sources.insert(link.json())
			exists = db.sources.find_one({"url": link.url})
			if exists is not None:
				db.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(),"status": link.status,"step": link.step, "msg": link.msg}}, upsert=False)
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
			
			
			results =  [self.add_url(e["Url"], "bing", 0) for e in r.json()['d']['results']]
			new = [n for n in results if n is not False]
			print "\t- %d urls inserted" %len(new)
			print "\t- %d urls updated" %(len(results)-len(new))
			return True
		
		except requests.exceptions.HTTPError as e:
			return False

	def add_file(self):
		''' Method to extract url list from text file'''
		# self._log.step = "local file extraction"
		try:
			url_list = [re.sub("\n", "", n) for n in open(self.file).readlines()]
			i = 0
			y = 0
			if len(url_list) == 0:
				print "File %s is empty" %self.file
				return False
			
			results = [self.add_url(url, "file", 0) for url in url_list]
			new = [n for n in results if n is True]	
				
			print "\t-%d new urls has been inserted\n\t-%d urls updated" %(len(new), len(results)-len(new))
			return True
		
		except IOError, e:
		  	print "Please verify that your file is in the current directory."
		 	print "To set up a correct filename and add contained urls to sources database:"
		 	print "\t crawtext.py %s add --file =\"%s\"" %(self.name, self.file)
			print "self.debug: %s" %str(e)
			return False

	def crawl(self, mode):
		from newspaper.article import Article

		self.project_db = Database(self.project_name)
		self.project_db.set_colls()
		self.results = self.project_db.results.distinct("url")
		self.queue = self.project_db.queue.find()
		self.logs = self.project_db.logs.distinct("url")
		if self.put_to_seeds() is False:
			if self.debug:
				print "Unable to add more sources: already treated"
			return False
		
		from query import Query
		self.create_dir()
		q = Query(self.query, self.directory)
		if self.debug:
			print "Creating woosh QUERY"
		if self.debug:
			print self.project_db.queue.count()
		while self.project_db.queue.count() > 0:
			if self.debug: 
				print self.project_db.queue.count()
			for item in self.project_db.queue.find():
				if self.debug is True: print item
				if item['url'] not in self.results and item['url'] not in self.logs:
					if self.debug is True: print "not in logs and not in results"
					a = Article(item["url"], item["depth"], item["source_url"])
					if self.debug is True: print "Article loaded"
					if a.fetch():
						if self.debug is True: print "fetch"
						try:
							if a.extract():
								if self.debug is True: print "extract", a.text
								if mode == "soft":
									try:
										if self.debug is True: print self.query, q
										if a.parse(q):
											if self.debug is True: print a.url, "relevant"
											if a.depth < self.max_depth:
												if len(a.outlinks) > 0:
													if self.debug is True: print "Next", len(a.outlinks)
													self.project_db.insert_queue(a.outlinks)
											if self.debug is True: print "Article", a.export()
											self.project_db.insert_result(a.export())
											self.project_db.queue.remove(item)
											continue
										else:
											if self.debug is True: print a.url, "not relevant", a.log()
											self.project_db.logs.insert(a.log())
											self.project_db.queue.remove(item)
											continue
									except Exception as e:
										if self.debug is True: 
											print "try parsing", a.log()
										a.msg = "Error parsing: %s" %str(e)
										self.project_db.logs.insert(a.log())
										self.project_db.queue.remove(item)
										continue
								else:
									self.project_db.insert_log(a.log())
								self.project_db.queue.remove(item)
								continue	
							else:
								self.project_db.insert_log(a.log())
								self.project_db.queue.remove(item)
								continue
						except Exception as e:
							a.msg = "Error extracting: %s" %str(e)
							self.project_db.insert(a.log())
							self.project_db.queue.remove(item)
							continue
					else:
						if self.debug: 
							print a.log()
						self.project_db.insert_log(a.log())
						self.project_db.queue.remove(item)
						continue

				if self.project_db.queue.count() == 0:
			 		break
			if self.project_db.queue.count() == 0:
				break
		return True

	def put_to_seeds(self):

		for n in self.project_db.sources.find():
			# if n["status"][-1] is True:
			if n["url"] not in self.project_db.queue.distinct("url") and n["url"] not in self.logs and n["url"] not in self.results:
				print "putting", n["url"]		
				self.project_db.queue.insert({"url":n['url'], "depth": 0, "source_url":None, "origin":n["origin"]})
		
		if self.project_db.queue.count() == 0:
			return False
			#n["hash"] = hashlib.md5(n["url"]).hexdigest(), time.time()
			# if n["url"] not in self.project_db.queue.distinct("url") and n["url"] not in self.logs and n["url"] not in self.results:
				# 	self.project_db.queue.insert({"url":n['url'], "depth": 0, "source_url":None, "origin":n["origin"]})
		return True
	
	
	def stop(self, params):
		import subprocess, signal
		p = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
		out, err = p.communicate()
		cmd = "crawtext.py %s start" %self.name
		for line in out.splitlines():
			if cmd in line:
				pid = int([n for n in line.split(" ") if n != ""][0])
				#pid = int(line.split(" ")[0])
				print "Current crawl project %s killed" %self.name
				if self.exists():
					try:
						self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"stop crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
					except Exception, e:
						self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"start crawl", "status": False, "date": date, "msg": e}})

				os.kill(pid, signal.SIGKILL)
				return True
				
		if self.exists():
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"stop crawl", "status": False, "date": dt.now(), "msg": "No running project found"}})
			print "No running project %s found" %self.name
			return False
		else:
			print "No crawl job %s found" %self.name
			return False	

	def toobig(self,params):
		project_db = Database(self.name)
		db , size = project_db.get_size()
		if size > 99:
			self.stop(params)


if __name__== "crawtext":
	try:
		#print docopt(__doc__)	
		w = Worker(docopt(__doc__), debug=True)
		w.dispatch()
		sys.exit()	
	except KeyboardInterrupt:
		sys.exit()
	except Exception, e:
		print e
		sys.exit()

