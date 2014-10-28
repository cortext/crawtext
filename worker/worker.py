import re
from database import TaskDB
from packages.links import validate_url
from packages.emails import validate_email
from packages.ask_yes_no import ask_yes_no
from jobs import *
from logs import Log



class Worker(object):
	''' main access to Job Database'''
	TASKDB = TaskDB()
	__COLL__ = TASKDB.coll
	
	def __init__(self,user_input, debug=False):
		'''Job main config'''
		self.name = user_input['<name>']
		self.debug = debug
		self.log = Log(self.name)
		self.set_type()
		self.set_params(user_input)
		print "Running task %s %s for %s" %(self.action, self.type,self.name)
		
		self.map_ui()

	def map_ui(self):		
		if self.is_valid_name() is False:
			return self.log.push()
		self.set_doc()
		if self.exists():
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
			print "Incorrect Project Name : %s\nYou can't call your project with the name of an instruction." %(self.name)
			return False
		return True

	def exists(self):
		if self._doc is None:
			print "No project %s found" %(self.name)
			return False
		return True	
		
	def set_params(self, user_input):
		del user_input['<name>']
		self.params = dict()
		for k,v in user_input.items():
			if v is not None and v is not False:
				self.params[re.sub("--|<|>", "", k)] = v

	
	def has_params(self):
		try:
			if len(self.params.keys()) == 0:
				del self.params
				return False
			else:
				return True
		except AttributeError:
			return False

	
	def set_type(self):
		#user
		if validate_email(self.name) is True:
			#self.user = self.name
			self.type = "user"			
		#archive
		elif validate_url(self.name) is True:
			#self.input = self.name
			self.type = "archive"
		#crawl		
		else:
			self.type = "crawl"
		return self.type	


	def create(self, mode=None):
		question = "Do you want to create a %s project called %s ?" %(self.type, self.name)
		if ask_yes_no(question):
			from datetime import datetime
			dt = datetime.now()
			self.__COLL__.insert({"name":self.name, "type": self.type, "action":self.action, "creation_date": dt.replace(second=0,microsecond=0)})
			if mode is None:
				self.update()
			print "Successfully created %s: %s" %(self.type, self.name)
			return self.show()
		
	def has_action(self):
		if self.set_action() is None:
			return False
		return True

	def set_action(self):
		try:
			self.action = self.params['action']
			return self.action
		except KeyError:
			return None
	
	def set_doc(self):
		self._doc = self.__COLL__.find_one({"name":self.name})
		return self._doc

	def update(self):
		self.log.step = "Updating task"
		self.log.msg = "Sucessfully updated task with %s parameters"%(",".join(self.params.keys()))
		if self._doc is None:
			self.set_doc()
		try:
			self.__COLL__.update({"_id": self._doc['_id']}, {"$set":self.params})
			self.log.status = True
		except Exception as e:
			self.log.msg = "Unable to updated task with %s parameters: %s" %(",".join(self.params.keys()), e)
			self.log.status = False
		return self.log.push()
		
	def show(self,):
		print "=== PARAMS for %s===" %self.name
		print "- Last activity:"
		for k,v in self._doc.items():
			print "-", k,"==",v  
		print "Owner :", self._doc["user"]
		#Tasks?
		try:
			if self._doc["type"] == "crawl":
				try:
					print "Query:", self._doc["query"]
					print "Source file:", self._doc["file"]
					print "API key:", self._doc["key"]
				except IndexError:
					pass
		except Exception as e:
			print e
		# for n in self.__COLL__.find({"name": self.name}):
		# 	print n['type']
		

		print Database(self._doc["project_name"]).stats()
		return 

	def dispatch(self):
		self.params["name"] =  self.name
		self.params["type"] =  self.type
		self.params["id"] = self._doc["_id"]
		self.params["action"] =  self.action

		if self.action in ["report", "export"]:
			_class = (self.action).capitalize()
			self.action = "start"
		else:			
			_class = (self.type).capitalize()
		instance = globals()[_class]
		try:	
			job = instance(self.params, self.debug)
			instanciate = getattr(job,self.action)
		except AttributeError:
			instanciate = getattr(self,self.action)	
		if self.debug is True:
			print instance, self.action
		return instanciate()
		
		



