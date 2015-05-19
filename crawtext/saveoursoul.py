#!/usr/bin/env python
# -*- coding: utf-8 -*-

__name__ = "crawtext"
__script_name__ = "saveoursoul"
__version__ = "4.3.2"
__author__= "4barbes@gmail.com"
__doc__ = '''Crawtext.

Description:
A simple crawler in command line for targeted websearch.

Usage:
	crawtext.py (<name>) show [--debug]
	crawtext.py (<name>) (create|update|add) [--query=<query>] [--file=<file>][--url=<url>][--key=<key>] [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug] [--repeat=<repeat>]
	crawtext.py (<name>) add [--query=<query>] [--file=<file>][--url=<url>][--key=<key>] [--nb=<nb>] [--lang=<lang>] [--user=<email>] [--depth=<depth>] [--debug] [--repeat=<repeat>]
	crawtext.py (<name>) start [--debug]
	crawtext.py (<name>) restart [--debug]
	crawtext.py (<name>) stop [--debug]
	crawtext.py (<name>) export [--data=<data>] [--format=<format>] [--debug]
	crawtext.py (<name>) report [--user=<email>] [--format=<format>] [--debug]
	crawtext.py (<name>) delete [--debug]
	crawtext.py -l
'''

import os, sys, re
from copy import copy
from collections import defaultdict
from docopt import docopt
from datetime import datetime as dt
from database import *
import pymongo
import datetime
#from url import Link
from report import send_mail, generate_report
import hashlib
from article import Article, Page
from crawl import crawl
import requests
from logger import *
from bson.son import SON
import pickle

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))
RESULT_PATH = os.path.join(ABSPATH, "projects")
#search result nb from BING
MAX_RESULTS = 1000
#max depth
DEPTH = 100


class Crawtext(object):
	def __init__(self, name, user_input, debug):
		self.name = name
		self.debug = debug
		dt = datetime.datetime.today()
		self.date = dt.replace(minute=0, second=0, microsecond=0)
		self.task_db = TaskDB()
		self.coll = self.task_db.coll
		self.task = self.coll.find_one({"name":self.name})

		if self.name is not None:
			self.project_path = os.path.join(RESULT_PATH, name)
			self.dispatch_action(user_input)
		else:
			self.list_projects()

	def dispatch_action(self,user_input):
		for k,v in user_input.items():
			if k == "debug" and self.debug is True:
				#forcing to consider first the debug of the program
				pass
			if k.startswith("<"):
				# key = re.sub("<|>", "", k)
				# setattr(self,key,v)
				pass
			elif k.startswith("--"):
				key = re.sub("--", "", k)
				if v is None:
					v = False
				setattr(self,key,v)
			else:
				if v is not False and v is not None:
					action = getattr(self, k)
		logging.debug(self.__dict__.items())
		return action()

	def create(self):
		'''create a new task with user params and store it into db'''
		if self.task is None:
			new_task = copy(self.__dict__)
			logging.info(self.create.__doc__)

			del new_task['task']
			del new_task['task_db']
			del new_task['coll']
			#logging.debug(new_task.items())
			self.coll.insert(new_task)
			logging.info("Sucessfully created")

			return self.show()
		else:
			logging.info("Project already exists")
			return self.update()

	def update(self):
		'''udpating project'''
		logging.info(self.update.__doc__)
		new_task = copy(self.__dict__)
		for k,v in new_task.items():
			if v is None and v is False:
				if self.task[k] is not False and self.task[k] is not None:
					new_task[k] = self.task[k]
				else:
					del new_task[k]
		del new_task['coll']
		del new_task['task_db']
		del new_task['task']

		self.coll.update({"name":self.task["name"]}, new_task, upsert=True)
		logging.info("Sucessfully updated")
		return self.show()

		self.task  = self.coll.find_one({"name": self.name})
	def show(self):
		'''showing the task parameters'''
		if self.task is None:
			sys.exit("Project doesn't exists.")
		else:
			self.show_task()
			return self.show_project()

	def show_task(self):
		logging.info("Show current parameters stored for task")
		self.task = self.coll.find_one({"name": self.name})
		for k, v in self.task.items():
			if type(v) == list:
				print "*", k,":"
				for item in v:
					if type(item) == list:
						for n in item:
							print "\t\t-", n
					else:
						print "\t", item
			else:
				print "*", k,":", v
		return
	'''
	def show_project(self):
		self.load_project()

		try:
			print "********\n"
			print "SOURCES:"
			print "- Nb Sources indexées: %i" %self.sources.unique
			print "\t- pertinentes: %i" %self.sources.active.nb
			print "\t- non-pertinentes: %i" %self.sources.inactive.nb
			print "RESULTS:"
			print "- Nb Pages indexées: %i" %self.results.unique
			print "ERRORS:"
			print "- Nb Pages non-indexées: %i" %self.logs.unique
			print "PROCESSING"
			print "- Nb Pages en cours de traitement: %i" %self.queue.unique
			print "********\n"
			return self
		except AttributeError:
			print "********\n"
			print "No data loaded into project"
			print "********\n"
			return self
			'''

	def start(self):
		if self.task is None:
			sys.exit("Project doesn't exists.")
		else:
			print self.coll.find_one({"name":self.name})
			logging.info("Loading task parameters")
			self.load_task()
			self.config_crawl()
			self.crawler()
			#self.update_task()
			return self.show()




	def mapp_ui(self, ui):
		'''Mapping user parameters'''
		logging.info(self.load_ui.__doc__)
		for k, v in ui.items():
			k = re.sub("--|<|>", "", k)

			if type(v) == list:
				for item in v:
					if type(item) == list:
						#if it's a list we just map the last value
						if item[-1] is not None:
							setattr(self, k, item[-1])
						else:
							setattr(self, k, False)
					else:
						if item is None:
							setattr(self, k, False)
						else:
							setattr(self, k, item)
			else:
				if v is None or v is False:
					setattr(self, k, False)
				else:
					setattr(self, k, v)
		return self
	def load_task(self):
		logging.info("Loading task from TaskDB")
		for k, v in self.task.items():
			if k == "debug" and self.debug is True:
				#forcing to consider first the debug of the program
				pass

			if type(v) == list:
				for item in v:
					if type(item) == list:
						#if it's a list we just map the last value
						if item[-1] is not None:
							setattr(self, k, item[-1])
						else:
							setattr(self, k, False)
					else:
						if item is None:
							setattr(self, k, False)
						else:
							setattr(self, k, item)
			elif v is None:
				setattr(self, k, False)
			elif v is False:
				setattr(self, k, False)
			else:
				setattr(self, k, v)
		return self

	def load_project(self):
		logging.info("Loading Project DB")
		self.project = Database(self.name)
		for n in self.project.create_colls(["results", "sources", "logs", "queue"]):
			setattr(self, str(n), self.project.use_coll(str(n)))
			logging.info("\t- %s: %i" %(n,self.__dict__[n].count()))
		return self
	def stats(self):
		self.netw_err = range(400, 520)
		self.spe_err =  [100, 101, 102, 404, 700, 800]

		self.all_err = self.spe_err + self.netw_err
		stats = dict.fromkeys(self.project.colls,dict())
		stats['sources'] = {'active':self.sources.active.count()}
		stats['sources'].update({'inactive':self.sources.inactive.count()})

		errortype = sorted(self.logs.distinct("code"))
		for code in self.logs.distinct("code"):
			stats["logs"]= {"err_list": [[{"code": k[0], "nb":k[1], "msg" :k[2]}] for k in zip(
										self.logs.distinct("code"),
										[self.logs.find({"code":code}).count() for code in self.logs.distinct("code")],
										[self.logs.find_one({"code":code})['msg'] for code in self.logs.distinct("code")]
										)]
										}

		for k in stats.keys():

			stats[k]= {	"nb":self.__dict__[k].count()}
			if len(self.__dict__[k].distinct("depth"))) > 0:
				stats[k] = {"max_depth":max(self.__dict__[k].distinct("depth"))}
			else:
				stats[k] = {"max_depth":0}
			if stats[k]["nb"]> 0:
				for i in range(0, stats[k]['max_depth']+1):
					stats[k]["depth_"+str(i)] = self.__dict__[k].find({"depth": i}).count()


													# "msg":self.logs.find_one({"code":code})['msg']),
													# }})
		return stats



	def show_project(self):
		self.load_project()
		self.project.load_data()
		self.project_stats = self.stats()
		for k,v in project_stats.items():
			print k.upper()
			print "=" *len(k)
			for i,j in sorted(v.items()):

				if type(j) != list:
					print "\t-", i, j
					pass
				else:
					for err in j:
						for l,m in err[0].items():
							print "\t\t#",l,":", m

	def create_dir(self):
		try:
			self.directory = getattr(self,"directory")
		except AttributeError:
			self.directory = os.path.join(RESULT_PATH, self.name)
			if not os.path.exists(self.directory):
				os.makedirs(self.directory)
				index = os.path.join(self.directory, 'index')
				try:
					self.index_dir = os.makedirs('index')
				except:
					pass
				logging.info("A specific directory has been created to store your projects\n Location:%s"	%(self.directory))
		return self.directory

	def filter_last_items(self, field="status", filter="True"):
		filter_active = [
		  {"$unwind": "$"+filter},
		  {"$group": {
		    "_id": '$_id',
		    "url" : { "$first": '$url' },
		    "source_url" : { "$first": '$source_url' },
		    "depth" : { "$first": '$depth' },
		   	field :  { "$last": "$"+field },
		    "date" :  { "$last": '$date' },
		    }},
		  {"$match": { field: filter }},
		  ]

		return filter_active

	def config_crawl(self):
		''' set configuration for crawler: filter with the query or open
		if project has no query and at least one seed (file or url)
			then the filter is off
			and the crawl insert the seed into sources
		elif the project has a query:
			then the filter is on
			and the crawl insert the seed into sources
		'''
		logging.info("Set crawler: Activating parameters and adding seeds to sources")
		self.create_dir()

		if any([self.key, self.url, self.file]) is False:
			#logging.info("Invalid parameters task should have at least one seed (file, url or API key for search)")
			return sys.exit("Invalid parameters task should have at least one seed (file, url or API key for search)")

		elif self.query is False:
			self.target = False
			if self.key is True:
				logging.warning("Search for seeds with an API key will not work unless you provide a query")
				return sys.exit("Please provide a query")
		else:
			#mapping project values
			self.load_project()
			#Attention un petit hack en cas de pb avec le srv mongo

			self.target = True
			if len(self.queue.distinct("url")) > 0:
				#do not update sources
				return self
			if self.url is not False:
				print "Adding url"
				self.upsert_url(self.url, "manual")
			if self.file is not False:
				print "Adding urls in file"
				self.upsert_file()
			if self.key is not False:
				print "Adding urls from search"
				self.get_seeds()
				#if self.sources.unique == 0:
				#	self.get_seeds()
				# elif self.repeat is not False:
				# 	self.update_seeds()
			return self
	def update_crawl(self):
		raise NotImplementedError

	def bing_search(self):
		# dt = datetime.datetime.now()
		#petit hack pour éviter les projets qui ont l'historique activé et cexu qui ne l'ont pas avant de le réimplémenter
		if type(self.task["date"]) == list:
			self.task["date"] = self.self.task["date"][-1]
		if (dt.day, dt.month, dt.year, dt.hour) == (self.task['date'].day, self.task['date'].month, self.task['date'].year, self.task['date'].hour) :
			logging.info("Search already done today in less than 1h ")
		# 	return False
		logging.info("bing is searching %s urls" %self.nb)
		web_results = []
		for i in range(0,self.nb, 50):

			#~ try:
			r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
				params={'$format' : 'json',
					'$skip' : i,
					'$top': 50,
					'Query' : '\'%s\'' %self.query,
					},auth=(self.key, self.key)
					)

			#logging.info(r.status_code)

			msg = r.raise_for_status()
			if msg is None:
				for e in r.json()['d']['results']:
					#print e["Url"]
					web_results.append(e["Url"])

		if len(web_results) == 0:
			return False
		return web_results

	def get_seeds(self):
		logging.info("Get_seeds")
		try:
			if self.nb is False:
				self.nb = MAX_RESULTS
		except AttributeError:
			self.nb = MAX_RESULTS

		if self.nb > MAX_RESULTS:
			logging.warning("Maximum search results is %d results." %MAX_RESULTS)
			self.nb = MAX_RESULTS
			logging.warning("Maximum search results has been set to %d results." %MAX_RESULTS)

		if self.nb%50 != 0:
			logging.warning("Maximum search results has to be a multiple of 50 ")
			self.nb = self.nb - (self.nb%50)
			logging.warning("Maximum search results has been set to %d results." %self.nb)

		bing_sources =  self.bing_search()
		if bing_sources is not False:
			total_bing_sources = len(bing_sources)
			logging.info("Search into Bing got %i results" %total_bing_sources)
			for i,url in enumerate(bing_sources):
					try:
						self.sources.insert({
											"url":url,
											"source_url": "search",
											"depth": 0,
											"nb":[i],
											"total":[total_bing_sources],
											"msg":["inserted"],
											"code": [100],
											"status": [True],
											"date": [self.date]
										})
					except pymongo.errors.DuplicateKeyError:
						self.sources.update({
											"url":url},
											{"$push":
											{"nb":i,
											"total":total_bing_sources,
											"msg":"updated",
											"code": 101,
											"status": True,
											"date": self.date
											}})
			logging.info("%i urls from BING search inserted" %i)
			return self
		else:
			logging.warning("Bing search for source failed.")
			return self

	def push_to_queue(self):
		for n in self.sources.active.find():

			try:
			 	self.queue.insert(n)
			except pymongo.errors.DuplicateKeyError:
				pass
		return self.queue

	def upsert_url(self, url, source_url):
		try:
			self.sources.insert({"url":url,
											"source_url": source_url,
											"depth": 0,
											"msg":["inserted"],
											"code": [100],
											"status": [True],
											"date": [self.date],
											})
		except pymongo.errors.DuplicateKeyError:
			self.sources.update({"url":url},
											{"$push":{
													"msg":"updated",
													"code": 100,
													"status": True,
													"date": self.date
													}})

			return
	def upsert_file(self):
		try:
			if self.directory is not False:
				filepath = os.path.join(self.directory, self.file)
			else:
				filepath = os.path.join(self.project_path, self.file)
		except AttributeError:
			filepath = os.path.join(PROJECT_PATH, self.file)

		nb = []
		with open(filepath, 'r') as f:
			for url in f.readlines():
				self.upsert_url(url, "file %s") %self.file
		return self

	def crawler(self):
		logging.info("Crawler activated with query filter %s" %self.target)
		# if self.sources.nb == 0:
		# 	sys.exit("Error: no sources found in the project.")
		try:
			self.project.load_sources()
			self.project.load_queue()
			self.project.load_logs()
		except AttributeError:
			self.load_project()





		#logging.info("Begin crawl with %i active urls"%self.sources.active_nb)
		self.push_to_queue()
		logging.info("Processing %i urls"%self.queue.count())



		#print self.queue.list

		while self.queue.count() > 0:
			for item in self.queue.find():
				if item["url"] in self.results.distinct("url"):
					logging.info("in results")
					self.queue.remove(item)

				elif item["url"] in self.logs.distinct("url"):
					logging.info("in logs")
					self.queue.remove(item)
				else:
					#print "Treating", item["url"], item["depth"]
					try:
						p = Page(item["url"], item["source_url"],item["depth"], item["date"], True)
					except KeyError:
						p = Page(item["url"], item["source_url"],item["depth"], self.date, True)
					if p.download():
						a = Article(p.url,p.html, p.source_url, p.depth,p.date, True)
						if a.extract():
							#Targeted crawk filtering for pertinency
							if self.target:
								if a.filter(self.query, self.directory):
									if a.check_depth(a.depth):
										a.fetch_links()
										if len(a.links) > 0:
											for url, domain in zip(a.links, a.domains):
												if url not in self.queue.distinct("url") and url not in self.results.distinct("url"):
													self.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
													if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
												try:
													self.results.insert(a.export())
												except pymongo.errors.DuplicateKeyError:
													#self.results.update(a.export())
													pass

									else:
										logging.debug("depth exceeded")
										self.logs.insert(a.log())
								else:
									logging.debug("Not relevant")
									self.logs.insert(a.log())
							else:
								if a.check_depth(a.depth):
									a.fetch_links()
									if len(a.links) > 0:
										for url, domain in zip(a.links, a.domains):
											try:
												self.queue.insert({"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date})
											except pymongo.errors.DuplicateKeyError:
												pass
												if self.debug: logging.info("\t-inserted %d nexts url" %len(a.links))
											try:
												self.results.insert(a.export())
											except pymongo.errors.DuplicateKeyError:
												pass
								else:
									logging.debug("Depth exceeded")
									try:
										self.logs.insert(a.log())
									except pymongo.errors.DuplicateKeyError:
										self.logs.update({"url":a.url}, {"$push":{"msg": a.msg}})

						else:
							logging.debug("Error Extracting")
							try:
								self.logs.insert(a.log())
							except pymongo.errors.DuplicateKeyError:
								self.logs.update({"url":a.url}, {"$push":{"msg": a.msg}})
					else:
						logging.debug("Error Downloading")
						self.logs.insert(p.log())

					self.queue.remove(item)
					logging.info("Processing %i urls"%self.queue.count())
				if self.queue.nb == 0:
					break
			if self.queue.nb == 0:
				break
			if self.results.count() > 200000:
				self.queue.drop()
				break

		return sys.exit(1)
	def stop(self):
		import subprocess, signal
		p = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
		out, err = p.communicate()
		cmd = "crawtext.py %s start" %self.name
		for line in out.splitlines():
		  if cmd in line:
		      pid = int([n for n in line.split(" ") if n != ""][0])
		      #pid = int(line.split(" ")[0])
		      logging.warning("Current crawl project %s killed" %self.name)
		      '''
				if self.exists():

				try:
		              self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"stop crawl", "status": True, "date": dt.now(), "msg": "Ok"}})
		          except Exception, e:
		              self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"start crawl", "status": False, "date": date, "msg": e}})
				'''
		      os.kill(pid, signal.SIGKILL)
		'''
	      if self.exists():
	          self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"stop crawl", "status": False, "date": dt.now(), "msg": "No running project found"}})
	          print "No running project %s found" %self.name
	          return False
	      else:
	          print "No crawl job %s found" %self.name
	          return False
		'''
	def report(self):
		logging.info("Report")
		self.load_project()
		#self.load_data()
		self.create_dir()
		if self.user is None or self.user is False:
			self.user = __author__
		#data = self.show_project()
		if send_mail(self.user, self.project) is True:
			logging.info("A report email has been sent to %s\nCheck your mailbox!" %self.user)
			#self.coll.update({"name": self.task['name']}, {"$push": {"action":"report: mail", "status":True, "date": self.date, "msg": "Ok"}})
		else:
			logging.info("Impossible to send mail to %s\nCheck your email!" %self.user)
			#self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: mail", "status":False, "date": self.date, "msg": "Error while sending the mail"}})
		if generate_report(self.task, self.project, self.directory):
			#self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": True, "date": self.date, "msg": "Ok"}})
			logging.info("Report sent and stored!")
			return sys.exit(0)
		else:
			#self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"report: document", "status": False, "date": self.date, "msg": "Unable to create report document"}})
			return sys.exit("Report failed")
	def export(self):
		self.load_project()
		self.create_dir()

		logging.info("Export")
		from export import generate
		if generate(self.name, self.data, self.format, self.directory):
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"export", "status": True, "date":dt.now(), "msg": "Exported"}})
			logging.info("Export done!")
			return sys.exit()
		else:
			self.coll.update({"_id": self.task['_id']}, {"$push": {"action":"export", "status": False, "date": dt.now(), "msg": "Error while exporting"}})
			return sys.exit("Failed to export")

	def list_projects(self):
		for n in self.coll.find():
			try:
				print "-", n["name"]
			except KeyError:
				self.coll.remove(n)

				#print "-", "[ERROR]", n.keys()
		return sys.exit(0)



if __name__ == "crawtext":
	c = Crawtext(docopt(__doc__)["<name>"],docopt(__doc__), True)

	# if c.active:
	# 	c.show_task()
	#  	c.show_project()
	# 	c.set_crawler()
	# 	sys.exit(0)
