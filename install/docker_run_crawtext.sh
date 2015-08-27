#!/bin/bash

#add -v
sudo docker run -it --link mongo-srv:mongo-srv  crawtext

#add -v pour les volumes des report
#sudo docker run -d --link mongo-srv:mongo-srv  -v /home/c24b/projets/crawtext/projects:/scripts/projects crawtext python /scripts/scheduler.py
#Revenir sur le scheduler
