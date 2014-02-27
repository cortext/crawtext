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
from boilerpipe.extract import Extractor

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

	
class Seeds(set):	
	'''Create Root Url'''
	def __init__(self, query, bing=None, local=None, db=None):
		'''Creating the first seeds for Crawler with 2 methods'''	
		self.query = query
		self.key = bing
		self.path = local
		self.db = db

	def get_bing(self):
		print ''' Method to add urlist results from BING API (Limited to 5000 req/month). ''' 
		
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

			for e in r.json()['d']['results']:
				if url not in self.db.queue.find(url): 
					self.db.queue.insert(e['Url'])
			return True
		except:
			self.db.report.insert({"url":e['Url'], "error_code": r.status_code, "type": "Error Fetching content"})
			return False

	def get_local(self):
		''' Method to add url to queue'''
		for url in open(self.path).readlines():
			if url not in self.db.queue.find(url):
				self.db.queue.insert(url)
			else:
				continue
		return True


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
				self.db.queue.insert(url)
			self.results.insert({"url": self.url, "title":self.title})	
		return True


class Crawl():

	def __init__(self, cfg):
		'''simple parsing parameter'''

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
			self.db = Database(cfg['database_name'])
			self.db.create_tables() 
		else:
			self.db = Database('myproject')
			self.db.create_tables()
		# if 'project_name' in cfg.keys() and cfg['project_name'] != '':
		# 	self.project_name = cfg['project_name']
			
		# 	self.db = Database(cfg['project_name'])
		# 	self.db.create_tables()
		# else: self.project_name = False
		
		

	def do_page(self, url):
		'''Create the page results'''
		p = Page(url, self.query, self.db)
		if p.url not in self.db.results.distinct():	
			if p.pre_check() and p.retrieve() and p.is_relevant():
				p.extract_content()
				print "insert.."
				self.db.results.insert({"url":p.url,'content':p.src})
				self.db.queue.insert(p.extract_urls())
				self.db.remove(p.url)
					#~ self.res[p.url] = {
						#~ 'pointers' : set(),
						#~ #'source' : p.src,
						#~ #'content_txt' : p.boiled_txt,
						#~ #'content' : p.soup.get_text(),
						#~ 'outlinks' : p.extract_urls(),
					#~ }
			self.db.queue.remove(url)
		
	
	def start(self):
		'''Start the crawler '''
		self.seeds = Seeds(self.query, self.bing, self.local, self.db)

		if (self.seeds.get_bing() and self.seeds.get_local()) or (self.seeds.get_bing() or self.seeds.get_local()):
			for url in self.db.queue.distinct("url"):
				self.do_page(url)

	def prepare(self):
		''' Check the url has not be already treated'''
		#~ self.toSee = set()
		#~ for k, v in self.res.iteritems():
			#~ ''' Here is the place where I'm supposed to take backlink information'''
			#~ self.toSee.update([url for url in v['outlinks'] if url not in self.seen])
		#~ print "toSee", len(self.toSee)
		#~ print "Seen", len(self.seen)
		#~ print "res", len(self.res)

	def clean(self):
		
		print "Cleaning..."
		'''Removing the link already passed'''
		for e in self.res.values():
			print e
			for link in e['outlinks'].copy():
				if link not in self.res.keys():
					e['outlinks'].remove(link)
				else:
					self.res[link]['pointers'].add(link)
		for e in self.res:
			self.res[e]['pointers'] = list(self.res[e]['pointers'])
			self.res[e]['outlinks'] = list(self.res[e]['outlinks'])

	def export(self, path_to_file):
		print "writing to file %s" % path_to_file
		f = open(path_to_file, "wb")
		f.write(json.dumps(self.res, encoding="utf-8"))
		f.close()


def crawtext(query, depth, bing_account_key=None, local_seeds=None, database_name= None):
	'''Main worker with threading and loop on depth'''
	cfg = {
		'query' : query,
		'bing_account_key' : bing_account_key,
		'local_seeds' : local_seeds,
		'depth' : depth,
		'database_name':database_name,
	}

	c = Crawl(cfg)
	c.start()
	while c.db.queue.count() != 0:
		for url in c.db.queue.distinct("url"):
			print url
			#~ c.do_page
			
	#~ def worker():
	    #~ while True:
	        #~ item = q.get()
	        #~ c.do_page(item)
	        #~ q.task_done()

	#~ while depth >= 0:
		#~ print "##### DEPTH", depth, "#####"
		#~ c.prepare()
		#~ q = Queue.Queue()
		#~ for i in range(4):
		     #~ t = threading.Thread(target=worker)
		     #~ t.daemon = True
		     #~ t.start()
#~ 
		#~ for item in c.toSee:
		    #~ q.put(item)
#~ 
		#~ q.join()
		#~ depth = depth - 1
#~ 
	#~ c.clean()
	#~ c.export(path_to_export_file)


if __name__ == '__main__':
	
	crawtext(	'viande algues',
				1,
				bing_account_key="J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o",
				local_seeds="myseeds.txt")

	#sys.exit()

