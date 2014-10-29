#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
from datetime import datetime
import subprocess
from job import Job 

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
			
			
					