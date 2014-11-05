from database import Database
import sys
from datetime import datetime as dt
class Log(object):
	def __init__(self, name):
		self.name = name
		self.db = Database(name)
		self.coll = self.db.use_coll("logs")
		self.status = True
		self.code = 0
		self.msg = ""
		self.step = ""
		self.date = dt.now()
	def show(self):
		log = {}
		values = ["msg", "status", "code", "step"]
		for k in values:
			log[k] = self.__dict__[k]
		return log

	def export(self):
		print "Export"
		pass
	
	def push(self):
		self.coll.insert(self.show())
		print self.msg
		if self.status is False:
			return sys.exit()

	def pull(self):
		for n in self.task.find({"name":self.name}):
			print n

