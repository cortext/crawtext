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
		self.name = user_input['<name>']
		self.action = None
		#~ self.repeat = None
		#~ self.user = None
		now = datetime.datetime.now()
		self.creation_date = now.replace(second=0, microsecond=0)
		self.last_run = None
		self.next_run = None
		self.nb_run = 0
		#~ self.status = {}
		self.status = []
		self.get_input(user_input)
		
	
	def __select_jobs__(self, query):
		'''mapping job database'''
		job_list = [n for n in self.COLL.find(query)]
		if len(job_list) == 0:
			return None
		else:	
			return job_list
	
	def __update_status__(self):
		'''insert current status of the job once shceduled'''
		raise NotImplementedError
		
		
	#~ def get_job(self, job):
		#~ '''mapping data parameters from db to job'''
		#~ return [setattr(job, k, v) for k, v in self.__dict__.items() if v is not None and v is not False and k != "name"]
	
	def __set_config__(self, job):
		'''mapping data parameters from current to job'''
		for k, v in self.__dict__.items():
			if v is not None and v is not False:
				setattr(job, k, v)
				
	def __get_config__(self, job):
		'''mapping task parameters to job'''
		config = self.COLL.find_one({"name":self.name, "action":self.action})
		if config is None:
			print "No configuration found for this job"
		else:
			for k,v in config.items():
				if v is not None and v is not False and k != "name":
					setattr(job, k, v)
		return 
		
	def __get_input__(self, user_input):
		'''mapping user input into job parameters'''
		self.name = user_input['<name>']
		task = None
		#user
		if validate_email(self.name) is True:
			self.user = self.name
			del self.name
			return self.show_user()
		
		else:
			self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
			self.job_list = self.select_jobs({"name":self.name})
			for k,v in user_input.items():
				if v is True and k in self.ACTION_LIST:
					task = k+"_job"
				if v is not None and k in self.CRAWL_LIST:	
					task ="update_crawl"
					self.action = "crawl"
				if v is not None and k in self.PROJECT_LIST:	
					task = "update_project"
				if v is not None and v is not False and k != "<name>":
					setattr(self, re.sub("--|<|>","", k), v)
						
			#archive	
			if validate_url(self.name) is True:
				self.action = "archive"
				
			else:
				self.action = "crawl"
				#sources_management
				if user_input["-s"] is True:
					task = "update_source"
					for k,v in user_input.items():
						if v is True and k in self.OPTION_lIST:
							option = k
						if v is not None and v is not False:
							setattr(self,re.sub("<|>","", k), v)
					return self.update_sources(option)
				
			
			
			self.job_list = self.select_jobs({"name":self.name})
			
			if self.job_list is None and task is None:
				return self.create_job()
			elif self.job_list is not None and task is None:
				return self.show_job()
			else:
				func = getattr(self,task)
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
	
			
	def create_job(self):
		'''create one specific task'''
		del self.job_list
		if ask_yes_no("Do you want to create a new project?"):
			#schedule to be run in 5 minutes
			self.next_run = self.creation_date.replace(minute = self.creation_date.minute+1)
			project_db = Database(self.project_name)
			if project_db.use_coll("results").count() > 0 or project_db.use_coll("sources").count()> 0 or project_db.use_coll("logs").count()> 0:
				print "An old project %s exists with data.\n If you reactivate the project it will add new data to the existing ones."
				if ask_yes_no("Do you want to clean the database?"):
					project_db.drop(collection, "results")
					project_db.drop(collection, "logs")
					project_db.drop(collection, "sources")		
			self.COLL.insert(self.__dict__)
			print "Sucessfully created '%s' task for project '%s'."%(self.action,self.name)
			return
			
	def show_job(self):
		
		print "\n"
		print "===================="
		print self.name.upper()
		print "===================="
		for job in self.job_list:
			print "Job: ", job["action"]
			print "--------------"
			for k,v in job.items():
				if k == '_id' or k =="action" or k == "name":
					continue
				if v is not False or v is not None:
					print k+":", v
			print "--------------"
		print "____________________\n"
		return None
		
		
	def __update_crawl__(self):
		if self.job_list is None:
			print "No project called %s" %self.name
			return self.create_job()
		else:
			job = Crawl(self.name)
			self.get_config(job)
			
			#update key ==> if works inserted into job
			if hasattr(self, 'key') and hasattr(job, 'query'):
				if job.get_bing(self.key) is False:
					self.COLL.update({"name":self.name, "action":self.action}, {"$push": {"status": job.logs}})
					
				else:
					self.COLL.update({"name":self.name, "action":self.action}, {"$set": {"key": self.key}})
					print "updated key"
			#update query 
			elif hasattr(self, 'query'):
				self.COLL.update({"name":self.name, "action":self.action}, {"$set": {"query": self.query}})
				print "Updated query"
			else:
				print "oups"
				print job.logs
					
	def __update_sources__(self, option):
		if self.job_list is None:
			print "No project called %s" %self.name
			return self.create_job()
		else:	
			c = Crawl(self.name)
			task = option+"_sources"
			if task == "expand_sources":
				self.COLL.update({"name":self.name, "action": self.action}, {"$set": {"option": task}})
				print "Results will automatically added to sources to expand the crawl"
			self.set_config(c)
			func = getattr(c, task)
			return func()
						
	
	def delete_job(self):
		'''delete project and archive results'''
		e = Export(self.project_name)
		e.run_job()
		print self.unschedule_job()
		db = Database(self.project_name)
		db.client.drop_database(self.project_name)
		print "Project %s sucessfully deleted." %self.project_name
		return
			
	def start_job(self):
		
		if self.job_list is None:
			print "No active job found for %s" %(self.name)
			self.create_job()
		else:
			for doc in self.job_list:
				func = doc["action"].capitalize()
				instance = globals()[func]
				
				job = instance(self.name)
				
				self.get_config(job)
				job.run_job()
				print job.logs
			#~ self.COLL.update({"name":self.name, "action":"crawl"}, {"$inc": {"nb_run": 1}})	
			#~ self.COLL.update({"name":self.name, "action":"crawl"},  {"$set":{"next_run":self.next_run, 'last_run': self.last_run}})
			#~ self.refresh_task()
			#~ return self.update_status()	
	
	def stop_job(self):
		job = instance(self.name)		
		self.get_config(job)
		job.stop()
		print job.logs
	
	def unschedule_job(self):
		'''delete a specific task'''
		#~ self.select_jobs({"name":self.name, "action":self.action})
		self.COLL.remove({"name":self.name, "action":self.action})
		#here change name to archives_db_name_date
		return "All tasks %s of project %s has been sucessfully unscheduled." %(self.action, self.name)
	
	def report_job(self):
		
		e = Report(self.name)
		print e.run_job()
		#self.status = e.status
		return
	
	def export_job(self):	
		#next change self.action
		self.select_jobs({"name":self.name, "action":"crawl"})
		if self.job_list is None:
			print "No active crawl job found for %s. Export can be executed" %self.name
			return
		else:
			
			e = Export(self.name, 'json', None)
			e.run_job()
			#~ self.status = e.status
			#~ return self.update_status()
		
				
		
