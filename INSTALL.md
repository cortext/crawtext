= INSTALL INSTRUCTIONS =

== Installing CrawText V5 ==

=== OSX and Debian Distribution ===

==== Previous recommandations ====
1. Activate your new virtual env (no mandatory)
2. Make sure you have git installed
``` apt-get install git ```

==== Install V5 =====
1. Clone the repo
``` git clone https://github.com/cortext/crawtext ```

2. Moove into crawtext directory
``` cd crawtext  ```

2. switch to V5 branch

``` git checkout V5 ```

3. Run the installer for your OS:

* debian-based distrib
``` chmod+x  deb-install.sh```
``` ./deb-install.sh```

* MAC OS-X distrib
``` chmod+x  mac-install.sh```
``` ./mac-install.sh```

=== Windows distribution ===
==== Previous recommandations =====
As Crawtext is not compatible with DOS version
you will have to install a Virtual Machine  and Docker

1. Install a VM
Install VirtualBox VM following the step on [https://www.virtualbox.org/]


2.Install Docker

Your machine must be running Windows 7.1, 8/8.1 or newer to run Docker. Windows 10 is not currently supported
Follow the step on [https://docs.docker.com/installation/windows/]

=====Install V5 =====

1. Create the environnement for CrawText
```docker build -t crawtext ./install```

2. Activate the mongoengine in background

```sudo docker run  --name mongo-srv -v /home/c24b/projets/docker/data:/data/db -P -d mongo:latest```


=== Run a crawl ===

For the moment you only have two options
* Create a small python script into the crawtext dir
    nano new_project.py
    ```
    from crawtext import Crawtext
    params = {"url":"","query":"(mottanai) OR (motanai)", "lang": "fr", "repeat": True, "max_depth":2}
    c = Crawtext("mottanai")
    c.start(params)
    ```
* Use a YAML file and config.py
    YAML file + config.py

