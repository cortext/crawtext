from database import Database


class Log(object):
	def __init__(self, db):
		self.name = name
		self.db = Database(name)
		self.coll = self.db.logs		
	
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

