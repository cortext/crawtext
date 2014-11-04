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
		self.debug = debug
		self.set_name(user_input)
		self.log = Log(self.name)
		self.set_params(user_input)
		if self.exists():
			if self.has_params():
				self.update()
				sys.exit()
			else:
				if self.action is None:
					self.action = "show"
				self.start_action()
				sys.exit()
		else:
			if self.action is None:
				self.create()
			sys.exit()
		
	def set_name(self, user_input):
		if self.debug:
			print "Setting name %s and project name" %(user_input['<name>'])
		self.name = user_input['<name>']
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		del user_input['<name>']
		if self.is_valid_name() is False:
			return sys.exit()
	
	def set_params(self, user_input):	
		self.params = dict()
		if self.debug:
			print "setting_params"
		for k,v in user_input.items():

			if v is not None and v is not False:
				self.params[re.sub("--|<|>", "", k)] = v
		self.type = self.set_type()
		self.action = self.set_action()
		return self.params

	def has_params(self):
		if self.debug:
			print "Checking nb of params: %s" %len(self.params)
		try:
			if len(self.params) > 0:
				return True
		except Exception as e:
			print e
			return False
	
	def set_type(self):
		if self.debug:
			print "Setting type of : %s" %self.name
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
			if self.debug:
				print "Setting action: %s" %self.params['action']
			self.action = self.params['action']
			del self.params["action"]
			return self.action
		except KeyError:
			return None

	def exists(self):
		if self.debug:
			print "Checking if doc exists"
		self._doc = self.__COLL__.find_one({"name":self.name,"type": self.type})
		if self._doc is None:
			print "No project %s with active %s found" %(self.name, self.type)
			if self.debug:
				print "Exists: False"
			return False
		if self.debug:
			print "Exists: True"
		return True
	
	def start_action(self):
		if self.debug:
			print "Start_action : Sending to  %s" %self.action
		
		if self.action == "delete":
			if self.has_params() is None:
				return self.delete()
			else:
				return self.unset()	

		elif self.action == "unschedule":
			if self.has_params() is None:
				self.unschedule()
			self.params = {"repeat": "month"}
			return self.unset()

		elif self.action == "add":
			if self.has_params() is None:
				print "Missing argument to add"
				return sys.exit()
			else:
				_class = (self.type).capitalize()
				instance = globals()[_class]	
				job = instance(self._doc, self.debug)
				return job.add(self.params)
		else:		
			if self.debug is True:
				print self.type,">>>", self.action

		_class = (self.type).capitalize()
		instance = globals()[_class]	
		job = instance(self._doc, self.debug)
		start = getattr(job, str(self.action))
		return start()
			
	def is_valid_name(self):
		if self.debug:
			print "Checking if name is valid"
		ACTION_LIST = ["report", "extract", "export", "archive", "user", "debug", "wos", "list", "crawl", "stats", "start","stop", "delete",'schedule', "unschedule"]
		if self.name in ACTION_LIST :
			print "Incorrect Project Name : %s\nYou probably forget to put a name for your project..." %(self.name)
			return False
		return True

	def create(self, mode=None):
		if self.debug:
			print "Creating new job"
		question = "Do you want to create a %s project called %s ?" %(self.type, self.name)
		if ask_yes_no(question):
			
			self.__COLL__.insert({"project_name": self.project_name, "name":self.name, "type": self.type, "action":self.action, "creation_date": self.log.date.replace(second=0,microsecond=0)})
			print "Successfully created %s: %s" %(self.type, self.name)
			if self.has_params():
				return self.update()
			return
			
		
	def update(self):
		if self.debug:
			print "Updating %s job with %s" %(self.type, ",".join(self.params.keys()))
		if self.exists():
			if self.action not in ["add", "export", "report", "delete"]:
				self.log.step = "Updating task"
				self.log.msg = "Sucessfully updated task with %s "%(",".join(self.params.keys()))
				try:
					self.__COLL__.update({"_id": self._doc['_id']}, {"$set":self.params})
					self.log.status = True
				except Exception as e:
					self.log.msg = "Unable to updated task with %s parameters:\n %s" %(",".join(self.params.keys()), e)
					self.log.status = False
				return self.log.push()
		
			else:
				if self.action not in ["add", "delete"]:
					#create a project with a specific action
					self.__COLL__.insert(self.__COLL__.insert({"project_name": self.project_name, "name":self.name, "type": self.type, "action":self.action, "creation_date": self.log.date.replace(second=0,microsecond=0)}))
				return self.start_action()	
		
	def unset(self):
		try:
			if self.params["data"] is not None:
				if self.params["data"] is ACTION_LIST:
					task = self.__COLL.find_one({"name":self.name, "action": self.params["data"]})
					if task is not None:
						self.__COLL__.remove({"_id":task['_id']})
						print "Successfully deleted task %s for project %s"%(self.params['data'], self.name)
					else:
						print "Task %s for project %s doesn't exist. Exiting"%(self.params['data'], self.name)

		except KeyError:
			pass
		try:
			self.__COLL__.update({"_id": self._doc['_id']}, {"$unset":self.params})
			self.log.status = True
		except Exception as e:
			self.log.msg = "Unable to unset %s parameters.Error is \n %s" %(",".join(self.params.keys()), e)
			self.log.status = False
		return self.log.push()
	
	def delete(self):
		deleted= []
		for n in self.__COLL__.find({"name": self.name}):
			d = self.__COLL__.remove({"_id": n['_id']})
			if d is not None:
				print "-%s" %(n["name"] )
				deleted.append(d)

		if len(deleted) > 0:
			print "All %d tasks of project %s has been sucessfully deleted" %(len(deleted), self.name)
		job = Job(self._doc, self.debug)
		return job.delete()
	
	def unschedule(self):
		for n in self.__COLL__.find({"name": self.name}):
			self.__COLL__.update({"_id": n['_id']}, {"$set":{"active":False}})
