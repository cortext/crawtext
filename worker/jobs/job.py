
import re
from datetime import datetime as dt
from ..database import Database
from ..database import TaskDB
from packages.ask_yes_no import ask_yes_no


class Job(object):
	'''defaut job class for worker'''
	
	def __init__(self, doc, debug):
		
		self.debug = debug
		self.name = doc["name"]
		self.action = doc["action"]
		#self.type = doc["type"]
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
		
		#self.log = Log()
	def schedule(self):
		try:
			print self.params['repeat']
			self.task.update({'_id': self.id}, {"$set":{"repeat": self.params["repeat"]}})
		except KeyError:
			print "No recurrence found."
		return 

	def unschedule(self):		
		return self.task.update({'_id': self.id}, {"$unset":{"repeat": self.params["repeat"]}, "$set":{"active":False}})

	def stats(self):
		print self.db.stats()
		return

	def list(self):
		tk = TaskDB()
		for n in tk.find():
			print n["name"], n["type"]
	
	def delete(self):
		print self.params
