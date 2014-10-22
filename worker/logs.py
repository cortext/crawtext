class Log(Exception):
	DB = TaskDB()
	COLL = DB.coll

	def __init__(self, id, step="", status=False, msg= "", code=""):
		DB = TaskDB()
		COLL = DB.coll
		self.step = step
		self.status = status
		self.msg = msg
		self.code = code

class LogError(Log):
	def __init__(self, id, step="", status=False, msg= "", code=""):
		Log.__init__(id, step="", status=False, msg= "", code="")
		