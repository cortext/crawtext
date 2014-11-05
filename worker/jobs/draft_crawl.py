def send_seeds_to_queue(self):
		self._log.step = "Sending seeds urls to start crawl"
		self._log.status = True

		for doc in self._db.sources.find():
			try:
				self._db.queue.insert(doc)
			except Exception as e:
				self._log.msg = e
				print self._log.msg

		if self._db.queue.count() == 0:
			self._log.msg = "Error while sending urls into queue: queue is empty. check sources status"
			self._log.code = 600.1
			self._log.status = False
			
		return self._log.push()

def config(self):

	'''see option expand'''
		# if self.option == "expand_sources":
		# 	self._log.msg = "Config : expand mode"
		# 	self._log.code = 600.4
		# 	self._log.status = self.expand_sources()
				
		'''see get_local on set up'''	
		# if self.file is not None:
		# 	self._log.msg = "Getting seeds from file %s" %self.file
		# 	self._log.code = 600.5
		# 	self._log.status  = self.get_local(self.file)
			
		'''see get_bing on set up'''
		# if self.key is not None:
		# 	self._log.msg = "Config : Bing search for new sources"
		# 	self._log.code = 600.2
		# 	self._log.status = self.get_bing()
		# 	if self._log.status is False:
				# self._log.msg = "Config : No API Key for searching new sources."
				# if self._db.sources.count() == 0:
				# 	self._log.status = False		
				# else:
				# 	self._log.status = True
def delete(self):
		self._log.step = "deleting sources"
		self._log.status = True
		print self._log.step
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

def start(self):
		print "start"
		# if self.config():
		# 	start = dt.now()
		# 	self._log.step = "Crawl Job: start"
		# 	self._log.msg = "Starting: Crawl job starts on %s" %self.date
		# 	while self._db.queue.count() > 0:
		# 		self.__crawl__()	
		# 	end = dt.now()
		# 	elapsed = end - start
		# 	self._log.msg = "%s. Crawl done sucessfully in %s s" %(self._log.msg,str(elapsed))
		# 	self._log.status = True
		# 	return self._log.push()

def __crawl__(self):
		self._log.step = "Crawl Job: crawl sources"
		for doc in self._db.sources.find():
			source = self.set_source(doc)
			print source
		return 
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
	