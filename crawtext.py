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
	crawtext.py <name> add [--url=<url>] [--file=<file>] [--key=<key>] [--user=<email>] [--r=<repeat>] [--option=<expand>]
	crawtext.py <name> delete [-q] [-k] [-f] [--url=<url>] [-u] [-r]
	crawtext.py (<name>) report [-email] [--user=<email>] [--r=<repeat>]
	crawtext.py (<name>) export [-csv|-json] [--r=<repeat>]
	crawtext.py (<name>) start [--maxdepth=<depth>]
	crawtext.py (<name>) stop
	crawtext.py (-h | --help)	
'''

from docopt import docopt
#from worker.worker import Worker
import os, sys
import re
from datetime import datetime as dt
from database import TaskDB, Database
from links import Link

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
				self.show()
			else:
				self.create(params)
		else:
			job = getattr(self, str(action))
			job(params)
				
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
			for k, v in self.task.items():
				print k, ":", v 

		else:
			print "No crawl job %s found" %self.name
				
	def report(self, params):
		if self.exists():
			print "Report"
			#Report(self.name)
		else:
			print "No crawl job %s found" %self.name
		return 
		#Report(self.name)

	def export(self,params):
		if exists():
			if len(params) != 0:
				params = self.clean_params(params)
			print "Export"
		else:
			print "No crawl job %s found" %self.name
		return 

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
			params["creation_date"] = dt.now()
			params["directory"] = self.create_dir()
			params["date"] = [dt.now()]
			params["status"] = ["True"]
			params["msg"] = ['Ok']
			self.coll.insert(params)
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
				except Exception, e:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":action, "status": False, "date": date, "msg": e}})	
			else:
				print "Nothing to add to crawl job %s" %self.name
				
			return self.show()
		else:
			print "No crawl job %s found" %self.name
				
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
				
			#Report(self.name)
		else:
			print "No crawl job %s found" %self.name
			
	def delete_dir(self):
		import shutil
		directory = os.path.join(RESULT_PATH, self.project_name)
		if os.path.exists(directory):
			shutil.rmtree(directory)
			print "Directory %s: %s sucessfully deleted"	%(self.name,directory)
		else:
			print "No directory found for crawl project %s"(self.name)
		return

	def delete_db(self):
		db = Database(self.project_name)
		db.drop_db()
		print "Database %s: sucessfully deleted" %self.project_name
		return
	def sources_stats():
		active = self.db.sources.find({"status":True}, { "status": {"$slice": -1 } } ).count()
		inactive = self.db.sources.find({"status":False}, { "status": {"$slice": -1 } } )
		print "- %d invalid urls" %inactive.count()
		print "- %d valid urls" %active
		if inactive.count() > 0:
			print "Following urls are inactive:"
			for u in inactive:
				print '\t-'+u['url']+": "+u['msg']

	def start(self, params):
		
		if self.exists():
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"start crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
			print "Starting project"
			try:
				if self.config():
					self.sources_stats()			
					
				else:
					sys.exit()
			except KeyboardInterrupt:
				sys.exit()
		else:
			print "No crawl job %s found" %self.name
			
	def check_query(self):
		print "- Verifying query:"
		try:
			self.query = self.task["query"]
			print "\t-Query: %s" %self.query
			return True
		except KeyError:
			print "No query has been set. Unable to start crawl."	
			return False
	def check_file(self):
		print "- Adding or updating sources:"
		try:
			self.file = self.task['file']
			print "Verifying sources from file: %s" %self.file
			if self.add_file() is False:
				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl: add sources from file", "status": False, "date": dt.now(), "msg": "Filename incorrect"}})
				return False
			return True
		except KeyError as e:
			return False
	def check_bing(self):
		try:
			self.key = self.task['key']
			print "Verifying source from search results for: %s" %self.query
			if self.add_bing() is False:	
		 		self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl: add sources from file", "status": False, "date": dt.now(), "msg": "API Key: Wrong credential for Search"}})
		except KeyError as e:
			return False

	def check_url(self):
		try:
			self.url = self.task['url']
			print "Verifying source from the given url: %s" %self.url
			if self.add_url(self.url,origin="manual", depth=0):
		 		print "\t- Inserted url: %s " %self.url
		 	else:
		 		print "\t- Updated url: %s" %self.url
		except KeyError:
			return False
	
	def config(self):
		print "Checking configuration:"
		self.db = Database(self.project_name)
		self.db.create_colls(["results","sources", "logs", "queue", "treated"])
		if self.check_query():
			error = []
			if self.check_file() is False:
				error.append('file')
			elif self.check_bing() is False:
				error.append('bing')
			elif self.check_url() is False:
				error.append('url')
			sources_nb = self.db.sources.count()
			if sources_nb == 0:
				if len(error) == 3:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": False, "date": dt.now(), "msg": "No sources set by user"}})
			 		print "No sources found\nHelp: You need at least one url into sources database to start crawl:"
			 		print "add url or key or file to you project:"
			 		print "\tpython crawtext.py %s add --url=\"yoururl.com/examples\""
			 		print "\tpython crawtext.py %s add --file=\"seed_examples.txt\""
			 		print "python crawtext.py %s add --key=\"3X4MPL3\""		
				else:
					print ">>>No sources found to start crawl. \nCheck the configuration of your project for url, file or key"
				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": False, "date": dt.now(), "msg": "No sources from db"}})	
				return False
			else:
				if len(error) > 0:
					for n in error:
						print "Error on adding sources from %s. But sources database is not empty!" %n
						print "Check it for next time!"

				self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
				return True
		
	
	def add_url(self, url, origin="default", depth=0, source_url = None):
		'''Insert url into sources with its status'''		
		link = Link(url, origin=origin, depth=depth, source_url="")
		exists = self.db.sources.find_one({"url": link.url})
		if exists is not None:
			self.db.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(),"status": link.status, "msg": link.msg}}, upsert=False)
			return False
		else:
			self.db.sources.insert(link.json())
			exists = self.db.sources.find_one({"url": link.url})
			if exists is not None:
				print self.db.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now(), "status": link.status}}, upsert=False)
			return True
		

	def add_bing(self, nb = 50):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		import requests
		# self._log.step = "Searching sources from Bing"
		if nb > 50:
			print "Not able yet to add more than 50 urls"
			return False
		try:
			r = requests.get(
				'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
				params={
					'$format' : 'json',
					'$top' : nb,
					'Query' : '\'%s\'' %self.query,
				},	
				auth=(self.key, self.key)
				)
			r.raise_for_status()
			try:
				url_list =  [e["Url"] for e in r.json()['d']['results']]	
				for url in url_list:
					if self.add_url(url, origin="bing",depth=0):
						i = i +1
				if i > 0:
					print "\t%d new urls has been inserted from search into database." %i
				else:
					print "\tExisting urls from search have been updated"
				return True
			except Exception as e:
				print e
				return False
		except Exception as e:
			print e
			return False

	def add_file(self):
		''' Method to extract url list from text file'''
		# self._log.step = "local file extraction"
		try:
			i = 0
			y = 0
			for url in open(self.file).readlines():
				url = re.sub("\n", "", url)
				if self.add_url(url, origin="file", depth=0):
					i = i+1
				y = y+1
			print "\t-%d new urls has been inserted\n\t-%d urls updated" %(i, y-i) 
			return True

		except Exception as e:
			print e
			print "Please verify that your file is in the current directory."
			print "To set up a correct filename and add to sources database:"
			print "\t crawtext.py %s add --file =\"./%s\"" %(self.name, self.file)
			print "Debug: %s" %e
			return False

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

