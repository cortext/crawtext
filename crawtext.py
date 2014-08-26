#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Crawtext.
Description:
A simple crawler in command line.

Usage:
	crawtext.py archive [ -f <format> ] <url>
	crawtext.py <name>
	crawtext.py <user>
	crawtext.py <archive_url>
	crawtext.py <name> report 
	crawtext.py <name> export  [ -f <format> ] [-c <coll_type>]
	crawtext.py <name> start 
	crawtext.py <name> stop 
	crawtext.py <name> delete
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
	# Pour obtenir un rapport : 	crawtext.py pesticides report 
	# Pour obtenir un export : 		crawtext.py pesticides export 
	# Pour supprimer un projet : 	crawtext.py pesticides delete 
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
	Executer un projet								crawtext.py pesticides start 
	Stopper un projet								crawtext.py pesticides stop 
	Supprimer un projet								crawtext.py pesticides delete
	
'''

__all__ = ['crawtext', 'manager','database', "scheduler", "dispatcher"]
import os, sys

CRAWTEXT = "crawtext"
CRAWTEXT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))


import __future__
from docopt import docopt

if __name__== "__main__":
	from wk import Worker
	try:		
		w = Worker()
		print w.process(docopt(__doc__))
	except KeyboardInterrupt:
		sys.exit()
