
class Log():
	def __init__(self):
		self.action = None
		self.project_name = None
		self.task = None
		# self.date = []
		# self.active = []
		# self.status = 
		# self.step = []
		# self.code = []
		# self.msg = []
		

	def store_log(self):
		print self._logs
	def clean_job(self):
		pass
	def __update_logs__(self):	
		if self.__data__ is None:
			if self._logs["status"] is True:
				self._logs["msg"]  = "No active '%s' job for project '%s'found" %(self.action, self.name)
				self.create()
			
		try:		
			_id = self.__data__['_id']
			self.__COLL__.update({"_id":_id}, {"$set":{"active":self._logs["status"]}})
			self.__COLL__.update({"_id":_id}, {"$push":{"status":self._logs}})
		except KeyError:
			pass
		if self.debug is True:
			print self._logs["msg"]

		return self._logs["status"]

