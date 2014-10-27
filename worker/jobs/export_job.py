#!/usr/bin/env python
# -*- coding: utf-8 -*-


from job import Job 

class Export(Job):
	def __init__(self,doc):
		Job.__init__(self, doc)
		try:
			self.format = self.format
		except AttributeError:
			self.format = "json"
		try:
			self.coll_type = self.coll_type
		except AttributeError:
			self.coll_type = None
		
		self._dict_values = {}
		self._dict_values["sources"] = {
							"filename": "%s/export_%s_sources_%s.%s" %(self.project_name, self.name, self.date, self.format),
							"format": self.format,
							"fields": 'url,origin,date.date',
							}
		self._dict_values["logs"] = {
							"filename": "%s/export_%s_logs_%s.%s" %(self.project_name,self.name, self.date, self.format), 
							"format":self.format,
							"fields": 'url,code,scope,status,msg',
							}
		self._dict_values["results"] = {
							"filename": "%s/export_%s_results_%s.%s" %(self.project_name,self.name, self.date, self.format), 
							"format":self.format,
							"fields": 'url,domain,title,content.content,outlinks.url,crawl_date',
							}	
							
	def create(self):
		self._logs['step'] = "creating export"
		if self.__data__ is None:
			self._logs['msg'] =  "No active project found for %s" %self.name
			self._logs['status'] = False
			self.__update_logs__()
			return False
		else:
			self._logs['msg'] =  "Exporting"
			self._logs['status'] = True
			self.__update_logs__()
			if self.coll_type is not None:
				return self.export_one()
			else:
				return self.export_all()		
			
	def export_all(self):
		self._logs['step'] = "export all"
		datasets = ['sources', 'results', 'logs']
		filenames = []
		for n in datasets:
			dict_values = self.dict_values[str(n)]
			if self.format == "csv":
				print ("- dataset '%s' in csv:") %n
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,n,dict_values['fields'], dict_values['filename'])	
				filenames.append(dict_values['filename'])		
			else:
				print ("- dataset '%s' in json:") %n
				c = "mongoexport -d %s -c %s -o %s"%(self.name,n,dict_values['filename'])				
				filenames.append(dict_values['filename'])
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			
			
			#subprocess.call(["mv",dict_values['filename'], self.project_name], stdout=open(os.devnull, 'wb'))
			print ("into file: '%s'") %dict_values['filename']
		
		ziper = "zip %s %s_%s.zip" %(" ".join(filenames), self.name, self.date)
		subprocess.call(ziper.split(" "), stdout=open(os.devnull, 'wb'))
		self._logs['status'] = True
		self._logs['msg']= "\nSucessfully exported 3 datasets: %s of project %s into directory %s" %(", ".join(datasets), self.name, self.project_name)		
		return self.__udpate_logs__()
	
	def export_one(self):
		self._logs['step'] = "export one"
		if self.coll_type is None:
			self._logs['status'] = False
			self._logs['msg'] =  "there is no dataset called %s in your project %s"%(self.coll_type, self.name)
			return self.__udpate_logs__()
		try:
			dict_values = self.dict_values[str(self.coll_type)]
			if self.form == "csv":
				print ("Exporting into csv")
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,self.coll_type,dict_values['fields'], dict_values['filename'])
			else:
				print ("Exporting into json")
				c = "mongoexport -d %s -c %s --jsonArray -o %s"%(self.name,self.coll_type,dict_values['filename'])				
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			#moving into report/name_of_the_project
			subprocess.call(["mv",dict_values['filename'], self.project_name], stdout=open(os.devnull, 'wb'))
			self._logs['status'] = False
			self._logs['msg'] =  "Sucessfully exported %s dataset of project %s into %s/%s" %(str(self.coll_type), str(self.name), self.project_name, str(dict_values['filename']))
			return self.__udpate__logs()
			
		except KeyError:
			self._logs['status'] = False
			self._logs['msg'] =  "there is no dataset called %s in your project %s"%(self.coll_type, self.name)
			return self.__udpate__logs()
			
	def start(self):
		if self.coll_type is not None:
			return self.export_one()
		else:
			return self.export_all()
			
					