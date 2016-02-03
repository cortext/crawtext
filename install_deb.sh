#!/bin/bash
echo "============================"
echo "* Installing Crawtext V5   *"
echo "============================"
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "**********************"
echo "Installing required Debian Packages"
#~ sudo apt-get install libffi-dev libssl-dev git libxml2-dev libxslt1-dev python-dev zlib1g-dev 
#~ sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10
#~ echo "deb http://repo.mongodb.org/apt/debian wheezy/mongodb-org/3.2 main" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
#~ sudo apt-get update
#~ sudo apt-get install -y mongodb-org=3.2 mongodb-org-server=3.2 mongodb-org-shell=3.2 mongodb-org-mongos=3.2 mongodb-org-tools=3.2
#~ sudo mkdir -p /data/db
echo "**********************"
echo "Creating a virtual env"
#Create a new virtualenv in the current directory
virtualenv $PWD --no-site-packages -p /usr/bin/python2.7

# First, locate the root of the current virtualenv
while [ "$PWD" != "/" ]; do
    # Stop here if this the root of a virtualenv
    if [ \
        -x bin/python \
        -a -e lib/python*/site.py \
        -a -e include/python*/Python.h ]
    then
        break
    fi
    cd ..
done
if [ "$PWD" = "/" ]; then
    echo "Could not activate: no virtual environment found." >&2
    exit 1
fi

# Then Activate
export VIRTUAL_ENV="$PWD"
export PATH="$VIRTUAL_ENV/bin:$PATH"
#Downloading from pip all the required packages
#pip install -r "$VIRTUAL_ENV/requirements.pip"

#virtualenv -p /usr/bin/python2.7 --no-site-packages ../crawtext_box


#~ source ../crawtext_box/bin/activate
#pip install -r requirements.txt

#alias = "source ../crawtext_box/bin/activate"



echo "Installing python dependencies"
#~ git clone https://github.com/cortext/crawtext crawtext
#~ git checkout dev

pip install -r requirements.pip
pip install requests[security]
unset PYTHON_HOME
exec "${@:-$SHELL}"

echo "**********************"
echo "Install of crawtext is completed!"
echo "Have fun!"
cd crawtext
exit 0

#~ virtualenv -p /usr/bin/python2.7 crawtext
#~ source crawtext/bin/activate
#~ pip install -r requirements.txt
