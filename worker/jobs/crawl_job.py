#!/usr/bin/env python
# -*- coding: utf-8 -*-

from job import Job
from datetime import datetime as dt
import requests

from packages.query import Query
from packages.links import check_url
from extractor.article import Article, ArticleException
from packages.urls import Link, LinkException

class Crawl(Job):	
	def update_sources(self):
		if self.__data__ is None:
			print "No existing project %s with %s job" %(self.name, self.action)
			self.create()
			return self.log.update()

	def get_bing(self, key=None):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		self.log.step = "bing extraction"
		if key is not None:
			self.key = key
		if self.key == None:
			self.log.msg = "No API key registered"
			self.log.code = 600.3
			self.log.status = False
			self.log.update()
			return False
		else:
			print self.__db__.sources.count(), "sources in db"
			#~ print "There is already %d sources in database" %nb
			#~ print "and %d sources with a bad status" %self.__db__.sources.find({"status":"false"}).count()
			
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
				
				
				self.log.msg =  "Inserted %s urls from Bing results. Sources nb is now : %d" %(i, self.__db__.sources.count())
				self.log.status = True
				self.log.update()
				return True

			except Exception as e:
				self.log.code = "601"+"."+str(e.args[0])
				self.log.msg = "Error adding sources from BING: %s" %e.args
				self.log.status = False
				self.log.update()	
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
			self.log.update()
			return True
		
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self.log.code = float(str(602)+"."+str(e.args[0]))
			self.log.status = False
			self.log.msg"]= "Failed inserting url for file %s : %s %s" %(self.file, e.args[1],"./"+self.file)
			self.log.update()
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
				self.__db__.sources.remove({"url":url})
			return True

		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self.log.code = float(str(602)+"."+str(e.args[0]))
			self.log.status = False
			self.log.msg"]= "Failed deleting url for file %s failed : %s '." %(self.file, e.args[1])
			self.log.update()
			return False
		
	def expand_sources(self):
		'''Expand sources url adding results urls collected from previous crawl'''
		self.log.step = "expanding sources from results"
		self.log.status = True
		self.log.msg = "Urls from results sucessfully inserted into sources"
		for url in self.__db__.results.distinct("url"):
			self.insert_url(url, "automatic", depth=0)
		
		if len(self.__db__.results.distinct("url")) == 0 :
			self.log.status = False
			self.log.code = 603
			self.log.msg = "No results to put in seeds. Expand option failed"
		self.log.update()
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
				self.log.update()
				self.file = self.url
				self.get_local()
				self.log.update()
				print self.log.msg"]

			else:
				self.log.msg = "Url %s sucessfully inserted into sources" %self.url
				url = check_url(self.url)[-1]				
				self.insert_url(url,"manual", depth=0)
				self.log.update()
				print self.log.msg"]
		return self.log.status"]

		#???? Ca doit etre les reste de la creation d'objet?
		#self.__COLL__.update({"_id": self.__data__["_id"]},{"$unset":{"url": self.url}})
		
	def delete_sources(self):
		self.log.step = "deleting sources"
		self.log.status = True
		self.log.msg = "Urls sucessfully deleted"
		if hasattr(self, 'url'):
			ext = (self.url).split(".")[-1]
			if ext == "txt":
				self.log.msg = "Not url but file: all urls in the file will be deleted"
				self.file = self.url
				self._logs['status'] = self.delete_local()
				self._logs['inactive'] = "True"
				

			else:
				url = check_url(self.url)[-1]
				if url in self.__db__.sources.distinct("url"):
					self._logs['status'] = self.__db__.sources.remove({"url":url})
					self.log.msg = "Succesfully deleted url %s to sources db of project %s"%(url, self.name)
					self._logs['inactive'] = "True"
				else:
					self.log.msg = "No url %s found in sources db of %s project"%(url, self.name)
					self._logs['inactive'] = "True"
					self._logs['status'] = False
		else:
			self.__db__.sources.drop()
			self.log.msg = "Succesfully deleted every url %s to seeds of crawl job %s"%(url, self.name)
			self._logs['inactive'] = "True"
		return self.log.update()
		
	def insert_url(self, url, origin="default", depth=0):
		'''Insert or updated url into sources if false inserted or updated into logs'''
		self.log.step = "inserting url"
		self.log.status = True
		self.log.msg = "Urls sucessfully inserted"
		status, status_code, error_type, url = check_url(url)
		is_source = self.__db__.sources.find_one({"url": url})
		
		#incorrect url
		if status is False:
			self.log.status = False
			#existing
			if url in self.__db__.logs.distinct("url"):
				self.log.msg = "Error inserting url: updated url %s in logs" %url
				self.__db__.logs.update({"url":url}, {"$push":{"date": self.date, "scope": self.log.scope"], "msg":self.log.msg"], "code": status_code, "status": "False"}})
			#new
			else:
				#self.log.msg = "Status is false error inserting url"
				self.__db__.logs.insert({"url":url, "status": status, "code": [status_code], "msg":[error_type], "origin":[origin], "depth":[depth],"scope":[self.log.scope"]], "date": [self.date]})
				self._logs['msg'] = "Incorrect url %s.\n%s\n Not inserted into sources but logs" %(url, error_type)
			
		#existing url
		elif is_source is not None:
			self.__db__.sources.update({"url":url},{"$set":{"status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth, "scope":"inserting"},"$push":{"date": self.date}})
			self._logs['msg'] = "Succesfully updated existing url %s into sources" %url
		
		#new url
		else:
			self.__db__.sources.insert({"url":url, "status": status, "code": status_code, "msg":error_type, "origin":origin, "depth":depth,"scope":"inserting", "date": [self.date]})
			self._logs['msg'] = "Succesfully inserted new url %s into sources" %url
		self.log.update()
		
		return status 
		
	def delete_url(self, url):
		self.log.step = "Deleting url"
		self.log.status = True
		self.log.msg = "Urls sucessfully deleted"
		if self.__db__.sources.find_one({"url": url}) is not None:
			self.__db__.sources.remove({"url":url})
			
		else:
			self.log.msg = "Url can't be deleted. Url %s was not in sources. Check url format" %url
			self.log.status = False
		
		self.log.update()
		print self.log.msg"]
		return self.log.status"]
			
	def send_seeds_to_queue(self):
		self.log.step = "Sending seeds urls to start crawl"
		for doc in self.__db__.sources.find():
			if doc["status"] is True:
				self.__db__.queue.insert({"url":doc["url"], "depth":doc["depth"]})
		if self.__db__.queue.count() == 0:
			self.log.msg = "Error while sending urls into queue: queue is empty. check sources status"
			self.log.code = 600.1
			self.log.status = False
			self.log.update()
		return self.log.status"]	
				
	def config(self):
		'''initializing  the crawl job with required params'''
		self.log.scope = "config crawl job"
		self.query = None
		self.file = None
		self.option = None
		self.key = None
		self.log.status = True
		self.log.msg = "Configuration"
		
		for k, v in self.__data__.items():
			setattr(self,k,v)

		
		if self.query is None:
			self.log.msg = "Config error: no query has been set."
			self.log.status = False
			self.log.code = 600.1
			self.log.update()
			return False

		self.woosh_query = Query(self.query)

		if self.option == "expand_sources":
			self.log.msg = "Config : expand mode"
			self.log.code = 600.4
			self.log.status = self.expand_sources()
				
			
		if self.file is not None:
			self.log.msg = "Getting seeds from file %s" %self.file
			self.log.code = 600.5
			self.status  = self.get_local(self.file)
			

		if self.key is not None:
			self.log.msg = "Config : Bing search for new sources"
			self.log.code = 600.2
			self.log.status = self.get_bing()
			if self.log.status"] is False:
				self.log.msg = "Config : No API Key for searching new sources."
				if self.__db__.sources.count() == 0:
					self.log.status = False		
				else:
					self.log.status = True
					
		if self.__db__.sources.count() == 0:
			self.log.msg = "No sources registered"
			self.log.code = 600.3
			self.log.status = False
			self.log.update()
			return False
		
		self._logs['status'] = self.send_seeds_to_queue()
		
		return self._logs['status']

		
		
		
	def start(self):
		if self.config():
			self.log.msg = "Running crawl job  on %s" %self.date

			print self.log.msg"] 
			start = dt.now()
			for doc in self.__db__.queue.find():
				print self.__db__.queue.find().count(), "in queue"
				link = Link(doc["url"])
				if link.url not in self.__db__.results.distinct('url') or link.url not in self.__db__.logs.distinct('url'):
					if link.is_valid():
						page = Article(link, depth= doc["depth"])

						try:
							page.build()
							try:
								page.is_relevant(self.woosh_query)
								existing = self.__db__.results.find_one({"url": page.url})
								if existing is not None:
									existing = self.__db__.results.update({"_id": existing['_id']},{"$push":{"date": page.date}})
								else:
									self.__db__.results.insert(page.json())
								for link in page.outlinks:
									if link not in self.__db__.results.distinct('url'):
										self.__db__.queue.insert({"url":link, "depth": page.depth+1})
								print page.title
							except ArticleException:
								res = self.__db__.logs.find_one({"url": page.url})
								if res is not None:
									print self.__db__.logs.update({"_id": res['_id']},{"$push":{"date": page.date}})
									del page.date
									print self.__db__.sources.update({"_id": res['_id']},{"$set":page.log})
								else:
									print self.__db__.logs.insert(page.log)

						except LinkException:
							source = self.__db__.sources.find_one({"url": page.url})
							if source is not None:
								print self.__db__.sources.update({"_id": source['_id']},{"$push":{"date": page.date}})
								del page.date
								print self.__db__.sources.update({"_id": source['_id']},{"$set":page.log})
							else:
								print self.__db__.logs.insert(page.log)
						except ArticleException:
							res = self.__db__.logs.find_one({"url": page.url})
							if res is not None:
								print self.__db__.logs.update({"_id": res['_id']},{"$push":{"date": page.date}})
								del page.date
								print self.__db__.sources.update({"_id": res['_id']},{"$set":page.log})
							else:
								print self.__db__.logs.insert(page.log)

								#print self.__db__.logs.upsert({"url": page.url}, {page.log, {"date":[page.log.date]})
						#print page.url
						#if page.build() is not False:
						#	print page.title
							#print page.links
					# print url, page.depth
					# try:
					# 	if page.is_relevant(self.woosh_query):
					# 		self.__db__.results.insert(page.pretty())
					# 		next_links = [{"url":link, "depth": doc['depth']+1} for link in page.outlinks]
					# 		if len(next_links) != 0:
					# 			self.__db__.queue.insert(next_links)
						
					'''
						# else:
						# 	if page.url not in self.__db__.results.distinct("url"):
						# 		self.__db__.results.insert(page)
					# 	else:
					# 		self.__db__.sources.insert(article._logs)
					# else:
					# 	self.__db__.sources.insert(page._logs)
					'''
					self.__db__.queue.remove({"url": doc["url"]})
					
			end = dt.now()
			elapsed = end - start
			delta = end-start

			self.log.msg = "%s. Crawl done sucessfully in %s s" %(self.log.msg"],str(elapsed))
			self.log.status = True
			return self.log.update()
		
		else:
			print self.log.msg"]
			return self.log.update()
	
	def stop(self):
		self.log.step = "Stopping exec of job of crawl project %s" %(self.name)
		self.log.msg = "Stopping crawl job on %s" %self.date
		self.__db__.queue.drop()
		self.log.status = True	
		return self.log.status"]
		#~ r = Report(self.name)
		#~ r.run_job()
