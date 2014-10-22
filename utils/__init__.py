from goose import *
from text import *
from encoding import *
from url import *

from distutils.util import strtobool
import sys
import re
from validate_email import validate_email

        
def yes_no(question):
    sys.stdout.write('%s [y/n]\n' % question)
    while True:
        try:
            return strtobool(raw_input().lower())
        except ValueError:
            sys.stdout.write('Please respond with \'y\' or \'n\'.\n')
            
def validate_url(url):
	regex = re.compile("^((http)://|(www)\.)[a-z0-9-]+(\.[a-z0-9-]+)+([/?].*)?$", re.I)
	valid_url = re.match(regex, url)
	if valid_url:
		return True
	else:
		#print 'Enter a valid URL.'
		return False
		

def ask_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.
    
    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":"yes",   "y":"yes",  "ye":"yes",
             "no":"no",     "n":"no"}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while 1:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return defaut
        elif choice in valid.keys():
            return strtobool(valid[choice])
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

