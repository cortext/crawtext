#!/usr/bin/env python
# -*- coding: utf-8 -*-

from worker import Worker
import docopt

__name__ = "crawtext"
__version__ = "4.2.0b2"
__doc__ = '''Crawtext.
Description:
A simple crawler in command line for targeted websearch.

Usage:
    crawtext.py (<name>)
    crawtext.py (<name>) (--query=<query>) (--key=<key> |--file=<file> [--nb=<nb>] |--url=<url>) [--lang=<lang>] [--user=<email>] [--r=<repeat>] [--depth=<depth>]
    crawtext.py <name> add [--query=<query>] [--url=<url>] [--file=<file>] [--key=<key>] [--user=<email>] [--r=<repeat>] [--option=<expand>] [--depth=<depth>] [--nb=<nb>] [--lang=<lang>]
    crawtext.py <name> delete [-q] [-k] [-f] [--url=<url>] [-u] [-r] [-d]
    crawtext.py (<name>) report [-email] [--user=<email>] [--r=<repeat>]
    crawtext.py (<name>) export [--format=(csv|json)] [--data=(results|sources|logs|queue)][--r=<repeat>]
    crawtext.py (<name>) start [--maxdepth=<depth>]
    crawtext.py (<name>) stop
    crawtext.py (<name>) toobig
    crawtext.py (-h | --help)   
'''


if __name__== "crawtext":
    try:
        #print docopt(__doc__)  
        w = Worker(docopt(__doc__), debug=False)
        w.dispatch()
        sys.exit()  
    except KeyboardInterrupt:
        sys.exit()
    except Exception, e:
        print e
        sys.exit()
