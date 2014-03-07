#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from datetime import datetime

import re
#from debug import *
from database import Database
import re
from bs4 import BeautifulSoup as bs
from boilerpipe.extract import Extractor
#from goose import Goose

from urlparse import urlparse
import datetime
from itertools import izip

#connexion lib
import requests
from random import choice
#specific parsing
import json

from abpy import Filter
#from extractors import ContentExtractor

class Page(object):
	''' récupère la page brute a partir d'une url'''
	def __init__(self, url, query, db):
		
		self.url = url.split('#')[0]
		self.db = db
		
	def pre_check(self):
		'''Filter unwanted extensions and adds using Addblock list'''
		adblock = Filter(file('easylist.txt'))
		unwanted_extensions = ['css','js','gif','asp', 'GIF','jpeg','JPEG','jpg','JPG','pdf','PDF','ico','ICO','png','PNG','dtd','DTD', 'mp4', 'mp3', 'mov', 'zip','bz2', 'gz', ]
		return bool ( ( self.url.split('.')[-1] not in unwanted_extensions )
					and
					( len( adblock.match(self.url) ) == 0 ) )
	
	def relative_or_absolute(self):
		if urlparse(self.url).netloc == '':
			print urlparse(self.url), "relative"
		else:
			"absolute"
		print urlparse(self.url).path
					
	def request(self):
		requests.adapters.DEFAULT_RETRIES = 2
		user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
		headers = {
			'User-Agent': choice(user_agents),
		}
		

		proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128', }
		#random.choice(proxies.keys())
		
		#proxies = {}
		try:
			print "connectin...."
			self.req = requests.get((self.url), headers = headers,allow_redirects=True, proxies=proxies, timeout=5)
			self.src = self.req.text
			self.root= urlparse(self.url).netloc
			
			return self
		except requests.exceptions.ConnectionError:
			self.db.report.insert({"url":url, "status_code":404, "description": "Connexion Error"})
			return False
		except Exception:
			
			self.db.report.insert({"url":url, "status_code":"200", "description": "Invalid url"})
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
			#Return true?
			return self
	
	def extract_content(self):
		'''Extract content using BoilerPipe Extractor+ BeautifulSoup'''
		#Goose works properly but problem to caall twice the url
		#~ g = Goose({'target_language':'en'})
		#~ goo = g.extract(url=self.url)
		#~ self.title = goo.title
		#~ self.content = goo.cleaned_text
		#~ print g.extract(url=self.url).meta_description
		#~ print g.extract(url=self.url).cleaned_text
		self.soup = bs(self.src)
		self.content = Extractor(html=self.req.text).getHTML()
		self.title = self.soup.title.text
		
	def extract_urls(self):
		''' Extract and clean urls'''
		self.outlinks = []
		for e in self.soup.find_all('a', {'href': True}):
			print "soup" , e
			url = e.attrs['href']
			print "soup", url
			if url not in [ '#', None, '\n', '', '/' ] and 'javascript' not in url:
				print url
				self.outlinks.append(url)

		return self.outlinks

	#~ def get_title(self):
		#~ p_title = re.compile("\<title\>(?P<title>.*?)<\/title\>")		
		#~ try:
			#~ self.title = p_title.search(self.req.text).group('title')
			#~ return self
		#~ except AttributeError:
			#~ self.db.report.insert({"url":url, "status_code":self.req.status_code, "description": "Error extracting title"})
			#~ self.db.queue.remove({"url":url})
			#~ return False
			
	def is_relevant(self, query):
		'''Reformat the query properly: supports AND, OR and space'''
		if 'OR|or|+' in query:
			for each in query.split('OR'):
				query4re = each.lower().replace(' ', '.*')
				if re.search(query4re, self.src, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE):
					return True
		elif 'AND|and|\|' in query:
			query4re = self.query.lower().replace(' AND ', '.*').replace(' ', '.*')
			return bool(re.search(query4re, self.src, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE))

		else:
			query4re = query.lower().replace(' ', '.*')
			return bool(re.search(query4re, self.src, re.IGNORECASE) or re.search(query4re, self.url, re.IGNORECASE))
			
	
def get_bing(query, key, db):	

	r = requests.get(
		'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
		params={
			'$format' : 'json',
			'$top' : 10,
			'Query' : '\'%s\'' % query,
		},
		auth=(key, key)
		)
	try:
		for e in r.json()['d']['results']:
			print e['Url']
			try:
				if url not in self.db.queue.find(url): 
					db.queue.insert({"url": e['Url']})
			except:
				db.report.insert({"url":e['Url'], "error_code": r.status_code, "type": "Error Fetching url from Bing API"})
			#~ 
		return True
	
	except:
		db.report.insert({"url":None, "error_code": r.status_code, "type": "Error Fetching results page from Bing API", query: query})
def get_local(db, path):
	for url in open(path).readlines():
		print url
		db.queue.insert({"url": url})					

def crawtext(db):
	count = 0
	query = "algues vertes"
	path = "myseeds.txt"
	key = "J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o"
	get_local(db, path)
	get_bing(query, key, db)
	
	while db.queue.count() != 0 and count < 10:
		#Here multiproc
		
		for url in db.queue.distinct("url"):
			if url not in db.report.distinct("url"):			
				print query
				p = Page(url, db, query)
				if p.pre_check() and p.request() and p.is_relevant(query):
					p.extract_content()
					p.extract_urls()
					p.backlinks = [link for link in p.outlinks if link == p.url]
					#données à ajouter aux résultats
					outlink_list = [{"url": url} for url in p.outlinks]
					print p.outlinks
					db.results.insert({"url":p.url, 'outlinks':p.outlinks, 'backlinks':p.backlinks, 'title':p.title,})
					for n in outlink_list:
						print n
						db.queue.insert(n)
			db.queue.remove({"url":url})
			print db.get_txt_report()
			if db.queue.count() == 0:
				break
			if count > 10:
				break
		count = count+1
		return
		
if __name__ == '__main__':
	#file de traitement
	db = Database("craw_test_4")
	db.create_tables()
	crawtext(db)
	#db.queue.insert([{"url": n['url']} for n in report.find() if n['status'] == "error"])
	
	
	
