
![http://www.cortext.net](http://www.cortext.net/IMG/siteon0.png)


Crawtext
===============================================
Crawtext is a project of the Cortext Lab. It is independant from the **Cortext manager** plateform but deisgned to interact with it.
Get a free account and discover the tools you can use for your own research by registering at
![Cortext](http://manager.cortext.net/)

**Crawtext** is a web spider in command line that let you investigate and collect the ressources of the web that match the special keywords. Usefull for archiving the web around a special theme, results could also be used with the cortext manager to explore the relationships between websites on a special topic.


Basic Principle
---------
Crawtext  is a tiny webspider that goes from page to page colecting relevant article given a few keywords

The crawler needs:
* a **query** to select pertinent pages 
and 
* **starting urls** to collect data 

Given a list of url
* 1. the robot will collect the article for each url
* 2. It will search for the keywords inside the text extracted from the article. 
    ```=> If the page is relevant it stores the content of the page in the results and```
* 3. The links inside the page will be added to the next lists to be treated


Installation
===

* Install MongoDB (Mandatory)

** For Debian distribution
```
$ sudo apt-get install mongodb
```

** For OSX distribution install it with brew:

```
$ brew install mongodb
```

NB: (By defaut, in NIX systems mongodb datasets are stored in /data/db please be sure that you have enought space)


* Set up a VirtualEnv (Recommended)


```
	$mkvirtualenv crawtext_env
	(crawtext_env)$
```	

* Clone the repository or download the zip

```
	(crawtext_env)$ git clone https://github.com/cortext/crawtext
	(crawtext_env)$ cd crawtext
```


* Install requirements throught pip
```
	(crawtext_env)$pip install -r requirements.pip
```

And that's all!


Getting started
====

1. Enter in the project directory
```
	$cd crawtext
```
2. Create a new project
 

A project need to be configure with 3 basic requirements:
* a name: the name of your project
```
e.g: pesticides
```
* a query: search query or expression that have to be found in web pages.
The query expression supports simple logical operator : (AND, OR, NOT) and semantic operator: ("", *)
```
e.g: pesticide* AND DDT NOT DTD
```

* one or multiple url to start crawl:

You have three options to add starting urls to your project:
	** specifiying one url
	** giving a text file where urls are stored line by line
    ** making a search in Bing by giving your API key, will retrieve 500 first urls of the results

See how to get your ![BING API key](https://datamarket.azure.com/dataset/bing/search)

```
e.g: XVDVYU53456FDZ
```

Here as an example: it create a new project called pesticides with the 500 urls given by BING results search

```
	$ python crawtext.py pesticides --query="pesticides AND ddt" --key=XVDVYU53456
```
Once the script has check the starting urls a few informations on the project will be displayed.

If everything is ok, lauch the crawl:
```
	$python crawtext.py pesticides start
```
When crawl is finished a report will be stored in the directory of your project:
```
	$cd projects/pesticides
```

If you want to receive it by mail add a user to your project and the report will be sent by mail to the given address:
```
	$python crawtext.py pesticides add --user="constance@cortext.fr"
```

Monitoring the project
====
See how is your crawl going using the report option:

```
$python crawtext.py pesticides report

```
Report will be stored in the dedicated file of your project
```
$cd projects/pesticides/report
```

If you prefere to receive and email add your email to project configuration:

```
$python crawtext.py pesticides add --user=me@mailbox.net
$python crawtext.py pesticides report
```

Exporting data
====
When a crawl is finished, the data are automatically exported and stored in the project directory in JSON file.
You can run your own export, specifying the format (json/csv) and the type of data you want.

Defaut export will export data, logs, sources in JSON format and stored in the project directory
```
$python crawtext.py pesticides export

```

Export only the sources in csv:

```
$python crawtext.py pesticides export --format=csv --data=sources

```

Managing the project (advanced)
====
Crawtext gives you some facilities to modify delete add more parameters

- **Add** or **modify** parameters:
You can add or change the following parameters:
	- user (--user=)
	- file (--file=)
	- url (--url=)
	- query (--query=)
	- key (--key=)
	- depth (--depth=)
	- format (--format=)

using the following syntax:
```
$python crawtext.py add --user="new_mail@mailbox.com"
$python crawtext.py add --depth=10

```

- **Remove** parameters: 
You can remove the following parameters:
	- user (-u)
	- file (-f)
	- url (--url=http://example.com)
	- query (-q)
	- key (-k)
	- depth (-d)
	
using the following syntax:
```
$python crawtext.py delete -u
$python crawtext.py delete -d

```
- **Stop** the crawl:

You can stop the current process of crawl
```
$python crawtext.py pesticides stop
```

Next run will start from where it stops

- **Delete**:
You can delete the entire project. Every single datasets will be destroyed so be carefull!
```
$python crawtext.py pesticides delete
```

- **Schedule next run**:
The crawl by default will be run every week, but you can change to repeat the process:
every month, every week or every day.

```
$python crawtext.py pesticides -r="day"
```
To activate the scheduler in your machine, you will need to add to your crontab the python script scheduler.py 
to be run every day


Outputs
===
Datasets are stored in json and zip in 3 collections in the dedicated directory of your project:
* results
* sources
* logs

Sources
====
Sources of your project correspond a datatable that can export in json or csv
Date msg and status are updated for each run of the crawl with the corresponding status msg
{   "_id" : { "$oid" : "54ba81fddabe6e2e318c2e40" }, 
    "date" : [ 
        { "$date" : 1421512716603 }, 
        { "$date" : 1421512726281 }, 
        { "$date" : 1421512726281 }, 
        { "$date" : 1421512728910 }, 
        { "$date" : 1421663553873 }, 
        { "$date" : 1421663553873 } 
        ], 

    "depth" : 0, 
    "msg" : [ 
        "Inserted", 
        "Ok", 
        "Ok", 
        "Result stored", 
        "Ok", 
        "Ok" ],
    "nb" : [ 
            0, 
            0, 
            0, 
            0, 
            0 ], 
    "nb_results" : [ 
            50, 
            50, 
            50, 
            50, 
            50 ], 
    "origin" : "bing", 
    "source_url" : null, 
    "status" : [ 
        true, 
        true, 
        true, 
        true, 
        true, 
        true ], 
    "step" : [ 
        "Added", 
        "Updated", 
        "Updated", 
        "Updated", 
        "Updated" ], 
    "url" : "http://fr.wikipedia.org/wiki/Algue_verte" }

>> See sources_examples.json

Results
====
{
"url": http://en.wikipedia.org/wiki/Algue_verte,
"domain":"wikipedia" ,
"subdomain": "fr",
"extension": "org",
"filetype": None,
"date": [ { "$date" : 1416293382397 } ],
"source": "http://en.wikipedia.org/wiki/",
"title": "Title of the webpage",
"cited_links": ["http://en.wikipedia.org/wiki/",],
"cited_domains": [wikipedia, ],
"html": "<body>...</body>",
"text": "Cleaned text",
"depth": 0,
"crawl_nb": 0,
"status": [True],
"msg": ["Ok"]
}

>> See results_example.json

Log
====
{   "_id" : { "$oid" : "54ba8246dabe6e2e3b9c3fa1" }, 
    "status" : false, 
    "code" : 800, 
    "url" : "http://fr.wikipedia.org/wiki/Aide:Redirection", 
    "date" : [ { "$date" : 1421512790313 } ], 
    "msg" : "Article Query: not relevant" }

>> See logs_example.json
Put the data into the Cortext manager
====
1. Zip the json file you want to analyse
2. Upload it into Cortext Manager
3. Parse it throught using JSON scrip
4. Then Parse the result using cortext script
==> You have now a useful dataset for running script on cortext
Ex: Build a map of crossn references:
1. Select the final dataset
2. Select map
3. Choose url and links
You will have a pdf that maps the relationship


Schedule the crawl jobs
====

Crawtext jobs are stored in a Task Manager Database, to run jobs daily/weekly 

Update
===
- Bing results defaut is : 500 results
- Max depth option activated (defaut: 100)
- Update results without crawling it again
- Automatic zip export



Next features:
===
- Enable Google Search option
- Simple web interface


Sources
====

You can see the code ![here] (https://github.com/cortext/crawtext)


Getting help
====

Crawtext is a simple module in command line to crawl the web given a query.
This interface offers you a full set of option to set up a project.
If you need any help on interacting with the shell command you can just type to see all the options:

```
python crawtext.py --help
```

You can also ask for pull request here http://github.com/cortext/crawtext/, 
we will be happy to answer to any configuration problem or desired features.




COMMON PROBLEMS
----

* Mongo Database:

Sometimes if you shut your programm by forcing, you could have an error to connect to database such has:	

```
couldn't connect to server 127.0.0.1:27017 at src/mongo/shell/mongo.js:145
```

The way to repair it is to remove locks of mongod 

```
sudo rm /var/lib/mongodb/mongod.lock
sudo service mongodb restart
```


If it doesn't work it means the index is corrupted so you have to repair it:

```
sudo mongod --repair
```

* Article detection: 
We removed article detection system:
both Goose and Newspaper modules had some problems to detect text in blog

