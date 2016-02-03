#!/bin/bash
echo "============================"
echo "* Installing Crawtext V5   *"
echo "============================"

echo "**********************"
echo "Installing required OSX Packages"
echo "LXML"
xcode-select --install
sudo port install py27-lxml
brew unlink libxml2
brew unlink libxslt
brew install libxml2
brew install libxslt
brew link libxml2 --force
brew link libxslt --force


#sudo apt-get install git libxml2-dev libxslt1-dev python-dev zlib1g-dev 
brew update
brew install mongodb
mkdir -p /data/db
echo "**********************"
"Creating a virtual env"
virtualenv -p /usr/bin/python2.7 crawtext_env
source crawtext/bin/activate
#pip install -r requirements.txt
echo "Installing python dependencies"
#~ git clone https://github.com/cortext/crawtext crawtext
#git checkout dev
cd install/
sudo pip install -r requirements.pip
cd ../
echo "**********************"
echo "Install of crawtext is completed! Have fun!"
exit 0
