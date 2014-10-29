from job import Job
from database import Database

class Stats(Job):
	def start(self):
		db = Database(self.name)
		db.get_error_list()