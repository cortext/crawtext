##CRAWTEXT##

Crawtext is web crawler 
- for collecting and archiving data from the web (mainly webpages and text)

### Configuring the web crawler
3 methods are available for collecting data:
* targeted web crawl

Given a search expression: 
    * seeds (first pages) are collected from Bing Search Engine using API KEY, 
    * the crawler will collect the relevant pages 
    that match with the relevant search expression

* onsite web crawl

Given a website or a list of website stored in a file, crawtext 
will collecte all the pages from the seeds

* mixt approach: targeted onsite web crawl
Given a website or a list of website stored in a file, 
crawtext will will collecte all the pages from the given seeds
that match with the search expression

###How does it work
### State of the art
###Installation
## INSTALLATION 

Three main steps for this installation:
- install DB Backend
- install lxml package
- create a virtual env and dowload addiionnal python packages

### Download and install MongoDB 
    
    * On LINUX (Debian based distribution):
    Packages are compatibles with:
        * Debian 7 Wheezy (and older)
        * Ubuntu 12.04 LTS and 14.04 LTS (and older)
    ``` 
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
    echo "deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.2 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
    sudo apt-get update
    sudo apt-get install -y mongodb-org=3.2.1 mongodb-org-server=3.2.1 mongodb-org-shell=3.2.1 mongodb-org-mongos=3.2.1 mongodb-org-tools=3.2.1
    ``` 
    * On MAC OS/X: 
    (from LionX to newest)
    ``` 
    brew update
    brew install mongodb --with-openssl
    ```
    * On Windows:
        refer to [official MongoDB installation procedure] [https://docs.mongodb.org/manual/tutorial/install-mongodb-on-windows/]

Now check if mongodb is working in commandline

```
$ mongo
MongoDB shell version: 3.2.0
connecting to: test
>
```
Type Ctrl+C to quit
    
    
### Activate a virtualenv
Verify you have virtualenv installed
```
$ virtualenv --version
```
If you got a “Command not found” when you tried to use virtualenv, try:
```
$ sudo pip install virtualenv
```
or
``` 
sudo apt-get install python-virtualenv # for a Debian-based system
```
```
$ virtualenv cortext-box
$ cd cortext-box
$ source bin/activate
```
## Install LXML

lxml distribution for python requires a few aditionnal packages
* On Debian
```
sudo apt-get install libxml2-dev libxslt-dev python-dev
```
* On MAC

```
brew install libxml2
brew install libxslt
brew link libxml2 --force
brew link libxslt --force
```
* On windows

Select the source file that corresponds to you architecture (32 or 64 bits)
open an run it
[lxml ditributions | http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml]

# Clone the repository
```
$ git clone https://github.com/cortext/crawtext
```

# Enter into crawtext directory

``` 
$ cd crawtext
``` 
# Install additionnal packages

``` 
$ pip install -r requirements.pip

``` 

Full crawtext is now correctly installed
See configuration file to setup environnement and create a project


### Configuration

#### Default environnement
Crawtext provides a default running environnement with:
- a task database for scheduler that list every crawtext projet ever run will be created
- a default environnement for crawtext
- a user directory with one directory per project in wich results crawl are dowloaded
- a default uri for those who want to expose crawl on a website

You can change every aspect of this environnement by changing the settings.json file inside config directory
and make Crawtext Environnement fit with your requirements

Configuration of settings throught json file into `config/settings.json`

### Creating a crawl project
Crawtext provides a default project as a demo into config/example.json



### Activating scheduler

Not Implemented Yet

