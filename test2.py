#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from os.path import exists
import sys
import requests
import json
import re
import threading
from bs4 import BeautifulSoup
from urlparse import urlparse
from random import choice
from boilerpipe.extract import Extractor

import __future__


from database import Database
from abpy import Filter
adblock = Filter(file('easylist.txt'))

user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
#pourquoi ne pas prendre le problème à l'envers et dire je ne veux que htm, html et pdf
unwanted_extensions = ['css','js','gif','asp', 'GIF','jpeg','JPEG','jpg','JPG','pdf','PDF','ico','ICO','png','PNG','dtd','DTD', 'mp4', 'mp3', 'mov', 'zip','bz2', 'gz', ]
#proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128'}

def start(path, db):
	'inserting seeds form local file'''
	for url in open(path).readlines():
		url = urlparse(re.sub('\n', '', url), allow_fragments=False)
		uri ='http://'+url.netloc+re.sub('/$', '', url.path)
		
		if url not in db.queue.distinct("url"):
			db.queue.insert({"url":uri})
			db.sources.insert({"url":uri})
	''' inserting seeds from API'''
	
class Page(object):
	def __init__(self, url, db):
		self.url = url
		self.txt = None
		self.html = None 
		self.outlinks = None
		self.backlinks = None
		self.db = db
		print "creating a new page"
	
	def request(self):
		try:
			#removing proxies
			#~ requests.adapters.DEFAULT_RETRIES = 2
			print "Requesting for ",self.url
			self.req = requests.get(self.url, headers={'User-Agent': choice(user_agents)},timeout=5)
			if 'text/html' not in self.req.headers['content-type']:
				self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Content type is not TEXT/HTML"})
				return False
			#Error on ressource or on server
			elif self.req.status_code in range(400,520):
				self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Connexion error"})
				return False
			#Redirect
			elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
				self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Redirection"})
				return False
			else:
				try:
					
					self.src = self.req.text
					return True
				except Exception, e:
					self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Error fetching text"})
					return False
		except Exception, e:
			self.db.report.insert({"url":self.url, "error_code": None, "type": e})
			return False				
	
	def extract(self):
		#extract link
		self.content = self.req.text
		self.title = bs4(self.req.text).string.title
		p_link = re.compile("\<a.href\=\(?P<outlink>\d*)\<\/a\>")
		self.outlinks = [link.group('outlink') for link in p_link.finditer(self.content)]
		self.backlinks = [link.group('outlink') for link in p_link.finditer(self.content) if link.group == self.url]
		# here define the article 
		#hard cleaning
		self.txt = re.sub("\<.*?\>", "", self.content)
		self.db.results.insert({"url":p.url,'content':p.src, 'outlink':self.outlinks, 'content_txt' : p.boiled_txt,
										'content' : p.soup.get_text(), 'title':p.soup.string.title})
	def insert(self, step=0):
		self.db.queue.insert([{"url": url} for url in self.outlinks])
		self.db.queue.remove({"url":self.url})
		step = step+1
		
		return step
		
	def create(self):
		while True:
			if self.request() is True:
				self.extract()
				self.insert()
			else:
				continue
			if self.step > 1:
				break
if __name__ == '__main__':
		project_name = "test_test_test"
		db = Database(project_name)
		db.create_tables()
		start("./myseeds.txt",db)
		print "Links in Queue", db.queue.count()
		for url in db.queue.distinct("url"):
			print "from DB", url
			p = Page(url, db)
			p.create()
		
		
