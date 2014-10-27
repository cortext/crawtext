#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
import subprocess
from job import Job 

class Export(Job):
	def __init__(self,doc, debug):
		Job.__init__(self, doc, debug)
		try:
			self.format = self.format
		except AttributeError:
			self.format = "json"
		try:
			self.data = self.data
		except AttributeError:
			self.data = None
	

		self._dict_values = {}
		self._dict_values["sources"] = {
							"filename": "./%s/export_%s_sources_%s.%s" %(self.project_name, self.name, self.date, self.format),
							"format": self.format,
							"fields": 'url,origin,date.date',
							}
		self._dict_values["logs"] = {
							"filename": "./%s/export_%s_logs_%s.%s" %(self.project_name,self.name, self.date, self.format), 
							"format":self.format,
							"fields": 'url,code,scope,status,msg',
							}
		self._dict_values["results"] = {
							"filename": "./%s/export_%s_results_%s.%s" %(self.project_name,self.name, self.date, self.format), 
							"format":self.format,
							"fields": 'url,domain,title,content.content,outlinks.url,crawl_date',
							}	
							
	def create(self):
		self.log.step = "creating export"
		if self._doc is None:
			self.log.msg =  "No active project found for %s" %self.name
			self.log.status = False
			self.log.push()
			return False
		else:
			self.log.msg =  "Exporting"
			self.log.status = True
			self.log.push()
			if self.data is not None:
				return self.export_one()
			else:
				return self.export_all()		
			
	def export_all(self):
		self.log.step = "export all"
		datasets = ['sources', 'results', 'logs']
		filenames = []
		for n in datasets:
			file_info = self._dict_values[str(n)]
			if self.format == "csv":
				print ("- dataset '%s' in csv:") %n
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,n,file_info['fields'], file_info['filename'])	
				filenames.append(file_info['filename'])		
			else:
				print ("- dataset '%s' in json:") %n
				c = "mongoexport -d %s -c %s -o %s"%(self.name,n,file_info['filename'])				
				filenames.append(file_info['filename'])
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			
			
			#subprocess.call(["mv",dict_values['filename'], self.project_name], stdout=open(os.devnull, 'wb'))
			print ("into file: '%s'") %file_info['filename']
		print filenames
		ziper = "zip %s %s_%s.zip" %(" ".join(filenames), self.name, self.date)
		subprocess.call(ziper.split(" "), stdout=open(os.devnull, 'wb'))
		self.log.status = True
		self.log.msg= "\nSucessfully exported 3 datasets: %s of project %s into directory %s" %(", ".join(datasets), self.name, self.project_name)		
		return self.log.push()
	
	def export_one(self):
		self.log.step = "export one"
		if self.data is None:
			self.log.status = False
			self.log.msg =  "there is no dataset called %s in your project %s"%(self.data, self.name)
			return self.log.push()
		try:
			dict_values = self._dict_values[str(self.data)]
			if self.form == "csv":
				print ("Exporting into csv")
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,self.data,dict_values['fields'], dict_values['filename'])
			else:
				print ("Exporting into json")
				c = "mongoexport -d %s -c %s --jsonArray -o %s"%(self.name,self.data,dict_values['filename'])				
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			#moving into report/name_of_the_project
			subprocess.call(["mv",dict_values['filename'], self.project_name], stdout=open(os.devnull, 'wb'))
			self.log.status = False
			self.log.msg =  "Sucessfully exported %s dataset of project %s into %s" %(str(self.data), str(self.name), self.project_name, str(dict_values['filename']))
			return self.log.push()
			
		except KeyError:
			self.log.status = False
			self.log.msg =  "there is no dataset called %s in your project %s"%(self.data, self.name)
			return self.log.push()
			
	def start(self):
		if self.data is not None:
			return self.export_one()
		else:
			return self.export_all()
			
					