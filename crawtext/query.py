#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import whoosh
from whoosh.index import create_in
from whoosh.fields import *
from whoosh.qparser import QueryParser
#from whoosh.qparser import MultifieldParser
import os, re
DEBUG = True
class Query(object):
	def __init__(self, query, directory):
		self.query = query
		indexdir = os.path.join(directory, 'index')
		
		if not os.path.exists(indexdir):
			os.makedirs(indexdir)
		schema = Schema(title=TEXT, content=TEXT)
		self.ix = create_in(indexdir, schema)
		
		if '"' in self.query:
			print "exact"
			self.exact_matching = True
			self.query = re.sub('"', '', query.lower())
			self.pquery = re.compile(self.query)

 		else:
 			self.query = self.query.lower()
 			self.exact_matching = False
			self.pquery = QueryParser("content", self.ix.schema).parse(query)
			
		
		
	def index_doc(self, doc):
		with self.ix.writer() as writer:
			writer.add_document(title=doc['title'], content=doc['content'])
		return writer
	
	def rematch(self, doc):
		print "WWW>>>>>>>"
		print re.findall(self.pquery, (unicode(doc['content'])).lower())
		if len(re.findall(self.pquery, doc['content'].lower())) == 0:
			return False
		return True
		
			
	def match(self,doc):
		self.index_doc(doc)
		with self.ix.searcher() as searcher:
			results = searcher.search(self.pquery)
			w = self.ix.writer()
			w.delete_document(0)
			try: 
				hit = results[0]
				if DEBUG: print results
				return True
			except IndexError:
				return False
