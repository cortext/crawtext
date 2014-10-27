#!/usr/bin/env python
# -*- coding: utf-8 -*-

from job import Job
from report_job import Report
from datetime import datetime as dt
import requests

from packages.query import Query
from packages.links import check_url
from extractor.article import Article, ArticleException
from packages.urls import Link, LinkException

class Crawl(Job):
	def add(self):
		self.log.step = "Adding sources"
		self.log.date = dt.now()
		try:
			if self.params['url']:
				self.insert_url(self.params['url'])
				self.log.msg = "Sucessfully added url %s" %(self.params['url'])
				self.log.status = True
			elif self.params['file']:
				self.file = self.params['file']
				self.log.msg = "Sucessfully added urls from file %s" %(self.params['file'])
				self.log.status = True
				self.get_local()
			elif self.params['email']:
				self.log.msg = "Sucessfully added owner %s" %(self.params['email'])
				self.log.status = True
				self.task.update({'_id': self.id}, {"$push":{"user": self.params["email"]}})
			elif self.params['user']:
				self.log.msg = "Sucessfully added owner %s" %(self.params['user'])
				self.log.status = True
				self.task.update({'_id': self.id}, {"$push":{"user": self.params["user"]}})
			return self.log.push()
		except KeyError:
			self.log.msg = "Error: Unable to add url file or user to project %s.\nYou can only add file , url or user to project\nPlease add one of the following parameters:\n\t--url='www.yoururl.com'\n\t--file='yourfile.txt'\n\t--user='you@cortext.net'" %self.name
			self.log.status = False
			return self.log.push()

	def update_sources(self):
		self.log.step = "Update sources"
		self.log.date = dt.now()
		if self._doc is None:
			self.log.msg =  "No existing project %s with %s job" %(self.name, self.action)
			self.log.status = False
			self.log.push()
			return self.create()
		


	def get_bing(self, key=None):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		self.log.step = "Searching sources from Bing"
		if key is not None:
			self.key = key
		if self.key == None:
			self.log.msg = "No API key registered"
			self.log.code = 600.3
			self.log.status = False
			self.log.push()
			return False
		else:
			print self.db.sources.count(), "sources in db"
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
				for i, url in enumerate(url_list):
					i = i+1
					self.insert_url(url, origin="bing",depth=0)
				
				
				self.log.msg =  "Inserted %s urls from Bing results" %str(i)
				self.log.status = True
				self.log.push()
				return True

			except Exception as e:
				self.log.code = "601"+"."+str(e.args[0])
				self.log.msg = "Error adding sources from BING: %s" %e.args
				self.log.status = False
				self.log.push()
				return False
		
	def get_local(self, afile = None):
		''' Method to extract url list from text file'''
		self.log.step = "local file extraction"
		if afile != None:
			self.file = a.file
		try:
			for url in open(self.file).readlines():
				if url == "\n":
					continue
				url = re.sub("\n", "", url)
				status, status_code, error_type, url = check_url(url)
				self.insert_url(url, origin="file", depth=0)
				
			self.log.status = True
			self.log.msg = "Urls from file %s have been successfuly added to sources" %(self.file)
			self.log.push()
			return True
		
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self.log.code = float(str(602)+"."+str(e.args[0]))
			self.log.status = False
			self.log.msg= "Failed inserting url for file %s : %s %s" %(self.file, e.args[1],"./"+self.file)
			self.log.push()	
			return False

	def delete_local(self):
		'''delete sources contained in self.file'''
		self.log.step = "deleting sources from file"
		self.log.status = True
		self.log.msg = "Urls sucessfully deleted"
		#~ print "Removing the list of url contained in the file %s" %self.file
		try:
			for url in open(self.file).readlines():
				url = re.sub("\n", "", url)
				self.db.sources.remove({"url":url})
			self.log.push()
			return True

		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self.log.code = float(str(602)+"."+str(e.args[0]))
			self.log.status = False
			self.log.msg= "Failed deleting url for file %s failed : %s '." %(self.file, e.args[1])
			self.log.push()
			return False
		
	def expand_sources(self):
		'''Expand sources url adding results urls collected from previous crawl'''
		self.log.step = "expanding sources from results"
		self.log.status = True
		self.log.msg = "Urls from results sucessfully inserted into sources"
		for url in self.db.results.distinct("url"):
			self.insert_url(url, "automatic", depth=0)
		
		if len(self.db.results.distinct("url")) == 0 :
			self.log.status = False
			self.log.code = 603
			self.log.msg = "No results to put in seeds. Expand option failed"
		self.log.push()
		return self.logs["status"]	
	
	def add_sources(self):
		self.update_sources()
		self.log.step = "adding sources from user_input"
		self.log.status = True
		self.log.msg = "Urls sucessfully inserted into sources"
		
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.log.msg = "Not url but file: all urls in the file will be added"
				self.log.push()
				self.file = self.url
				self.get_local()
				

			else:
				self.log.msg = "Url %s sucessfully inserted into sources" %self.url
				url = check_url(self.url)[-1]				
				self.insert_url(url,"manual", depth=0)
				
		return self.log.push()

		#???? Ca doit etre les reste de la creation d'objet?
		#self.__COLL__.update({"_id": self._doc["_id"]},{"$unset":{"url": self.url}})
		
	def delete_sources(self):
		self.log.step = "deleting sources"
		self.log.status = True
		self.log.msg = "Urls sucessfully deleted"
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.log.msg = "Not url but file: all urls in the file will be deleted"
				self.file = self.url
				self.log.status = self.delete_local()
				
				

			else:
				url = check_url(self.url)[-1]
				if url in self.db.sources.distinct("url"):
					self.log.status = self.db.sources.remove({"url":url})
					self.log.msg = "Succesfully deleted url %s to sources db of project %s"%(url, self.name)
					self._logs['inactive'] = "True"
				else:
					self.log.msg = "No url %s found in sources db of %s project"%(url, self.name)
					self._logs['inactive'] = "True"
					self.log.status = False
		else:
			self.db.sources.drop()
			self.log.msg = "Succesfully deleted every url %s to seeds of crawl job %s"%(url, self.name)
			self._logs['inactive'] = "True"
		return self.log.push()
		
	def insert_url(self, url, origin="default", depth=0):
		'''Insert or updated url into sources if false inserted or updated into logs'''
		# self.log.step = "inserting url"
		# self.log.status = True
		# self.log.msg = "Urls sucessfully inserted"
		link = Link(url)
		link.parse()
		print link.is_valid()
		print link.__dict__
		return self.db.sources.insert(link.__dict__, upsert=False)
		'''
		link = Link(url)
		if link.is_valid():

		is_source = self.db.sources.find_one({"url": url})
		
		#incorrect url
		if status is False:
			self.log.status = False
			#existing
			if url in self.db.logs.distinct("url"):
				pass
				#self.log.msg = "Error inserting url: updated url %s in logs" %url
				#self.db.logs.update({"url":url}, {"$push":{"date": self.date, "scope": self.log.step, "msg":self.log.msg, "code": status_code, "status": "False"}})
			#new
			else:
				pass
				#self.log.msg = "Status is false error inserting url"
				#self.db.logs.insert({"url":url, "status": status, "code": [status_code], "msg":[error_type], "origin":[origin], "depth":[depth],"scope":[self.log.step], "date": [self.date]})
				#self._logs['msg'] = "Incorrect url %s.\n%s\n Not inserted into sources but logs" %(url, error_type)
			
		#existing url
		elif is_source is not None:
			self.db.sources.update({"url":url},{"$set":{"status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth, "scope":"inserting"},"$push":{"date": self.date}})
			self._logs['msg'] = "Succesfully updated existing url %s into sources" %url
		
		#new url
		else:
			self.db.sources.insert({"url":url, "status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth,"scope":"inserting", "date": [self.date]})
			self._logs['msg'] = "Succesfully inserted new url %s into sources" %url
		self.log.push()
		'''

		return status 
		
	def delete_url(self, url):
		self.log.step = "Deleting url"
		self.log.status = True
		self.log.msg = "Urls sucessfully deleted"
		if self.db.sources.find_one({"url": url}) is not None:
			self.db.sources.remove({"url":url})
			
		else:
			self.log.msg = "Url can't be deleted. Url %s was not in sources. Check url format" %url
			self.log.status = False
		
		return self.log.push()
		
			
	def send_seeds_to_queue(self):
		self.log.step = "Sending seeds urls to start crawl"
		self.log.status = True
		for doc in self.db.sources.find():
			if doc["status"] is True:
				self.db.queue.insert({"url":doc["url"], "depth":doc["depth"]})
		if self.db.queue.count() == 0:
			self.log.msg = "Error while sending urls into queue: queue is empty. check sources status"
			self.log.code = 600.1
			self.log.status = False
			
		return self.log.push()
				
	def config(self):
		'''initializing  the crawl job with required params'''
		self._doc = self.task.find_one({"name":self.name})
		#, "type": self.type
		self.log.step = "Crawl job configuration"
		self.query = None
		self.file = None
		self.option = None
		self.key = None
		self.log.status = True
		self.log.msg = "Configuration"
		
		for k, v in self._doc.items():
			setattr(self,k,v)

		
		if self.query is None:
			self.log.msg = "Config error: no query has been set."
			self.log.status = False
			self.log.code = 600.1
			
			return self.log.push()

		self.woosh_query = Query(self.query)

		if self.option == "expand_sources":
			self.log.msg = "Config : expand mode"
			self.log.code = 600.4
			self.log.status = self.expand_sources()
				
			
		if self.file is not None:
			self.log.msg = "Getting seeds from file %s" %self.file
			self.log.code = 600.5
			self.log.status  = self.get_local(self.file)
			

		if self.key is not None:
			self.log.msg = "Config : Bing search for new sources"
			self.log.code = 600.2
			self.log.status = self.get_bing()
			if self.log.status is False:
				self.log.msg = "Config : No API Key for searching new sources."
				if self.db.sources.count() == 0:
					self.log.status = False		
				else:
					self.log.status = True
					
		if self.db.sources.count() == 0:
			self.log.msg = "No sources registered"
			self.log.code = 600.3
			self.log.status = False
			self.log.push()
			return False
		
		self.log.status = self.send_seeds_to_queue()
		
		return self.log.push()

		
		
		
	def start(self):
		if self.config() is False:
			print self.log.msg
			print self.log.msg
			return self.log.push()
		else:	
			self.log.msg = "Running crawl job  on %s" %self.date
			print self.log.msg 
			start = dt.now()
			for doc in self.db.queue.find():
				try:
					depth = doc["depth"]
				except KeyError:
					depth = 0
				try:
					source_url = doc["source_url"]
				except KeyError:
					source_url = None
				print self.db.queue.find().count(), "in queue"
				link = Link(doc["url"],source_url=source_url, depth=depth)
				if link.is_valid():
					if link.url not in self.db.results.distinct('url') or link.url not in self.db.logs.distinct('url'):
						page = Article(link, depth)
						try:
							page.build()
							try:
								page.is_relevant(self.woosh_query)
								existing = self.db.results.find_one({"url": page.url})
								if existing is not None:
									existing = self.db.results.update({"_id": existing['_id']},{"$push":{"date": page.date}})
								else:
									self.db.results.insert(page.json())
								for link in page.outlinks:
									if link not in self.db.results.distinct('url'):
										self.db.queue.insert({"url":link, "depth": page.depth+1})
								print page.title
							except ArticleException:
								res = self.db.logs.find_one({"url": page.url})
								if res is not None:
									print self.db.logs.update({"_id": res['_id']},{"$push":{"date": page.date}})
									del page.date
									print self.db.sources.update({"_id": res['_id']},{"$set":page.log})
								else:
									print self.db.logs.insert(page.log)

						except LinkException:
							source = self.db.sources.find_one({"url": page.url})
							if source is not None:
								print self.db.sources.update({"_id": source['_id']},{"$push":{"date": page.date}})
								del page.date
								print self.db.sources.update({"_id": source['_id']},{"$set":page.log})
							else:
								print self.db.logs.insert(page.log)
						except ArticleException:
							res = self.db.logs.find_one({"url": page.url})
							if res is not None:
								print self.db.logs.update({"_id": res['_id']},{"$push":{"date": page.date}})
								del page.date
								print self.db.sources.update({"_id": res['_id']},{"$set":page.log})
							else:
								print self.db.logs.insert(page.log)

								#print self.db.logs.upsert({"url": page.url}, {page.log, {"date":[page.log.date]})
						#print page.url
						#if page.build() is not False:
						#	print page.title
							#print page.links
					# print url, page.depth
					# try:
					# 	if page.is_relevant(self.woosh_query):
					# 		self.db.results.insert(page.pretty())
					# 		next_links = [{"url":link, "depth": doc['depth']+1} for link in page.outlinks]
					# 		if len(next_links) != 0:
					# 			self.db.queue.insert(next_links)
						
					'''
						# else:
						# 	if page.url not in self.db.results.distinct("url"):
						# 		self.db.results.insert(page)
					# 	else:
					# 		self.db.sources.insert(article._logs)
					# else:
					# 	self.db.sources.insert(page._logs)
					'''
					self.db.queue.remove({"url": doc["url"]})
					
			end = dt.now()
			elapsed = end - start
			delta = end-start

			self.log.msg = "%s. Crawl done sucessfully in %s s" %(self.log.msg,str(elapsed))
			self.log.status = True
			return self.log.push()
		
		
	
	def stop(self):
		self.log.step = "Stopping exec of job of crawl project %s" %(self.name)
		self.log.msg = "Stopping crawl job on %s" %self.date
		self.db.queue.drop()
		self.log.status = True	
		return self.log.status
		#~ r = Report(self.name)
		#~ r.run_job()
	def report(self):
		return Report(self.__dict__)