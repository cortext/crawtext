#!/usr/bin/env python
# -*- coding: utf-8 -*-

help = """Crawtext: crawl and archive the web
 
Usage:
    crawtext
    crawtext [<start>|<stop>|<export>|<report>] 
    crawtext <setup> [--env=<env>] [--project=<project>]
 
Options:
  -h --help          C'est généré automatiquement.
  --option=<valeur>  Description de l'option.
 
==============
"""

__script__ = "crawtext"
__version__ = "6.0.0"
__author_username__= "c24b"
__author_email__= "4barbes@gmail.com"
__author__= "Constance de Quatrebarbes"

print __script__
#~ import docopt
#~ 
#~ 
#~ try:
    #~ arguments = docopt(__doc__, version=__version__)
    #~ print("a", arguments)
#~ except Exception as e:
    #~ print "e", e
    #~ from crawler import Crawler
    #~ c = Crawler()
