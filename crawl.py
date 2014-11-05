from datetime import datetime as dt

class Crawl(object):
	def __init__(self, params):
		for k,v in params.items():
			setattr(self,k, v)
		self.db = Database(self.project_name)
	
	

	def config(self):
		#adding to sources
		if self.file:
			self.get_local()
		elif self.url:
			self.add_url()
		elif self.key():
			self.add_bing()
	
	def request(self):
		pass
	def extract(self):
		pass
	def process(self):
		pass
	#def start(self):


