#!/usr/bin/env python
# -*- coding: utf-8 -*-

from job import Job
from report_job import Report
from datetime import datetime as dt
import requests

from packages.query import Query
#from packages.links import check_url
from extractor.article import Article, ArticleException
from extractor.links import Link
#from packages.urls import Link, LinkException

class Crawl(Job):
	
	def add(self):
		self._log.step = "Adding data to crawl job config (source or user)"
		self._log.date = dt.now()
		try:
			if self._doc['url']:
				self._log.step = "Adding url to crawl job"
				self.insert_url(self._doc['url'], origin="manual", deppth="0")
				self._log.msg = "Sucessfully added url %s" %(self._doc['url'])
				self._log.status = True
				return self._log.push()
			elif self._doc['file']:
				self._log.step = "Adding file to crawl job"
				self.file = self._doc['file']
				self.get_local()
				return self._log.push()
			elif self._doc['email']:
				self._log.step = "Adding user to crawl job"
				self._log.msg = "Sucessfully added owner %s" %(self._doc['email'])
				self._log.status = True
				self.task.update({'_id': self.id}, {"$push":{"user": self._doc["email"]}})
				return self._log.push()
			elif self._doc['user']:
				self._log.step = "Adding user to crawl job"
				self._log.msg = "Sucessfully added owner %s" %(self._doc['user'])
				self._log.status = True
				self.task.update({'_id': self.id}, {"$push":{"user": self._doc["user"]}})
				return self._log.push()
			
		except KeyError:
			self._log.msg = "Error: Unable to add url file or user to project %s.\nYou can only add file , url or user to project\nPlease add one of the following parameters:\n\t--url='www.yoururl.com'\n\t--file='yourfile.txt'\n\t--user='you@cortext.net'" %self.name
			self._log.status = False
			return self._log.push()
		except Exception as e:
			self._log.msg = e
			self._log.status = False
			return self._log.push()
	
	def add_url(self, url, origin="default", depth=0):
		'''Insert url into sources with its status'''
		self._log.step = "inserting url into sources"
		self._log.msg = "Url %s sucessfully inserted" %url
		
		link = Link(url, origin=origin, depth=depth, source_url="")
		exists = self._db.sources.find_one({"url": link.url})
		link.status = link.is_valid()
		if exists is not None:
			self._db.sources.update({"_id":exists['_id']}, {"$set": {"status": link.status},"$push": {"date":dt.now()}}, upsert=False)
		else:
			self._db.sources.insert(link.json())
			if exists is not None:
				self._db.sources.update({"_id":exists['_id']}, {"$push": {"date":dt.now()}}, upsert=False)	
			else:
				print link.url, exists,
		return link.status

	def add_bing(self, key=None):
		''' Method to extract results from BING API (Limited to 5000 req/month) automatically sent to sources DB ''' 
		self._log.step = "Searching sources from Bing"
		if key is not None:
			self.key = key
		if self.key == None:
			self._log.msg = "No API key registered"
			self._log.code = 600.3
			self._log.status = False
			
			return self._log.push()
		else:
			print self._db.sources.count(), "sources in db"
			#~ print "There is already %d sources in database" %nb
			#~ print "and %d sources with a bad status" %self._db.sources.find({"status":"false"}).count()
			
			#try:
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
			
			
			self._log.msg =  "Inserted %s urls from Bing results" %str(i)
			self._log.status = True
			return self._log.push()

			#except Exception as e:
			#	print e
			#	self._log.code = "601"+"."+str(e.args[0])
			#	self._log.msg = "Error adding sources from BING: %s" %e.args
			#	self._log.status = False
			#	return self._log.push()
		
	def add_local(self, afile = None):
		''' Method to extract url list from text file'''
		self._log.step = "local file extraction"
		if afile != None:
			self.file = a.file
		try:
			for url in open(self.file).readlines():
				if url != "\n":
					url = re.sub("\n", "", url)
					#status, status_code, error_type, url = check_url(url)
					self.insert_url(url, origin="file", depth=0)
			self._log.status = True
			self._log.msg = "Urls from file %s have been successfuly added to sources" %(self.file)
			return self._log.push()
		
		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self._log.code = float(str(602)+"."+str(e.args[0]))
			self._log.status = False
			self._log.msg= "Failed inserting url for file %s : %s %s" %(self.file, e.args[1],"./"+self.file)
			return self._log.push()	

	def delete(self):
		self._log.step = "deleting sources"
		self._log.status = True
		
		try:
			if self._doc['url']:
				self._doc["url"] = self.url
				ext = (self.url).split(".")[-1]
				if ext == "txt":
					self._log.msg = "Not url but file: all urls in the file will be deleted"
					self.file = self.url
					self._log.status = self.delete_local()
					return self._log.push()
				else:
					self._log.status = self.delete_url()
			elif self._doc['file']:
				self._log.status = self.delete_local()
				return self._log.push()
		except KeyError:
			self._db.sources.drop()
			self._log.msg = "Succesfully deleted every sources of crawl job %s"%(url, self.name)
			return self._log.push()
	
	def delete_url(self, url):
		self._log.step = "deleting url from sources"
		
		link = Link(url)
		exists = self._db.sources.find_one({"url": link.url})
		if exists:
			self._db.sources.remove({"_id": exists["_id"]})
			self._log.msg = "Succesfully deleted url %s to sources db of project %s"%(url, self.name)
			self._log.status = True
		else:
			self._log.msg = "No url %s found in sources db of %s project"%(url, self.name)
			self._log.status = False
		return self._log.push()	
	
	def delete_local(self):
		'''delete sources contained in self.file'''
		self._log.step = "deleting sources from file"
		self._log.status = True
		self._log.msg = "Urls sucessfully deleted"
		#~ print "Removing the list of url contained in the file %s" %self.file
		try:
			for url in open(self.file).readlines():
				url = re.sub("\n", "", url)
				self._db.sources.remove({"url":url})			
			return self._log.push()

		except Exception as e:
			#~ print "Please verify that your file is in the current directory. To set up a correct filename and add directly to sources:\n\t crawtext.py %s -s append your_sources_file.txt" %(e.args[1],self.file, self.name)
			self._log.code = float(str(602)+"."+str(e.args[0]))
			self._log.status = False
			self._log.msg= "Failed deleting url for file %s failed. Verify that your file exists\n Error is : %s '." %(self.file, e.args[1])
			return self._log.push()
		
	def expand(self):
		'''Expand sources url adding results urls collected from previous crawl'''
		self._log.step = "Crawl Job: expand"
		self._log.status = True
		self._log.msg = "Urls from results sucessfully inserted into sources"
		for url in self._db.results.distinct("url"):
			self.insert_url(url, source="automatic", depth=0)
		
		if len(self._db.results.distinct("url")) == 0 :
			self._log.status = False
			self._log.code = 603
			self._log.msg = "No results to put in seeds. Expand option failed"
		self._log.push()
		return self._logs["status"]	
	
	def add_sources(self):
		self._log.step = "Crawl Job: add_sources"
		try:
			if self._doc['action'] == "expand":
				self._log.msg = "Reload : expand "
				self._log.code = 600.4
				self._log.status = self.expand()
				self._log.push()

			if self._doc['file'] is not None:
				self._log.msg = "Reload: get_local"
				self.file = self._doc['file']
				self._log.status  = self.get_local(self.file)
				self._log.push()
			
			if self._doc['key'] is not None:
				self._log.msg = "Reload : add_bing"
				self._log.status = self.get_bing()
				self._log.push()
		
		except KeyError as e:
			print e.args

		
	def config(self):
		'''initializing  the crawl job with required params'''
	
		self._log.step = "Crawl job: configuration"
		self._log.status = True
		self._log.msg = "Config:"
		
		#Query is the only one mandatory
		self.query = None
		for k, v in self._doc.items():
			setattr(self,k,v)
		
		if self.query is None:
			self._log.msg = "Config error: no query has been set."
			self._log.status = False
			self._log.code = 600.1	
			return self._log.push()
		else:
			self.woosh_query = Query(self.query)
		
		#Sources can't be empty to start crawl	
		if self._db.sources.count() == 0:
			self._log.msg = "Config: no sources registered"
			self._log.code = 600.3
			self._log.status = False
			self._log.push()
			#adding sources from _doc params
			self.add_sources()
			self.log_push()
		return self._log.push()	
		

	def start(self):
		if self.config():
			start = dt.now()
			self._log.step = "Crawl Job: start"
			self._log.msg = "Starting: Crawl job starts on %s" %self.date
			#while self._db.queue.count() > 0:
			self.__crawl__()	
			end = dt.now()
			elapsed = end - start
			self._log.msg = "%s. Crawl done sucessfully in %s s" %(self._log.msg,str(elapsed))
			self._log.status = True
			return self._log.push()
	
	def set_source(self, doc):
		source = dict()
		source["depth"] = 0
		for k, v in doc.items():
			source[k] = v	
		return source
		
	def __crawl__(self):
		for doc in self._db.sources.find():
			source = self.set_source(doc)
			print source

			#self._db.queue.remove({"url": doc["url"]})
			# print self._db.queue.find().count(), "in queue"
			# 		link = Link(doc["url"],source_url=source_url, depth=depth)
			# 		if link.is_valid():
			# 			if link.url not in self._db.results.distinct('url') or link.url not in self._db.logs.distinct('url'):
			# 				page = Article(link, depth)t
			# 				try:
			# 					page.build()
			# 					try:
			# 						page.is_relevant(self.woosh_query)
			# 						existing = self._db.results.find_one({"url": page.url})
			# 						if existing is not None:
			# 							existing = self._db.results.update({"_id": existing['_id']},{"$push":{"date": page.date}})
			# 						else:
			# 							try:
			# 								self._db.results.insert(page.json())
			# 							except Exception as e:
			# 								self._log.step = "Inserting results"
			# 								self._log.msg = e
			# 								print self._log.show()
			# 						for link in page.outlinks:
			# 							if link not in self._db.results.distinct('url'):
			# 								try:	
			# 									self._db.queue.insert({"url":link, "depth": page.depth+1})
			# 								except Exception as e:
			# 									self._log.step = "Inserting outlinks "
			# 									self._log.msg = e
			# 									print self._log.show()
									
			# 					except ArticleException:
			# 						res = self._db.logs.find_one({"url": page.url})
			# 						if res is not None:
			# 							print self._db.logs.update({"_id": res['_id']},{"$push":{"date": page.date}})
			# 							del page.date
			# 							print self._db.sources.update({"_id": res['_id']},{"$set":page.log})
			# 						else:
			# 							print self._db.logs.insert(page.log)

			# 				except LinkException:
			# 					source = self._db.sources.find_one({"url": page.url})
			# 					if source is not None:
			# 						print self._db.sources.update({"_id": source['_id']},{"$push":{"date": page.date}})
			# 						del page.date
			# 						print self._db.sources.update({"_id": source['_id']},{"$set":page.log})
			# 					else:
			# 						print self._db.logs.insert(page.log)
			# 				except ArticleException:
			# 					res = self._db.logs.find_one({"url": page.url})
			# 					if res is not None:
			# 						print self._db.logs.update({"_id": res['_id']},{"$push":{"date": page.date}})
			# 						del page.date
			# 						print self._db.sources.update({"_id": res['_id']},{"$set":page.log})
			# 					else:
			# 						print self._db.logs.insert(page.log)	
	
	def stop(self):
		self._log.step = "Stopping exec of job of crawl project %s" %(self.name)
		self._log.msg = "Stopping crawl job on %s" %self.date
		self._db.queue.drop()
		self._log.status = True	
		return self._log.status
		#~ r = Report(self.name)
		#~ r.run_job()
	
	def report(self):
		return Report(self.__dict__)