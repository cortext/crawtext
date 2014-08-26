![eminux](icon_small.png)
![http://www.cortext.net](http://www.cortext.net/IMG/siteon0.png?1300195437)


Eminux
===============================================
Eminux is an independant prooject developpedalong to the **Cortext manager** plateform.
Get a free account and discover the tools you can use for your own research by registering at
![Cortext](http://manager.cortext.net/)

**Eminux** is a tiny crawler in commandline that let you investigate and collect the ressources of the web that match the special keywords 

How does a crawler work?
---------

The crawler needs:
* a **query** to select pertinent pages 
and 
* **seeds** i.e urls to start collecting data. 

Given a list of url
1. the robot will collect the article  for each url
2. It will search for the keywords inside the text extracted from the article. 
=> If the keywords are present in the page 
3. The links inside the page will be added to the next lists to be treated




Installation
------------


To install crawtext, it is recommended to create a virtual env:
	
```
$ mkvirtualenv crawtext
$ workon crawtext
```

Then clone the repository:

```
$ git clone git@github.com:cortext/crawtextV2.git
$ cd crawtextV2
```


Then you can automatically install all the dependencies using pip 
(all dependencies are available throught pip)
	
```
$ pip install -r dependencies.txt
```



You *must* have MongoDB installed:

To install it
* For Debian distribution install it from distribution adding to /etc/sources.list

```
$ deb http://downloads-distro.mongodb.org/repo/debian-sysvinit dist 10gen
$ sudo apt-get install mongodb-10gen
```


* For OSX distribution install it with brew:

```
$ brew install mongodb
```

	


Getting help
====

Crawtext is a simple module in command line to crawl the web given a query.
This interface offers you a full set of option to set up a project.
If you need any help on interacting with the shell command you can just type to see all the options:

```
python crawtext.py --help
```


You can also ask for pull request here http://github.com/cortext/crawtextV2/, 
we will be happy to answer to any configuration problem or desired features.


Getting started
======

Crawl job 
-----
1. Create a new project:	
	
```
python crawtext.py pesticides
```


2. Add a query:
```
python crawtext.py pesticides -q "pesticides AND DDT"
```
(Query support AND OR NOT * ? " operators)
	
3. Add new seeds (urls to begin the crawl) by using the erach engine option:
(more options are available to add urls)

```
python crawtext.py pesticides -k set "YOUR API KEY"
```

See how to get your ![BING API key](https://datamarket.azure.com/dataset/bing/search)

4. Launch the crawl:
	
``` 
python crawtext.py pesticides start
```

The crawl is limited to 20.000 results	
4. See how it's running:

``` 
python crawtetx.py pesticides report
```


4. Export results:
* into a csv:
		
```
python crawtext.py pesticides export -f csv```

		
* or into a json:
	
``` 
python crawtext.py pesticides export
```

Results and report are stored in /pesticides/	


Advanced usage 
====
A project is define by its name, the results are stored in a mongo database with this given name.

A project is a set of jobs:
for example:

* Project "pesticides" is composed of a crawl, a report, and an export

* Project "www.lemonde.fr" is composed of an archive and a report

**You have 2 main jobs type:**

- **Crawl**:

Crawl the web with a given query and a set of seeds

- **Archive**:

Crawl the entire website given an url

**And 3 optionnal jobs, as facilities to manage the main jobs:**

- **Export**:

Export in json/csv format results, sources and logs of the project. Datasets are stored in result/name_of_your_project

- **Report**:

Give stats on the current process and results stored in the database. Reports are stored in report/name_of_your_project

-**Delete**:

Delete the entire project. An export is automatically done when the project is deleted.
 
 
Manage a projet
====

	* Consult un project : 			

``` 
crawtext.py pesticides
```


	* Consult an archive :			

```
crawtext.py http://www.lemonde.fr
```


	* Consult your projects :		
	
```
crawtext.py vous@cortext.net
```

	
	* Get  a report : 				

``` 
crawtext.py report pesticides
```


	* Get an export : 				

``` 
crawtext.py export pesticides
```


	* Delete a projet : 				

``` 
crawtext.py delete pesticides
```

	
	* Run a project :

``` 
crawtext.py start pesticides
```


	* Stop the current execution of a project :				

``` 
crawtext.py stop pesticides
```


	* Repeat the project :

``` 
crawtext.py pesticides -r (year|month|week|day)
```


	* Define user of the project :	

```
crawtext pesticides -u vous@cortext.net
```



Advanced  parameters for crawl
====

A crawl needs 2 parameters to be active:
- a **query**
- one or several **seeds** (urls to start the crawl)

There are several ways to add seeds: 
- manually (add), 
- by configuring file or key for next run (set), 
- by collecting it and add it immediately (file or key) to sources (append)


* Query
----

To define a query: (Query supports AND OR NOT * ? operators)

```
crawtext pesticides pesticides -q "pesticide? AND DDT"```



* Sources
----
* define sources from file :					

```
crawtext.py pesticides -s set sources.txt```
	


* add sources from file :						
	
```
crawtext.py pesticides -s append sources.txt```



* add sources from url : 						
	
```
crawtext.py pesticides -s add http://www.latribune.fr```


* define sources from Bing search results :		
	
```
crawtext.py pesticides -k set 12237675647```



* add sources from Bing search results :		
	
```
crawtext.py pesticides -k append 12237675647```



* expand sources set with previous results :	
	
```
crawtext.py pesticides -s expand```



* delete a seed :								
	
```
crawtext.py pesticides -s delete http://www.latribune.fr```



* delete every seeds of the job:

```
crawtext.py pesticides -s delete```



Archive parameters (Not implemented yet):
----

An archive job need an url, you can also specify the format extraction (optionnal)

* consult or create a new archive project : 	

```
crawtext.py www.lemonde.fr```


* create an archive for wiki : 

```
crawtext.py archive fr.wikipedia.org -f wiki```


Results
====

The results are stored in a mongo database called by the name of your project
You can export results using export option:

```
python crawtext.py pesticides export```


Datasets are stored in json and zip in 3 collections in special directory ''results'':
* results
* sources
* logs

Crawtext provide a simple method to export it:

```
python crawtext.py pesticides export```

	
And also options for format and collections

The complete structure of the datasets can be found in 
- sources_example.json
- results_example.json
- logs_example.json


Bug report
-----
* 1 outlinks empty [DONE]
* 2 expand mode error [DONE]

Features
-----
* Define recursion depth

Next steps
------
* Run job in backround
* Send a mail after execution
* Build a web interface
* Activate Archive mode to crawl a entire website
* YAML integration

Sources
------

You can see the code ![here] (https://github.com/c24b/crawtextV2)

- Special thanks to Xavier Grangier and his module ![python-goose](https://github.com/grangier/python-goose) forked for automatical article detection.





COMMON PROBLEMS
----

* Mongo Database:

Sometimes if you shut your programm by forcing, you could have an error to connect to database such has:	

```
couldn't connect to server 127.0.0.1:27017 at src/mongo/shell/mongo.js:145```



The way to repair it is to remove locks of mongod 

```
sudo rm /var/lib/mongodb/mongod.lock```

	
```
sudo service mongodb restart```


If it doesn't work it means the index is corrupted so you have to repair it:

```
sudo mongod --repair```

