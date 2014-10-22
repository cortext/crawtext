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
		self.db = Database(self.name)
		self.db.create_colls(['sources', 'results', 'logs', 'queue'])	
		self.logs = {}
		self.logs["step"] = "crawl init"
		date = datetime.now()
		self.date = date.strftime('%d-%m-%Y_%H:%M')
		
	def get_bing(self, key=None):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		self.logs["step"] = "bing extraction"
		if key is not None:
			self.key = key
		
		#~ print "There is already %d sources in database" %nb
		#~ print "and %d sources with a bad status" %self.db.sources.find({"status":"false"}).count()
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
			url_list =  [e["Url"] for e in r.json()['d']['results']]
			for url in url_list:
				self.insert_url(url,origin="bing",depth=0)
			count = self.db.sources.count() - nb
			self.logs["msg"] =  "Inserted %s urls from Bing results. Sources nb is now : %d" %(count, nb)
			self.logs["status"] = True
		
		except Exception as e:
			#raise requests error if not 200
			try:
				if r.status_code is not None:
					self.logs["code"] = r.status_code
					self.logs["status"] = False
					self.logs["msg"] = "Error requestings new sources from Bing :%s" %e
					#~ print "Error requestings new sources from Bing :%s" %e
					
			except Exception as e:
				#~ print "Error requestings new sources from Bing :%s" %e
				self.logs["code"] = float(str(601)+"."+str(e.args[0]))
				self.logs["msg"] = "Error fetching results from BING API. %s" %e.args
				self.logs["status"] = False
		
		return self.logs["status"]		
		
		
	def get_local(self, afile = None):
		''' Method to extract url list from text file'''
		self.logs["step"] = "local file extraction"
		if afile is None:
			afile = self.file
		try:
			for url in open(afile).readlines():
				if url == "\n":
					continue
				url = re.sub("\n", "", url)
				status, status_code, error_type, url = check_url(url)
				self.insert_url(url, origin="file", depth=0)
				
			self.logs["status"] = True
			self.logs["msg"] = "Urls from file %s have been successfuly added to sources" %(afile)
			
		
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self.logs["code"] = float(str(602)+"."+str(e.args[0]))
			self.logs["status"] = False
			self.logs["msg"]= "Failed inserting url for file %s : %s '." %(self.file, e.args[1])
		return self.logs["status"]		
		
	def delete_local(self):
		'''delete sources contained in self.file'''
		self.logs["step"] = "deleting sources from file"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully deleted"
		#~ print "Removing the list of url contained in the file %s" %self.file
		try:
			for url in open(self.file).readlines():
				url = re.sub("\n", "", url)
				self.db.sources.remove({"url":url})	
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self.logs["code"] = float(str(602)+"."+str(e.args[0]))
			self.logs["status"] = False
			self.logs["msg"]= "Failed deleting url for file %s failed : %s '." %(self.file, e.args[1])
		return self.logs["status"]
		
	def expand_sources(self):
		'''Expand sources url adding results urls collected from previous crawl'''
		self.logs["step"] = "expanding sources from results"
		self.logs["status"] = True
		self.logs["msg"] = "Urls from results sucessfully inserted into sources"
		for url in self.db.results.distinct("url"):
			self.insert_url(url, "automatic", depth=0)
		
		if len(self.db.results.distinct("url")) == 0 :
			self.logs["status"] = False
			self.logs["code"] = 603
			self.logs["msg"] = "No results to put in seeds. Expand option failed"
		return self.logs["status"]
			
	def add_sources(self):
		self.logs["step"] = "adding sources from user_input"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully inserted into sources"
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.file = self.url
				self.get_local()
			else:
				self.logs["msg"] = "Url %s sucessfully inserted into sources" %self.url
				url = check_url(self.url)[-1]
				self.insert_url(url,"manual", depth=0)			
		return self.logs["status"]
		
	def delete_sources(self):
		self.logs["step"] = "deleting sources from user_input"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully deleted"
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.file = self.url
				self.delete_local()
			else:
				url = check_url(self.url)[-1]
				if url in self.db.sources.distinct("url"):
					self.db.sources.remove({"url":url})
					self.logs["msg"] = "Succesfully deleted url %s to sources db of project %s"%(url, self.name)
				else:
					self.logs["msg"] = "No url %s found in sources db of %s project"%(url, self.name)
		else:
			self.db.sources.drop()
			self.logs["msg"] = "Succesfully deleted every url %s to seeds of crawl job %s"%(url, self.name)
		return self.logs["status"]
		
	def insert_url(self, url, origin="default", depth=0):
		'''Insert or updated url into sources if false inserted or updated into logs'''
		self.logs["step"] = "inserting url"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully inserted"
		status, status_code, error_type, url = check_url(url)
		is_source = self.db.sources.find_one({"url": url})
		
		#incorrect url
		if status is False:
			self.logs["status"] = False
			#existing
			if url in self.db.logs.distinct("url"):
				self.logs["msg"] = "Error inserting url: updated url %s in logs" %url
				self.db.logs.update({"url":url}, {"$push":{"date": self.date, "scope": self.logs["scope"], "msg":self.logs["msg"], "code": status_code}})
			#new
			else:
				self.logs["msg"] = "Error inserting url: inserted url %s in logs"%url
				self.db.logs.insert({"url":url, "status": status, "code": [status_code], "msg":[error_type], "origin":origin, "depth":depth,"scope":[self.logs["scope"]], "date": self.date})
			self.logs['msg'] = "Incorrect url %s.\n%s\n Not inserted into sources" %(url, error_type)
		
		#existing url
		elif is_source is not None:
			self.db.sources.update({"url":url},{"$set":{"status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth, "scope":"inserting"},"$push":{"date": self.date}})
			self.logs['msg'] = "Succesfully updated existing url %s into sources" %url
		
		#new url
		else:
			self.db.sources.insert({"url":url, "status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth,"scope":"inserting", "date": [self.date]})
			self.logs['msg'] = "Succesfully inserted new url %s into sources" %url
		return self.logs["status"] 
		
	def delete_url(self, url):
		self.logs["step"] = "Deleting url"
		self.logs["status"] = True
		self.logs["msg"] = "Urls sucessfully deleted"
		if self.db.sources.find_one({"url": url}) is not None:
			self.db.sources.remove({"url":url})
			
		else:
			self.logs["msg"] = "Url can't be deleted. Url %s was not in sources. Check url format" %url
			self.logs["status"] = False
		
		return self.logs["status"]
					
	def delete(self):
		''' Deleting sources from user_input'''
		self.logs["step"] = "Deleting sources"
		#~ e = Export(self.name, "json","sources")
		#~ e.run_job()
		self.db.sources.drop()
		self.logs["msg"] = 'Every single source has been deleted from project %s.'%self.name		
		return self.logs["status"]
		
	def collect_sources(self):
		''' collect sources from options expand key or file'''
		self.logs["step"] = "Collecting sources"
		self.logs["status"] = True
		if self.option == "expand_sources":
			self.expand_sources()
			
				
		if self.file is not None:
			#print "Getting seeds from file %s" %self.file
			self.get_local(self.file)
				
		if self.key is not None:
			if self.query is None:
				self.logs["msg"] = "Unable to collect sources from Bing search no query has been set."
				self.logs["code"] = 600.1
				self.logs["status"] = False
				
			else:
				self.get_bing() 
		return self.logs["status"]
			
	def send_seeds_to_queue(self):
		self.logs["step"] = "Sending seeds urls to start crawl"
		for doc in self.db.sources.find():
			self.db.queue.insert({"url":doc["url"], "depth":doc["depth"], "status": doc["status"]})
		if self.db.queue.count() == 0:
			self.logs["msg"] = "Error while sending urls into queue: queue is empty"
			self.logs["code"] = 600.1
			self.logs["status"] = False
		return self.logs["status"]	
				
	def config(self):
		'''initializing  the crawl job with required params'''
		self.logs["scope"] = "config crawl job"
		if self.query is not None:
			self.query = Query(self.query)
		
		self.collect_sources()
		
		if self.db.sources.count() == 0:
			self.logs["msg"] = "Unable to start crawl: no seeds have been set."
			self.logs["code"] = 600.2
			self.logs["status"] = False
			print self.logs	
		else:
			self.send_seeds_to_queue()			
		
		return self.logs["status"]
		
	def run_job(self):
		if self.config() is False:
			return self.logs
		
		self.logs["msg"] = "Running crawl job  on %s" %self.date
		start = datetime.now()
		for doc in self.db.queue.find():
			if doc["url"] != "":
				page = Page(doc["url"],doc["depth"])
				page = Page(doc["url"],0)
					
				if page.check() and page.request() and page.control():
					article = Article(page.url, page.raw_html, page.depth)
					if article.get() is True:
						print article.status
						if article.is_relevant(self.query):		
							if article.status not in self.db.results.find(article.status):
								self.db.results.insert(article.status)
							else:
								article["status"] = False
								article["msg"]= "article already in db"
								self.db.logs.insert(article.status)	
							
							if article.outlinks is not None and len(article.outlinks) > 0:
								#if article.outlinks not in self.db.results.find(article.outlinks) and article.outlinks not in self.db.logs.find(article.outlinks) and article.outlinks not in self.db.queue.find(article.outlinks):
								for url in article.outlinks:
									if url not in self.db.queue.distinct("url"):
										self.db.queue.insert({"url":url, "depth": page.depth+1})
								
					else:
						self.db.logs.insert(article.status)	
				else:	
					self.db.logs.insert(article.status)
			else:
				self.db.logs.insert(page.status)
			self.db.queue.remove({"url": doc["url"]})
					
		end = datetime.now()
		elapsed = end - start
		delta = end-start

		self.logs["msg"] = "%s. Crawl done sucessfully in %s s" %(self.logs["msg"],str(elapsed))
		self.logs["status"] = True
		return self.logs
	
	def stop(self):
		self.logs["step"] = "Stopping exec of job of %s project %s" %(self.action, self.name)
		self.logs["msg"] = "Stopping crawl job on %s" %self.date
		self.db.queue.drop()
		self.logs["status"] = True	
		return self.logs["status"]
		#~ r = Report(self.name)
		#~ r.run_job()
		
				
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
		
		date = datetime.today()
		self.date = date.strftime('%d-%m-%Y')
		self.form = form
		if self.form is None:
			self.form = "json"
		
		
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
		date = datetime.now()
		self.name = name
		self.db = Database(self.name)
		self.date = date.strftime('%d-%m-%Y_%H-%M')
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
			

