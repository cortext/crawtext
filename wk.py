#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
from database import *
import re
from datetime import datetime as dt
from job import *
#from abc import ABCMeta, abstractmethod
import datetime
import docopt
from utils import *


class Worker(object):
	''' main access to Job Database'''
	DB = Database(TASK_MANAGER_NAME)
	COLL = DB.use_coll(TASK_COLL)
	#values for docopt and YAML?
	ACTION_LIST = ["report", "extract", "export", "archive", "start","stop", "delete","list", 'schedule', "unschedule"]
	PROJECT_LIST = ["--user", "--repeat"]
	CRAWL_LIST = ["--query", "--key"]
	OPTION_lIST	= ['add', 'delete', 'expand']
	
	
	def __init__(self,user_input):
		self.action = "create_or_show"
		self.repeat = None
		self.user = None
		now = datetime.datetime.now()
		self.creation_date = now.replace(second=0, microsecond=0)
		self.last_run = None
		self.next_run = None
		self.nb_run = 0
		self.status = {}
		self.logs = []
		self.process_input(user_input)
		
	
	def select_jobs(self, query):
		'''mapping job database'''
		self.job_list = [n for n in self.COLL.find(query)]
		self.job = None
		if len(self.job_list) == 0:
			self.job_list = None	
		else:
			if len(self.job_list) == 1:
				self.job = self.job_list[0]	
		return self.job_list
	def update_status(self):
		'''insert current status of the job once shceduled'''
		self.select_jobs({"name":self.name, "action": self.action})
		if self.job:
			self.COLL.update({"_id":self.job["_id"]}, {"$push":{"logs": self.status}})
			return True
		return False
		
	def process_input(self, user_input):
		'''mapping user input into task return job parameters'''
		self.name = user_input['<name>']
		self.values = {}
		
		#user
		if validate_email(self.name) is True:
			self.action = "show_user"
			self.user = self.name
			return self.show_user()
		#archive	
		elif validate_url(self.name) is True:
			self.action = "archive"
			self.url = self.name
			self.status["project"] = self.name
			self.status["date"] = datetime.datetime.now()
			
			try:
				self.format = user_input['<format>']
				self.COLL.insert(self.__dict__)	
				self.status["step"] = "user creation"
				self.status["status"] = "true"
				print "Successfully created an archive job in project %s" %self.name
				return self.update_status()
				
			except KeyError:
				self.format = "defaut"
				self.COLL.insert(self.__dict__)	
				print "Successfully created an archive job in project %s", self.name
				self.status["step"] = "creation"
				self.status["status"] = "true"
				return self.update_status()
		else:
			self.name = user_input["<name>"]
			self.status["project"] = self.name
			self.status["date"] = datetime.datetime.now()
			#sources_management
			if user_input["-s"] is True:
				self.action = "update_sources"
				for k,v in user_input.items():
					if v is True and k in self.OPTION_lIST:
						self.option = k
					if v is not None and v is not False:
						setattr(self,re.sub("<|>","", k), v)
				self.status["step"] = "update source"
				self.status["status"] = "true"
				return self.update_sources()
				
			else:
				self.status["project"] = self.name
				self.status["date"] = datetime.datetime.now()
				self.action = "create_or_show"
				self.select_jobs({"name":self.name, "action":"crawl"})
				for k,v in user_input.items():
					if v is True and k in self.ACTION_LIST:
						self.action = k+"_job"
					if v is not None and k in self.CRAWL_LIST:	
						self.action ="update_crawl"
					if v is not None and k in self.PROJECT_LIST:	
						self.action ="update_project"
					if v is not None and v is not False and k != "<name>":
						setattr(self, re.sub("|<|>","", k), v)
						self.values[re.sub("--|<|>", "", k)] = v
					
				self.status["step"] = "dispatch %s" %self.action
				self.status["status"] = "true"
				func = getattr(self,self.action)
				return func()			
		
				
	def show_user(self):
		user_data = [n for n in self.COLL.find({"user": self.user})]
		if len(user_data) == 0:
			print "No user %s registered" %self.user
			return False
		else:
			print "Project owned by:",self.user, "\n"
			for i, n in enumerate(user_data):
				i = i+1
				print "%s) %s job for '%s'"%(str(i), n["action"], n["name"])
			return True
	
	def create_or_show(self):
		if self.job is None:
			return self.create_job()
		else:
			return self.show_job()		
			
	def create_job(self):
		'''create one specific task'''
		if ask_yes_no("Do you want to create a new project?"):
			#schedule to be run in 5 minutes
			
			self.action = "crawl"
			self.next_run = self.creation_date.replace(minute = self.creation_date.minute+1)
			self.status= {"status":"true", "scope": ["creation"], "msg": ["created"]}
			project_db = Database(self.name)
			if project_db.use_coll("results").count() > 0 or project_db.use_coll("sources").count()> 0 or project_db.use_coll("logs").count()> 0:
				print "An old project %s exists with data.\n If you reactivate the project it will add new data to the existing ones."
				if ask_yes_no("Do you want to clean the database?"):
					project_db.drop(collection, "results")
					project_db.drop(collection, "logs")
					project_db.drop(collection, "sources")
					
			self.COLL.insert(self.__dict__)
			print "Sucessfully created '%s' task for project '%s'."%(self.action,self.name)
			self.status["step"] = "creation" %self.action
			self.status["status"] = "true"
			return self.update_status()
			
		
	
	def show_job(self):
		if self.job_list is not None:
			#print "%s: %s"%(order.capitalize(), query[str(order)])
			print "\n"
			print "____________________"
			print self.name.upper()
			print "____________________\n"
			for job in self.job_list:
				print "> ", job["action"],":\n"
				print "  parameters"
				print "--------------"
				for k,v in job.items():
					if k == '_id' or k =="action" or k == "name":
						continue
					if v is not False or v is not None:
						print k+":", v
				print "--------------"
			print "____________________"
			return None
		else:
			self.status = "No task for project %s"% self.name
			return self.status
	
	def archive(self):
		a = Archive(self.name)
		self.COLL.insert(a.__dict__)
		print "Sucessfully scheduled Archive job for %s Next run will be executed in 3 minutes" %self.url
		self.status["step"] = "schedule archive"
		self.status["status"] = "true"
		return self.update_status()
	
	def update_crawl(self):
		self.status["action"] = self.action
		if self.job is None:
			print "No active crawl has been found for project %s" %self.name
			return self.create_job()
		else:
			c = Crawl(self.name)
			if self.values.keys()[0] == "key":
				try :
					self.query = self.job["query"]				
					print "Adding urls into sources requesting  results from BING for search expression:\t'%s'" %self.job["query"]
					self.status["step"] = "update crawl"
					self.status["status"] = "true"
					if c.get_bing(self.values["key"]) is False:
						self.status = c.status
						self.COLL.update({"_id":self.task["_id"]}, {"$set": self.status})
						return self.update_status()
				except KeyError:
					self.status = c.status
					self.status["status"] = "false"
					print self.status["msg"]
					#self.COLL.update({"_id":self.job["_id"]}, {"$set": self.status})
					return self.update_status()
			
			self.COLL.update({"_id":self.job["_id"]}, {"$set": self.values})	
			self.status = c.status
			return self.update_status()
				
	def update_sources(self):
		self.status["step"] = "udpate source"
		
		c = Crawl(self.name)
		
		#delete
		
		if self.option == "delete_job":
			#all
			if self.value is None:
				self.status = c.delete()
				return self.update_status()
			#url
			else:
				ext = (self.url).split(".")[-1]
				if ext == "txt":
					print "Deleting the list of urls contained in the file %s" %self.url
					for url in open(self.url).readlines():
						if url == "\n":
							pass
						url = re.sub("\n", "", url)
						url = check_url(url)[-1]
						c.delete_url(self.url)
						self.status = c.status
					print "All sources from %s sucessfully deleted from sources database." %self.url
					return self.update_status()
				else:
					self.url = check_url(self.url)[-1]
					print c.delete_url(self.url)
					self.status = c.status
					return self.update_status()
		
		#expand
		elif self.option == "expand":
			status = c.expand()
			self.COLL.update({"_id":self.task["_id"]},{"$set":{"option": self.option, "status":status, "msg": c.status["msg"]}}) 
			if status is False:
				self.COLL.update({"_id":self.task["_id"]},{"$set":{"scope":"udpate_sources", "status":status, "msg": c.status["msg"], "error_code":600.3}}) 
			self.status = c.status
			print self.status["msg"]
			return self.update_status()
			
		elif self.option == "add":
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				print "Adding the list of url contained in the file %s" %self.url
				self.file = self.url
				status = c.get_local(self.file)
				if status is False:
					self.COLL.update({"_id":self.task["_id"]},{"$set":c.status}) 
				self.status = c.status
				return self.update_status()
			else:
				url = check_url(self.url)[-1]
				c.insert_url(url,"manual")
				print "Succesfully added url %s to seeds of crawl job %s"%(url, self.name)
				return self.update_status()
		else:
			return self.update_status()
						
	#~ def update_project(self):
		#~ self.select_tasks({"name": self.name})
		#~ #values = [[k, v] for k,v in doc.items() if k != "name"]
		#~ if self.task_list is None:
			#~ print "No project%s found" %self.name
			#~ return self.create_task()
		#~ else:
			#~ for n in self.task_list:
				#~ self.COLL.update({"_id":n["_id"]},{"$set":{self.value: getattr(self, self.value)}})
			#~ if self.value == "repeat":
				#~ self.refresh_task()
			#~ return "Succesfully updated the entire project %s with new value: %s" %(self.name, getattr(self, self.value))
	
	def delete_job(self):
		'''delete project and archive results'''
		if self.job is None:
			return "No active crawl job found for %s" %self.name
		else:
			if self.job_list is not None:
				print "****Archiving*****" 
				e = Export(self.name)
				e.run_job()
				self.unschedule_job()
				db = Database(self.name)
				db.client.drop_database(self.name)
			return "Project %s sucessfully deleted." %self.name
	
			
	def start_job(self):
		self.select_tasks({"name":self.name})
		if self.task is None:
			return "No active crawl job found for %s" %self.name
		else:
			c = Crawl(self.name)
			#here little trick start in 1 minute taken in charge by the daemon or the cron
			#log = os.spawnl(os.P_NOWAIT, e.run_job())
			print c.run_job()
			self.status = c.status
			
			self.COLL.update({"name":self.name, "action":"crawl"}, {"$inc": {"nb_run": 1}})	
			self.COLL.update({"name":self.name, "action":"crawl"},  {"$set":{"next_run":self.next_run, 'last_run': self.last_run}})
			self.refresh_task()
			return self.update_status()	
	
	def stop_job(self):
		self.select_task({"name":self.name})
		print self.task
		if self.task is None:
			print "No active crawl job found for %s" %self.name
			return 
		else:
			e = Crawl(self.name)
			e.stop()
			print "Job %s of %s stopped" %(self.action, self.name)
			return self.update_status()	
	
	def report_job(self):
		e = Report(self.name)
		e.run_job()
		self.status = e.status
		return self.update_status()
	
	def export_job(self):	
		self.select_task({"name":self.name, "action":"crawl"})
		if self.task is None:
			print "No active crawl job found for %s. Export can be executed" %self.name
			return
		else:
			e = Export(self.name, self.format, self.coll_type)
			e.run_job()
			self.status = e.status
			return self.update_status()
		
				
		
