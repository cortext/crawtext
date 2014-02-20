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

#Why?
#~ reload(sys) 
#~ sys.setdefaultencoding("utf-8")

user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00', ]
unwanted_extensions = ['css','js','gif','GIF','jpeg','JPEG','jpg','JPG','pdf','PDF','ico','ICO','png','PNG','dtd','DTD', 'mp4', 'mp3', 'mov']


class Seeds(set):	
	def __init__(self, query, bing=None, local=None):
		''' A seed is a set of url who has query, key, path properties'''	
		self.query = query
		self.key = bing
		self.path = local

	def get_bing(self):
		''' Method to extract results (defaut results_nb is 10) from BING API (Limited to 5000 req/month). ''' 
		try:
			r = requests.get(
					'https://api.datamarket.azure.com/Bing/Search/v1/Web', 
					params={
						'$format' : 'json',
						'$top' : 5,
						'Query' : '\'%s\'' % self.query,
					},
					auth=(self.key, self.key)
				)

			for e in r.json()['d']['results']:
				self.add(e['Url'])

			return True

		except:
			return False

	def get_local(self):
		''' Method to extract url list from text file'''
		try:
			for url in open(self.path).readlines():
				self.add(url)
			return True

		except:
			return False



class Page():

	def __init__(self, url, query):

		self.url = url.split('#')[0]
		self.query = query

	def pre_check(self):
		'''Filter unwanted extensions and adds using Addblock list'''
		return bool ( ( self.url.split('.')[-1] not in unwanted_extensions )
					and
					( len( adblock.match(self.url) ) == 0 ) )

	def retrieve(self):
		''' Request a specific HTML file and return text file stored in self.src''' 
		try:
			self.req = requests.get( self.url, headers={'User-Agent': choice(user_agents)}, timeout=3 )
			if 'text/html' not in self.req.headers['content-type']:
				return False
			else:
				self.src = self.req.text
				return True
		except:
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
		'''Extract content using BoilerPipe + BeautifulSoup'''
		self.soup = BeautifulSoup(Extractor(html=self.src).getHTML())

	def extract_urls(self):
		''' Extract and clean urls'''
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
				self.outlinks.add(url)

		return self.outlinks


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

		self.res = {}
		self.seen = set()

	def do_page(self, url):
		'''Create the page results'''
		p = Page(url, self.query)
		self.seen.add(p.url)
		if p.pre_check() and p.retrieve() and p.is_relevant():
			p.extract_content()

			self.res[p.url] = {
				'pointers' : set(),
				'source' : p.src,
				'content_txt' : p.boiled_txt,
				'content' : p.soup.get_text(),
				'outlinks' : p.extract_urls(),
			}

	def start(self):
		'''Start the crawler '''
		self.seeds = Seeds(self.query, self.bing, self.local)

		if (self.seeds.get_bing() and self.seeds.get_local()) or (self.seeds.get_bing() or self.seeds.get_local()):
			for e in self.seeds:
				self.do_page(e)

	def prepare(self):
		''' Check the url has not be already treated'''
		self.toSee = set()
		for k, v in self.res.iteritems():
			''' Here is the place where I'm supposed to take backlink information'''
			self.toSee.update([url for url in v['outlinks'] if url not in self.seen])
		print "toSee", len(self.toSee)
		print "Seen", len(self.seen)
		print "res", len(self.res)

	def clean(self):
		'''Remobing the link already passed'''
		'''Voir le copy() et tester avec de l'insertion en BDD'''
		for e in self.res.values():
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


def crawtext(query, depth, path_to_export_file, bing_account_key=None, local_seeds=None):
	'''Main worker with threading and loop on depth'''
	cfg = {
		'query' : query,
		'bing_account_key' : bing_account_key,
		'local_seeds' : local_seeds,
		'depth' : depth,
		'path_to_export_file' : path_to_export_file,
	}

	c = Crawl(cfg)
	c.start()

	def worker():
	    while True:
	        item = q.get()
	        c.do_page(item)
	        q.task_done()

	while depth >= 0:
		print "##### DEPTH", depth, "#####"
		c.prepare()
		q = Queue.Queue()
		for i in range(10):
		     t = threading.Thread(target=worker)
		     t.daemon = True
		     t.start()

		for item in c.toSee:
		    q.put(item)

		q.join()
		depth = depth - 1

	c.clean()
	c.export(path_to_export_file)


if __name__ == '__main__':

	crawtext('Bretagne',10, './results.json', local_seeds='myseeds.txt')
	sys.exit()

