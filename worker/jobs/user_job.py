#!/usr/bin/env python
# -*- coding: utf-8 -*-

from job import Job
class User(Job):
	def show(self):
		print "\n===================="
		print "USER:", (self.name.upper())
		print "===================="
		print "%i projects active" %(self.__COLL__.find({"user": self.name, "status":"active"}).count())
		if self.__COLL__.find({"user": self.name}) is None:
			print "User not registrated"
			return 
		for job in self.__COLL__.find({"user": self.name}):
			
			print "Job: ", job["action"]
			print "--------------"
			for k,v in job.items():
				if k == '_id' or k == 'status':
					continue
				if v is not False or v is not None:
					print k+":", v			
			print "--------------"
		
		print "____________________\n"
		return 
		
	def create(self):
		self._logs["step"] = "registering new user"
		self._logs["status"] = True
		self.user = self.name
		self.name = "none"
		self.action = "crawl"
		self.active = False
		j = Job(self.__dict__)
		return j.create()
	def delete(self):
		print self.name
		jobs = self.__COLL__.find({"user": self.name})
		if jobs is None:
			"No project found with user %s", self.name
		else:
			for job in jobs:
				print job
				j = Job(job)
				print j.delete()
		
	def unschedule(self):
		self._logs["step"] = "unscheduling user"
		self._logs["status"] = True
		
		if self.__COLL__.find({"user": self.name}) is None:
			self._logs["msg"] = "User not registrated"
			self._logs["status"] = True
			return 
		else:
			for job in self.__COLL__.find({"user": self.name}):
				print job["user"], job["name"]
				#print job.upsert({"_id": job['_id']}, {"$unset":{"user": self.name}})
				print self.__COLL__.insert({"_id": job['_id']}, {"$unset":{"user": self.name}})
			self._logs["msg"] = "User successfully unregistered from project"
		print self._logs["msg"]
		return self._logs