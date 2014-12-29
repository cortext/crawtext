=!PyBing=

==Overview==
!PyBing is a Python wrapper for the Bing search API. It provides both a thin wrapper around the Bing Search API as well as a more complete object oriented query API. Since Bing provides a very simple JSON API, this wrapper gives you a Pythonic interface to building and executing queries against Bing.

==Installing !PyBing==
To grab the latest version of !PyBing from !PyPi, use easy_install:
{{{
$ easy_install pybing
}}}

You can also install !PyBing by doing a checkout from Google Code and putting the pybing directory somewhere along your PYTHONPATH.

{{{
$ mkdir /home/jjg/pybing
$ export PYTHONPATH=/home/jjg/
$ svn checkout http://pybing.googlecode.com/svn/trunk/ /home/jjg/pybing/
}}}

==Using !PyBing's thin API wrapper==
{{{
>>> from pybing import Bing
>>> bing = Bing('<your AppId here>')
>>> response = bing.search_web('python bing')
>>> print response['SearchResponse']['Web']['Total']
1060000
>>> results = response['SearchResponse']['Web']['Results']
>>> print len(results)
10
>>> for result in results[:3]:
...     print repr(result['Title'])
...
u'Python Wrapper on Bing API \u2014 The Uswaretech Blog - Django Web ... '
u'PyUnit - the standard unit testing framework for Python'
u'How to transmit arguments from c++ to python '
}}}

==Using !PyBing's Query API Wrapper==
All of the various source types aren't built out yet, but the Web Query is working. Here's an example:

{{{
>>> from pybing.query import WebQuery
>>> query = WebQuery('<your AppId here>', query='python bing')
>>> results = query.execute()
>>> for result in results[:3]:
...     print repr(result.title)
...
u'Python Wrapper on Bing API \u2014 The Uswaretech Blog - Django Web ... '
u'PyUnit - the standard unit testing framework for Python'
u'How to transmit arguments from c++ to python '
}}}

==Getting an AppID==
In order to use the Bing API, you'll need a Bing AppID. This is actually really easy to get if you have a Windows Live account (MS Passport, MSN Messenger, Hotmail, etc all work). The page to grab an ID is here http://www.bing.com/developers/createapp.aspx. Just follow the steps and you should have an AppID in no time.

==Thanks==
Thank you to the guys at Uswaretech for bingapi.py. I noticed their implementation and thought I'd have a go at creating one. If you take a look at their client, you'll notice that !PyBing's simple client is very similar to theirs, so I'd like to thank them for their inspiration.

Be sure to check over to their project, more info can be found here:
http://uswaretech.com/blog/2009/06/bing-python-api/

==Copyrights, etc==
Everything here is Copyright (C) 2009 *JJ Geewax* (http://geewax.org)
