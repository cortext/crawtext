#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, sys
from datetime import datetime as dt

def send_mail(user, db):
	from packages.format_email import createhtmlmail
	from packages.private import username, passw
	import smtplib

	fromaddrs = "crawlex@cortext.net"
	toaddrs  = user
	html = db.mail_report()
	txt = db.show_stats()
	subject = "Crawlex on Duty: report of %s, breaking news from the front!" %str(db.db_name)
	msg = createhtmlmail(html, txt, subject, fromaddrs)
	# The actual mail send
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(username,passw)
	server.sendmail(fromaddrs, toaddrs, msg)
	server.quit()
	return True

def generate_report(task, db, directory):
	date = dt.now()
	date = date.strftime('%d-%m-%Y_%H-%M')
	directory = os.path.join(directory, 'reports')
	if not os.path.exists(directory):
		os.makedirs(directory)
	filename = "%s/%s.txt" %(directory, date)

	with open(filename, 'w') as f:
		f.write("\n======PROJECT PARAMS======\n")
		for k, v in task.items():
			if k not in ["action", "status","msg", "date", "creation_date", "_id"]:
				if k == "creation_date":
					v = task[k].strftime('%d-%m-%Y %H-%M-%S')
					f.write(str(k)+": "+str(v)+"\n")
				try:
					f.write(str(k)+": "+str(v)+"\n")
				except Exception:
					pass
			
		f.write(db.show_stats())
		
		f.write("\n\n======HISTORY OF THE PROJECT======\n")
		
		date_list = [n.strftime('%d-%m-%Y %H-%M-%S') for n in task["date"]]
		status_list = list(zip(task["action"], task["status"],task["msg"], date_list))
		for msg in status_list:
			f.write("\n-"+str(msg))
	print "Your report is ready!\nCheck here: %s" %(filename)
	return True
