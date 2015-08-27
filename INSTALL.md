INSTALL INSTRUCTIONS
====

Installing CrawText V5 
======
OSX and Debian Distributions
======== 

Previous recommandations 
==========

1. Install Python 2.7

Crawtext is running with "Python 2.7":

Please make sure you have the correct version installed:

``` sudo apt-get install python2.7 ```

2. Create and activate a brand new virtual env (no mandatory)

install virtualenv:

``` pip install --user virtualenv ```

create virtualenv with the correct python version
``` virtualenv -p /usr/bin/python2.7 /home/user/crawtext_env ```

activate
``` source /home/user/crawtext_env ```

You will be using a brand new and clean environnement as show in terminal
```(crawtext_env) user@computer_name:/home/user ```

(Remember: to leave the virtual env)
    ```(crawtext_env) user@computer_name:/home/user deactivate 
        user@computer_name:/home/user
    ```

3. Make sure you have git installed

``` apt-get install git ```

Install V5 
===========
1. Clone the repo
``` git clone https://github.com/cortext/crawtext ```

2. Move into crawtext directory
``` cd crawtext  ```

3. switch to V5 branch

``` git checkout V5 ```

4. Run the installer for your OS:

* debian-based distrib
``` chmod+x  deb-install.sh```
``` ./deb-install.sh```

* MAC OS-X distrib
``` chmod+x  mac-install.sh```
``` ./mac-install.sh```

Windows distribution 
========
Previous recommandations 
============
As Crawtext is not compatible with MS-DOS version
you will have to install a Virtual Machine  and Docker

1. Install a VM
Install VirtualBox VM following the step on [https://www.virtualbox.org/]


2.Install Docker

Your machine must be running Windows 7.1, 8/8.1 or newer to run Docker. Windows 10 is not currently supported
Follow the step on [https://docs.docker.com/installation/windows/]

Install V5 
============

1. Create the environnement for CrawText
```docker build -t crawtext ./install```

2. Activate the mongoengine in background

```sudo docker run  --name mongo-srv -v /home/c24b/projets/docker/data:/data/db -P -d mongo:latest```


Start a crawl 
=====

For the moment you only have two options
* Create a small python script into the current dir
    nano new_project.py
    ```
    from crawtext import Crawtext
    params == {"key":"","query":"(mottanai) OR (motanai)", "lang": "fr", "repeat": True, "max_depth":2}
    c == Crawtext("mottanai")
    c.start(params)
    ```
    you can see also the [example.py] file
    a complete list of options will be soon available
    
* Use a YAML file and config.py
    YAML file + config.py

