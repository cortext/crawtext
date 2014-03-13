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
def start(self.path):
	'inserting seeds form local file'''
	for url in open(self.path).readlines():
		if url not in self.db.queue.find({"url":url}):
			self.db.queue.insert({"url":url})
	''' inserting seeds from API'''
	
class Page(object):
	def __init__(self, url):
		self.url = url
		self.txt = None
		self.html = None 
		self.outlinks = None
		self.backlinks = None
		
	def request(self):
		try:
			#removing proxies
			requests.adapters.DEFAULT_RETRIES = 2
			self.req = requests.get(self.url, headers={'User-Agent': choice(user_agents)},allow_redirects=True, timeout=5)
			if 'text/html' not in self.req.headers['content-type']:
				self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Content type is not TEXT/HTML"})
				
			#Error on ressource or on server
			elif self.req.status_code in range(400,520):
				self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Connexion error"})
				
			#Redirect
			elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
				self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Redirection"})
				
			else:
				try:
					print self.req
					self.src = self.req.text
					
		except Exception, e:
			self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Error fetching text"})
						
	def extract(self.req):
		#extract link
		self.content = self.req.text
		self.title = bs4(self.req.text).string.title
		p_link = re.compile("\<a.href\=\(?P<outlink>\d*)\<\/a\>")
		self.outlinks = [link.group('outlink') for link in p_link.finditer(self.content)]
		self.backlinks = [link.group('outlink') for link in p_link.finditer(self.content) if link.group == self.url]
		# here define the article 
		#hard cleaning
		self.txt = re.sub("\<.*?\>", "", self.content)
		
	def insert(self):
		self.db.queue.insert(self.outlinks)
		self.db.queue.remove(self.url)
		
		
	
class Seeds():
	''' Init the Great Machine! '''
	def __init__(self, query, bing=None, local=None, db=None):
		''' A seed is a set of url who has query, key, source file(path) properties'''	
		self.query = query
		self.key = bing
		self.path = local
		self.db = db
		self.date = datetime.now()
	
	def get_local(self):
		for url in open(self.path).readlines():
			if url not in self.db.queue.find({"url":url}):
				self.db.queue.insert({"url":url})
				
			else:
				self.db.bad_status(url, None, "Url already in Database You should clean it maybe")
		return True
				
	def get_bing(self):
		print "getting bing working"
		return True
	#~ def get_bing(self):
		#~ try:
			#~ r = requests.get(
				#~ 'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
				#~ params={
					#~ '$format' : 'json',
					#~ '$top' : 10,
					#~ 'Query' : '\'%s\'' % self.query,
				#~ },
				#~ auth=(self.key, self.key)
				#~ )
			#~ 
			#~ for e in r.json()['d']['results']:
				#~ self.db.sources.insert({"url":e['Url']})
			#~ return True
			#~ 
		#~ except:
			#~ print "Error Fetching Result Set from Search Please check your API Key"
			#~ return False	

class Page():

	def __init__(self, url, query, db):

		self.url = url.split('#')[0]
		self.query = query
		self.db = db
		
	def pre_check(self):
		'''Filter unwanted extensions and adds using Addblock list'''
		return bool ( ( self.url.split('.')[-1] not in unwanted_extensions )
					and
					( len( adblock.match(self.url) ) == 0 ) )

	def retrieve(self):
		''' Request a specific HTML file and return html file stored in self.src''' 
		try:
			print self.url, self.req.status_code
			#removing proxies
			requests.adapters.DEFAULT_RETRIES = 2
			self.req = requests.get(self.url, headers={'User-Agent': choice(user_agents)},allow_redirects=True, timeout=5)

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
				
				
				
		except requests.exceptions.ConnectionError as e:
			self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": e})
			return False
		except requests.exceptions.RequestException as e:
			self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": e.args})
			#Catching wired error
			# template = "An exception of type {0} occured. Arguments:\n{1!r}"
			# message = template.format(type(ex).__name__, ex.args)
			# print message	
			#httplib.BadStatusLine
			#HTTPConnectionPool(host='fr.wikipedia.org', port=80): Max retries exceeded with url: / (Caused by <class 'httplib.BadStatusLine'>: '')
			#print "Exception:",e
			return False
		
	def is_relevant(self):
		'''Reformat the query properly: supports AND, OR and space'''
		if 'OR' in self.query:
			for each in self.query.split('OR'):
				query4re = each.lower().replace(' ', '.*')
				if re.search(query4re, self.src, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE):
					return True

		elif 'AND' in self.query:
			query4re = self.query.lower().replace(' AND ', '.*').replace(' ', '.*')
			return bool(re.search(query4re, self.src, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE))

		else:
			query4re = self.query.lower().replace(' ', '.*')
			return bool(re.search(query4re, self.src, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE))

	def extract_content(self):
		'''Extract content using BoilerPipe Extractor + BeautifulSoup'''
		print Extractor(html=self.src).getHTML()
		self.soup = BeautifulSoup(Extractor(html=self.src).getHTML())
		self.title= self.soup.title.string

	def extract_urls(self):
		''' Extract outlink url'''
		self.outlinks = set()
		self.netloc = 'http://' + urlparse(self.url)[1]

		for e in self.soup.find_all('a', {'href': True}):
			url = e.attrs['href']
			if url not in [ '#', None, '\n', '' ] and 'javascript' not in url:
				if urlparse(url)[1] == '':
					if url[0] == '/':
						url = self.netloc + url
					else:
						url = self.netloc + '/' + url
				elif urlparse(url)[0] == '':
					url = 'http:' + url
				print "insert new url"
				self.outlinks.add(url)
				self.db.queue.insert(url)
			self.results.insert({"url": self.url, "title":self.title, "outlinks":self.outlinks})	
		return True

class Crawl():
	def __init__(self, cfg):
		
		if 'query' in cfg.keys() and cfg['query'] != '':
			self.query = cfg['query']
		else: self.query = False

		if 'bing_account_key' in cfg.keys() and cfg['bing_account_key'] != '':
			self.bing = cfg['bing_account_key']
		else: self.bing = False

		if 'local_seeds' in cfg.keys() and cfg['local_seeds'] != '':
			self.local = cfg['local_seeds']
		else: self.local = False
		
		if 'project_name' in cfg.keys() and cfg['project_name'] != '':
			self.db = Database(database_name=cfg['project_name'])
		else: self.db = Database('crawtext')
		
		self.db.create_tables()
		print "database %s sucessfully created!" %cfg['project_name']
		
	def start(self):
		'''Start the crawler '''
		self.seeds = Seeds(self.query, self.bing, self.local, self.db)
		self.seeds.get_local()
		for u in self.db.queue.distinct("url"):
			print u
			self.do_page(u)
			#~ for e in self.seeds:
				#~ self.do_page(e)
				#enregistrement des seeds dans table source pour prochain crawling
			self.db.sources.insert(u)
	
	def do_page(self, url):
		p = Page(url, self.query, self.db)
		if p.url not in self.db.results.distinct("url"):	
			if p.pre_check() and p.retrieve() and p.is_relevant():
				print "extract content"
				p.extract_content()
				self.outlinks = p.extract_urls()
				print "inserting new doc"
				self.db.results.insert({"url":p.url,'content':p.src, 'outlink':self.outlinks, 'content_txt' : p.boiled_txt,
										'content' : p.soup.get_text(), 'title':p.soup.string.title})
				self.db.queue.insert(self.outlinks)			
		self.db.queue.remove(url)

def crawtext(query, depth=1, bing_account_key=None, local_seeds=None, project_name=None):
	''' Main worker with threading and loop on depth '''
	cfg = {
		'query' : query,
		'bing_account_key' : bing_account_key,
		'local_seeds' : local_seeds,
		'depth' : depth,
		'project_name':project_name,
	}

	c = Crawl(cfg)
	c.start()
	while c.db.queue.count() != 0:
		for url in c.db.queue.distinct("url"):
			print url
			c.do_page(item)	
			
if __name__ == '__main__':
	crawtext(	'viande algues',
				depth = 0,
				bing_account_key=open("keypass_").read(),
				local_seeds="./myseeds.txt",
				project_name = "test")

	#sys.exit()
	


