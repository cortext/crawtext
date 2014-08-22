from distutils.util import strtobool
import sys
import re
from validate_email import validate_email

regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'^www'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
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
		print 'Enter a valid URL.'
		return False
		

