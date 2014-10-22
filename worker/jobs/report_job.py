#!/usr/bin/env python
# -*- coding: utf-8 -*-

from job import Job
import os
from debug_job import Debug
class Report(Job):
	#~ def __init__(self, name, format="txt"):
		#~ date = dt.now()
		#~ self.name = name
		#~ self.db = Database(self.name)
		#~ self.date = date.strftime('%d-%m-%Y_%H-%M')
		#~ self.format = format
	def start(self):
		self._logs['step'] = "Generate report"
		if self.__data__ is None:
			self._logs['status']= False
			self._logs['msg'] =  "No active job found for %s. Enable to export" %self.name
			return self.__update_logs__()
		
		self._logs['status']= True
		self.report_date = self.date.strftime('%d-%m-%Y_%H-%M')
		self.directory = "%s/reports" %self.project_name
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		filename = "%s/%s.txt" %(self.directory, self.report_date)
		d = Debug(self.__dict__)
		logs =  d.export()
		with open(filename, 'a') as f:
			f.write("\n======DATABASE INFO======\n")
			f.write(self.__db__.stats())
			f.write("\n======PROCESS INFO======\n")
			f.write(logs)
		self._logs['msg'] = ("Successfully generated report for %s\nReport name is: %s") %(self.name, filename)
		return self.__update_logs__()
	