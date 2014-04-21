#!/usr/bin/env/python
# -*- coding: utf-8 -*-
import os, re
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import MimeWriter
import mimetools
import cStringIO
from time import gmtime, strftime
import smtplib
from database import Database
try:
	from cfg import username, password
	from email.MIMEText import MIMEText
except:
	print "Email reports disabled (%s)" % sys.exc_info()[0]

class Report():
	def __init__(self, docopt_args):
		database_name = docopt_args['<project>']
		self.fromEmail="constance@cortext.fr"
		self.toEmails=re.split(",", docopt_args['--email'])
		self.date = (datetime.now()).strftime("%d %m %Y %H:%M")
		self.name = database_name
		self.title = "[Crawtext] Projet %s" %(self.name)
		d = Database(database_name)
		self.report = d.report()
		self.generate()
		self.send()

	def generate(self, attachment=None):
		#Creating template
		THIS_DIR = os.path.dirname(os.path.abspath(__file__))
		j2_env = Environment(loader=FileSystemLoader(THIS_DIR),trim_blocks=True)
		self.body = j2_env.get_template('template.html').render(msg=self.report, date=self.date, title = self.title)
		"""Create a mime-message that will render HTML in popular MUAs, text in better ones"""
		
		self.text = "If you cannot read correctly this e-mail please send a message to constance@cortext.fr or send a pull request to official repo http://github.com/cortext/crawtext/"
		out = cStringIO.StringIO() # output buffer for our message 
		txtin = cStringIO.StringIO(self.text)
		htmlin = cStringIO.StringIO(self.body)
		writer = MimeWriter.MimeWriter(out)
		#
		# set up some basic headers... we put subject here
		# because smtplib.sendmail expects it to be in the
		# message body
		#
		
		writer.addheader("From", self.fromEmail)
		writer.addheader("Subject", (self.title).encode("utf-8"))
		writer.addheader("MIME-Version", "1.0")
		if attachment is not None:
			attachment = MIMEText(attachement.read())
			attachment.add_header('Content-Disposition', 'attachment', filename=attachment)           
			self.msg.attach(attachment)
		#
		# start the multipart section of the message
		# multipart/alternative seems to work better
		# on some MUAs than multipart/mixed
		#
		writer.startmultipartbody("alternative")
		writer.flushheaders()
		#
		# the plain text section
		#
		subpart = writer.nextpart()
		subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
		pout = subpart.startbody("text/plain", [("charset", 'us-ascii')])
		mimetools.encode(txtin, pout, 'quoted-printable')
		txtin.close()
		#
		# start the html subpart of the message
		# start the html subpart of the message
		#
		subpart = writer.nextpart()
		subpart.addheader("Content-Transfer-Encoding", "quoted-printable")
		#
		# returns us a file-ish object we can write to
		#
		pout = subpart.startbody("text/html", [("charset", 'us-ascii')])
		mimetools.encode(htmlin, pout, 'quoted-printable')
		htmlin.close()
		#
		# Now that we're done, close our writer and
		# return the message body
		#
		writer.lastpart()
		self.msg = out.getvalue()
		out.close()
		return self.msg
	
	def send(self):
		html = unicode(self.msg).encode("utf-8")
		#text = 'Rapport d\'indexation: %s' %self.msg
		#subject = "Rapport d'indexation du %s" %self.date
		server = smtplib.SMTP("smtp.gmail.com","587")
		
		# The actual mail send
		for n in self.toEmails:
			server = smtplib.SMTP('smtp.gmail.com:587')
			server.starttls()
			server.login(username,password)
			server.sendmail(self.fromEmail, n, self.msg)
			server.quit()
			print 'Msg Sent Sucessfully to %s. Check your mailbox!' %(n)
		return True

	def export(self):
		#generate the dumps of Mongo DB
		filename = "text.txt"
		f = file(filename)
		#Send it by mail
		attachment = MIMEText(f.read())
		attachment.add_header('Content-Disposition', 'attachment', filename=filename)           
		self.msg.attach(attachment)
		raise NotImplementedError

def send_report(docopt_args):
	Report(docopt_args)
	return	

#if __name__ == '__main__':
	#r = Report("jp", fromEmail="constance@cortext.fr", toEmails=["4barbes@gmail.com", "constance@cortext.fr"])
	