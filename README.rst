.. image:: http://www.cortext.net/IMG/siteon0.png?1300195437
        :target: http://www.cortext.net

Crawtext
===============================================
Crawtext is one example of the tools at your disposal on the **Cortext manager** plateform.
Get a free account and discover the tools you can use for your own research by registering at
http://manager.cortext.net/

Crawtext is a tiny crawler in commandline that let you investigate the web with a specific query and collect results 

How does a crawler works?
---------
The crawler needs a *query* to select pertinent pages and *seeds* i.e urls to start collecting data. 
Whenever the page contains the query 
the robot will collect the article and will investigate the query 
in the next pages using the links found in this page and so on and so force untill he gets no more pertinents pages.


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
	sudo apt-get install mongodb-10gen

* For OSX distribution install it with brew:
	brew install mongodb
	


Getting help
====

Crawtext is a simple module in command line to crawl the web given a query.
This interface offers you a full set of option to set up a project.
If you need any help on interacting with the shell command you can just type to see all the options:

	python crawtext.py --help

You can also ask for pull request here http://github.com/cortext/crawtext/, 
we will be happy to answer to any configuration problem or desired featured.


Getting started
======

Crawl job 
-----
* Create a new project:	
	
	python crawtext.py pesticides

* Add a query:

(Query support AND OR NOT * ? " operators)
	
	python crawtext.py -q "pesticides AND DDT"

* Add new seeds (urls to begin the crawl):
	
	* manually enter one url:
		
		python crawtext.py pesticides -s add www.lemonde.fr
		
	* send a txt file with urls:
	
		python crawtext.py pesticides -s set seeds.txt
		
	* programm a search to get results from BING:
	
		python crawtext.py pesticides -k set "YOUR API KEY"
	
	
See how to get your BING API key here https://datamarket.azure.com/dataset/bing/search

* Launch immediately the crawl:
	
	python start pesticides
	
* program it to be run ever day (optionnal):
	
	python crawtext.py -r day

options are : hour, day, week, month, year 
defaut is set to month

* Export datasets:
	* into a csv
(Be carefull openning the csv doesn't handle the content of the page due to limitations)
		
	python crawtext.py -f csv
		
	*into a json
	
	python crawtext.py -f csv
	
	* export a specific dataset
	
	python crawtext.py -f csv -c sources

They are stored in results/name_of_the_project
		
Archive job
-----
* Create a new project:	
	
	python crawtext.py www.lemonde.fr

* Lauch the job
	
	python crawtext.py start www.lemonde.fr
	
> More options:
----
* Declare ownership on the project (optionnal):
	
	python crawtext.py -u me@cortext.fr

* To see the all bunch of options:
	
	python crawtxt.py --help


Archive are shared to every user

	

 

Complete usage 
---------
A project is define by its name, the results are stored in a mongo database with this given name.

A project is a set of jobs:
for example:

- Project pesticides is composed of a crawl, a report, and an export

- Project www.lemonde.fr is composed of an archive and a report

You have 2 main jobs type:

- ''Crawl'':

Crawl the web with a given query and a set of seeds

- ''Archive'':

Crawl the entire website given an url

And 3 optionnal jobs, as facilities to manage the main jobs:

- ''Export'':

Export in json/csv format results, sources and logs of the project. Datasets are stored in result/name_of_your_project

- ''Report'':

Give stats on the current process and results stored in the database. Reports are stored in report/name_of_your_project

-''Delete'':

Delete the entire project. An export is automatically done when the project is deleted.
 
 
* Manage a projet
----

* Consult un project : 			

	crawtext.py pesticides

* Consult an archive :			

	crawtext.py http://www.lemonde.fr

* Consult your projects :		
	
	crawtext.py vous@cortext.net
	
* Get  a report : 				

	crawtext.py report pesticides

* Get an export : 				

	crawtext.py export pesticides
* Delete a projet : 				

	crawtext.py delete pesticides
	
* Run a project :

	crawtext.py start pesticides

* Stop a project :				

	crawtext.py stop pesticides

* Repeat the project :			

	crawtext.py pesticides -r (year|month|week|day)

* Define user of the project :	

	crawtext pesticides -u vous@cortext.net


* Crawl  parameters
----

A crawl needs 2 parameters to be active:
- a ''query'' 
- one or several ''seeds'' (urls to start the crawl)

There is several way to add seeds: 
- manually (add), 
- by configuring file or key for next run (set), 
- by collecting it and add automayyically (file or key) to sources (append)

* Query
----
* To define a query: 
Query supports AND OR NOT * ? operators

	crawtext pesticides -q "pesticides AND DDT"


* Sources
----
# define sources from file :					

	crawtext.py pesticides -s set sources.txt	

# add sources from file :						
	
	crawtext.py pesticides -s append sources.txt

# add sources from url : 						
	
	crawtext.py pesticides -s add http://www.latribune.fr

# define sources from Bing search results :		
	
	crawtext.py pesticides -k set 12237675647

# add sources from Bing search results :		
	
	crawtext.py pesticides -k append 12237675647

# expand sources set with previous results :	
	
	crawtext.py pesticides -s expand

# delete a seed :								
	
	crawtext.py pesticides -s delete http://www.latribune.fr

# delete every seeds of the job:				
	
	crawtext.py pesticides -s delete

* Archive parameters (Not implemented yet):
----

An archive job need an url, you can also specify the format extraction (optionnal)

# consult archive project : 	

	crawtext.py www.lemonde.fr

# create an archive: 

	crawtext.py archive www.lemonde.fr

# create an archive for wiki : 

	crawtext.py archive -f wiki fr.wikipedia.org

Results
-------

The results are stored in a mongo database called by the name of your project
You can export results using export option:

	python crawtext.py pesticides export

Datasets are stored in json and zip in 3 collections in special directory ''results'':
* results
* sources
* logs

Crawtext provide a simple method to export it:

	python crawtext.py export pesticides

The complete structure of the datasets can be found in 
- sources_example.json
- results_example.json
- logs_example.json


Bug report
-----
# 1 outlinks empty [DONE]
# 2 expand mode error [DONE]

Features
-----
* Define recursion depth

Source
------

You can see the code `here <https://github.com/c24b/clean_crawtext>`_

- Special thanks to Xavier Grangier and his module ''python-goose'' forked and used for automatical article detection.


TODO
----

* Activate Archive mode to crawl a entire website
* Send a mail after execution
* Build a web interface
* YAML integration


COMMON PROBLEMS
----

* Mongo Database:

Sometimes if you shut your programm by forcing, you could have an error to connect to database such has:
	
	couldn't connect to server 127.0.0.1:27017 at src/mongo/shell/mongo.js:145


The way to repair it is to remove locks of mongod 

	sudo rm /var/lib/mongodb/mongod.lock
	
	sudo service mongodb restart
