#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import exists
import sys
import requests
import json
import re
import threading
import Queue

from bs4 import BeautifulSoup
from urlparse import urlparse
from random import choice
from goose import Goose

import __future__



from abpy import Filter
adblock = Filter(file('easylist.txt'))

from database import Database
#For testing in strange env
#~ reload(sys) 
#~ sys.setdefaultencoding("utf-8")

user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
#pourquoi ne pas prendre le problème à l'envers et dire je ne veux que htm, html et pdf
unwanted_extensions = ['css','js','gif','asp', 'GIF','jpeg','JPEG','jpg','JPG','pdf','PDF','ico','ICO','png','PNG','dtd','DTD', 'mp4', 'mp3', 'mov', 'zip','bz2', 'gz', ]
#proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128'}

	
class Seeds():	
	'''First seed list for Queue'''
	def __init__(self, query, bing=None, local=None):
		'''Creating the first seeds for Crawler with 2 methods'''	
		self.query = query
		self.key = bing
		self.path = local
	
		
	def get_bing(self):
		self.sources = None
		''' Method to add urlist results from BING API (Limited to 5000 req/month). ''' 
		
		try:
			r = requests.get(
				'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
				params={
					'$format' : 'json',
					'$top' : 10,
					'Query' : '\'%s\'' % self.query,
				},
				auth=(self.key, self.key)
				)
			self.bing_sources = [e for e in r.json()['d']['results']]
			if self.local_sources is not None or len(self.local_sources) != 0:
				return True
			else:
				self.error_type= "No search results via Bing API. Please check your API key"
				self.status = False
		except Exception:
			self.error_type= "Error Fetching content via Bing API. Please check your API key"
			self.status = False
			return False

	def get_local(self):
		''' Method to add url to queue'''
		self.local_sources = [url for url in open(self.path).readlines()]
		if self.local_sources is not None or len(self.local_sources) != 0:
			return True
		else:
			self.error_type= "Error Acessing content from the provided sources list. Please check your document %s" %(self.path)
			self.status = False
			return False	
	
		
class Page():

	def __init__(self, url, query, db):

		self.url = url.split('#')[0]
		self.query = query
		self.db = db
		self.src = None
		self.article = None
		self.title = None
		self.status = None
		self.outlinks = None

	def pre_check(self):
		'''Filter unwanted extensions and adds using Addblock list'''
		self.status = bool ( ( self.url.split('.')[-1] not in unwanted_extensions )
					and
					( len( adblock.match(self.url) ) == 0 ) )
		if self.status is False:
			self.error_type = "Unwanted extension"
		return self.status
		
	def request(self):
		''' Request a specific HTML file and return html file stored in self.src''' 
		try:
			print self.url
			#requests
			requests.adapters.DEFAULT_RETRIES = 2
			user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 coSafari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
			headers = {'User-Agent': choice(user_agents),}
			proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128', }
			self.req = requests.get((self.url), headers = headers,allow_redirects=True, proxies=proxies, timeout=5)

			if 'text/html' not in self.req.headers['content-type']:
				self.status = False
				self.error_type = "Not an HTML/text document"
				#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Content type is not TEXT/HTML"})
				return False
			#Error on ressource or on server
			elif self.req.status_code in range(400,520):
				self.status = False
				#self.error_code = self.req.status_code
				self.error_type = "Error loading ressource or connecting serveur. HTTP Error code : %s" %self.req.status_code
				#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Connexion error"})
				return False
			#Redirect
			elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
				self.status = False
				self.error_type = "Redirecting to another url.HTTP Error code : %s" %self.req.status_code
				#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Redirection"})
				return False
			
			else:
				try:
					self.src = self.req.text
					return True

				except Exception, e:
					self.status = False
					self.error_type = "Error Fetching Request Answer %s" %e
					#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Error fetching text"})
					return False
				
				
				
		except requests.exceptions.ConnectionError as e:
			self.status = False
			self.error_type = "Requests Exception Connexion Error: %s" %e.args
			#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": e.args})
			return False
		except requests.exceptions.RequestException as e:
			sel.status = False
			self.error_type = "Requests Exception Connexion Error: %s" %e.args
			#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": e})
			##self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": e.args})
			
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
					self.status = True
					return True

		elif 'AND' in self.query:
			query4re = self.query.lower().replace(' AND ', '.*').replace(' ', '.*')
			self.status = bool(re.search(query4re, self.src, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE))
			if self.status is False:
				self.error_type = "Query is not relevant for article content"
			return self.status

		else:
			query4re = self.query.lower().replace(' ', '.*')
			self.status = bool(re.search(query4re, self.src, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE))
			if self.status is False:
				self.error_type = "Query is not relevant for article content"
			return self.status
			
	def extract_content(self):
		'''Extract content using Goose & BeautifulSoup'''
		try:
			self.soup = BeautifulSoup(self.src)
			g = Goose()
			article = g.extract(raw_html=self.src)
			self.title = article.title
			self.src = article.cleaned_text
			self.description = article.meta_description
			return self.is_relevant()
				
				
		except Exception as e:
			self.status = False
			self.error_type = "Error generating result %s" %e
			return False

	def extract_urls(self):
		''' Extract outlink url'''
		self.outlinks = set()
		self.netloc = 'http://' + urlparse(self.url)[1]
		print self.url
		for e.attrs['href'] in self.soup.find_all('a', {'href': True}):
			url = e.attrs['href']
			#clean url
			if url not in [ '#', None, '\n', '' ] and 'javascript' not in url and self.pre_check:
				if urlparse(url)[1] == '':
					if url[0] == '/':
						url = self.netloc + url
					else:
						url = self.netloc + '/' + url
				elif urlparse(url)[0] == '':
					url = 'http://' + url

			#check if url not already treated
				if url not in self.db.results.distinct("url") or not in self.report.distinct("url")
					self.outlinks.add(url)
			
			#self.db.queue.insert(url)
			#self.results.insert({"url": self.url, "title":self.title, "description":self.description, "article": self.article, "outlinks":self.outlinks, "backlinks": self.backlinks})	
		self.outlinks =list(self.outlinks)
		if self.outlinks is not None:
			return True
		else:
			self.status = False
			self.error_type = "Error retrieving outlink list %s" %e
			return False

class Crawl():

	def __init__(self, cfg):
		'''Load initial config'''

		if 'query' in cfg.keys() and cfg['query'] != '':
			self.query = cfg['query']
		else: self.query = False

		if 'bing_account_key' in cfg.keys() and cfg['bing_account_key'] != '':
			self.bing = cfg['bing_account_key']
		else: self.bing = False

		if 'local_seeds' in cfg.keys() and cfg['local_seeds'] != '':
			self.local = cfg['local_seeds']
		else: self.local = False
		
		if 'database_name' and cfg['database_name']!='':
			self.db_name = cfg['database_name']
			
		else:
			self.db_name = False
		if 'mode' and cfg['mode'] != '':
			self.mode = cfg['mode']
		else:
			self.mode = False
			
	def process(self, url, db):
		if self.request() and self.extract_content() and self.extract_urls():
			final_result = {
			"url": url,
			"article": self.content,
			"title": self.title,
			"description": self.description,
			"backlinks": "NotImplementedYet",
			"outlinks":self.outlinks,
			}
			
			db.results.insert(final_result)
			next_urls = [{"url": url} for url in final_result["outlinks"]]
			db.queue.insert(next_urls)
			
		else:	
			db.errors.insert({"status": self.status, "error_type": self.error_type, "url": self.url})
		return db.queue.remove(url)
			

		
	
	def start(self):
		'''Start the crawler creating the first seeds '''
		if self.db_name is False:
			
			create_database("defaut_job_crawtest")
			#self.sourcing()
			#self.mode = "sourcing"
		self.seeds = Seeds(self.query, self.bing, self.local, self.db)

		if (self.seeds.get_bing() and self.seeds.get_local()) or (self.seeds.get_bing() or self.seeds.get_local()):
			sources
			db.sources.insert(final_result)
				self.do_page(url)


	



def crawtext(query, depth, bing_account_key=None, local_seeds=None, database_name= None):
	'''Main worker with threading and loop on depth'''
	cfg = {
		'query' : query,
		'bing_account_key' : bing_account_key,
		'local_seeds' : local_seeds,
		'depth' : depth,
		'database_name':database_name,
		'mode': 'sourcing',
	}

	c = Crawl(cfg)
	c.start()
	while c.db.queue.count() != 0:
		for url in c.db.queue.distinct("url"):
			print url
			#~ c.do_page
			
	
if __name__ == '__main__':
	
	crawtext(	'viande algues',
				1,
				bing_account_key="J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o",
				local_seeds="myseeds.txt")

	#sys.exit()

