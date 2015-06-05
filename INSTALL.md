## Installation


###How to make crawtext work on my computer?
====


First, build the environnement for CRAWTEXT

```

	$user@computer:~/crawtext docker build -t crawtext ./install

```	
Then activate the mongo daemon in background

```
	
	sudo docker run  --name mongo-srv -v /home/c24b/projets/docker/data:/data/db -P -d mongo:latest
```
	
###How to create a crawl projet?
====
Two methods are allowed to setup a crawl:

* commandline (shell)
* YAML file + config.py

###How to run the crawl projet?
====
* To run it you can activate the daemon module of crawtext in background
stored in scheduler.py in a cronjob every day at 00h00


```
		0 0 * * * python crawtext/scheduler.py
```
	
* Or activate your project using cmdline: 

```
		python scripts/crawtext.py my-project start
```

