#!/usr/bin/env python
# -*- coding: utf-8 -*-


from job import Job

class Archive(Job):
	
	#~ def schedule(self):
		#~ #super(Job, schedule)
		#~ print "archive"
		#~ pass
	def config(self):
		if self.__db__.queue.count() > 0:
			self.__db__.queue.drop()
		self.__db__.queue.insert({"url":self.name, "depth":0})
		return 
	def start(self):
		self.config()
		for doc in self.__db__.queue.find():
			if doc['url'] not in self.__db__.treated.find({"url":doc["url"]}):
				doc['status'], doc['status_code'], doc['error_type'], doc['url'] = check_url(doc['url'])
				if doc['status'] is False:
					self.__db__.logs.insert(doc)
				else:
					page = Page(doc["url"],doc["depth"])
					if page.check() and page.request() and page.control():
						article = Article(page.url, page.raw_html, page.depth)
						if article.get() is True:
							print article.links
						else:
							self.__db__.logs.insert(article.__repr__())
					else:
						self.__db__.logs.insert(page.__repr__())
			
			self.__db__.treated.insert(doc)
			self.__db__.queue.remove({"url": doc["url"]})				
			#put url in queue
			#page.extract()
		#~ except Exception as e:
			#~ print "Error in config %s" %e
			#~ self.delete()
		return True