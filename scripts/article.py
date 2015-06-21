#!/usr/bin/env python
# -*- coding: utf-8 -*-

__title__ = 'crawtext'
__author__ = 'c24b'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014-2015, c24b'

import copy
import os
import glob
import re
from bs4 import BeautifulSoup
import requests

#from url import Link
from utils import encodeValue

from datetime import datetime as dt
from query import Query
from link import Link
from text import clean_text


import logging
logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="quickanddirty.log", format=FORMAT, level=logging.INFO)

#results for bing
MAX = 1000
DEPTH = 100


class Page(object):
	"""Article objects abstract an online news article page
	"""
	def __init__(self, url, source_url= None, depth ="",date="", debug= False):
		"""
		"""
		#logging.info("Page Init")
		self.debug = debug
		self.depth = depth
		self.date = date
		self.url = url
		self.source_url = source_url
		self.html = u''
		self.status = True

	def check_depth(self, depth, max_depth=None):
		logging.info("Page check depth")
		if max_depth == "" or max_depth is None or max_depth is False:
			max_depth = DEPTH
		try:
			depth = int(depth)
		except TypeError:
			logging.warning(e)
			depth = 0
		if depth > max_depth:
			if self.debug: print "depth for this page is %d and max is set to %d" %(depth,max_depth)
			self.step = "Validating url"
			self.code = "102"
			self.msg = "Depth of this page is %d and > %d" %(depth, max_depth)
			self.status = False
			return False
		return True



	def is_valid(self):
		#logging.info("Valid url?")
		url = Link(self.url, self.source_url, self.debug)
		if url.is_valid():
			#logging.info("Yes")
			return True
		else:
			self.msg = url.msg
			self.code = url.code
			self.step = "Validating page"
			self.status = False
			return False

	def fetch(self):
		try:

			# req = requests.get((self.url), headers = headers ,allow_redirects=True, proxies=None, timeout=5)
			req = requests.get(self.url, allow_redirects=True, timeout=5)
			logging.info("GET")
			req.raise_for_status()
			try:
				self.html = req.text
				self.msg = "Ok"
				self.code = 200
				self.status = True
				if 'text/html' not in req.headers['content-type']:
					self.msg ="Control: Content type is not TEXT/HTML"
					self.code = 404
					self.status = False
					return False
			#Error on ressource or on server
				elif req.status_code in range(400,520):
					self.code = int(req.status_code)
					self.msg = "Control: Request error on connexion no ressources or not able to reach server"
					self.status = False
					return False
				else:
					return True

			except Exception as e:
				self.msg = "Requests: answer was not understood %s" %e
				self.code = 400
				self.status = False
				return False

		except Exception as e:
				logging.warning(e)
				self.msg = str(e)
				try:
					self.code = req.status_code
				except Exception as e:
					self.code = 400
				self.status = False
				return False
	def log(self):
		# if self.debug is True:
		#     print {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code}
		return {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code, "depth": self.depth}

	def export(self):
		return {"url":self.url, "source_url": self.source_url, "depth": self.depth, "html": self.html}

	#~ def download(self):
		#~ if self.is_valid():
			 #~ if self.fetch():
					#~ return True
		#~ else:
			#~ return False



class Article(object):
	def __init__(self, url, html, source_url=u'', depth="",  date="", debug= False):
		self.url = url
		self.html = html
		self.source_url = source_url
		self.depth = depth
		self.date = date
		self.debug = debug
		self.keywords = []
		self.description = u''
		self.metalang = ""
		self.meta = None
		self.status = True
		self.crawl_nb = 0
		self.msg = ""
		self.code = 100
		logging.info("Article init")
		
	def extract(self):
		self.doc = BeautifulSoup(self.html)
		self.text = clean_text(self.html)
		logging.info("Extract")
		if self.doc is not None:
			try:
				self.title = (self.doc.find("title").get_text()).encode('utf-8')
				self.text = (self.doc.find("body").get_text()).encode('utf-8')
				self.links, self.domains, self.domains_ids = self.fetch_links()
				self.get_meta()
				logging.info("Extracted!")
				return True
			except Exception as ex:
				logging.info(ex)
				self.status = False
				self.msg = str(ex)
				self.code = 700
				return False
		else:
			logging.info("Error in loading html")
			self.status = False
			self.msg = "No html loaded"
			self.code = 700
			return False

	def get_meta(self):
		self.meta = self.doc.findAll("meta")
		self.meta = [(n["name"], n["content"]) for n in self.meta if n is not None and "content" in n and "name" in n]
		return self.meta

	def correct_lang(self,filter_lang):
		if filter_lang is True and self.metalang is not None:
			if self.metalang != filter_lang:
				return False
		return True

	def check_link(self, url, source_url):
		url = Link(url, source_url)
		if url.is_valid():
			return url.url
		else:
			return None

	def format_outlink(self, linklist):
		for link in linklist:
			yield {"url":link, "depth":self.depth+1, "source_url": self.url}

	def fetch_links(self):
		''' extract raw_links and domains '''
		self.domains = []
		self.links = []
		self.domain_ids = []
		links = [n.get('href') for n in self.doc.find_all("a")]
		links = [n for n in links if n is not None and n != "" and n != "/" and n[0] !="#"]

		for url in links:
			if url.startswith('mailto'):
				pass
			if url.startswith('javascript'):
				pass
			else:
				l = Link(url)
				if l.is_valid():
					url, domain, domain_id = l.clean_url(url, self.url)
					self.domains.append(domain)
					self.links.append(url)
					self.domain_ids.append(domain_id)
		return (self.links, self.domains, self.domain_ids)


	def fetch_domains(self):
		self.domains = []
		for n in self.links:
			url = Link(n, self.url)
			if url.is_valid():
				self.domains.append(url.domain)
		return self.domains

	def fetch_domains_id(self):
		self.domain_ids = []
		for n in self.links:
			url = Link(n, self.url)
			if url.is_valid():
				self.domain_ids.append(url.netloc)
		return self.domain_ids

	def get_outlinks(self):
		self.fetch_links()
		self.outlinks= [n for n in self.format_outlink(self.links)]
		self.fetch_domains()
		self.fetch_domains_id()
		return self.outlinks


	def check_lang(self, lang):
		if self.lang is not None:
			if self.lang == self.metalang:
				return True
			else:
				return False
		return False

	def filter(self, query, directory):
		if self.is_relevant(query, directory):
			return True
		else:
			self.code = 800
			self.msg = "Article Query Filter: text not relevant"
			self.status = False
			return False

	def check_depth(self, max_depth):
		if self.depth > max_depth :
			if self.debug: print "depth for this page is %d and max is set to %d" %(self.depth,max_depth)
			self.step = "Validating url"
			self.code = "102"
			self.msg = "Depth is %s" %str(self.depth)
			self.status = False
			return False
		return True


	def export(self):
		l = Link(self.url,self.source_url)
		self.url_id = l.url_id
		return {
				"url": l.url,
				"url_id": self.url_id,
				"link_id": l.subdomain+"_"+l.domain,
				"domain": l.domain,
				"subdomain": l.subdomain,
				"extension": l.extension,
				"filetype": l.filetype,
				"date": [dt.now()],
				"source_url": self.source_url,
				"title": self.title,
				"cited_links": self.links,
				"cited_links_ids": self.domain_ids,
				"cited_domains": self.domains,
				"html": self.html,
				"text": self.text,
				"depth": self.depth,

				#"keywords": self.keywords,
				#"description": self.description,
				"meta": self.meta,
				"crawl_nb": 0,
				"status": [True],
				"msg": ["Ok"]
				#"lang": self.metalang,
				}


	def is_relevant(self, query, directory):
		q = Query(query, directory)
		return q.match({"content": encodeValue(self.text)})

	def log(self):
		if self.debug is True:
			print "Log sent", {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code}
		return {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code}

	# def json(self):
	#     result = {}
	#     values = ['title', 'date', 'depth','outlinks', 'inlinks', 'source_url']
	#     for k,v in self.__dict__.items():
	#         if k in values and v is not None:
	#             if type(v) == set:
	#                 v = list(v)
	#             result[k] = v
	#     return result
