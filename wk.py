#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
from database import *
import re
from datetime import datetime as dt
from job import *
#from abc import ABCMeta, abstractmethod

import docopt
from utils import *


class Worker(object):
	''' main access to Job Database'''
	DB = Database(TASK_MANAGER_NAME)
	COLL = DB.use_coll(TASK_COLL)
	#values for docopt and YAML?
	ACTION_LIST = ["report", "extract", "export", "archive", "start","stop", "delete","list"]
	SCOPE_LIST = ["-u", "-r", "-q", "-k", "-s"]
	OPTION_lIST	= ['add', 'set', 'append', 'delete', 'expand']
	DATA_C_LIST = ['<url>', '<file>', '<query>', '<key>']
	DATA_U_LIST = ['<user>', '<repeat>']
	DATA_A_LIST = ['<format>']
	
	
	def __init__(self):
		#defaut params
		self.name = None
		self.action = "unset"
		self.msg ="created"
		self.repeat = "month"
		self.user = "constance@cortext.net"
		self.status = True
		
		#schedule params
		now = datetime.datetime.now()
		self.creation_date = now.replace(second=0, microsecond=0)
		self.last_run = None
		self.next_run = None
		self.nb_run = 0
		#self.started = False
		#self.scheduled = False
			
	def task_from_ui(self, user_input):
		'''mapping user input into task return job parameters'''
		self.name = user_input['<name>']
		self.value = None
		#user
		if validate_email(self.name) is True:
			self.action = "show_user"
			self.user = self.name
			return self
		#archive	
		elif validate_url(self.name) is True:
			self.action = "archive"
			self.url = self.name
			self.scheduled = True
			try:
				self.format = 	user_input['<format>']
			except KeyError:
				self.format = "defaut"
				return self	
		#archive job
		elif user_input["archive"] is True:
			self.action = 'archive'
			self.url = user_input['<url>']
			self.name = self.url
			self.scheduled = True
			try:
				self.format = user_input['<format>']
			except KeyError:
				self.format = "defaut"
			return self
		#crawl management or report or export
		else:
			self.action = "create_or_show"
			for k,v in user_input.items():
				if v is True and k in self.ACTION_LIST:
					if user_input["-s"] is False:
						self.action = k
					else:
						self.action = "update_sources"
						self.option = k
						
				elif v is True and k in self.SCOPE_LIST:
					self.scope = re.sub("-", "", k)
					
				elif v is True and k in self.OPTION_lIST: 
					self.option = k
					if user_input['-s'] is True:
						self.action = "update_sources"
					else:
						self.action = "update_crawl"
					
				elif v is not None and k in self.DATA_C_LIST:
					k = re.sub("<|>", "", k)
					setattr(self, k, v)
					self.action = "update_crawl"
					self.scheduled = True
					self.value = k
				elif v is not None and k in self.DATA_U_LIST:
					k = re.sub("<|>", "", k)
					setattr(self, k, v)
					self.value = k
					self.action = "update_project"
				else:
					continue
			
			return self
				
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
		if self.action == "create_or_show":
			#defaut action to create is a crawl
			self.action = "crawl"
			
		self.select_tasks({"name": self.name, "action":self.action})
		if self.task is None:
			return self.create_task()
		else:
			return self.show_task()		
			
	def create_task(self):
		'''create one specific task'''
		if ask_yes_no("Do you want to create a new project?"):
			#schedule to be run in 5 minutes
			#self.next_run = self.creation_date.replace(minute = self.creation_date.minute+5)
			self.schedule_task()
			#subprocess.Popen(["python","crawtext.py","start", str(self.name)])
			return "Sucessfully created '%s' task for project '%s'."%(self.action,self.name)
		else: sys.exit()
	
	def select_task(self, query):
		self.task = self.COLL.find_one(query)
		return self.task
		
	def select_tasks(self, query):
		'''show tasks that match the filter with a specific order return the set of tasks'''
		self.task_list = [n for n in self.COLL.find(query)]
		self.task = None
		if len(self.task_list) == 0:
			self.task_list = None
			return None
		else:
			if len(self.task_list) == 1:
				self.task = self.task_list[0]
				
			return len(self.task_list)	
			
	def show_task(self):
		if self.task_list is not None:
			#print "%s: %s"%(order.capitalize(), query[str(order)])
			print "\n"
			print "____________________"
			print self.name.upper()
			print "____________________\n"
			for task in self.task_list:
				print "> ", task["action"],":\n"
				print "  parameters"
				print "--------------"
				for k,v in task.items():
					if k == '_id' or k =="action" or k == "name":
						continue
					if v is not False or v is not None:
						print k+":", v
				print "--------------"
			return "____________________"
		else:
			print "No task for project %s"% self.name
			
	def update_crawl(self):
		self.action = "crawl"
		self.msg = "updated"
		self.select_task({"name": self.name, "action": self.action})
		if self.task is None:
			print "No active crawl has been found for project %s" %self.name
			self.create_task()
		else:
			
			if self.scope == "q":
				self.COLL.update({"_id":self.task["_id"]}, {"$set":{"query": self.query}})
				return "Sucessfully updated query to : %s on crawl job of project %s" %(self.query, self.name)
			elif self.scope == "k":
				self.COLL.update({"_id":self.task["_id"]},{"$set":{"key": self.key}})
				print "Sucessfully added a new BING API KEY to crawl job of project %s"%(self.name)
				if self.option == "append":
					c = Crawl(self.name)
					try:
						if c.get_bing() is True:
							return "%s seeds from search successfully added to sources of crawl project '%s'" %(c.seeds_nb, self.name)
						else:
							return c.status["msg"]
					except KeyError:
						return "Unable to search new seeds beacause no query has been set.\nTo set a query to your crawl project '%s' type:\n python crawtext.py %s -q \"your awesome query\"" %(self.name, self.name)
				
			else:
				return self.update_sources()	
				
	def update_sources(self):
		self.Msg = "udpated"
		self.select_task({"name": self.name, "action": "crawl"})
		c = Crawl(self.name)
		#delete 
		if self.option == "delete":
			#all
			if self.value is None:
				return c.delete()
			#url
			else:
				self.url = check_url(self.url)[-1]
				return c.delete_url(self.url)
		
		#expand
		elif self.option == "expand":
			
			self.COLL.update({"_id":self.task["_id"]},{"$set":{"option": self.option}})
			print "Successfully added option expand for crawl project %s"% self.name
			c.expand()
			return c.status["msg"]
		elif self.option == "add":
			url = check_url(self.url)[-1]
			c.insert_url(url,"manual")
			return "Succesfully added url %s to seeds of crawl job %s"%(url, self.name)
		else:
			#set
			if self.value is not None:
				self.COLL.update({"_id":self.task["_id"]},{"$set":{self.value: getattr(self, self.value)}})			
				if self.option == "set":
					return "Sucessfully added a new %s \"%s\" to crawl job of project %s"%(self.value, getattr(self, self.value), self.name)
				#append
				else:
					print "Sucessfully added a new %s \"%s\" to crawl job of project %s"%(self.value, getattr(self, self.value), self.name)		
					c.get_local()
					return c.status["msg"]
					
	def update_project(self):
		self.select_tasks({"name": self.name})
		#values = [[k, v] for k,v in doc.items() if k != "name"]
		if self.task_list is None:
			print "No project%s found" %self.name
			return self.create_task()
		else:
			for n in self.task_list:
				self.COLL.update({"_id":n["_id"]},{"$set":{self.value: getattr(self, self.value)}})
			if self.value == "repeat":
				self.refresh_task()
			return "Succesfully updated the entire project %s with new value: %s" %(self.name, getattr(self, self.value))
		
	def refresh_task(self):
		'''after a run update the last_run and set nb_run how to log msg?'''
		if self.last_run is None:
			self.last_run = self.creation_date
		
		if self.repeat == "week":
			self.next_run = self.last_run.replace(day = self.last_run.day+7)
		else:	
			if self.repeat == "day":
				self.next_run = self.last_run.replace(day=self.last_run.day+1)
			
			elif self.repeat == "month":
				self.next_run = self.last_run.replace(month=self.last_run.month+1)
			elif self.repeat == "year":
				self.next_run = self.last_run.replace(year=self.last_run.year+1)
			else:
				self.next_run = None
		self.COLL.update({"name":self.name, "action": self.action}, {"$set":{"next_run": self.next_run, "last_run": self.last_run}})
		return self.next_run
		
	def schedule_task(self):
		'''schedule task inserting into db'''
		self.COLL.insert(self.__dict__)
		return "%s on project %s has been sucessfully scheduled to be run next %s" %(self.action, self.name, self.repeat)
		
	def schedule_project(self):
		'''schedule complete tasks set for one crawl inserting into db'''
		for action in ["crawl", "report", "export"]:
			w = Worker()
			w.action = action
			self.COLL.insert(w.__dict__)
		return "Project %s with crawl, report and export has been sucessfully scheduled and will be run next %s" %(self.name, self.repeat)
	
	def unschedule(self):
		'''delete all tasks attached to the project'''
		self.select_tasks({"name":self.name})
		if self.task_list is None:
			return "No project %s  has been found." %(self.name)
		else:
			for n in self.task_list:
				self.COLL.remove({"name": self.name, "action":n["action"]})
			return "Every tasks of  project %s has been sucessfully unscheduled" %(self.name)
	
	def unschedule_task(self):
		'''delete a specific task'''
		self.select_tasks({"name":self.name, "action":"crawl"})
		if self.task_list is None:
				return "No project %s with task %s has been found." %(self.name,self.action)
		else:	
			self.COLL.remove({"name": self.name, "action":self.action})
			#here change name to archives_db_name_date
			return "Task %s of project %s has been sucessfully unscheduled." 
			
		return "Task %s of project %s has been sucessfully unscheduled" %(self.action, self.name)
	
	def archive(self):
		a = Archive(self.name)
		self.COLL.insert(a.__dict__)
		return "Sucessfully scheduled Archive job for %s Next run will be executed in 3 minutes" %self.url
	
	def delete(self):
		'''delete project and archive results'''
		self.select_task({"name":self.name, "action":"crawl"})
		if self.task is None:
			return "No active crawl job found for %s" %self.name
		else:
			self.select_tasks({"name":self.name})
			if self.task_list is not None:
				print "Before deleting project :\n****Archiving*****" 
				e = Export(self.name)
				e.run_job()
				self.unschedule()
				db = Database(self.name)
				db.client.drop_database(self.name)
			return "Project %s sucessfully deleted." %self.name
	
	def set_next_run(self):
		if self.next_run == "unset":
			self.next_run = datetime.datetime.now()
			self.next_run = self.next_run.replace( second=0, microsecond=0)
			mins = self.next_run.minute+5
			self.next_run = self.next_run.replace(minute = mins) 
			return self.next_run
			
	def start(self):
		
		print self.select_tasks({"name":self.name})
		if self.task is None:
			return "No active crawl job found for %s" %self.name
		else:
			e = Crawl(self.name)
			log = os.spawnl(os.P_NOWAIT, e.run_job())
			
			if log is False:
				self.COLL.update({"name":self.name, "action":"crawl"}, {"$set":{"status":e.status}})
				self.COLL.update({"name":self.name, "action":"crawl"},  {"$set":{"next_run":self.last_run}})
			else:
				self.refresh_task()
				self.COLL.update({"name":self.name, "action":"crawl"}, {"$inc": {"nb_run": 1}})
				self.COLL.update({"name":self.name, "action":"crawl"}, {"$set":{"status":True}})
				self.COLL.update({"name":self.name, "action":"crawl"},  {"$set":{"next_run":self.next_run, 'last_run': self.last_run}})
			return True
	
	def stop(self):
		self.select_task({"name":self.name, "action":"crawl"})
		if self.task is None:
			return "No active crawl job found for %s" %self.name
		else:
			e = Crawl(self.task)
			return e.stop()		
			
	def report(self):
		e = Report(self.name)
		return e.run_job()
	
	def export(self):
		self.select_task({"name":self.name, "action":"crawl"})
		if self.task is None:
			print "No active crawl job found for %s" %self.name
		else:	
			e = Export(self.name)
			return e.run_job()
		
	def process(self, user_input):
		self.task_from_ui(user_input)
		func = getattr(self,self.action)
		return func()
		
				
		
