import lxml
from lxml import etree
from lxml.html.clean import autolink_html
from lxml.html.clean import Cleaner
from urlparse import urlparse
from packages.tldextract import tldextract

#LXML PARSER
cleaner = Cleaner()
cleaner.javascript = True # This is True because we want to activate the javascript filter
cleaner.style = True      # This is True because we want to activate the styles & stylesheet filter
cleaner.comments = True
cleaner.embedded = True
cleaner.forms= True
cleaner.frames = True
#cleaner.safe_attrs_only = True

import re
notalpha = re.compile('[^a-zA-Z]', re.I)
notag = re.compile("<.*?>|</.*?>", re.I)

#BS PARSER
from bs4 import BeautifulSoup as bs
from bs4 import Comment

#~ def make_links_absolute(soup, url):
    #~ return [urlparse.urljoin(url, tag['href']) for tag in soup.findAll('a', href=True)]

import urlparse as url_parse

def make_links_absolute(soup, url):
    links = []
    for tag in soup.findAll('a', href=True):
        try:
            tag['href'] = url_parse.urljoin(url, tag['href'])
            links.append(tag["href"])
        except ValueError:
            continue
            
    return links
def clean_html(soup):
    try:
        soup = bs(" ".join([s.extract() for s in soup('script')]))
        soup = bs(" ".join([s.extract() for s in soup('iframe')]))
        soup = bs(" ".join([s.extract() for s in soup('form')]))
        soup = bs(" ".join([s.extract() for s in soup('embed')]))
        soup = bs(" ".join([s.extract() for s in soup('style')]))
    except TypeError:
        soup = str(soup)
        soup = re.sub(re.compile("<script.*\<\\script>"), "", soup)
        soup = re.sub(re.compile("<iframe.*\<\iframe>"), "", soup)
        soup = re.sub(re.compile("<embed.*\<\\embed>"), "", soup)
        soup = re.sub(re.compile("<form(.*)\<\\form>"), "", soup)
        soup = re.sub(re.compile("<style.*?\<\\style>"), "", soup)
    soup = re.sub(re.compile("<\!--.*?-->"), "", str(soup))
    return bs(soup)

def get_text(soup):
    return re.sub(notag, " ", str(soup))

def get_title(soup):
    try:
        title = soup.title
    except AttributeError:                
        title = soup.find('title')
        if title is None:
            title = soup.find("h1")
            if title is None:
                return ""
    try:
        return title.text
    except AttributeError:
        return ""

