#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
import os

class Query(object):
	def __init__(self, query):
		if not os.path.exists("index"):
			os.makedirs("index")
		schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True))
		self.ix = create_in("index", schema)
		self.q = query
		self.query = QueryParser("content", self.ix.schema).parse(query)
		
		
	def index_doc(self, doc):
		with self.ix.writer() as writer:
			writer.add_document(title=doc['title'], content=doc['content'])
		return writer
	
	def match(self,doc):
		self.index_doc(doc)
		with self.ix.searcher() as searcher:
			results = searcher.search(self.query)
			w = self.ix.writer()
			w.delete_document(0)
			try: 
				hit = results[0]
				#print hit
				return True
			except IndexError:
				return False
