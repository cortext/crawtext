#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "crawtext"
__version__ = "4.2.0b2"
__doc__ = '''Crawtext.
Description:
A simple crawler in command line for targeted websearch.

Usage:
	crawtext.py (<name>)
	crawtext.py (<name>) (--query=<query>) (--key=<key> |--file=<file> [--nb=<nb>] |--url=<url>) [--lang=<lang>] [--user=<email>] [--r=<repeat>] [--depth=<depth>]
	crawtext.py <name> add [--query=<query>] [--url=<url>] [--file=<file>] [--key=<key>] [--user=<email>] [--r=<repeat>] [--option=<expand>] [--depth=<depth>] [--nb=<nb>] [--lang=<lang>]
	crawtext.py <name> delete [-q] [-k] [-f] [--url=<url>] [-u] [-r] [-d]
	crawtext.py (<name>) report [-email] [--user=<email>] [--r=<repeat>]
	crawtext.py (<name>) export [--format=(csv|json)] [--data=(results|sources|logs|queue)][--r=<repeat>]
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
#from url import Link
from report import send_mail, generate_report
import hashlib
from article import Article
from config import Config
from crawl import crawl

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")

class Worker(object):
	def __init__(self,user_input,debug=False):
		'''Job main config'''
		if type(user_input) == str:
			self.name = user_input
		else:
			self.user_input = user_input
			self.name = self.user_input['<name>']
			del self.user_input['<name>']
			
		self.debug = debug
		if self.debug:
			print "debug mode activated"
		self.db = TaskDB()
		self.coll = self.db.coll
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		
				
	def dispatch(self, params=None):
		if params is not None:
			self.user_input = params
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
		opt = {"-q":"query","-k":"key","-f":"file","-u":"user","-r":"repeat", "--url":"url", "-d":"depth"}
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
					try: 
						format = params['format']
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
						try:
							user = params['user']
							if send_mail(user, db) is True:
								print "A report email has been sent to %s\nCheck your mailbox!" %user
								self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":True, "date": dt.now(), "msg": "Ok"}})
								self.coll.upsert({"_id": self.task['_id']}, {"user":params["user"]}, False)
								self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: add user", "status":True, "date": dt.now(), "msg": "Ok"}})
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
			return self.show()
		else:
			self.type = "crawl"
			params = self.clean_params(params)
			params["name"] = self.name
			params["project_name"] = self.project_name
			params["type"] = self.type
			params["action"] = ["create"]
			params["directory"] = self.create_dir()
			params["creation_date"] = dt.now()
			params["date"] = [dt.now()]
			params["status"] = ["True"]
			params["msg"] = ['Ok']
			self.coll.insert(params)
			config = Config(self.name, self.type)
			if config.setup():
				print "Created a new crawl job called %s" %self.name
				self.exists()
				return self.show()

	def add(self, params):
		if self.exists():
			if len(params) != 0:
				params = self.clean_params(params)
				action = "add: %s" %(",".join(params.keys()))
				date = dt.now()
				status = True
				try:
					
					self.add_url(params["url"], "manual", 0)
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":action, "status": status, "date": date, "msg":'Ok'}})	
					return True
				except Exception:
					pass

				try:
					self.coll.update({"_id": self.task['_id']}, {"$set": params})
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":action, "status": status, "date": date, "msg":'Ok'}})	
					print "Sucessfully added parameters %s from %s crawl job" %(",".join(params.keys()), self.name)
					# self.update_sources(params)
					# ret
					return True
					
				except Exception, e:
					self.coll.update({"_id": self.task['_id']}, {"$push": {"action":action, "status": False, "date": date, "msg": str(e)}})	
					return False
			else:
				print "Nothing to add to crawl job %s" %self.name
				return self.show()	
			
		else:
			print "No crawl job %s found" %self.name
			return False

	def update_sources(self, params):
		update = [n for n in params.keys() if n in ["file", "url", "key"]]
		cfg = Config(self.name, "crawl", debug=False)
		if len(update) != 0:
			for n in update:		
				if n == "file":
					if cfg.check_file() is False:
						print "Error no url from file %s has been added to sources" %params[n]
				elif n == "url":
					if cfg.check_url() is False:
						print "Error no url has been added"
				else:
					self.query = self.task["query"]
					if cfg.check_bing() is False:
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
		self.debug = True
		if self.debug: print "start"
		cfg = Config(self.name, "crawl", self.debug)
		if cfg.setup():
			if cfg.crawl_setup():
				print "Configuration is Ok"
				if crawl(cfg.project_name, cfg.query, cfg.directory, cfg.max_depth, self.debug):
					print "Finished"
				try:
					user = cfg.task['user']
				except KeyError:
					params['user'] = "constance@cortext.net"
				self.report(params)
				return self.coll.update({"_id": cfg.task['_id']}, {"$push": {"action":"crawl", "status": True, "date": dt.now(), "msg": cfg.msg}})	
		
			#put_to_seeds
		return self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"config", "status": False, "date": dt.now(), "msg": cfg.msg}})	

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

	

'''
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
'''