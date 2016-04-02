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
### Install LXML

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

### Clone the repository
```
$ git clone https://github.com/cortext/crawtext

$ cd crawtext
``` 
### Install additionnal packages

``` 
$ pip install -r requirements.pip

``` 

Full crawtext is now correctly installed
See configuration file to setup environnement and create a project
