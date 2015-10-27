import lxml
from lxml import etree
from lxml.html.clean import autolink_html
from lxml.html.clean import Cleaner

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
notalpha = re.compile('[^a-zA-Z]')

#BS PARSER
from bs4 import BeautifulSoup as bs
from bs4 import Comment

def make_links_absolute(soup, url):
    return [urlparse.urljoin(url, tag['href']) for tag in soup.findAll('a', href=True)]
                        
def clean_html(soup):
    soup = bs(" ".join([s.extract() for s in soup('script')]))
    soup = bs(" ".join([s.extract() for s in soup('iframe')]))
    soup = bs(" ".join([s.extract() for s in soup('form')]))
    soup = bs(" ".join([s.extract() for s in soup('embed')]))
    soup = bs(" ".join([s.extract() for s in soup('style')]))
    soup = bs(re.sub(re.compile("<!--(.*)-->"), "", str(soup)))
    return soup
