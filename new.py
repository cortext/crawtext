#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from random import choice

from datetime import datetime
from database import Database

import re
from bs4 import BeautifulSoup as bs
#~ from boilerpipe.extract import Extractor
#from goose import Goose
#~ from jpype import *
import requests
from urlparse import urlparse
from abpy import Filter

class Page(object):
	def __init__(self, url, db, query):
		#database
		#self.db = db
		self.curr_page = None
		self.title = None
		self.url = url
		self.query = query
		
		
		
	def fetch(self):
		requests.adapters.DEFAULT_RETRIES = 2
		#here take the hyphe complete list of user_agents
		user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
		headers = {'User-Agent': choice(user_agents),}

		proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128', }
		#random.choice(proxies.keys())
		
		#proxies = {}
		try:
			print "connecting to %s " %self.url
			self.req = requests.get((self.url), headers = headers,allow_redirects=True, proxies=proxies, timeout=5)
			self.root_url= urlparse(self.url).netloc
			self.content = self.req.text
			return self.check()
			
		except requests.exceptions.ConnectionError:
			self.db.report.insert({"url":self.url, "status_code":"404", "description": "Connexion Error"})
			self.db.queue.remove({"url":self.url})
			return False
		
		except Exception, e:	
			self.db.report.insert({"url":self.url, "status_code":"Unknown", "description": str(e)})
			self.db.queue.remove({"url":self.url})
			return False
			
	def check(self):
		if self.req.status_code != 200:
			self.db.report.insert({"url":self.url, "status_code":self.req.status_code, "description": "Connexion Error"})
			self.db.queue.remove({"url": self.url})
			return False
			
		elif 'text/html' not in self.req.headers['content-type']:
			self.db.report.insert({"url":self.url, "status_code": self.req.status_code, "description": "Content type is not TEXT/HTML"})
			self.db.queue.remove({"url": self.url})
			return False
		#Error on ressource or on server
		elif self.req.status_code in range(400,520):
			self.db.report.insert({"url":self.url, "status_code": self.req.status_code, "description": "Connexion error"})
			self.db.queue.remove({"url": self.url})
			return False
		#Redirection
		elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
			self.db.report.insert({"url":self.url, "status_code": self.req.status_code, "description": "Redirection"})
			self.db.queue.remove({"url": self.url})
			return False	
		else:			
			return True
	
	def clean_url(self, url):
		uri = urlparse(url)
		
		if uri.path =='' or uri.path =='/':
			return None
		if uri.netloc == '' and uri.path !='':
			print self.root_url
			return re.sub("$\/", "",self.root_url)+uri.path
		else:
			return uri.netloc+uri.path
	
	def is_html(self):
		'''Filter unwanted extensions and adds using Addblock list'''
		adblock = Filter(file('easylist.txt'))
		unwanted_extensions = ['css','js','gif','asp', 'GIF','jpeg','JPEG','jpg','JPG','pdf','PDF','ico','ICO','png','PNG','dtd','DTD', 'mp4', 'mp3', 'mov', 'zip','bz2', 'gz', ]
		return bool(
					( self.url.split('.')[-1] not in unwanted_extensions)
					and
					(len(adblock.match(self.url) ) == 0 )
					)
		
	def is_relevant(self):
		'''Reformat the query properly: supports AND, OR and space'''
		if 'OR|or|\|' in self.query:
			for each in self.query.split('OR'):
				query4re = each.lower().replace(' ', '.*')
				if re.search(query4re, self.content, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE):
					print "Relevant"
					return True
		elif 'AND|and|\&|\+' in self.query:
			query4re = self.query.lower().replace(' AND ', '.*').replace(' ', '.*')
			self.answer = bool(re.search(query4re, self.content, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE))
			return self.answer
		else:
			query4re = self.query.lower().replace(' ', '.*')
			self.answer = bool(re.search(query4re, self.content, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE))
			return self.answer
	
	def create(self):
		if self.is_html() is True: 
			if self.fetch() is True: 
				if self.is_relevant() is True:			
					self.soup = bs(self.req.text)
					self.content = bs(self.req.text).text
					#self.content = Extractor(html=self.req.text).getHTML()
					self.title = self.soup.title.text
					self.outlinks = [self.clean_url(e['href']) for e in self.soup.find_all('a', {'href': True})]
					#~ self.backlinks = [ url for url in self.outlinks if url == self.root_url and url not in self.backlinks]
					self.db.results.insert({"title": self.title, "content": self.content, "root_url": self.root_url, "curr_url": self.url, "next_urls": self.outlinks})
					print self.outlinks
					for url in self.outlinks:
						try:
							self.db.queue.insert({"url": url} )
						except Exception, e:
							print e
		return self.db.queue.remove({"url": self.url})

def do_job(url, db, query):
	p = Page(url, db, query)
	return p.create()
	
from multiprocessing import Process, Queue
from Queue import Empty
	
if __name__ == '__main__':
	#file de traitement
	
	db = Database("test_47")
	db.create_tables()
	#db.queue.insert([{"url": "http://www.tourismebretagne.com/informations-pratiques/infos-environnement/algues-vertes"},])
	query = "algues vertes"
	while db.queue.count() != 0:
		work_queue = Queue()
		for url in db.queue.distinct("url"):
			work_queue.put(url) 
		processes = [Process(target=do_job, args=(work_queue, db, query)) for i in range(5)]
		for p in processes:
			p.start()
		for p in processes:
			p.join()
			
			
	print db.queue.count()
