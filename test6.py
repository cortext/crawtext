#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
from random import choice

from datetime import datetime
from database import Database
import pymongo
from pymongo import MongoClient
from pymongo import errors


import re
import json
from bs4 import BeautifulSoup as bs
#from boilerpipe.extract import Extractor
from goose import Goose
import requests
from urlparse import urlparse
from abpy import Filter
client = MongoClient('mongodb://localhost,localhost:27018')
db = client['test_craw']
print db
db.results = db['results']
db.queue = db['queue'] 
db.report = db['report']
db.sources = db['sources']


def clean(url):
	uri = urlparse(url)
	if uri.path =='' or uri.path =='/':
		return None
	if uri.netloc == '' and uri.path !='':
		print self.root_url
		return re.sub("$\/", "",self.root_url)+uri.path
	else:
		return uri.netloc+uri.path
@check_status
def request(url):
	'''return Raw request in a json dict'''
	requests.adapters.DEFAULT_RETRIES = 2
	#here take the hyphe complete list of user_agents
	user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
	headers = {
		'User-Agent': choice(user_agents),
	}

	proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128', }
	#random.choice(proxies.keys())
	
	#proxies = {}
	try:
		print "connecting to %s " %url
		req = requests.get((url), headers = headers,allow_redirects=True, proxies=proxies, timeout=5)
		if check_status(req) is False:
			return {"url": url, "status_code":req.status_code,"description": req.description, "status": False}
		
		else:
			return {"url": url, "raw_content":req.text, "status": True}
	except requests.exceptions.ConnectionError:
		return {"url": url, "status_code":"404", "status":False, "description": "Connexion Error"}
	except requests.exceptions.MissingSchema:
		return {"url": url, "status_code":"-1", "status":False, "description": "Invalid shema url, please check the url"}
			
def check_status(req):
	if 'text/html' not in req.headers['content-type']:
		req.description = "Content type is not TEXT/HTML"
		return False
	#Error on ressource or on server
	elif req.status_code in range(400,520):
		req.description = "Connexion error"
		return False
	#Redirect
	elif len(req.history) > 0 | req.status_code in range(300,320): 
		req.description = "Redirection"
		return False
	else:
		return True

def create_db(name ="job_crawtext"):
	
	crawl_date = datetime.utcnow()
	crawl_date = crawl_date.timetuple()
	db_name= name+'_'+"-".join([str(n) for n in crawl_date])
	
		return db

def extract(url):
	result = request(url)
	if result["status"] is True:
		soup = bs(result["raw_content"])
		g = Goose()
		article = g.extract(raw_html=result["raw_content"])
		title = article.title
		text = article.cleaned_text
		description = article.meta_description
		outlinks = list(set([e.attrs['href'] for e in soup.find_all('a', {'href': True})]))
		clean(outlinks, url)
		backlinks = [ n for n in outlinks if n == url and n not in oulinks]
		return {"status": True, "url":url, "description": description, "title":title, "outlinks":outlinks, "backlinks":backlinks}
	else:
		return result
	
from multiprocessing import Pool

if __name__=="__main__":
	#create_db()
	p = Pool(5)
	liste = ["http://www.tourismebretagne.com/informations-pratiques/infos-environnement/algues-vertes","http://www.developpement-durable.gouv.fr/Que-sont-les-algues-vertes-Comment.html"]
	results = p.map(extract, liste)
	print results
