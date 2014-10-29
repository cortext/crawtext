
import re, os, sys
from datetime import datetime as dt
from database import Database
from database import TaskDB
from packages.ask_yes_no import ask_yes_no
from logs import Log


ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")

class Job(object):
	'''defaut job class for worker'''
	def __init__(self, doc, debug):
		self.debug = debug
		now = dt.now()
		self.date = now.replace(second=0, microsecond=0)
		self._doc = doc
		for k, v in self._doc.items():
			setattr(self, k, v)
		# for k,v in doc.items():
		# 	print k
		# 	setattr(self, k,v)

		#PROJECT DB
		self._db = Database(self.project_name)

		self._db.create_colls(["results","sources", "logs", "queue", "treated"])
		#Logs
		self._log = Log(self.name)
		self._log.type = self.type
		self._log.action = self.action
		self.create_dir()
		
	
	def schedule(self):	
		self._log.step = "Scheduling job"
		self._log.date = dt.now()
		try:	
			self._log.status = True
			self.task.update({'_id': self.id}, {"$set":{"repeat": self.params["repeat"]}})
			self._log.msg = "Job is now scheduled to run every %s" %(self.params["repeat"])
		except KeyError:
			self._log.status = False
			self._log.msg = "No recurrence found."
		self._log.push()
		return 

	def unschedule(self):		
		self._log.step = "Unscheduling job"
		self._log.date = dt.now()
		self._log.msg = "Job is now unscheduled"
		self._log.push()
		return self.task.update({'_id': self.id}, {"$unset":{"repeat": self.params["repeat"]}, "$set":{"active":False}})

	def stats(self):
		self._log.step = "Stats"
		self._log.date = dt.now()
		self._log.msg = "Results overview"
		print self._db.stats()

		return

	def list(self):
		tk = TaskDB()
		for n in tk.find():
			print n["name"], n["type"]
	
	def delete(self):
		self._log.step = "Delete"
		self._log.date = dt.now()
		self._log.msg = "Deleted project"
		self._db.drop("database", self.project_name)
		return 
		
	
	def create_dir(self):
		self.directory = os.path.join(RESULT_PATH, self.project_name)
		print self.directory
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		return self.directory


	def report(self):
		return Report(self.doc, self.debug)
	def export(self):
		return Export(self.doc, self.debug)

	def show(self):
		print "=== PARAMS for %s===" %self.name
		for k,v in self.__dict__.items():
			if not k.startswith("_"):
				print "-", k,"==",v  
		print Database(self.project_name).stats()
		return 

	def start(self):
		_class = (self.type).capitalize
		instance = globals()[_class]	
		print instance
		job = instance(self._doc, self.debug)
		start = getattr(job, str(self.action))
		return start()