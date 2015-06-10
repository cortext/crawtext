#!/bin/bash

#add -v
sudo docker run -it --link mongo-srv:mongo-srv  crawtext
