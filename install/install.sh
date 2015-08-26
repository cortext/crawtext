#!/bin/bash
echo "Installing Crawtext V5 on ubuntu"


#Installing MongoDB 3
echo "Installing MONGO DB 3"
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo "deb http://repo.mongodb.org/apt/ubuntu "$(lsb_release -sc)"/mongodb-org/3.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
#pip install -r ./requirements.pip
#sudo apt-get install zip unzip
#wget https://github.com/cortext/crawtext/archive/V5.zip
sudo apt-get install git
echo "Cloning repo"
git clone https://github.com/cortext/crawtext crawtext
git checkout V5
cd crawtext/install
echo "Cloning dependencies"
sudo pip install -r ./requirements.pip
exit 0
