#!/usr/bin/env python
# -*- coding: utf-8 -*-
__name__="db_stats"
__doc__= "A tool to chekc integrity of the crawl"
__author__="Constance de Quatrebarbes"

import sys
from database import TaskDB, Database

def check_project(name):
	'''check the parameters of the project'''
	taskdb = TaskDB()
	project = taskdb.coll.find_one({"name": name})
	print "The project has been run %d times for:" %len(project["date"])
	
		
	if project is not None:
		for a,s in zip(project["action"], project["status"]):
			print "-", a, s
		#~ for k, v  in project.items():
			#~ if v is not False:
				#~ print "_______________________________________"
				#~ print "|",k,"|", v,"|"
				#~ 
		#~ print "_______________________________________"
		return project
	else:
		sys.exit("No project found")
	
	
def check_sources(project_name):
	'''check the sources status'''
	project_db = Database(project_name)
	project_db.create_colls()
	sources_nb = project_db.sources.count()
	error_nb = len([n["status"][-1] for n in project_db.sources.find() if n["status"][-1] is False])
	ok_nb = len([n["status"][-1] for n in project_db.sources.find() if n["status"][-1] is True])
	http_error = len([n["code"][-1] for n in project_db.sources.find() if n["code"][-1] == 400])
	content_error = len([n["code"][-1] for n in project_db.sources.find() if n["code"][-1] == 404])
	forbidden_error = len([n["code"][-1] for n in project_db.sources.find() if n["code"][-1] == 403])
	extraction_error = len([n["code"][-1] for n in project_db.sources.find() if n["code"][-1] == 700])
	others = len([n["code"][-1] for n in project_db.sources.find() if n["code"][-1] not in [700, 400, 403, 404]])
	print "Error nb: %d sources on %d total" %(error_nb, sources_nb)
	print "Error type:"
	print "- %d network errors (impossible to acess to the website)" %(http_error+forbidden_error)
	print "- %d errors because page is not HTML (PDF or Video, or img ...)" %content_error
	print "- %d errors on extracting the text" %extraction_error
	print "- %d errors undefined" %others
	print "\n"
	print "Details:"
	for n in project_db.sources.find():
		if n["code"][-1] != 100 and n["code"][-1] not in [700, 400, 403, 404]:
			print "\t-", n["url"]
			print n["code"][-1],"\t", n["msg"][-1]

def check_results(project_name):
	project_db = Database(project_name)
	project_db.create_colls()
	nb_results = project_db.results.count()
	results = project_db.results.find()
	print nb_results, "results"
	#~ for n in results:
		#~ print "url", n["url"]
		#~ print "outlinks", len(set(n["cited_links_ids"]))
		#~ print "depth", n["depth"]

def check_logs(project_name):
	project_db = Database(project_name)
	project_db.create_colls()
	nb_logs = project_db.logs.count()
	print nb_logs, "errors"
	logs = project_db.logs.find()
	
	http_error = len([n["code"] for n in project_db.logs.find() if n["code"] in [400, 401, 402,403]])
	content_error = len([n["code"] for n in project_db.logs.find() if n["code"] == 404])
	extraction_error = len([n["code"] for n in project_db.logs.find() if n["code"] == 700])
	others = len([n["code"] for n in project_db.logs.find() if n["code"] not in [700, 400, 403, 404]])
	for n in logs:
		if n["code"] not in [700,401, 400, 403, 404]:
			print n["code"], n["msg"]
		#~ print n["status"][-1], n["code"][-1]
		#n["status"], n["msg"]
	
def main(project_name):
	check_project(project_name)
	check_sources(project_name)
	check_results(project_name)
	check_logs(project_name)
	sys.exit()

main("RRI_ET_4")
