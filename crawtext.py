#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "crawtext"
__version__ = "3.1.0b1"
__doc__ = '''Crawtext.
Description:
A simple crawler in command line.

Usage:
	crawtext.py (<name>)
	crawtext.py (<name>) (--query=<query>) (--key=<key> |--file=<file> [--nb=<nb>] |--url=<url>) [--user=<email>] [--r=<repeat>] [--depth=<depth>]
	crawtext.py <name> add [--url=<url>] [--file=<file>] [--key=<key>] [--user=<email>] [--r=<repeat>] [--option=<expand>] [--depth=<depth>] [--nb=<nb>]
	crawtext.py <name> delete [-q] [-k] [-f] [--url=<url>] [-u] [-r]
	crawtext.py (<name>) report [-email] [--user=<email>] [--r=<repeat>]
	crawtext.py (<name>) export [-csv|-json] [--r=<repeat>]
	crawtext.py (<name>) start [--maxdepth=<depth>]
	crawtext.py (<name>) stop
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
from crawler import process_data

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")

class Worker(object):
	def __init__(self,user_input, debug=False):
		'''Job main config'''
		self.db = TaskDB()
		self.coll = self.db.coll
		self.debug = debug
		self.user_input = user_input
		self.name = self.user_input['<name>']
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		del self.user_input['<name>']
		
		
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
		opt = {"-q":"query","-k":"key","-f":"file","-u":"user","-r":"repeat", "--url":"url"}
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
							print "A report email will be send to %s\nCheck your mailbox!" %user
							self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":True, "date": dt.now(), "msg": "Ok"}})
							return 					
						else:
							self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":False, "date": dt.now(), "msg": "Error while sending the mail"}})
					except KeyError:
						print "No user has been set: \ndeclare a user email for your project to receive it by mail."
						self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":False, "date": dt.now(), "msg": "User email unset, unable to send mail"}})
						
				if generate_report(self.task, db):
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": True, "date": dt.now(), "msg": "Ok"}})
				else:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": False, "date": dt.now(), "msg": "Unable to create report document"}})
				return True
			
		else:
			print "No crawl job %s found" %self.name
		return False

	def export(self,params):
		if exists():
			if len(params) != 0:
				pass
				#params = self.clean_params(params)
				#Export(self.name).start()
			return True
		else:
			print "No crawl job %s found" %self.name
			return False

	def create_dir(self):
		directory = os.path.join(RESULT_PATH, self.project_name)
		if not os.path.exists(directory):
			os.makedirs(directory)
		print "Directory for %s created\n Location:%s"	%(self.name, directory)
		return directory

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
			print "NO we won't delete this directory now!"
			pass
			# shutil.rmtree(directory)
			# print "Directory %s: %s sucessfully deleted"	%(self.name,directory)
		else:
			print "No directory found for crawl project %s"(self.name)
		return False

	def delete_db(self):
		db = Database(self.project_name)
		db.drop_db()
		print "Database %s: sucessfully deleted" %self.project_name
		return True
	
	
		
	def start(self, params):
		if self.exists():
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"start crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
			print "Starting project"
			if self.config():
				if self.crawl():
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"finished crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
				return True
			else:
				return
		
		else:
			print "No crawl job %s found" %self.name
			return False
				
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
		# try:
		# 	print self.db.sources.count(), "url in sources"
		# except AttributeError:
		# 	self.db.sources = self.db.create_colls["sources"]

		# try:
		self.key = self.task['key']
		print "Adding sources from search results on : %s" %self.query
		if self.add_bing() is False:
	 		self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl: add sources from file", "status": False, "date": dt.now(), "msg": "API Key: Wrong credential for Search"}})
	 		return False
	 	return True
		# except KeyError as e:
		# 	print e
		# 	return False

	def check_url(self):
		try:
			self.url = self.task['url']
			print "Adding source from the given url: %s" %self.url
			if self.add_url(self.url,manual,0):
		 		print "\t- inserted" 
		 	else:
		 		print "\t- updated"
		except KeyError:
			return False
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
		

	def config(self):
		print "Checking configuration:"
		if self.check_query() is False:
			return False
		else:
			print "- Verifying sources:"
			
			db = Database(self.project_name)
			sources = db.use_coll("sources")
			sources_nb = sources.count()
			
			if sources_nb == 0:
				pass
			if sources_nb == 0:			
				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "False", "date": dt.now(), "msg": "No sources from db"}})	
				print "No sources found\nHelp: You need at least one url into sources database to start crawl."
				return False
			else:
				print db.show_stats()
				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": "True", "date": dt.now(), "msg": "Ok"}})
				return True
			
		
	def add_url(self, url, origin="default", depth=0, source_url = None):
		'''Insert url into sources with its status inserted or updated'''
		db = Database(self.project_name)
		db.create_colls(["sources"])
		link = Link(url, origin, depth, source_url)
		exists = db.sources.find_one({"url": link.url})
		if exists is not None:
		 	db.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(),"status": link.status, "msg": link.msg}}, upsert=False)
		 	return False
		else:
			db.sources.insert(link.json())
			exists = db.sources.find_one({"url": link.url})
			if exists is not None:
				db.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(),"status": link.status, "msg": link.msg}}, upsert=False)
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
			
			
			results =  [self.add_url(e["Url"], "bing",0) for e in r.json()['d']['results']]
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
			print "Debug: %s" %str(e)
			return False

	def crawl(self):
		print "Crawl"
		db = Database(self.project_name)
		db.set_colls()
		queue = [{"url":n["url"], "depth":0} for n in db.sources.find() if n["status"][-1] is True]
		print "Crawling"
		print "%d sources as seeds" %len(queue)
		db.queue.insert(queue)
		while db.queue.distinct("url") != 0:
			for item in db.queue.find():
				for data in process_data(item, self.query, db):
					print len(data["outlinks"])
					db.insert_results(data)
					db.queue.insert(data["outlinks"])
				db.queue.remove({"url":n})
		db.queue.drop()
		print "Fini!"
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


if __name__== "crawtext":
	try:
		#print docopt(__doc__)	
		w = Worker(docopt(__doc__), debug=False)
		w.dispatch()
		sys.exit()	
	except KeyboardInterrupt:
		sys.exit()
	except Exception, e:
		print e
		sys.exit()

