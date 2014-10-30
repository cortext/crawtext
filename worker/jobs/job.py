
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
		#PROJECT DB
		self._db = Database(self.project_name)
		#Logs
		self._log = Log(self.name)
		self._log.type = self.type
		self._log.action = self.action
		
		
	def create(self):
		self._db.create_colls(["results","sources", "logs", "queue", "treated"])
		self.mk_dir()
		return {"project_name": self.project_name, "name":self.name, "type": self.type, "action":self.action, "creation_date": self.log.date.replace(second=0,microsecond=0), "logs":[self._log], "date": [self._log.date]}

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
		print "Job delete"
		self._log.step = "Delete job"
		self._log.date = dt.now()
		self._log.msg = "Deleted project"
		self._db.drop("database", self.project_name)
		self.rm_dir()
		return self._log.push()
		
	
	def mk_dir(self):
		self.directory = os.path.join(RESULT_PATH, self.project_name)
		print self.directory
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		return self.directory
	def rm_dir(self):
		self.directory = os.path.join(RESULT_PATH, self.project_name)
		print self.directory
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		return self.directory

	def report(self):
		return Report(self._doc, self.debug)	
	def export(self):
		return Export(self._doc, self.debug)	

	def show(self):

		print "=== PARAMS for %s===" %self.name
		for k,v in self.__dict__.items():
			if not k.startswith("_"):
				print "-", k,"==",v  
		print Database(self.project_name).stats()
		return 

class Report(Job):
	def __init__(self, doc, debug):
		Job.__init__(self, doc, debug)
		self.start()
	
	def start(self):
		self._log.step = "Generate report"
		if self._doc is None:
			self._log.status= False
			self._log.msg =  "No job found for %s. Exiting" %self.name
			return self._log.push()
		try:
			if self._doc['user'] is not None:
				print "Hello %s !" %self._doc['user']
				if ask_yes_no("Do you want to receive the report by email?"):
					if self.send_mail(self._doc['user']) is True:
						print "A report email will be send to %s\nCheck your mailbox!" %self._doc['user']
						return 
		except KeyError:
			print "No user has been set: declare a user email for your project to receive it by mail"
		self._log.status= True
		self.report_date = self.date.strftime('%d-%m-%Y_%H-%M')
		self.directory = os.path.join(self.directory, 'reports')
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		filename = "%s/%s.txt" %(self.directory, self.report_date)
		# if self.debug is True:
		# 	d = Debug(self.__dict__)
		# 	logs =  d.export()
		with open(filename, 'a') as f:
			f.write("\n======DATABASE INFO======\n")
			f.write(self._db.stats())
			# f.write("\n======PROCESS INFO======\n")
			# if self.debug is True:
			# 	f.write(self._log.show())
				
		# print self._db.stats()
		
		self._log.msg = ("Successfully generated report for %s\nReport name is: %s") %(self.name, filename)
		return self._log.push()

	def send_mail(self, user):
		from packages.format_email import createhtmlmail
		import smtplib
		from .private import username, passw
		fromaddrs = "crawlex@cortext.net"
		
		toaddrs  = user
		html = self._db.mail_report()
		txt = self._db.stats()
		subject = "Crawlex on Duty: report of %s, breaking news from the front!" %self.name
		msg = createhtmlmail(html, txt, subject, fromaddrs)
		# The actual mail send
		server = smtplib.SMTP('smtp.gmail.com:587')
		server.starttls()
		server.login(username,passw)
		server.sendmail(fromaddrs, toaddrs, msg)
		server.quit()
		return True
class Export(Job):
	def __init__(self,doc, debug):
		Job.__init__(self,doc,debug)
		self.set_params(doc)
		self.set_outfile()
		
		
		
	def set_params(self, doc):
		self.date = datetime.strftime(datetime.now(), "%d-%b-%Y@%H_%M_%S")
		try:
			self.data = doc['data']		
			self.scope = "one"
		except KeyError:
			self.data = ['results', 'logs','sources']
			self.scope = "all"
		try:
			self.format = doc['f']
		except KeyError:
			self.format = "json"
		self.set_fields()
		self.set_outfile()	

	
	def set_outfile(self):
		if self.format == []:
			self.format = "json"
		if self.scope == "one":
			dir_f = "%s_%s.%s" %(self.data, self.date, self.format)
			self.outfile = os.path.join(self.directory, dir_f)
			return self.outfile
		else:

			self.outfile = []
			for n in self.data:
				dir_f = "%s_%s.%s" %(n, self.date, self.format)
				self.outfile.append(os.path.join(self.directory, dir_f))
			return self.outfile
	
	
	def set_fields(self):
		fields = {	"logs":'url,origin,date.date', 
					"results":'url,domain,title,content.content,outlinks.url,crawl_date',
					"sources":'url,origin,date.date,status'
				 }
		if self.scope == "one":
			self.fields =  fields[str(self.data)]
			return self.fields	
		else:
			self.fields = fields
			return self.fields	

	def create(self):
		self._log.step = "creating export"
		if self._doc is None:
			self._log.msg =  "No active project found for %s" %self.name
			self._log.status = False
			self._log.push()
			return False
		else:
			self._log.msg =  "Exporting"
			self._log.status = True
			self._log.push()
	
	def csv(self,data, fields, outfile):
		c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,data,fields,outfile)
		return subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))

	def json(self,data, fields, outfile):
		c = "mongoexport -d %s -c %s -o %s --jsonArray"%(self.name,data, outfile)
		return subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))		
	
	def export_one(self):
		
		self._log.msg = "Exporting %s info of %s into %s" %(self.data, self.name, self.outfile)
		print self._log.msg
		instance = getattr(self, self.format)
		return instance(self.data, self.fields, self.outfile)

	def export_all(self):
		if len(self.format) == 0:
			self.format = "json"
		self._log.msg = "Exporting all collections of %s in %s format" %( self.name, self.format)
		print self._log.msg

		instance = getattr(self, str(self.format))
		
		for coll,f, o in zip(self.data, self.fields, self.outfile):
			instance(coll, f, o)

	def start(self):
		if self._doc is None:
			print "No project %s found" %(self.name)
			return False
		else:
			self._log.step = "Export"
			job = getattr(self, "export_"+self.scope)
			job()
			self._log.push()
			
			
					