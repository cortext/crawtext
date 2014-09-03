#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os, sys

from validate_email import validate_email
from datetime import datetime
from utils import yes_no
from database import *
import requests
from page import Page
from multiprocessing import Pool
import subprocess
from utils.url import *
from query import Query
from scrapper.article import Article		
			 
class Crawl(object):
	def __init__(self, name): 
		self.name = name
		self.option = None
		self.file = None
		self.key = None
		self.query = None		
		#mapping from task_manager
		DB = Database(TASK_MANAGER_NAME)
		COLL = DB.use_coll(TASK_COLL)
		values = COLL.find_one({"name":self.name, "action": "crawl"})
		for k,v in values.items():
			setattr(self, k, v)
		self.db = Database(self.name)
		self.db.create_colls(['sources', 'results', 'logs', 'queue'])	
		
	def get_bing(self, key=None):
		if key is not None:
			self.key = key
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		self.status = {}
		self.status["scope"] = "search seeds from BING"
		print "There is %d sources in database" %self.db.sources.count()
		print "And %d sources with a bad status" %self.db.sources.find({"status":"false"}).count()
		try:
			#defaut is Web could be composite Web + News
			#defaut nb for web is 50 could be more if manipulating offset
			#defaut nb for news is 15 could be more if manipulating offset
			#see doc https://onedrive.live.com/view.aspx?resid=9C9479871FBFA822!112&app=Word&authkey=!ANNnJQREB0kDC04
			r = requests.get(
					'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
					params={
						'$format' : 'json',
						'$top' : 50,
						'Query' : '\'%s\'' %self.query,
					},	
					auth=(self.key, self.key)
					)
			
			r.raise_for_status()
			i = 0
			url_list =  [e["Url"] for e in r.json()['d']['results']]
			for url in url_list:
				status, self.status_code, self.error_type, final_url = check_url(url)
				if status is False:
					self.db.logs.insert({"url": url, "status": status, "msg": "Incorrect format url", "scope": self.status["scope"], "code":self.status_code, "date": datetime.now()})
				else:
					i = i+1
					self.insert_url(url,origin="bing")
					
			self.seeds_nb = i
			self.status["status"] = True
			self.status["msg"] = "Inserted %s urls from Bing results. Sources nb is now : %d" %(self.seeds_nb, self.db.sources.count())
			print self.status["msg"]
			return True
		except Exception as e:
			
			#raise requests error if not 200
			if r.status_code is not None:
				self.status["code"] = r.status_code
			else:
				r.status_code = 601
			self.status["msg"] = "Error fetching results from BING API. %s" %e.args
			self.status["status"] = False
			
			return False
		
		
	def get_local(self, afile = ""):
		''' Method to extract url list from text file'''
		self.status = {}
		self.status["scope"] = "crawl search bing"
		if afile == "":
			afile = self.file
		try:
			i = 0
			for url in open(afile).readlines():
				if url == "\n":
					continue
				url = re.sub("\n", "", url)
				status, status_code, error_type, url = check_url(url)
				if status is True:
					if self.insert_url(url, origin="file") is True:
						i = i+1
				else:
					self.db.logs.insert({"url": url, "status": status, "msg": error_type, "scope": self.status["scope"], "code":status_code, "file": afile})
			self.seeds_nb = i
			self.status["status"] = True
			self.status["msg"] = "%s urls have been added to seeds from %s" %(self.seeds_nb, afile)
			return True
		except Exception as e:
			print e.args[0]
			self.status["code"] = float(str(602)+"."+str(e.args[0]))
			self.status["msg"]= "%s '%s'.\nPlease verify that your file is in the current directory To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			print self.status["msg"]
			return False
		
	
	def expand(self):
		'''Expand sources url adding results urls collected from previous crawl'''
		self.status = {}
		self.status["scope"] = "crawl expand"
		if len(self.db.results.distinct("url")) == 0:
			self.status["status"] = False
			self.status["code"] = 603
			self.status["msg"] = "No results to put in seeds. Expand option failed"
			return False
		else:
			i = 1
			for url in self.db.results.distinct("url"):
				check = self.insert_url(url, "automatic")
				if self.insert_url(url, "automatic") is True:
					i = i+1
					
			self.seed_nb = i
			self.status["status"] = True
			self.status["msg"] = "Successfuly added %s urls in sources" %self.seed_nb	
			return True
				
	def insert_url(self, url, origin="default", depth="0"):
		'''Inséré ou mis à jour'''
		status, status_code, error_type, url = check_url(url)
		is_source = self.db.sources.find_one({"url": url})
		is_error = self.db.logs.find_one({"url": url})
		if is_source is not None:
			if is_error is not None: 
				self.db.sources.update({"url":url},{"$set":{"status": "false", "scope":"inserting"},"$push":{"date": datetime.today()}})
				self.db.logs.update({"_id":is_error["_id"]},{"$set":{"status": "false", "scope": "inserting"},"$push":{"date": datetime.today()}})
				return 
			elif status is False:
				self.db.logs.insert({"url":url,"status": "false", "scope": "inserting","date": [datetime.today()]})
			self.db.sources.update({"url":url},{"$set":{"status": "true"},"$push":{"date": datetime.today()}})
		else:
			self.db.sources.insert({"url":url, "origin":origin, "status": "true","date": [datetime.today()]})
		return 
		'''
		if url in self.db.sources.find({"url": url}):
			print "found", url
			#self.db.sources.update({"url":url}, {"$push": {"date":datetime.today()}})
			
		if url in self.db.logs.find({"url": url}):
			print "found in logs"
			self.db.logs.update({"url":url},{"$push": {"date":datetime.today()}})
			if url in self.db.sources.find({"url":url}):
				self.db.sources.update({"url":url},{"$set":{"status": "false"},"$push":{"date": datetime.today()}})
				#self.db.sources.update({"url":url},{"$push:"{"date": datetime.today()}})
			else:
				self.db.sources.insert({"url":url,"depth":0, "origin":origin,"status": "false","date":[datetime.today()]})
			return False
		else:
			if url in self.db.sources.find({"url":url}):
				self.db.sources.update({"url":url}, {"$set":{"status": "false"}, "$push": {"date":datetime.today()}})
			else:
				self.db.sources.insert({"url":url,"depth":0, "origin":origin,"status": "true","date":[datetime.today()]})
			return True
		'''
	def delete_url(self, url):
		if self.db.sources.find_one({"url": url}) is not None:
			self.db.sources.remove({"url":url})
			return "'%s' has been deleted from seeds" %url
		else:
			return "url %s was not in sources. Check url format" %url
					
	def delete(self):
		e = Export(self.name, "sources")
		print e.run_job()
		print self.db.sources.drop()
		return 'Every single seed has been deleted from crawl job of project %s.'%self.name		
		
	def collect_sources(self):
		''' collect sources from options expand key or file'''
		if self.option == "expand":
			if self.expand() is False:
				return self.status
				#self.status['msg']= self.
		if self.file is not None:
			#print "Getting seeds from file %s" %self.file
			if self.get_local(self.file) is False:
				return self.status
				
		if self.key is not None:
			if self.query is None:
				print "collecting sources from bing"
				self.status["msg"] = "Unable to start crawl: no query has been set."
				self.status["code"] = 600.1
				self.status["status"] = False
				self.status["scope"] = "collecting sources"
				return False
			else:
				if self.get_bing() is False:
					return self.status
		return self.send_seeds_to_queue()
			
	def send_seeds_to_queue(self):
		print "sending urls to queue"
		for i, doc in enumerate(self.db.sources.find()):
			print i
			if doc["status"] == "false":
				pass
			else:
				self.db.queue.insert(doc)
			
		return True
				
	def run_job(self):
		self.status = {}
		self.status["scope"] = "running crawl job"
		
		query = Query(self.query)
			
		self.collect_sources()
		#~ if self.db.sources.count() == 0:
			#~ self.status["msg"] = "Unable to start crawl: no seeds have been set."
			#~ self.status["code"] = 600.1
			#~ self.status["status"] = False
			#~ 
		#~ else:
			#~ self.send_seeds_to_queue()
		#~ 
		start = datetime.now()
		if self.db.queue.count == 0:
			self.status["msg"] = "Error while sending urls into queue: queue is empty"
			self.status["code"] = 600.1
			self.status["status"] = False
			return self.status
		else:
			self.status["msg"] = "running crawl on %i sources with query '%s'" %(len(self.db.sources.distinct("url")), self.query)				
			
			while self.db.queue.count > 0:	
				for url in self.db.queue.distinct("url"):
					# if self.db.results.count() >= 10.000:
					# 	self.db.queue.drop()
						
					if url != "":
						page = Page(url)
						if page.check() and page.request() and page.control():
							article = Article(page.url, page.raw_html)
							if article.get() is True:
								print article.status
								if article.is_relevant(query):			
									self.db.results.insert(article.status)
									if article.outlinks is not None and len(article.outlinks) > 0:
										self.db.queue.insert(article.outlinks)
								else:
									self.db.logs.insert(article.status)	
							else:	
								self.db.logs.insert(article.status)
						else:
							print page.status
							self.db.logs.insert(page.status)	
					self.db.queue.remove({"url": url})
					
					if self.db.queue.count() == 0:		
						break
				if self.db.queue.count() == 0:		
						break
			end = datetime.now()
			elapsed = end - start
			delta = end-start

			self.status["msg"] = "%s. Crawl done sucessfully in %s s" %(self.status["msg"],str(elapsed))
			self.status["status"] = True
		return self.status
	
	def stop(self):		
		self.db.queue.drop()	
		r = Report(self.name)
		r.run_job()
		return "Current crawl job %s stopped." %self.name	
				
class Archive(object):
	def __init__(self, name):
		self.date = datetime.now()
		self.date = self.date.strftime('%d-%m-%Y_%H:%M')
		self.name = name
		self.url = name
	def run_job(self):
		print "Archiving %s" %self.url
		return True

class Export(object):
	def __init__(self, name, form=None, coll_type=None):
		
		self.date = datetime.today()
		
		self.form = form
		if self.form is None:
			self.form = "json"
		self.date = self.date.strftime('%d-%m-%Y')
		
		self.name = name
		self.coll_type = coll_type
		self.dict_values = {}
		self.dict_values["sources"] = {
							"filename": "export_%s_sources_%s.%s" %(self.name, self.date, self.form),
							"format": self.form,
							"fields": 'url,origin,date.date',
							}
		self.dict_values["logs"] = {
							"filename": "export_%s_logs_%s.%s" %(self.name, self.date, self.form), 
							"format":self.form,
							"fields": 'url,code,scope,status,msg',
							}
		self.dict_values["results"] = {
							"filename": "export_%s_results_%s.%s" %(self.name, self.date, self.form), 
							"format":self.form,
							"fields": 'url,domain,title,content.content,outlinks.url,crawl_date',
							}	
		
			
	def export_all(self):
		datasets = ['sources', 'results', 'logs']
		filenames = []
		for n in datasets:
			dict_values = self.dict_values[str(n)]
			if self.form == "csv":
				print "- dataset '%s' in csv:" %n
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,n,dict_values['fields'], dict_values['filename'])	
				filenames.append(dict_values['filename'])		
			else:
				print "- dataset '%s' in json:" %n
				c = "mongoexport -d %s -c %s -o %s"%(self.name,n,dict_values['filename'])				
				filenames.append(dict_values['filename'])
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			#moving into report/name_of_the_project
			
			subprocess.call(["mv",dict_values['filename'], self.directory], stdout=open(os.devnull, 'wb'))
			print "into file: '%s'" %dict_values['filename']
		ziper = "zip %s %s_%s.zip" %(" ".join(filenames), self.name, self.date)
		subprocess.call(ziper.split(" "), stdout=open(os.devnull, 'wb'))
		return "\nSucessfully exported 3 datasets: %s of project %s into directory %s" %(", ".join(datasets), self.name, self.directory)		
	
	def export_one(self):
		if self.coll_type is None:
			return "there is no dataset called %s in your project %s"%(self.coll_type, self.name)
		try:
			dict_values = self.dict_values[str(self.coll_type)]
			if self.form == "csv":
				print "Exporting into csv"
				c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(self.name,self.coll_type,dict_values['fields'], dict_values['filename'])
			else:
				print "Exporting into json"
				c = "mongoexport -d %s -c %s --jsonArray -o %s"%(self.name,self.coll_type,dict_values['filename'])				
			subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
			#moving into report/name_of_the_project
			subprocess.call(["mv",dict_values['filename'], self.directory], stdout=open(os.devnull, 'wb'))
			return "Sucessfully exported %s dataset of project %s into %s/%s" %(str(self.coll_type), str(self.name), self.directory, str(dict_values['filename']))
		except KeyError:
			return "there is no dataset called %s in your project %s"%(self.coll_type, self.name)
			
	def run_job(self):
		name = re.sub("[^0-9a-zA-Z]","_", self.name)
		self.directory = "%s/results/" %name
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		if self.coll_type is not None:
			return self.export_one()
		else:
			return self.export_all()
			
					
class Report(object):
	def __init__(self, name, format="txt"):
		self.date = datetime.now()
		self.name = name
		self.db = Database(self.name)
		self.date = self.date.strftime('%d-%m-%Y_%H-%M')
		self.format = format
	
	def txt_report(self):
		name = re.sub("[^0-9a-zA-Z]","_", self.name)
		self.directory = "%s/reports" %name
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		filename = "%s/Report_%s_%s.txt" %(self.directory, self.name, self.date)
		with open(filename, 'a') as f:
			f.write(self.db.stats())
		print "Successfully generated report for %s\nReport name is: %s" %(self.name, filename)
		return True
	
	def html_report(self):
		pass
	def email_report(self):
		pass			
	def run_job(self):
		if self.format == "txt":
			return self.txt_report()
		else:
			raise NotImplemented
			

