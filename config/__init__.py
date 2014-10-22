#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os



CMD = '''Crawtext.
Description:
A simple crawler in command line.

Usage:
	crawtext.py (<name>|<user>|<url>)
	crawtext.py <url>  [ --format=(default|wiki|forum) ]
	crawtext.py <name> start
	crawtext.py <name> stop
	crawtext.py <name> delete
	crawtext.py <name> schedule --repeat=<repeat>
	crawtext.py <name> unschedule [--task=<task>]
	crawtext.py <name> report [--format=<format>]
	crawtext.py <name> export [--format= --coll_type=<coll_type>]
	crawtext.py <name> debug
	crawtext.py <name> list
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
