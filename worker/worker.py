import re
from database import TaskDB
from packages.links import validate_url
from packages.emails import validate_email
from packages.ask_yes_no import ask_yes_no
from jobs import *
from logs import Log
import sys


class Worker(object):
	''' main access to Job Database'''
	TASKDB = TaskDB()
	__COLL__ = TASKDB.coll
	
	def __init__(self,user_input, debug=False):
		'''Job main config'''
		self.set_name(user_input)
		self.log = Log(self.name)
		self.debug = debug
		self.set_params(user_input)		
		if self.exists():
			if self.has_params():
				self.update()
			else:
				if self.action is None:
					self.action = "show"
				self.start_action()
			sys.exit()
		else:
			self.create()
			sys.exit()
		
	def set_name(self, user_input):
		self.name = user_input['<name>']
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		del user_input['<name>']
		if self.is_valid_name() is False:
			self.log.push()
			return sys.exit()
	
	def set_params(self, user_input):	
		self.params = dict()
		for k,v in user_input.items():

			if v is not None and v is not False:
				self.params[re.sub("--|<|>", "", k)] = v
		self.type = self.set_type()
		self.action = self.set_action()
		return self.params

	def has_params(self):
		try:
			if len(self.params) > 0:
				return True
		except Exception as e:
			print e
			return False
	def set_type(self):
		#user
		if validate_email(self.name) is True:
			#self.user = self.name
			self.type = "user"
			return self.type			
		#archive
		elif validate_url(self.name) is True:
			#self.input = self.name
			self.type = "archive"
			return self.type
		#crawl		
		else:
			self.type = "crawl"
			return self.type
	
	def set_action(self):
		try:
			self.action = self.params['action']
			del self.params["action"]
			return self.action
		except KeyError:
			return None

	def exists(self):
		self._doc = self.__COLL__.find_one({"name":self.name,"type": self.type})
		
		if self._doc is None:
			print "No project %s with active %s found" %(self.name, self.type)
			return False
		return True
	
	def start_action(self, params=None):
		if self.action in ["report", "export"]:
			_class = (self.action).capitalize()
			self.action = "start"
		elif self.action in ["add"]:
			print self.type
		else:
			_class = (self.type).capitalize()
			
		instance = globals()[_class]	
		print instance
		job = instance(self._doc, self.debug)
		start = getattr(job, str(self.action))
		return job.start()
			

	def map_ui(self):		
		if self.is_valid_name() is False:
			return self.log.push()
		self.set_doc()
		if self.exists() :
			if self.has_params():
				if self.has_action():
					if self.debug:
						print "Has action %s" %self.action
						print "Running %s project: %s" %(self.type, self.name)
						self.params['type'] = self.type
						print "Parameters =", self.params
					return self.dispatch()
					
				else:
					if self.debug:
						print "No action"
						print "Updating %s project: %s" %(self.type, self.name)
					return self.update()
			else:
				if self.debug:
					print "Showing %s project: %s" %(self.type, self.name)
				return self.show()	
		else:
			if self.has_params():
				if self.debug:
					print "creating a complete %s project" %(self.type)
				if self.set_action():
					if self.debug:
						print "Before starting project create it"
					action = self.params['action']
					del self.params['action']
					self.create()
					self.params['action'] = action
					if self.debug:
						print "Running it"
					return self.dipatch()

				return self.create()
			else:
				self.action = "create"
				if self.debug:
					print "creating a defaut %s" %(self.type)
				return self.create(mode="default")	
	

	def is_valid_name(self):
		ACTION_LIST = ["report", "extract", "export", "archive", "user", "debug", "wos", "list", "crawl", "stats", "start","stop", "delete",'schedule', "unschedule"]
		if self.name in ACTION_LIST :
			print "Incorrect Project Name : %s\nYou probably forget to put a name for your project..." %(self.name)
			return False
		return True

	def create(self, mode=None):
		question = "Do you want to create a %s project called %s ?" %(self.type, self.name)
		if ask_yes_no(question):
			print self.__COLL__.insert({"project_name": self.project_name, "name":self.name, "type": self.type, "action":self.action, "creation_date": self.log.date.replace(second=0,microsecond=0)})
			if self.has_params():
				self.update()
			print "Successfully created %s: %s" %(self.type, self.name)
			return self.show()
		
	def update(self):
		if self.action not in ["add", "export", "report"]:
			self.log.step = "Updating task"
			self.log.msg = "Sucessfully updated task with %s "%(",".join(self.params.keys()))
			
			if self._doc is None:
				self.set_doc()
			try:
				self.__COLL__.update({"_id": self._doc['_id']}, {"$set":self.params})
				self.log.status = True
			except Exception as e:
				self.log.msg = "Unable to updated task with %s parameters:\n %s" %(",".join(self.params.keys()), e)
				self.log.status = False
			return self.log.push()
		elif self.action == "add":
			print self.type, self.action
			_class = (self.type).capitalize()
			instance = globals()[_class]	
			job = instance(self._doc, self.debug)
			start = getattr(job, str(self.action))
			print start
			return start()
		else:
			return self.start_action()
	
		
	


