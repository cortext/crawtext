#!/bin/bash

sudo docker stop mongo-srv
sudo docker rm mongo-srv
sudo docker run  --name mongo-srv -v /home/c24b/projets/docker/data:/data/db -P -d mongo:latest
sudo docker ps 
