#!/usr/bin/env python
# -*- coding: utf-8 -*-
__version__ = '3.1.0'
__author__ = 'Constance de Quatrebarbes'
__name__ = 'crawtext'
__all__ = ['worker', 'jobs', 'extractor']
__doc__ = '''Crawtext.

Description:
A simple crawler in command line.

Usage:
	crawtext.py (<name>|<user>|<url>)
	crawtext.py <url>  [ --format=(default|wiki|forum) ]
	crawtext.py <name> (start | stop | delete | stats | debug |list)
	crawtext.py <name> schedule --repeat=<repeat>
	crawtext.py <name> unschedule [--task=<task>]
	crawtext.py <name> (report|export) [--format=<format>] [--coll_type=<coll_type>]
	crawtext.py <name> [--user=<email>] [--query=<query>] [--key=<key>] [--repeat=<repeat>]
	crawtext.py <name> -s add (<url>|<file>)
	crawtext.py <name> -s expand
	crawtext.py <name> -s delete [<url>]
	crawtext.py (-h | --help)
  	crawtext.py --version

Help:
#report --format=(txt|html|pdf|mail)
#export --format=(csv|json)  	
'''

from datetime import datetime as dt
from docopt import docopt
from worker import Worker

user_input = docopt(__doc__)

print __name__
if __name__ == "crawtext":
	print "Lauching crawtext"
	try:		
		w = Worker(user_input)
		start4 = dt.now()
		
	except KeyboardInterrupt:
		sys.exit()
