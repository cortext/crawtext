.. image:: http://www.cortext.net/IMG/siteon0.png?1300195437
        :target: http://www.cortext.net

Crawtext
===============================================
Crawtext is one example of the tools at your disposal on the **Cortext manager** plateform.
Get a free account and discover the tools you can use for your own research by registering at
`<http://manager.cortext.net/> Cortext _

Crawtext is a tiny crawler in commandline that let you investigate the web with a specific query 

How does a crawler works?
---
The crawler needs a *query* to select pertinent pages and *seeds* i.e urls to start collecting data. 
Whenever the page contains the query 
the robot will collect the article and will investigate the query 
in the next pages using the links found in this page.


Installation
------------


To install crawtext, it is recommended to create a virtual env:
	
	$mkvirtualenv crawtext
	
	$workon crawtext

Then you can automatically install all the dependencies using pip 
(all dependencies are available throught pip)
	
	$ pip -r requirements.txt


You *may* have MongoDB installed:

* For Debian distribution install it from distribution adding to /etc/sources.list
	deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen
then 
	sudo apt-get install mongodb-10gen
* For OSX distribution install it with brew
	brew install mongodb
	


Getting help
------------

Crawtext is a simple module in command line to crawl the web given a query.
This interface offers you a full set of option to set up a project.
If you need any help on interacting with the shell command you can just type to see all the options:
'''
python crawtext.py --help
'''

You can also ask for pull request here, we will be happy to answer.


Getting started
----------
* To create a new project:	
	python crawtext.py pesticides
* To add a query:(Query support AND OR NOT * ? " operators)
	python crawtext.py -q "pesticides AND DDT"

* To add new seeds (urls to begin the crawl):
	- manually enter onea url or delete it:
		python crawtext.py pesticides -s add www.lemonde.fr
        - send a txt file with urls:
        	python crawtext.py pesticides -s set seeds.txt
        - programm a search to get results from BING:
        	python crawtext.py pesticides -k "YOUR API KEY"
	See you to get your BING API key here https://datamarket.azure.com/dataset/bing/search

* To declare ownership on the project (optionnal):
	python crawtext.py -u me@cortext.fr
* To schedule a reccurency for your project (optionnal):
 	python crawtext.py -r day
 options are : hour, day, week, month, year 
 defaut is set to month

* To launch immediately the crawl:
 	python start pesticides
 

More options
---------

* Export
* Report
* Archive

* Unschedule the project
* Delete the project
* Delete url of sources
* Stop the current execution
* Expand sources
* Automatically put search results to seeds
* Automatically put seed file to seeds


Results
-------

The results are stored in a mongo database called by the name of your project
You can export results using export option:
	python crawtext.py pesticides export

Datasets are stored in json and zip in 3 collections:
* results
* sources
* logs

The complete structure of the datasets can be found in 
sources_example.json
results_example.json
logs_example.json


Source
------

You can see the code `here <https://github.com/c24b/clean_crawtext>`_


Special thanks
------

- Special thanks to xavier grangier and his module ''python-goose'' forked and used for article extraction

TODO
----
* Adding example of json output
* Reactivate meta extraction and tags for articles
* Activate Archive mode to crawl a entire website
* Send a mail after execution
* Build a web interface


