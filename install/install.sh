#!/bin/bash
echo "============================"
echo "* Installing Crawtext V5   *"
echo "============================"

echo "**********************"
echo "Installing required Debian Packages"

sudo apt-get install git libxml2-dev libxslt1-dev python-dev zlib1g-dev 
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo "deb http://repo.mongodb.org/apt/ubuntu "$(lsb_release -sc)"/mongodb-org/3.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org=3.0.5 mongodb-org-server=3.0.5 mongodb-org-shell=3.0.5 mongodb-org-mongos=3.0.5 mongodb-org-tools=3.0.5
echo "**********************"
echo "Installing python dependencies"
#~ git clone https://github.com/cortext/crawtext crawtext
#~ git checkout V5
cd crawtext/install
sudo pip install -r ./requirements.pip
cd ../
echo "**********************"
echo "Install of crawtext is completed!\n Have fun!"
exit 0
