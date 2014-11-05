#!/usr/bin/env python
# -*- coding: utf-8 -*-

from job import Job

class Debug(Job):
	def __init__(self, doc, debug):
		Job.__init__(self, doc, debug)
		self.start()
	'''
	def export(self):
		msg_log = []
		for job in self.__COLL__.find({"name": self.name}):
			status = job['status']
			msg_log.append("Job is still active? "+str(job["active"]))
			for i, row in enumerate(status):
				print row.values()
				row['date'] = row['date'].strftime("%d/%m/%Y,%H:%M%S")
				row['status'] = str(row['status'])
				m_row = str(float(i))+" "+",".join(row.values())
				print m_row
					#m_row = str(i)+" "+",".join(["Undef", row['msg'], str(row['status'])])
				msg_log.append(m_row)
		return "\n".join(msg_log)		
	'''
	
	def start(self):
		
		msg_log = []
		title = "\n====================\nDEBUG:%s\n====================" %(self.name.upper())
		msg_log.append(title) 
		
		for job in self.__COLL__.find({"name": self.name}):
			
			msg_log.append("Job is still active?\n"+ str(job["active"]))
			status = job['status']
			for i, row in enumerate(status):
				print str(i)+")"
				print "======"
				for k, v in row.items():

					print k, v
				print "======"
				#
				#msg_log.append([i,row.items])
		return 