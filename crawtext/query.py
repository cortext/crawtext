#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import whoosh
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
import os
from utils import encodeValue

class Query(object):
	def __init__(self, query, directory="", debug=False):
		self.debug = debug
		if self.debug: print "query"
		if directory != "":
			if self.debug: print "no directory"
			dir_index = os.path.join(directory, "index")
			if not os.path.exists(dir_index):
				os.makedirs(dir_index)
				if self.debug: print "dir created"
		else:
			if self.debug: print "no directory"
			if not os.path.exists("index"):
				os.makedirs("index")
				if self.debug: print "no directory"
		schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))
		self.ix = create_in("index", schema)
		self.q = query
		self.query = QueryParser("content", self.ix.schema).parse(query)
		
		
	def index_doc(self, doc):
		with self.ix.writer() as writer:
			try:
				writer.add_document(title=encodeValue(doc['title']), content=encodeValue(doc['content']))
			except KeyError:
				writer.add_document(content=encodeValue(doc['content']))
		return writer
	
	def match(self,doc):
		self.index_doc(doc)
		with self.ix.searcher() as searcher:
			self.results = searcher.search(self.query)
			w = self.ix.writer()
			w.delete_document(0)
			try: 
				self.hit = self.results[0]
				return True
			except IndexError:
				self.hit = None
				return False
