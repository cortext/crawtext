#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import logging
logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="crawtext.log", format=FORMAT, level=logging.DEBUG)

MAX_RESULTS = 1000

def get_bing_results(query, key, nb):
	''' Method to extract results from BING API (Limited to 5000 req/month) return a list of url'''
	start = 0
	step = 50
	if nb > MAX_RESULTS:
		logging.warning("Maximum search results is %d results." %MAX_RESULTS)
		nb = MAX_RESULTS

	if nb%50 != 0:
		nb = nb - (nb%50)
	web_results = []
	new = []
	inserted = []
	for i in range(0,nb, 50):
		params = {'$format' : 'json','$skip' : i,'$top': step, 'Query' : '\'%s\'' %query,}
		try:
			r = requests.get('https://api.datamarket.azure.com/Bing/Search/v1/Web',
				params={'$format' : 'json',
					'$skip' : i,
					'$top': step,
					'Query' : '\'%s\'' %query,
					},auth=(key, key)
					)
			# logging.info(r.status_code)
			msg = r.raise_for_status()
			if msg is None:
				web_results.extend([e["Url"] for e in r.json()['d']['results']])
			else:
				return (False, msg)
		except Exception as e:
			return (False, e)
	return (True, web_results)


def uniq(seq):
    checked = []
    for e in seq:
        if e not in checked:
            checked.append(e)
    logging.info("remove duplicate %d" %len(duplicate))
    return checked
