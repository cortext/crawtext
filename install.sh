#!/bin/bash
echo "============================"
echo "* Installing Crawtext V5   *"
echo "============================"

echo "**********************"
echo "Installing required Debian Packages"
sudo apt-get install libffi-dev libssl-dev git libxml2-dev libxslt1-dev python-dev zlib1g-dev 
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
echo "deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.2 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
sudo apt-get update
sudo apt-get install -y mongodb-org=3.2 mongodb-org-server=3.2 mongodb-org-shell=3.0.5 mongodb-org-mongos=3.0.5 mongodb-org-tools=3.2
sudo mkdir -p /data/db
echo "**********************"
creating a "virtual env"
virtualenv -p /usr/bin/python2.7 crawtext
source crawtext/bin/activate
#pip install -r requirements.txt

echo "Installing python dependencies"
#~ git clone https://github.com/cortext/crawtext crawtext
#~ git checkout dev

pip install -r requirements.pip
pip install requests[security]
cd ../
echo "**********************"
echo "Install of crawtext is completed!"
echo "Have fun!"
exit 0

virtualenv -p /usr/bin/python2.7 crawtext
source crawtext/bin/activate
pip install -r requirements.txt
