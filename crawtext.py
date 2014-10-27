#!/usr/bin/env python
# -*- coding: utf-8 -*-
<<<<<<< HEAD

'''Crawtext.
=======
__name__ = "crawtext"
__version__ = "3.1.0b1"
__doc__ = '''Crawtext.
>>>>>>> V3
Description:
A simple crawler in command line.

Usage:
<<<<<<< HEAD
	crawtext.py archive [ -f <format> ] <url>
	crawtext.py <name>
	crawtext.py <user>
	crawtext.py <archive_url>
	crawtext.py report <name> 
	crawtext.py export <name> [ -f <format> ] [-c <coll_type>]
	crawtext.py delete <name>
	crawtext.py start <name>
	crawtext.py stop <name>
	crawtext.py <name> -u <user>
	crawtext.py <name> -q <query>
	crawtext.py <name> -k set <key>
	crawtext.py <name> -k append [<key>]
	crawtext.py <name> -s set <file>
	crawtext.py <name> -s add <url>
	crawtext.py <name> -s append <file>
	crawtext.py <name> -s expand
	crawtext.py <name> -s delete [<url>]
	crawtext.py <name> -s delete					
	crawtext.py <name> -r <repeat>
	crawtext.py (-h | --help)
  	crawtext.py --version
  	
Options:
	Projets:
	# Pour consulter un projet : 	crawtext.py pesticides
	# Pour consulter vos projets :	crawtext.py vous@cortext.net
	# Pour obtenir un rapport : 	crawtext.py report pesticides
	# Pour obtenir un export : 		crawtext.py export pesticides
	# Pour supprimer un projet : 	crawtext.py delete pesticides
	Proprietaire:
	# pour définir le propriétaire du project: crawtext pesticides -u vous@cortext.net
	Requête:
	# pour définir la requête: crawtext pesticides -q "pesticides AND DDT"
	Sources:
	# pour définir les sources d'après un fichier :	crawtext.py pesticides -s set sources.txt	
	# pour ajouter des sources d'après un fichier :	crawtext.py pesticides -s append sources.txt
	# pour ajouter une nouvelle url : 				crawtext.py pesticides -s add www.latribune.fr
	# pour définir les sources d'après Bing :		crawtext.py pesticides -k set 12237675647
	# pour ajouter des sources d'après Bing :		crawtext.py pesticides -k append 12237675647
	# pour ajouter des sources automatiquement :	crawtext.py pesticides -s expand
	# pour supprimer une source :					crawtext.py pesticides -s delete www.latribune.fr
	# pour supprimer toutes les sources :			crawtext.py pesticides -s delete
	Récurrence
	# pour définir la récurrence :                	crawtext.py pesticides -r (monthly|weekly|daily)
	Executer un projet								crawtext.py start pesticides
	Stopper un projet								crawtext.py stop pesticides
	
'''

__all__ = ['crawtext', 'manager','database', "scheduler", "dispatcher"]
import os, sys

CRAWTEXT = "crawtext"
CRAWTEXT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))


import __future__
from docopt import docopt


 

if __name__== "__main__":
	from wk import Worker
	
	#~ user_input = docopt(__doc__)
		#~ is_valid = validate_email(user_input['<email>'])
		#~ if is_valid:
			#~ user_input['<name>'] = user_input['<email>']
		#~ else:
	try:		
		w = Worker()
		print w.process(docopt(__doc__))
=======
crawtext.py (<name>|<user>|<url>)
crawtext.py <url> 
crawtext.py <name> <action> [--repeat=<repeat>] [--format=<format>] [--data=<data>] [--file=<input>] [--url=<input>]
crawtext.py <name> [--user=<email>] [--query=<query>] [--key=<key>] [--repeat=<repeat>] [ --format=(default|wiki|forum) ]
crawtext.py (-h | --help)
crawtext.py --version

Help:
#report --format=(txt|html|pdf|mail)
#export --format=(csv|json)
crawtext.py <name> schedule --repeat=<repeat>
crawtext.py <name> unschedule [--task=<task>]
crawtext.py <name> report [--format=<format>]
crawtext.py <name> export [--format= --coll_type=<coll_type>]
crawtext.py <name> debug
crawtext.py <name> list
crawtext.py <name> -s add (<url>|<file>)
crawtext.py <name> -s expand
crawtext.py <name> -s delete [<url>]

'''



from docopt import docopt
from worker.worker import Worker
import os, sys

ABSPATH = os.path.dirname(os.path.abspath(sys.argv[0]))

if __name__== "crawtext":
	try:		
		w = Worker(docopt(__doc__), debug=True)		
>>>>>>> V3
	except KeyboardInterrupt:
		sys.exit()
