
import re, sys
from datetime import datetime as dt
from ..database import Database
from ..database import TaskDB
from packages.ask_yes_no import ask_yes_no
from ..logs import Log

class Job(object):
	'''defaut job class for worker'''
	
<<<<<<< HEAD
	def __init__(self, doc):
		self.debug = False
		if type(doc) == str:
			self.name = doc
		else:	
			self.name = doc["name"]
			self.action = doc["action"]
		self.__data__ = self.__COLL__.find_one({"name":self.name})		
=======
	def __init__(self, doc, debug):
		self.debug = debug
		self.name = doc["name"]

		self.action = doc["action"]
		#self.type = doc["type"]
>>>>>>> logs_job
		self.project_name = re.sub('[^0-9a-zA-Z]+', '_', self.name)
		now = dt.now()
		self.date = now.replace(second=0, microsecond=0)
		#TaskDB
		self.id = doc["id"]
		self.params = doc
		tk = TaskDB()
		self.task = tk.get()
		
		#PROJECT DB
		self.db = Database(self.project_name)

		self.db.create_colls(["results","sources", "logs", "queue", "treated"])
		#Logs
		self.log = Log(doc['name'])
		self.log.type = doc["type"]
		self.log.action = self.action
		self.set_doc()
		#self.log = Log()
	
	def schedule(self):
		self.log.step = "Scheduling job"
		self.log.date = dt.now()
		try:	
			self.log.status = True
			self.task.update({'_id': self.id}, {"$set":{"repeat": self.params["repeat"]}})
			self.log.msg = "Job is now scheduled to run every %s" %(self.params["repeat"])
		except KeyError:
			self.log.status = False
			self.log.msg = "No recurrence found."
		self.log.push()
		return 

	def unschedule(self):		
		self.log.step = "Unscheduling job"
		self.log.date = dt.now()
		self.log.msg = "Job is now unscheduled"
		self.log.push()
		return self.task.update({'_id': self.id}, {"$unset":{"repeat": self.params["repeat"]}, "$set":{"active":False}})

	def stats(self):
		self.log.step = "Stats"
		self.log.date = dt.now()
		self.log.msg = "Results overview"
		print self.db.stats()

		return

	def list(self):
		tk = TaskDB()
		for n in tk.find():
			print n["name"], n["type"]
	
	def delete(self):
		self.log.step = "Delete"
		self.log.date = dt.now()
		self.log.msg = "Deleted project"
		print self.params
	def set_doc(self):
		self._doc = self.task.find_one({"_id":self.id})
		if self._doc is None:
			self.log.status= False
			self.log.msg =  "No job found for %s. Exiting" %self.name
			return self.log.push()
		

