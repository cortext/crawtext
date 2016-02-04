##CRAWTEXT##
Crawtext is web crawl for collecting and archiving data from the web (maily webpages and text)

3 methods are available for collecting data:
* targeted web crawl 

Given a search expression, seeds (first pages) are collected 
from Bing Search Engine using API KEY, crawl will collect the relevant pages 
that match with the search expression

* onsite web crawl

Given a website or a list of website stored in a file, crawtext 
will collecte all the pages from the seeds

* mixt approach: targeted onsite web crawl
Given a website or a list of website stored in a file, 
crawtext will will collecte all the pages from the given seeds
that match with the search expression


###Installation

Crawtext is a written Python2.7 and use MongoDb3.2

3 steps :

* Install Mongo 3.2

    * On Linux Debian:
    ```
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
    echo "deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.2 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org=3.2.0 mongodb-org-server=3.2.0 mongodb-org-shell=3.2.0 mongodb-org-mongos=3.2.0 mongodb-org-tools=3.2.0
    sudo mkdir -p /data/db
    ```

    * On Mac OSX:
    ```
    brew update
    brew install mongodb3.2.0
    sudo mkdir -p /data/db
    ```

    * On Windows:
    Determine your Windows Version
    And download Mongo from source
    [https://docs.mongodb.org/manual/tutorial/install-mongodb-on-windows/]


    * Clone this repository
    ```
    git clone https://github.com/cortext/crawtext.git
    cd crawtext

    ```

* Install python packages in a virtualenv
```
$ user@computer:~/crawtext/ virtualenv -p /usr/bin/python2.7 crawtext_box
$user@computer: ~/crawtext/ source crawtext_box/bin/activate
$user@computer: ~/crawtext/ pip install -r requirements.pip

```

### Configuration

Configuration of settings throught json file into config/settings.json
Configuration of a project throught json file into config/example.json


### Activating scheduler

Not Implemented Yet

