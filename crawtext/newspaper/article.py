#!/usr/bin/env python
# -*- coding: utf-8 -*-

__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import copy
import os
import glob
import re
#from . import network
#from . import nlp
from . import settings
from . import urls
from .cleaners import DocumentCleaner
from .configuration import Configuration
from .extractors import ContentExtractor
from .outputformatters import OutputFormatter
from .utils import (URLHelper, encodeValue, RawHelper, extend_config,
                    get_available_languages)
#from .videos.extractors import VideoExtractor
from bs4 import BeautifulSoup
import requests
from link import Link
from urls import prepare_url

class ArticleException(Exception):
    pass


class Article(object):
    """Article objects abstract an online news article page
    """
    def __init__(self, url, depth="", source_url=u''):
        """The **kwargs argument may be filled with config values, which
        is added into the config object
        """
        self.depth = depth
        self.config = Configuration()
        
        self.extractor = ContentExtractor(self.config)

        if source_url == u'':
            source_url = urls.get_scheme(url) + '://' + urls.get_domain(url)

        # if source_url is None or source_url == '':
        #     raise ArticleException('input url bad format')

        # URL to the main page of the news source which owns this article
        self.source_url = encodeValue(source_url)

        url = encodeValue(url)
        self.url = urls.prepare_url(url, self.source_url)

        self.title = u''

        # URL of the "best image" to represent this article
        self.top_img = self.top_image = u''

        # stores image provided by metadata
        self.meta_img = u''

        # All image urls in this article
        self.imgs = self.images = []

        # All videos in this article: youtube, vimeo, etc
        self.movies = []

        # Body text from this article
        self.text = u''

        # `keywords` are extracted via nlp() from the body text
        self.keywords = []

        # `meta_keywords` are extracted via parse() from <meta> tags
        self.meta_keywords = []

        # `tags` are also extracted via parse() from <meta> tags
        self.tags = set()

        # List of authors who have published the article, via parse()
        self.authors = []

        # TODO: Date of when this article was published
        self.published_date = u''

        # Summary generated from the article's body txt
        self.summary = u''

        # This article's unchanged and raw HTML
        self.html = u''

        # The HTML of this article's main node (most important part)
        self.article_html = u''

        # Flags warning users in-case they forget to download() or parse()
        # or if they call methods out of order
        self.is_parsed = False
        self.is_downloaded = False

        # Meta description field in the HTML source
        self.meta_description = u""

        # Meta language field in HTML source
        self.meta_lang = u""

        # Meta favicon field in HTML source
        self.meta_favicon = u""

        # Meta tags contain a lot of structured data, e.g. OpenGraph
        self.meta_data = {}

        # The canonical link of this article if found in the meta data
        self.canonical_link = u""

        # Holds the top element of the DOM that we determine is a candidate
        # for the main body of the article
        self.top_node = None

        # A deepcopied clone of the above object before heavy parsing
        # operations, useful for users to query data in the
        # "most important part of the page"
        self.clean_top_node = None

        # lxml DOM object generated from HTML
        self.doc = None

        # A deepcopied clone of the above object before undergoing heavy
        # cleaning operations, serves as an API if users need to query the DOM
        self.clean_doc = None

        # A property dict for users to store custom data.
        self.additional_data = {}
        self.status = True
        if url == None:
            self.status = False
        if url == "":
            self.status = False
        self.links = []

    def fetch(self):
        try:

            # req = requests.get((self.url), headers = headers ,allow_redirects=True, proxies=None, timeout=5)
            req = requests.get(self.url, allow_redirects=True, timeout=5)
            req.raise_for_status()
            try:
                self.html = req.text
                self.msg = "Ok"
                self.code = 200
                self.status = True
                if 'text/html' not in req.headers['content-type']:
                    self.msg ="Control: Content type is not TEXT/HTML"
                    self.code = 404
                    self.status = False
                    return False
            #Error on ressource or on server
                elif req.status_code in range(400,520):
                    self.code = req.status_code
                    self.msg = "Control: Request error on connexion no ressources or not able to reach server"
                    self.status = False
                    return False
                else:
                    return True

            except Exception as e:
                self.msg = "Requests: answer was not understood %s" %e
                self.code = 400
                self.status = False
                return False
        except Exception as e:
            self.msg = "Requests: answer was not understood %s" %e
            self.code = 400
            self.status = False
            return False

    def extract(self):
        try:
            self.doc = self.config.get_parser().fromstring(self.html)
        except Exception:
            self.msg = "Parse Error: Unable to load html"
            self.code = 700
            return False
        
        self.clean_doc = copy.deepcopy(self.doc)
        # TODO: Fix this, sync in our fix_url() method
        parse_candidate = self.get_parse_candidate()
        self.link_hash = parse_candidate.link_hash  # MD5
        try:
            document_cleaner = DocumentCleaner(self.config)
        except Exception:
            self.msg = "Parse Error: Unable to clean doc"
            self.code = 701
            
        try:
            output_formatter = OutputFormatter(self.config)
        except Exception:
            self.msg = "Parse Error: Unable to output article"
            self.code = 702
            
        try:
            title = self.extractor.get_title(self.clean_doc)
            self.set_title(title)
        except Exception:
            self.msg = "Parse Error: Unable to extract title"
            self.code = 703
            soup = BeautifulSoup(self.html)
            title = soup.title.text
            self.set_title(title)
            

        # authors = self.extractor.get_authors(self.clean_doc)
        # self.set_authors(authors)
        try:
            self.meta_lang = self.extractor.get_meta_lang(self.clean_doc)
        except Exception as e:
            self.msg = "Parse Error: Unable to get meta lang "+str(e)
            self.code = 704
               
        if self.config.use_meta_language:
            try:
                self.extractor.update_language(self.meta_lang)
                output_formatter.update_language(self.meta_lang)
            except Exception:
                pass
        # meta_favicon = self.extractor.get_favicon(self.clean_doc)
        # self.set_meta_favicon(meta_favicon)

        # meta_description = \
        #     self.extractor.get_meta_description(self.clean_doc)
        # self.set_meta_description(meta_description)
        try:
            self.canonical_link = self.extractor.get_canonical_link(
                self.url, self.clean_doc)
        except Exception as e:
            self.canonical_link = self.url
            self.msg = "Parse Error: Unable to get canonical link %s" %str(e)
            self.code = 705
            
        self.tags = self.extractor.extract_tags(self.clean_doc)
        
        # meta_keywords = self.extractor.get_meta_keywords(
        #     self.clean_doc)
        # self.set_meta_keywords(meta_keywords)

        self.meta_data = self.extractor.get_meta_data(self.clean_doc)
        
        # TODO self.publish_date = ...

        # Before any computations on the body, clean DOM object
        try:
            self.doc = document_cleaner.clean(self.doc)
        except Exception as e:
            self.msg = "Parse Error: Unable to get document %s" %str(e)
            self.code = 708
            self.status = False
            return False

        text = u''

        try:
            
            self.top_node = self.extractor.calculate_best_node(self.doc)
            
            if self.top_node is not None:
                # video_extractor = VideoExtractor(self.config, self.top_node)
                # self.set_movies(video_extractor.get_videos())

                self.top_node = self.extractor.post_cleanup(self.top_node)
                self.clean_top_node = copy.deepcopy(self.top_node)

                text, article_html = output_formatter.get_formatted(
                    self.top_node)
                self.set_article_html(article_html)
                self.set_text(text)
                self.fetch_links()
                self.status = True
                self.release_resources()
                return True
            else:     
                try:
                    soup = BeautifulSoup(self.html)
                    self.text = soup.text
                    self.title = soup.title.text
                    self.links = [n.get('href') for n in soup.findAll("a")]       
                    self.status = True
                    self.msg = "Ok"
                    self.code = 200
                    self.release_resources()
                    return True

                except Exception as e:
                    self.msg = "Parse Error: Unable to extract with BeautifulSoup %s" %str(e)
                    self.code = 710
                    self.status = False
                    self.release_resources()
                    return False

        except Exception as e:
            print e
            soup = BeautifulSoup(self.html)
            self.text = soup.text
            self.title = soup.title.text
            self.links = [n.get('href') for n in soup.findAll("a")]       
            self.status = True
            self.msg = "Ok"
            self.code = 200
            self.release_resources()
            return True

    def parse(self, query):

        if self.is_relevant(query):
            self.outlinks = self.clean_outlinks()
            self.links = [n["url"] for n in self.outlinks ]
            
            #self.links = self.clean_outlinks()
            return True
        else:
            self.code = 800
            self.msg = "Article Query: not relevant"
            self.status = False
            return False
                
    def export(self):
        return {
                "url": self.url,
                "title": self.title,
                "links": self.links,
                # "html": article.html
                # "text": article.text
                }
    
    
    def log(self, debug = False):
        print self.status, self.msg, self.code 
        return {"url":self.url, "status": self.status, "msg": self.msg, "code": self.code}    
    
    def fetch_links(self):
        if self.links == []:
            self.links = self.extractor.get_urls(self.doc)
        return self.links

    def clean_outlinks(self):
        self.fetch_links()
        self.outlinks = []
        for n in set(self.links):
            if n is not None:
                if not n.startswith("#") and n !="/" and n != self.url and n not in ["javascript"]:
                    url = prepare_url(n, self.url)
                    self.outlinks.append({"url":url, "depth":self.depth+1, "source_url": self.url})
            # if n != None and n != "" and  n != "/" and n != self.source_url and n != self.url and n not in links:
            #     l = Link(n, origin="crawl", depth = self.depth+1, source_url= self.source_url)
            #     if l.status is True:
            #         print l.url
            #         # self.outlinks.append({"url":l.url, "depth":l.depth, "source_url": self.source_url})
            #         # self.links.append(l.clean_url)
        return self.outlinks
        # return self.links
    
    def is_valid_url(self):
        """Performs a check on the url of this link to determine if article
        is a real news article or not
        """
        return urls.valid_url(self.url)

    def is_valid_body(self):
        """If the article's body text is long enough to meet
        standard article requirements, keep the article
        """
        if not self.is_parsed:
            raise ArticleException('must parse article before checking \
                                    if it\'s body is valid!')
        meta_type = self.extractor.get_meta_type(self.clean_doc)
        wordcount = self.text.split(' ')
        sentcount = self.text.split('.')

        if meta_type == 'article' and wordcount > (self.config.MIN_WORD_COUNT):
            # #log.debug('%s verified for article and wc' % self.url)
            return True

        if not self.is_media_news() and not self.text:
            #log.debug('%s caught for no media no text' % self.url)
            return False

        if self.title is None or len(self.title.split(' ')) < 2:
            #log.debug('%s caught for bad title' % self.url)
            return False

        if len(wordcount) < self.config.MIN_WORD_COUNT:
            #log.debug('%s caught for word cnt' % self.url)
            return False

        if len(sentcount) < self.config.MIN_SENT_COUNT:
            #log.debug('%s caught for sent cnt' % self.url)
            return False

        if self.html is None or self.html == u'':
            #log.debug('%s caught for no html' % self.url)
            return False        
        return True

    def is_media_news(self):
        """If the article is related heavily to media:
        gallery, video, big pictures, etc
        """
        safe_urls = ['/video', '/slide', '/gallery', '/powerpoint',
                     '/fashion', '/glamour', '/cloth']
        for s in safe_urls:
            if s in self.url:
                return True
        return False

    
    def get_parse_candidate(self):
        """A parse candidate is a wrapper object holding a link hash of this
        article and a final_url of the article
        """
        if self.html:
            return RawHelper.get_parsing_candidate(self.url, self.html)
        return URLHelper.get_parsing_candidate(self.url)

    def build_resource_path(self):
        """Must be called after computing HTML/final URL
        """
        res_path = self.get_resource_path()
        if not os.path.exists(res_path):
            os.mkdir(res_path)

    def get_resource_path(self):
        """Every article object has a special directory to store data in from
        initialization to garbage collection
        """
        res_dir_fn = 'article_resources'
        resource_directory = os.path.join(settings.TOP_DIRECTORY, res_dir_fn)
        if not os.path.exists(resource_directory):
            os.mkdir(resource_directory)
        dir_path = os.path.join(resource_directory, '%s_' % self.link_hash)
        return dir_path

    def release_resources(self):
        # TODO: implement in entirety
        path = self.get_resource_path()
        for fname in glob.glob(path):
            try:
                os.remove(fname)
            except OSError:
                pass
        # os.remove(path)

    def set_title(self, title):
        if self.title and not title:
            # Title has already been set by an educated guess and
            # <title> extraction failed
            return
        title = title[:self.config.MAX_TITLE]
        title = encodeValue(title)
        if title:
            self.title = title

    def set_text(self, text):
        text = text[:self.config.MAX_TEXT]
        text = text.lower()
        text = re.sub("\n", "", text)
        text = encodeValue(text)

        if text:
            self.text = text

    def set_html(self, html):
        """Encode HTML before setting it
        """
        self.is_downloaded = True
        if html:
            self.html = encodeValue(html)

    def set_article_html(self, article_html):
        """Sets the HTML of just the article's `top_node`
        """
        if article_html:
            self.article_html = encodeValue(article_html)

    def is_relevant(self,query):
        if query.exact_matching:
            print query.query
            print query.rematch({"content": self.text})
            return
            
        self.relevant = query.match({"title":self.title, "content": self.text})
        return self.relevant
        #return query.match(indexed)
    
    def json(self):
        result = {}
        values = ['title', 'date', 'depth','outlinks', 'inlinks', 'source_url']
        for k,v in self.__dict__.items():
            if k in values and v is not None:
                if type(v) == set:
                    v = list(v)
                result[k] = v
        return result
