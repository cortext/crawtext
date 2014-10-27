#!/usr/bin/env python
# -*- coding: utf-8 -*-

from job import Job
import os
from debug_job import Debug
from packages.ask_yes_no import *

class Report(Job):
	
	def start(self):
		self.log.step = "Generate report"
		if self._doc is None:
			self.log.status= False
			self.log.msg =  "No job found for %s. Exiting" %self.name
			return self.log.push()
		
		if self._doc['user'] is not None:
			print "Hello %s !" %self._doc['user']
			if ask_yes_no("Do you want to receive the report by email?"):
				if self.send_mail(self._doc['user']) is True:
					print "A report email will be send to %s\nCheck your mailbox!" %self._doc['user']
					return 

		self.log.status= True
		self.report_date = self.date.strftime('%d-%m-%Y_%H-%M')
		self.directory = "%s/reports" %self.project_name
		if not os.path.exists(self.directory):
			os.makedirs(self.directory)
		filename = "%s/%s.txt" %(self.directory, self.report_date)
		# if self.debug is True:
		# 	d = Debug(self.__dict__)
		# 	logs =  d.export()
		with open(filename, 'a') as f:
			f.write("\n======DATABASE INFO======\n")
			f.write(self.db.stats())
			f.write("\n======PROCESS INFO======\n")
			if self.debug is True:
				f.write(logs)
		# print self.db.stats()
		
		self.log.msg = ("Successfully generated report for %s\nReport name is: %s") %(self.name, filename)
		return self.log.push()

	def send_mail(self, user):
		from packages.format_email import createhtmlmail
		import smtplib
		from .private import username, passw
		fromaddrs = "crawlex@cortext.net"
		
		toaddrs  = user
		html = self.db.mail_report()
		txt = self.db.stats()
		subject = "Crawlex on Duty: report of %s, breaking news from the front!" %self.name
		msg = createhtmlmail(html, txt, subject, fromaddrs)
		# The actual mail send
		server = smtplib.SMTP('smtp.gmail.com:587')
		server.starttls()
		server.login(username,passw)
		server.sendmail(fromaddrs, toaddrs, msg)
		server.quit()
		return True