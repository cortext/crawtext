import lxml
from lxml import etree
from lxml.html.clean import autolink_html
from lxml.html.clean import Cleaner
from readability.readability import Document
from bs4 import BeautifulSoup as bs
from bs4 import Comment
import logging
logging.getLogger("readability").setLevel(logging.WARNING)
import re

notalpha = re.compile('[^a-zA-Z]')
spaces = re.compile("\r\r|\t\t|\s\s|\n\n")
POSITIVE_K = ["entry-content","post","main","content","container","blog","article*","post","entry", "row",]
NEGATIVE_K = ["like*","ad*","comment.*","comments","comment-body","about","access","navbar", 
                "navigation","login", "sidebar.*?","share.*?","relat.*?","widget.*?","menu", "side-nav"]


def lxml_extractor(html, url):
    '''LXML PARSER'''
    cleaner = Cleaner()
    cleaner.javascript = True # This is True because we want to activate the javascript filter
    cleaner.style = True      # This is True because we want to activate the styles & stylesheet filter
    cleaner.comments = True
    cleaner.embedded = True
    cleaner.forms= True
    cleaner.frames = True
    cleaner.annoying_tags = True
    cleaner.kill_tags = NEGATIVE_K 
    cleaner.allow_tag = POSITIVE_K
    cleaner.safe_attrs_only = True
    #~ oc = document_fromstring(html, parser=parser, base_url=base_url, **kw)
  #~ File "/usr/local/lib/python2.7/dist-packages/lxml/html/__init__.py", line 752, in document_fromstring
    #~ value = etree.fromstring(html, parser, **kw)
    try:
        html = lxml.html.fromstring(html, base_url="url")
    
        tree = cleaner.clean_html(html)
        #tree.make_links_absolute(url)
        doc = lxml.html.tostring(tree)
        doc = soup_extractor(doc, url)
    except ValueError:
        doc = soup_extractor(html, url)
    
    #~ (title, doc, article, text) = read_extractor(html, url)
    #~ print title
    #~ doc = (self.doc).replace(unichr(160), " ")
    #~ doc = re.sub(spaces,"",self.doc)
    return doc
    
def read_extractor(html, url):
    from readability import Document
    '''readability extractor'''
    try:
        clean_doc = Document(html,url = url, positive_keywords=",".join(POSITIVE_K) , negative_keywords=",".join(NEGATIVE_K))
    
        #summary = clean_doc.summary()
    
        article = clean_doc.article
        text = re.sub("  |\t", " ",bs(article, "lxml").get_text())
        title = clean_doc.short_title()
    
        return (title, clean_doc, text)
    except Exception as e:
        return False

def soup_extractor(html, url):
    ''' beautifulsoup extractor'''
    soup = bs(html, "lxml")
    #print soup
    [s.extract() for s in soup('script')]
    [s.extract() for s in soup('noscript')]
    [s.extract() for s in soup('iframe')]
    [s.extract() for s in soup('form')]
    [s.extract() for s in soup('embed')]
    [s.extract() for s in soup('style')]
    [s.extract() for s in soup('footer')]
    #~ for k in NEGATIVE_K:
        #~ [s.extract() for s in soup(str(k))]
    soup = bs(re.sub(re.compile("<!--(.*)-->"), "", str(soup)), "lxml")
    doc = soup.text
    doc = re.sub(spaces," ",doc)
    #print doc

    #titre, text, links =  (soup.h1.text, soup.text, get_absolute_links(soup, url))
    #return (titre, text, links)
    return doc


