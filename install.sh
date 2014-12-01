#!/bin/bash
if [[ ! -z $VIRTUAL_ENV ]]; then
  if [[ -r /usr/local/bin/virtualenvwrapper.sh ]]; then
    source /usr/local/bin/virtualenvwrapper.sh
  fi
  deactivate
fi

BASEDIR=($pwd)
pip install virtualenv virtualenvwrapper
virtualenv -q $BASEDIR/virtual_crawtext --no-site-packages virtual_crawtext --no-site-packages
. my_virtual_env/bin/activate
# export VIRTUAL_ENV="/home/mike/var/virtualenvs/myvirtualenv"
# export PATH="$VIRTUAL_ENV/bin:$PATH"
# unset PYTHON_HOME

# 

# if [ ! -d "$BASEDIR/virtual_crawtext" ]; then
#     virtualenv -q $BASEDIR/virtual_crawtext --no-site-packages
#     echo "Virtualenv created."
# fi

# if [ ! -f "$BASEDIR/virtual_crawtext/updated" -o $BASEDIR/requirements.pip -nt $BASEDIR/virtual_crawtext/updated ]; then
#     pip install -r $BASEDIR/requirements.pip 
#     touch $BASEDIR/virtual_crawtext/updated
#     echo "Requirements installed."
# fi

