#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Crawtext
 
Usage:
  crawtext 
  crawtext [<start>|<stop>|<report>|<export>]
  crawtext <config> [(--env <env_file>)] [(--project <project_file>)]
   
Options:
  -h --help     
  --version     
  
 
"""
__script__ = "crawtext"
__name__ = "crawtext"
__version__ = "6.0.0"
__username__= "c24b"
__email__= "4barbes@gmail.com"
__author__= "Constance de Quatrebarbes"

import sys

if __name__ == "crawtext":
    from docopt import docopt
    from crawler import Crawler
    arguments = docopt(__doc__, version=__version__)
    #print arguments.items()
    options = {k:v for k, v in arguments.items() if v is not None and v is not False and type(v) != list}
    
    if len(options) == 0:
        c = Crawler()
        status = c.start()
        sys.exit(status)
        #~ if status:
            #~ c.export()
    else:
        action = options.keys()
        if len(action) == 0:
            action = action[0]
            if action == "<start>":
                c = Crawler()
                status = c.start()
                sys.exit(status)
            elif action == "<stop>":
                c = Crawler()
                status = c.stop()
                sys.exit(status)
            elif action == "<report>":
                c = Crawler()
                status = c.report()
                sys.exit(status)
            elif action == "<export>":
                c = Crawler()
                status = c.export()
                sys.exit(status)
            elif action == "<config>":
                c = Crawler(project=arguments['<project_file>'], env=arguments['<env_file>'])
                sys.exit(c.status)
        else:
            sys.exit("Error on calling crawtext")       
            
