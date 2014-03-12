#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import exists
import sys
import requests
import json
import re
from datetime import datetime

from bs4 import BeautifulSoup
from urlparse import urlparse
from random import choice
from goose import Goose

import pymongo
from pymongo import MongoClient
from pymongo import errors

from multiprocessing import Pool
import __future__



from abpy import Filter
adblock = Filter(file('easylist.txt'))


user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
#pourquoi ne pas prendre le problème à l'envers et dire je ne veux que htm, html et pdf
unwanted_extensions = ['css','js','gif','asp', 'GIF','jpeg','JPEG','jpg','JPG','pdf','PDF','ico','ICO','png','PNG','dtd','DTD', 'mp4', 'mp3', 'mov', 'zip','bz2', 'gz', ]
#proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128'}
def now():
	return datetime.utcnow()
	
def get_bing(api_key="", query=""):
	''' Method to add urlist results from BING API (Limited to 5000 req/month). ''' 
	#now = now()
	try:
		r = requests.get(
			'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
			params={
				'$format' : 'json',
				'$top' : 10,
				'Query' : '\'%s\'' % query,
			},
			auth=(api_key, api_key)
			)
		
		seeds = [{"url":e['Url'], "source_type": "search", "date": now()} for e in r.json()['d']['results']]
		if seeds is not None or len(seeds) != 0:
			return seeds
		else:
			return False
	except Exception, e:
		
		print e
		return False

def get_local(path=""):
	''' Method to add url to queue'''
	now = now()
	seeds = [{"url":url, "from":"source files", "date": now}  for url in open(path).readlines()]
	if local_sources is not None or len(local_sources) != 0:
		return local_sources
	else:
		return False	

class Database():
	def __init__(self,db_name):
		client = MongoClient('mongodb://localhost,localhost:27017')
		self.db = client[str(db_name)]
		self.results = self.db['results']
		self.queue = self.db['queue'] 
		self.report = self.db['report']
		self.error = self.db['error']
	
	def bad_status(self, url, error_code, error_type):
		'''insert into report url status false, url and type url then clean queue'''
		self.report.insert({'status':False,'url':url,'error_code':error_code, 'error_type': error_type}) 
		self.queue.remove({"url": url })
		return self
	
	def report(self):
		'''generate a simple report'''
		delim = "\n***STATISTIQUES de TRAITEMENT***"
		size = "\n\tsize of DB: %d" % ((self.db.command('dbStats', 1024)['storageSize'])/1024)
		work = "\n\t-url en cours de traitement: %d " % (self.queue.count()) 
		url = "\n\t-urls traitées: %d" % (self.report.count())
		error = "\n\t\t %d urls erronées" % (len(self.report.find({"status":False})))
		delim2 = "\n***STATISTIQUES du CRAWTEXT***"
		results = "\n\t-Nombre de liens indexés: %d " % (len(self.report.find({"status":True})))
		result = [delim, size, work, url, ok, error, delim2, results]
		return "".join(result)
		
class Page():

	def __init__(self, url, query, db):

		self.url = url.split('#')[0]
		self.query = query
		
		self.src = None
		self.article = None
		self.title = None
		self.status = None
		self.outlinks = None
		self.db = db
		
		
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
				return self.status
			#Error on ressource or on server
			elif self.req.status_code in range(400,520):
				self.status = False
				#self.error_code = self.req.status_code
				self.error_type = "Error loading ressource or connecting serveur. HTTP Error code : %s" %self.req.status_code
				#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Connexion error"})
				return self.status
			#Redirect
			elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
				self.status = False
				self.error_type = "Redirecting to another url.HTTP Error code : %s" %self.req.status_code
				#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Redirection"})
				return self.status
			
			else:
				try:
					self.src = self.req.text
					return True

				except Exception, e:
					self.status = False
					self.error_type = "Error Fetching Request Answer %s" %e
					#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": "Error fetching text"})
					return self.status
				
				
				
		except requests.exceptions.ConnectionError as e:
			self.status = False
			self.error_type = "Requests Exception Connexion Error: %s" %e.args
			#self.db.report.insert({"url":self.url, "error_code": self.req.status_code, "type": e.args})
			return self.status
		except requests.exceptions.RequestException as e:
			self.status = False
			self.error_type = "Requests Exception Connexion Error: %s" %e.args
			return self.status
		
		

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
			self.outlinks = self.extract_urls()
			self.final_result = {
			"url": url,
			"article": self.content,
			"title": self.title,
			"description": self.description,
			"backlinks": "NotImplementedYet",
			"outlinks":self.outlinks,
			}
			return self.is_relevant()
				
				
		except Exception as e:
			self.status = False
			self.error_type = "Error generating result %s" %e
			return False
	
	def clean_url(self, e):
		url = e.attrs['href']
		if url not in [ '#', None, '\n', '' ] and 'javascript' not in url and self.pre_check():
			if urlparse(url)[1] == '':
				if url[0] == '/':
					url = self.netloc + url
				else:
					url = self.netloc + '/' + url
			elif urlparse(url)[0] == '':
				url = 'http://' + url
			yield url
			
	def check_url(self, e):
		self.clean_url(e)	
		if url not in self.db.results.distinct("url") or url not in self.db.report.distinct("url"):
			yield url
		
		
		
			
	def extract_urls(self):
		''' Extract outlink url'''
		self.outlinks = set()
		self.netloc = 'http://' + urlparse(self.url)[1]
		p = Pool(5)
		self.outlinks= p.map(self.check_url, self.soup.find_all('a', {'href': True}))
		
			

			#check if url not already treated
			#~ if url not in self.db.results.distinct("url") or url not in self.report.distinct("url"):
				#~ self.outlinks.add(url)
			#~ 
			#self.db.queue.insert(url)
			#self.results.insert({"url": self.url, "title":self.title, "description":self.description, "article": self.article, "outlinks":self.outlinks, "backlinks": self.backlinks})	
		if self.outlinks is not None:
			return True
		else:
			self.status = False
			self.error_type = "Error retrieving outlink list %s" %e
			return False
	
	def create(self):
		if self.request() and self.extract_content():
			self.db.queue.insert(self.outlinks)
			self.db.results.insert(self.final_result)
		else:
			self.db.queue.remove(self.url)
			self.db.bad_status(self.url,self.status, self.error_type)
		return self.db.queue.remove({"url":self.url})
		
if __name__ == '__main__':
	seed = get_bing(api_key="J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o", query="algues vertes")
	db = Database("alguesvertes3")
	db.queue.insert(seed)
	#print db.report()
	for n in db.queue.distinct("url"):
		print n
		p = Page(n,query="algues vertes", db=db)
		p.create()
			
	
	#sys.exit()

