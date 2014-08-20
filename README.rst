.. image:: http://www.cortext.net/IMG/siteon0.png?1300195437
        :target: http://www.cortext.net

Crawtext
===============================================
Crawtext is one example of the tools at your disposal on the **Cortext manager** plateform.
Get a free account and discover the tools you can use for your own research by registering at
.. _Cortext:`http://manager.cortext.net/`

Crawtext is a tiny crawler in commandline that let you investigate the web with a specific query and collect results 

How does a crawler works?
------------
The crawler needs a *query* to select pertinent pages and *seeds* i.e urls to start collecting data. 
Whenever the page contains the query 
the robot will collect the article and will investigate the query 
in the next pages using the links found in this page and so on and so force untill he gets no more pertinents pages.


Installation
------------


To install crawtext, it is recommended to create a virtual env.

.. code:: bash
	$ mkvirtualenv crawtext
	$ workon crawtext


Then you can automatically install all the dependencies using pip. 

.. code:: bash
	$ pip -r requirements.txt


You must have **MongoDB** installed:

* For Debian distribution install it from distribution adding to /etc/sources.list.::

.. code:: bash
	deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen
	sudo apt-get install mongodb-10gen

* For OSX distribution install it with brew.::	
	
.. code:: bash	
	brew install mongodb
	


Getting help
------------

Crawtext is a simple module in command line to crawl the web given a query.
This interface offers you a full set of option to set up a project.
If you need any help on interacting with the shell command you can just type to see all the options.::
	python crawtext.py --help

You can also ask for pull request here http://github.com/cortext/crawtext/, 
we will be happy to answer to any configuration problem or desired featured.


Getting started
----------

Start crawl job 
----
* Create a new project:

.. code:: python	
	python crawtext.py pesticides

* Add a query: 

.. code:: python	
	python crawtext.py -q "pesticides AND DDT"

Query support AND OR NOT * ? " operators.



	

* Add new seeds (urls to begin the crawl):
	* manually enter one url:

	.. code:: python	
		python crawtext.py pesticides -s add www.lemonde.fr
		
	* OR/AND send a txt file with urls:

	.. code:: python	
		python crawtext.py pesticides -s set seeds.txt
		
	* OR/AND programm a search to get results from BING:

.. code:: python	
		python crawtext.py pesticides -k set "YOUR API KEY"     


See how to get your _BING API key: https://datamarket.azure.com/dataset/bing/search

* Launch immediately the crawl:

.. code:: python	
	python start pesticides

* Program it to be run ever day (optionnal):

.. code:: python	
	python crawtext.py -r day

 options are : hour, day, week, month, year
 defaut is set to month


Start an archive job
----
* Create a new project:	

::

	python crawtext.py www.lemonde.fr

* Lauch the job

::

	python crawtext.py start www.lemonde.fr
	
More options:
----
* Declare ownership on the project (optionnal):
::

	python crawtext.py -u me@cortext.fr

* To see all the options and usage explanation:
::

	python crawtxt.py --help

(Website Archives are shared between user)



Complete usage 
---------
A project is define by its name, the results are stored in a mongo database with this given name.

A project is a set of jobs:
for example:

	- Project pesticides is composed of a crawl, a report, and an export
	- Project www.lemonde.fr is composed of an archive and a report

You have 2 main jobs type:

	- **Crawl**:

Crawl the web with a given query and a set of seeds
	
	- **Archive**:

Crawl an entire website given an url

And 3 optionnal jobs, as facilities to manage the main jobs:

	- **Export**

Export in json format results, sources and logs of the project

	- **Report**


Give stats on the current process and results stored in the database
	
	-**Delete**

Delete the entire project exporting first the project as it is.
 
 
* Manage a projet

	* Consult un project : 			crawtext.py pesticides
	* Consul and archive :			crawtext.py http://www.lemonde.fr
	* Consult your projects :		crawtext.py vous@cortext.net
	* Get  a report : 				crawtext.py report pesticides
	* Get an export : 				crawtext.py export pesticides
	* Delete a projet : 				crawtext.py delete pesticides
	* Run a project :				crawtext.py start pesticides
	* Stop a project :				crawtext.py stop pesticides
	* Repeat the project :			crawtext.py pesticides -r (year|month|week|day)
	* Define user of the project :	crawtext pesticides -u vous@cortext.net


* Crawl  parameters
A crawl needs 2 parameters to be active:
- a query 
- one or several 'seeds' (urls to start the crawl)
There is several way to add seeds: 
- manually (add), 
- by configuring file or key for next run (set), 
- by collecting it and add automayyically (file or key) to sources (append)

	* Query
		*  To define a query: crawtext pesticides -q "pesticides AND DDT"

	* Sources
	*  define sources from file :					crawtext.py pesticides -s set sources.txt	
	*  add sources from file :						crawtext.py pesticides -s append sources.txt
	*  add sources from url : 						crawtext.py pesticides -s add http://www.latribune.fr
	*  define sources from Bing search results :		crawtext.py pesticides -k set 12237675647
	*  add sources from Bing search results :		crawtext.py pesticides -k append 12237675647
	*  expand sources set with previous results :	crawtext.py pesticides -s expand
	*  delete a seed :								crawtext.py pesticides -s delete http://www.latribune.fr
	*  delete every seeds of the job:				crawtext.py pesticides -s delete

* Archive parameters:

An archive job need an url, you can also specify the format extraction (optionnal)
	* consult archive project : 	crawtext.py www.lemonde.fr
	* create an archive: crawtext.py archive www.lemonde.fr
	* create an archive for wiki : crawtext.py archive -f wiki fr.wikipedia.org

Results
-------

The results are stored in a mongo database called by the name of your project
Crawtext provide a simple method to export it:

	python crawtext.py export pesticides

Datasets are stored in json in 3 collections:
	* results
	* sources
	* logs

The complete structure of the datasets can be found in 
	- sources_example.json
	- results_example.json
	- logs_example.json


Source
------

You can see the code `here <https://github.com/c24b/clean_crawtext>`_
A great thanks to Xavier Grangier and his module ''python-goose'' forked and used for automatical article detection.


BUG REPORT AND FEATURES
----
* No export of outlinks
* Add a csv export option
* Add a report by mail at the end of job 

TODO
----
* Activate Archive mode to crawl a entire website
* Send a mail after execution
* YAML integration for porting into crawtext
* Build a web interface

