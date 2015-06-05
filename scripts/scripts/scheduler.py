#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Utils to run crawl on a regular basis

from datetime import datetime
from database import TaskDB
from corbot import Crawtext    
import sys, time
from daemon import Daemon
from multiprocessing import Pool

class MyDaemon(Daemon):
	def run(self):
		while True:
			tk = TaskDB()
			p = Pool(5)
			task_list = [n for n in tk.coll.find()]
			p.map(runner, task_list)
			return False
			
def routine(n):
	now = datetime.today()
	today = (now.day, now.month, now.year)
	date = n["date"][-1]
	last_day = (date.day, date.month, date.year)
	last_action = n["action"][-1]
	last_status = n["status"][-1]
	try:
		routine = n["repeat"]
	except KeyError:
		routine = False
	print n["name"], routine, last_action, last_status
	if last_action == "running":
		c = Crawtext(n["name"], {"action":"report", "user":n["user"]})
		return
		
	if last_action == "created" and last_status is True:
		c = Crawtext(n["name"], {"action":"start"})
		return 
	elif last_action == "running" and last_status is False:
		c = Crawtext(n["name"], {"action":"start"})
		return
	if routine in ["year", "month", "week", "day"]:
		if routine == "year":
			if (last_day[0],last_day[1],last_day[2]+1)  == today:
				if last_status is True:
					c = Crawtext(n["name"], {"action":"start"})
				else:
					c = Crawtext(n["name"], {"action":"report"})
		if routine == "month":
			if (last_day[0],last_day[1]+1,last_day[2])  == today:
				if last_status is True:
					c = Crawtext(n["name"], {"action":"start"})
				else:
					c = Crawtext(n["name"], {"action":"report"})	
		elif routine == "week":
			if (last_day[0]+7,last_day[1],last_day[2])  == today:
				if last_status is True:
					c = Crawtext(n["name"], {"action":"start"})
				else:
					c = Crawtext(n["name"], {"action":"report"})
		elif routine == "day":
			if (last_day[0]+1,last_day[1],last_day[2])  == today:
				if last_status is True:
					c = Crawtext(n["name"], {"action":"start"})
				else:
					c = Crawtext(n["name"], {"action":"report"})
		return
def runner(n):
	now = datetime.today()
	day = (now.day, now.month, now.year)
	
	date = n["date"][-1]
	last_d = (date.day, date.month, date.year)		
	
	if last_d == day:
		if n["status"][-1] is False:
			c = Crawtext(n["name"], {"action":"show"})
			
		if n['action'][-1] in ["running"]:
			try:
				c = Crawtext(n["name"], {"action":"report", "user": n["user"]})
			except Exception, e:
				c = Crawtext(n["name"], {"action": "show"})
				c.udpate_status("running", False, str(e))
			pass
		elif ["config crawl"]:
			try:
				c = Crawtext(n["name"], {"action":"report", "user": n["user"]})
			except Exception, e:
				c = Crawtext(n["name"], {"action": "show"})
				c.udpate_status("running", False, str(e))
				
		elif n['action'][-1] in ["executed"]:
			try:
				c = Crawtext(n["name"], {"action":"report", "user": n["user"]})
				c.export()
			except Exception, e:
				c = Crawtext(n["name"], {"action": "show"})
				c.udpate_status("executed", False, str(e))
		else:	
			c = Crawtext(n["name"], {"action":"start"})
			c.report()
		
		
	elif n['repeat'] == "month":
		pass
	elif n['repeat'] == "day":	
		pass
	elif  n['repeat'] == "week":
		pass
	return False
	
def scheduler():
	daemon = MyDaemon('/tmp/daemon-example.pid')
	if len(sys.argv) == 2:
			if 'start' == sys.argv[1]:
					daemon.start()
			elif 'stop' == sys.argv[1]:
					daemon.stop()
			elif 'restart' == sys.argv[1]:
					daemon.restart()
			else:
					print "Unknown command"
					sys.exit(2)
			sys.exit(0)
	else:
			print "usage: %s start|stop|restart" % sys.argv[0]
			sys.exit(2)
 
if __name__ == "__main__":
	tk = TaskDB()
	#~ p = Pool(5)
	task_list = [n for n in tk.coll.find()]
	#~ p.map(runner, task_list)
	for n in task_list:
		routine(n)
