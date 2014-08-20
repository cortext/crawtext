#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from copy import deepcopy
from parsers import Parser
from cleaners import StandardDocumentCleaner
from formatters import StandardOutputFormatter
from extractors import StandardContentExtractor
import datetime
from BeautifulSoup import BeautifulSoup as bs

class Extractor(object):
	'''Generic Extractor'''	
	@staticmethod
	def run( url, raw_html,type, lang="en"):
		if type == "article":
			content = Article(url, raw_html, lang)
		elif type == "defaut":
			raise NotImplementedError	
		else:
			raise NotImplementedError	
		 	
		return content.get()
		


class Article(Extractor):
	'''Article'''
	def __init__(self, url, raw_html, lang):
		self.status = True
		self.url = url
		self.lang = lang
		# title of the article
		self.title = None	
		#text
		self.article = u""
		self.cleaned_text = u""
		# meta
		self.meta_description = u""
		self.meta_lang = u""
		self.meta_favicon = u""
		self.meta_keywords = u""
		#link and domain
		self.canonical_link = u""
		self.domain = u""
		# cleaned text
		self.top_node = None
		self.tags = set()
		self.final_url = url
		self.raw_html = raw_html
		# the lxml Document object
		self.parser = Parser()
		self.raw_doc = u""
		self.publish_date = None
		self.additional_data = {}
		self.links = []
		self.outlinks = []
		self.inlinks = []
		self.start_date = datetime.datetime.today()
	
	def get(self):
		try:
			self.doc = self.parser.fromstring(self.raw_html)
			#init extractor method
			extractor = StandardContentExtractor(self,"en")	
			# init the document cleaner
			cleaner = StandardDocumentCleaner(self)
			# init the output formatter
			formatter = StandardOutputFormatter(self, stopwords_class="en")
			#doc
			#self.doc = doc
			self.raw_doc = deepcopy(self.raw_html)
			
			self.title = extractor.get_title()
			#self.title = self.title
			#meta
			self.meta_lang = extractor.get_meta_lang()
			#self.meta_favicon = extractor.get_favicon()
			self.meta_description = extractor.get_meta_description()
			self.meta_description = self.meta_description.decode("utf-8")
			self.meta_keywords = extractor.get_meta_keywords()
			
			#domain and url
			self.canonical_link = extractor.get_canonical_link()
			self.domain = extractor.get_domain()
			#~ 
			#~ #tag
			self.tags = extractor.extract_tags()
			#~ #text
			self.doc = cleaner.clean()
			
			self.top_node = extractor.calculate_best_node()
			if self.top_node is not None:
				# post cleanup
				self.top_node = extractor.post_cleanup(self.top_node)
			# clean_text
			#self.cleaned_text = formatter.get_formatted_text()
			
			
			#self.content = self.content.decode("utf-8")
			self.links = extractor.get_links()
			self.outlinks = extractor.get_outlinks()
			try:
				self.content = formatter.get_formatted_text()
			except Exception as e:
				self.content = bs(self.raw_html).text
			#self.inlinks, self.inlinks_err = extractor.get_outlinks(self.links)
			# TODO
			# self.article.publish_date = self.extractor.get_pub_date(doc)
			# self.article.additional_data = self.extractor.more(doc)
			
			return self.repr()
			
		except Exception as e:
			self.status = False
			self.logs = {
				"url": self.url,
				"scope": "article extraction",
				"msg": e.args,
				"status": False,
				"code": -2
				}
			return self
				
	
	def repr(self):
		return {
				"url": self.canonical_link,
				"domain": self.domain,
				"title": self.title,
				"content": self.content,
				"description": self.meta_description,
				"links": [self.links],
				"outlinks": [self.outlinks],
				"crawl_date": self.start_date,
				"raw_html": self.raw_html,
				}
	
	def is_relevant(self, query):
		self.content = {"title":unicode(self.title), "content": unicode(self.content)}
		if query.match(self.content) is False:
			self.status = {"url":self.url, "code": -1, "msg": "Not Relevant","status": False, "title": self.title, "content": self.content}
			return False
		else:
			return True
