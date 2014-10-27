#!/usr/bin/env python
# -*- coding: utf-8 -*-

from job import Job

class List(Job):
	def show(self):
		for job in self.__COLL__.find():
			try:
				print "-", job['name'], job['action'], job["active"], job["user"], job["date"].strftime('%d-%m-%Y')
			except KeyError:
				print job
				out = Job(job)
				out.delete()
