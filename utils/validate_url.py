#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

def validate_url(url):
	regex = re.compile("^((http)://|(www)\.)[a-z0-9-]+(\.[a-z0-9-]+)+([/?].*)?$", re.I)
	valid_url = re.match(regex, url)
	if valid_url:
		return True
	else:
		#print 'Enter a valid URL.'
		return False