from database import Database
import sys
from datetime import datetime as dt

class Log(object):
	def __init__(self, name):
		self.name = name
		self.date = dt.now()
		self._db = Database(name)
		self._coll = self._db.use_coll("logs")
		self.status = True
		self.code = 0
		self.msg = ""
		self.step = ""
		
	def show(self):
		log = dict()
		log["code"] = self.__dict__["code"]
		values = ["msg", "status", "step"]
		for k in values:
			log[k] = str(self.__dict__[k])
		return log

	def export(self):
		print "Export"
		pass
	
	def push(self):
		log = self.show()
		print log
		self._coll.insert(log)
		print self.step, self.msg
		return self.status

	def pull(self):
		for n in self.task.find({"name":self.name}):
			print n

