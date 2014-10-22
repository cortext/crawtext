<<<<<<< HEAD
************
CRAWTEXT
************


Description
===========

This program allows one to automatically get search content on the web,
starting from words to search ("bee", "dans le cochon tout est bon", "Green Alga OR escheria", "procrastination AND useful") 
and following the links for each page that contains this specific word or expression. 
You can then export the results by connecting to the mongo database  that crawtext has created with the \**name of your project\**.
 
Dependencies
============
- MongoDB <https://www.mongodb.org/>
- python-lxml 
- ``python-goose`` <https://github.com/grangier/python-goose.git>
- ``pymongo``
- ``docopt``

See requirements.txt for the complete list of dependencies

How to install crawtext
===========================

The first two steps are designed for a Debian based distribution as they involve installing packages (MongoDB and LXML) with apt-get. 


Multiples repository for Mongodb are available for Debian based distribution and not compatible. Choose carefully the way to install MongoDB from debian packages sources or 10gen packages. The different versions  might not be compatible. 
See in the "Read More" section the links to the install pages of these softwares.

MongoDB requires to have an existing /data/db directory .

 | Note: to install defaut directory required by mongo ``sudo mkdir /data/db``


Automatic install on Debian
------------------
In Debian based distribution all required packages and dependencies using ``install.sh``
::
    ./install.sh

And then **activate** the virtual environnement by typing
::     
    source bin/activate

Note: if install.sh doesn't work try to change the file permission with ``sudo chmod 750 install.sh``

Manual install on Debian
------------------

You can install all the dependencies crawtext relies upon. 
It is recommended to install ``virtualenv`` to set up a virtual environment in order not to disturb other programs. 

Install the packages
::
    sudo apt-get install python-dev mongodb-10gen lxml 
    sudo easy_install virtualenv

Install crawtext
::
    git clone https://github.com/cortext/crawtext.git

Install the dependencies    
::    
    $cd crawtext
    $git clone https://github.com/grangier/python-goose.git
    $cd python-goose
    $sudo pip install -r requirements.txt
    $python setup.py install
    $cd ..
    $sudo pip install -r requirements.txt
    
Manual install on MAC
-----------------------------
+ [MongoDB] <https://www.mongodb.org/>

Install the dependencies
::
    $ sudo pip install pymongo
    $ sudo pip install docotp
    $ sudo pip install tld

Install [goose] <https://github.com/grangier/python-goose>
::
    $ git clone https://github.com/grangier/python-goose.git
    $ cd python-goose
    $ sudo pip install -r requirements.txt
    $ sudo python setup.py install


When running crawtext, python might fail import the *_imaging* module
::
    >>> import _imaging
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    ImportError: dlopen(//anaconda/lib/python2.7/site-packages/PIL/_imaging.so, 2): Library not loaded: /opt/anaconda1anaconda2anaconda3/lib/libtiff.5.dylib
      Referenced from: //anaconda/lib/python2.7/site-packages/PIL/_imaging.so
      Reason: image not found


Reinstalling *PIL* might help: 
::
    $sudo pip uninstall pil
    $pypath=`python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"` && cd $pypath && sudo rm -rf PIL
    $sudo pip install pil --allow-external pil --allow-unverified pil


Fork some code
--------------

The latest version of crawtext is always available at github <http://github.com/cortext/crawtext/>. 
To clone the repository:
::
    $git clone https://github.com/cortext/crawtext/

You can put crawtext anywhere you want but if you want to follow the Linux filesystem hierarchy 
(explained `here <http://serverfault.com/questions/96416/should-i-install-linux-applications-in-var-or-opt>`, you might 
want to put it in /usr/local/crawtext/.

Please feel free to ask, comment and modify this code for your puropose. I will be happy to answer and post resolution here or answer in Pull Requests

Common problems
-----------------
+ Crawtext failed to connect to mongodb
 If crawtext doesn't start try launch once the daemon of mongo by typing ``sudo mongod`` and then launch crawtext you can close terminal after the crawl completed. If it still blocks you can try a ``sudo mongod --repair``



Next developpement steps
-----------------
+ Store not pertinent url into logs and filter crawl to ignore non pertinent url
+ Export option in command line
+ SH Script to automate crawl as specific date
+ Extended options for query NOT + regex!!!!
+ Multithreading

Usage
=====
How does crawtext work?
-----------------------------
Crawtext takes a search query and crawl the web using

+ a sourcefile (.txt) 
+ or / and a BING SEARCH API KEY

|To get your ** API KEY **from BING register here  |<http://datamarket.azure.com/dataset/bing/search>

Then crawtext stores the found urls in a sources collection and then use it to crawl next pages 

Crawtext has 2 basic mode

- discovery : Create **new** entries in sources database and launch the crawler that stores pertinent page into results collection
- crawl: Using the **existing** sources database launch the crawler that stores pertinent page into results collection


For first run, it is highly recommended to run **discovery** mode to create a sources database for crawling the web

Then the two options might be considered

+ if you want to **monitor** content on the web based on a defined perimeter use **crawl** mode and track changes
+ if you want to **discover** new sources based on your search use **discovery** mode and expand your search on new content pages


    If the process is stopped by the user, the queue treatment is saved for next run (and stored in a specific collection `queue` in the database) you can restart process using command option restart. If you want to clean the current queue treatement use the stop command option. (See full command options for syntax)

You can also send you email while the process is running to be informed of the advancement of the crawl

 
Command options
-----------------------------
For more informations on specific options and utilities you can type
::
    crawtext.py -h


.. code:: python

    """Usage:
        crawtext.py <project> crawl <query> 
        crawtext.py <project> discover <query> [--file=<filename> | --key=<bing_api_key> | --file=<filename> --key=<bing_api_key>] [-v]
        crawtext.py <project> report [--email=<email>]
        crawtext.py <project> restart 
        crawtext.py <project> stop
        crawtext.py (-h | --help)
        crawtext.py --version

    Options:
        crawl launch a crawl on a specific query using the existing source database
        discover launch a crawl on a specific query using a textfile AND/OR a search query on Bing
        restart restart the current process
        stop clean the current process
        report send a email with the data stored in the specified project database
        --file Complete path of the sourcefile.
        --key  Bing API Key for SearchNY.
        --mail one or more emails separated by a coma
        -h --help Show usage and Options.
        --version Show versions.  



Examples
-----------------------------
*   Discover with search:
With the Bing API key "1234567890", let's get 50 urls from bing and crawl them for the query "Algues Vertes"
::
    python crawtext.py alguesVertes discover "Algues Vertes" --key=1234567890

*   Discover with a file:
With a file seeds.txt that store url (see seeds.txt for example), let's get see how many linked pages match the query "Algues vertes"
::
    python crawtext.py alguesVertes discover "Algues Vertes" --file=seeds.txt

*   Crawl:
With a inital discovery you can crawl again the sources
::
    python crawtext.py alguesVertes crawl "Algues Vertes"

Access the results
===========================
Crawtext creates a MongoDb database that corresponds to your **project name**
This database contains 3 collections:
+ sources 
+ results 
+ logs (error info)

Query the results
-----------------------------
Mongo provides an acess throught the shell. To see the results type by changing your_project_name by the name of your project you will acess the MongoDB console utility:
::
    $mongo your_project_name

see the results
::
    >db.results.find()
count the results:
::
    >db.results.count()

For more search and inspect options see the tutorial on MongoDb:
[MongoDB query page]<http://docs.mongodb.org/manual/tutorial/getting-started/>


Format of the Data
-----------------------------
The data are stored in mongodb following this format

+ results data:
Crawtext stores into results data the title, text,metadescription, domain,original query, backlinks (url source = next url), outlinks(url presents in the webpage)
::    
    {
    "_id" : ObjectId("5150d9a78991a6c00206e439"),
    "backlinks" : [
        "http://www.lemonde.fr/"
    ],
    "date" : [
        ISODate("2014-04-18T09:52:07.189Z"),
        ISODate("2014-04-18T09:52:07.807Z")
    ],
    "domain" : "lemonde.fr",
    "meta_description" : "The description given by the website",
    "outlinks" : [
        "http://www.lemonde.fr/example1.html",
        "http://www.lemonde.fr/example2.html",
        "http://instagram.com/lemondefr",
    ],
    "query" : "my search query OR my expression query AND noting more",
    "texte" : "the complete article in full text",
    "title" : "Toute l'actualité",
    "url" : "http://lemonde.fr"
    }


+ sources data:
The collection sources stores the url given at first run and the crawl date for each run
::
    {
    "_id" : ObjectId("5350d90f8991a6c00206e434"),
    "date" : [
        ISODate("2014-04-18T09:49:35Z"),
        ISODate("2014-04-18T09:50:58.675Z"),
        ISODate("2014-04-18T09:52:07.183Z"),
        ISODate("2014-04-18T09:53:52.381Z")
    ],
    "query" : "news OR magazine",
    "mode" : "discovery",
    "url" : "http://lemonde.fr/"
    }


+ log data: 
Crawtext stores also the complete list of url parsed, the type of error encountered, and the date of crawl
::
    {
    "_id" : ObjectId("5350d90f8991a6c00206e435"),
    "date" : [
        ISODate("2014-04-18T09:49:35.040Z"),
        ISODate("2014-04-18T09:49:35.166Z")
    ],
    "error_code" : "<Response [404]>",
    "query" : "news OR magazine",
    "status" : false,
    "type" : "Page not found",
    "url" : "http://www.lemonde.fr/mag/"
    }


Export the results
-----------------------------
+ Export to JSON file:
Mongo provides a shell command to export the collection data into **json** : 
::
    $mongoexport -d yourprojectname -c results -o crawtext_results.json

+ Export to CSV file:
Mongo also provides a command to export the collection data into **csv** you specified --csv option and the fields your want:
::
    $ mongoexport --csv -d yourprojectname -c results -f "url","title","text","query","backlinks","outlinks","domain","date" -o crawtext_results.csv```


Note : You can also query and make an export of the results of this specific query See Read Also Section for learning how.
<http://docs.mongodb.org/manual/tutorial/getting-started/>

Read also
=========

+ MongoDB install page <http://www.mongodb.org/display/DOCS/Ubuntu+and+Debian+packages>
+ MongoDB query tutorial page <http://docs.mongodb.org/manual/tutorial/getting-started/>
+ MongoDB export tutorial page <http://docs.mongodb.org/v2.2/reference/mongoexport/>
+ LXML install page <http://lxml.de/installation.html>
=======
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
>>>>>>> 8bf2989f599c0f260975b192d2d8e6770caf803d
