#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "crawtext"
__version__ = "3.1.0b1"
__doc__ = '''Crawtext.
Description:
A simple crawler in command line.

Usage:
	crawtext.py (<name>)
	crawtext.py (<name>) (--query=<query>) (--key=<key> |--file=<file>|--url=<url>) [--user=<email>] [--r=<repeat>]
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

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")

class Worker(object):
	def __init__(self,user_input, debug=False):
		'''Job main config'''
		db = TaskDB()
		self.coll = db.coll
		self.debug = debug
		self.name = user_input['<name>']
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		del user_input['<name>']
		self.dispatch(user_input)

	def dispatch(self,user_input):
		params = dict()
		action = None
		for k,v in user_input.items():
			if v is not None and v is not False:
				if k.startswith("-"):
					params[k] = v
				else:
					action = k
		if action is None:
			if len(params) == 0:
				self.show()
				sys.exit()
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
			print self.task
		else:
			print "No crawl job %s found" %self.name
	def report(self, params):
		if self.exists():
			print "Report"
			#Report(self.name)
		else:
			print "No crawl job %s found" %self.name
		
		#Report(self.name)
	def export(self,params):
		if exists():
			if len(params) != 0:
				params = self.clean_params(params)
			print "Export"
		else:
			print "No crawl job %s found" %self.name
		
		#Report(self.name)
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
			params["action"] = "crawl"
			params["creation_date"] = dt.now()
			params["directory"] = self.create_dir()
			self.coll.insert(params)
			print "Created a new crawl job called %s" %self.name
		self.show()

	def add(self, params):
		if self.exists():
			if len(params) != 0:
				params = self.clean_params(params)
				self.coll.update({"_id": self.task['_id']}, {"$set": params})	
				print "Sucessfully added parameters %s from %s crawl job" %(",".join(params.keys()), self.name)
				return self.show()
			else:
				print "Nothing to add to crawl job %s" %self.name
			#Report(self.name)
		else:
			print "No crawl job %s found" %self.name
		
	def delete(self, params):
		if self.exists():
			
			if len(params) != 0:
				params = self.clean_options(params)
				self.coll.update({"_id": self.task['_id']}, {"$unset": params})	
				print "Sucessfully deleted parameters %s from %s crawl job" %(",".join(params.keys()), self.name)
				return self.show()
			else:
				self.coll.remove({"_id": self.task['_id']})
				self.delete_db()
				print "Sucessfully deleted project %s"%(self.name)
				return self.delete_dir()
			#Report(self.name)
		else:
			print "No crawl job %s found" %self.name
	def delete_dir(self):
		import shutil
		directory = os.path.join(RESULT_PATH, self.project_name)
		if os.path.exists(directory):
			shutil.rmtree(directory)
			print "%s deleted"	%directory
		else:
			print "No directory found for crawl project %s"(self.name)
	def delete_db(self):
		db = Database(self.project_name)
		print db.drop_db()

		#db.drop('database', self.project_name)
	def start(self, params):
		if self.exists():
			c = Crawl(self.task)
			c.start()
		else:
			print "No crawl job %s found" %self.name
	def stop(self):
		import subprocess, signal
		p = subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
		out, err = p.communicate()
		for line in out.splitlines():
			if 'crawtext' in line:
				pid = int(line.split(None, 1)[0])
			os.kill(pid, signal.SIGKILL)
		return "kill current process"

class Crawl(object):
	def __init__(self, params):
		for k,v in params.items():
			setattr(self,k, v)
		self.db = Database(self.project_name)
	
	def start(self):
		for i in range(1000000000):
			print i

	def config(self):
		#adding to sources
		if self.file:
			self.get_local()
		elif self.url:
			self.add_url()
		elif self.key():
			self.add_bing()
	
	def request(self):
		pass
	def extract(self):
		pass
	def process(self):
		pass
	#def start(self):

if __name__== "crawtext":
	try:
		#print docopt(__doc__)	
		w = Worker(docopt(__doc__), debug=False)		
	except KeyboardInterrupt:
		sys.exit()

