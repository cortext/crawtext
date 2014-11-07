# -*- coding: utf-8 -*-
"""
Article objects abstract an online news article page.
"""

import copy
import os
import glob
import datetime
import nlp
from configuration import Configuration
from extractors import ContentExtractor
from utils import URLHelper, encodeValue, RawHelper, extend_config
from cleaners import DocumentCleaner
from outputformatters import OutputFormatter

class Article(object):
    """
    Main extractor for one article
    """
    def __init__(self, url, html, depth=0, title=u'', source_url=u'', config=None, **kwargs):
        """
        The **kwargs arguement can be filled with config values which we then
        push in.
        """
        self.url = url
        self.html = html
        self.date = datetime.datetime.now()
        self.config = config or Configuration()
        self.config = extend_config(self.config, kwargs)
        self.depth = depth
        try:
            self.parser = Parser()
        except Exception as e:
            print e
        self.extractor = ContentExtractor(config=self.config)
        
        self.title = encodeValue(title)
        

        # the url of the "best image" to represent this article, via reddit algorithm
        self.top_img = self.top_image = u''

        # stores image provided by metadata
        self.meta_img = u''

        self.imgs = self.images = [] # all image urls
        self.movies = [] # youtube, vimeo, etc

        # pure text from the article
        self.text = u''

        # keywords extracted via nlp() from the body text
        # meta_keywords are via parse() from <meta> tags
        # tags are related terms via parse() in the <meta> tags
        self.keywords = []
        self.meta_keywords = []
        self.tags = set()

        # list of authors who have published the article, via parse()
        self.authors = []

        self.published_date = u'' # TODO

        # summary generated from the article's body txt
        self.summary = u''

        # the article's unchanged and raw html
        self.html = u''

        # The html of the main article node
        self.article_html = u''

        # flags warning users in-case they forget to download() or parse()
        self.is_parsed = False
        self.is_downloaded = False

        # meta description field in HTML source
        self.meta_description = u""

        # meta lang field in HTML source
        self.meta_lang = u""

        # meta favicon field in HTML source
        self.meta_favicon = u""

        # Meta tags contain a lot of structured data like OpenGraph
        self.meta_data = {}

        # The canonical link of this article if found in the meta data
        self.canonical_link = u""

        # Holds the top Element we think is a candidate for the main body
        self.top_node = None

        # Holds clean version of top Element
        self.clean_top_node = None

        # the lxml doc object
        self.doc = None

        # a pure object from the orig html without any cleaning options done on it
        self.clean_doc = None

        # A property bucket for consumers of goose to store custom data extractions.
        self.additional_data = {}
        self.links = []
        self.outlinks = []
        self.inlinks = []

    

        
    
            
    
    def build(self):
        """
        Build a lone article from a url independent of the
        source (newspaper). We won't normally call this method b/c
        we want to multithread articles on a source (newspaper) level.
        """
        # try:
        #     self.download()
        # except LinkException:
        #     raise LinkException(self.url, log)
            
        if self.parse():
            print self.title
            return True
        else:
            return False

    
    def parse(self):
        """
        """
        # if self.html is None:
        #     self.msg = "No html source"
        #     return False

        self.doc = self.parser.fromstring(self.html)
        self.clean_doc = copy.deepcopy(self.doc)

        # TODO: Fix this, sync in our fix_url() method
        parse_candidate = self.get_parse_candidate()
        self.link_hash = parse_candidate.link_hash # MD5
        '''
        document_cleaner = self.get_document_cleaner()
        output_formatter = self.get_output_formatter()
        
        if self.doc is None:
           self.msg = "Article parsing error"
           self.code = 600
           return False
        
        title = self.extractor.get_title(self.doc)
        
        self.set_title(title)

        authors = self.extractor.get_authors(self.doc)
        self.set_authors(authors)

        meta_lang = self.extractor.get_meta_lang(self.doc)
        self.set_meta_language(meta_lang)

        meta_favicon = self.extractor.get_favicon(self.doc)
        self.set_meta_favicon(meta_favicon)

        meta_description = self.extractor.get_meta_description(self.doc)
        self.set_meta_description(meta_description)

        canonical_link = self.extractor.get_canonical_link(self.url, self.doc)
        self.set_canonical_link(canonical_link)

        tags = self.extractor.extract_tags(self.doc)
        self.set_tags(tags)

        meta_keywords = self.extractor.get_meta_keywords(self.doc)
        self.set_meta_keywords(meta_keywords)

        meta_data = self.extractor.get_meta_data(self.doc)
        self.set_meta_data(meta_data)

        # TODO self.publish_date = self.config.publishDateExtractor.extract(self.doc)
        links = self.extractor.get_urls(self.doc)
        self.set_links(links)
        self.set_outlinks(links)
        self.set_inlinks(links)
        # before we do any computations on the body itself, we must clean up the document
        self.doc = document_cleaner.clean(self.doc)

        text = u''
        self.top_node = self.extractor.calculate_best_node(self.doc)
        if self.top_node is not None:
            #video_extractor = self.get_video_extractor(self.doc)
            #self.set_movies(video_extractor.get_videos())

            self.top_node = self.extractor.post_cleanup(self.top_node)
            self.clean_top_node = copy.deepcopy(self.top_node)
            # try:
            text, article_html = output_formatter.get_formatted(self.top_node)
            self.set_article_html(article_html)
            self.set_text(text)
            self.set_outlinks(self.links)
            self.set_inlinks(self.links)
                
            
        else:
            print self.title

            # print "TOP node is None"
            # self.code= 700
            # self.msg =  "LXML extraction Error"
        '''    
        
        self.release_resources()

    def fetch_images(self):
        if self.clean_doc is not None:
            meta_img_url = self.extractor.get_meta_img_url(self)
            self.set_meta_img(meta_img_url)

            imgs = self.extractor.get_img_urls(self)
            self.set_imgs(imgs)

        if self.clean_top_node is not None and not self.has_top_image():
            first_img = self.extractor.get_first_img_url(self)
            self.set_top_img(first_img)

        if not self.has_top_image():
            self.set_reddit_top_img()

    def has_top_image(self):
        return self.top_img is not None and self.top_img != u''

    def is_valid_url(self):
        """
        Performs a check on the url of this link to
        determine if a real news article or not.
        """
        return valid_url(self.url)

    def is_valid_body(self):
        """
        If the article's body text is long enough to meet
        standard article requirements, we keep the article.
        """
        if not self.is_parsed:
            raise ArticleException('must parse article before checking \
                                    if it\'s body is valid!')
        meta_type = self.extractor.get_meta_type(self)
        wordcount = self.text.split(' ')
        sentcount = self.text.split('.')

        if meta_type == 'article' and wordcount > (self.config.MIN_WORD_COUNT - 50):
            log.debug('%s verified for article and wc' % self.url)
            return True

        if not self.is_media_news() and not self.text:
            log.debug('%s caught for no media no text' % self.url)
            return False

        if self.title is None or len(self.title.split(' ')) < 2:
            log.debug('%s caught for bad title' % self.url)
            return False

        if len(wordcount) < self.config.MIN_WORD_COUNT:
            log.debug('%s caught for word cnt' % self.url)
            return False

        if len(sentcount) < self.config.MIN_SENT_COUNT:
            log.debug('%s caught for sent cnt' % self.url)
            return False

        if self.html is None or self.html == u'':
            log.debug('%s caught for no html' % self.url)
            return False

        log.debug('%s verified for default true' % self.url)
        return True

    def is_media_news(self):
        """
        If the article is a gallery, video, etc related.
        """
        safe_urls = ['/video', '/slide', '/gallery', '/powerpoint',
                     '/fashion', '/glamour', '/cloth']
        for s in safe_urls:
            if s in self.url:
                return True
        return False

    def nlp(self):
        """
        Keyword extraction wrapper.
        """

        text_keyws = nlp.keywords(self.text).keys()
        title_keyws = nlp.keywords(self.title).keys()
        keyws = list(set(title_keyws + text_keyws))
        self.set_keywords(keyws)

        summary_sents = nlp.summarize(title=self.title, text=self.text)
        summary = '\r\n'.join(summary_sents)
        self.set_summary(summary)

    def get_parse_candidate(self):
        """
        A parse candidate is a wrapper object holding a link hash of this
        article and a final_url.
        """
        # TODO: Should we actually compute a hash using the html? It is more inconvenient if we do that
        if self.html:
            return RawHelper.get_parsing_candidate(self.url, self.html)
        return URLHelper.get_parsing_candidate(self.url)

    def get_video_extractor(self, article):
        return VideoExtractor(article, self.config)

    def get_output_formatter(self):
        return OutputFormatter(self.config)

    def get_document_cleaner(self):
        return DocumentCleaner(self.config)

    def get_extractor(self):
        return ContentExtractor(self.config)

    def build_resource_path(self):
        """
        Must be called after we compute html/final url.
        """
        res_path = self.get_resource_path()
        if not os.path.exists(res_path):
            os.mkdir(res_path)

    def get_resource_path(self):
        """
        Every article object has a special directory to store data in from
        initialization to garbage collection.
        """
        res_dir_fn = 'article_resources'
        resource_directory = os.path.join(self.config.PROJECT_DIR, res_dir_fn)
        if not os.path.exists(resource_directory):
            os.mkdir(resource_directory)
        dir_path = os.path.join(resource_directory, '%s_' % self.link_hash)
        return dir_path

    def release_resources(self):
        """
        TODO: Actually implement this properly.
        """
        path = self.get_resource_path()
        for fname in glob.glob(path):
            try:
                os.remove(fname)
            except OSError:
                pass
        # os.remove(path)

    def set_reddit_top_img(self, test_run=False):
        """
        Wrapper for setting images, queries known image attributes
        first, uses Reddit's img algorithm as a fallback.
        """

        #todo: move tests from here
        if test_run:
            s = images.Scraper(self)
            img = s.largest_image_url()
            print 'it worked, the img is', img

        try:
            s = images.Scraper(self)
            self.set_top_img_no_ckeck(s.largest_image_url())
        except Exception, e:
            log.critical('jpeg error with PIL, %s' % e)

    def set_title(self, title):
        """
        The prechecked_title boolean is important for cases where our
        educated guess of an article's title works and is actually
        better than the actual title being extracted.
        """
        prechecked_title = (self.title and not title)
        if prechecked_title:
            return
        title = title[:self.config.MAX_TITLE]
        title = encodeValue(title)
        if title:
            self.title = title

    def set_text(self, text):
        """
        """
        text = text[:self.config.MAX_TEXT-5]
        text = encodeValue(text)
        if text:
            self.text = text

    def set_html(self, html):
        """
        This method is quite important because many other objects
        besides this one will be modifying and setting the html.
        """
        self.is_downloaded = True
        if html:
           self.html = encodeValue(html)

    def set_article_html(self, article_html):
        """
        Sets the html of just our article body, the "top node".
        """
        if article_html:
            self.article_html = encodeValue(article_html)

    def set_meta_img(self, src_url):
        self.meta_img = encodeValue(src_url)
        self.set_top_img(src_url)

    def set_top_img(self, src_url):
        if src_url is not None:
            s = images.Scraper(self)
            if s.satisfies_requirements(src_url):
                self.set_top_img_no_ckeck(src_url)

    def set_top_img_no_ckeck(self, src_url):
        """
        We want to provide 2 api's for images. One at
        "top_img", "imgs" and one at "top_image", "images".
        """
        src_url = encodeValue(src_url)
        self.top_img = src_url
        self.top_image = src_url

    def set_imgs(self, imgs):
        """
        The motive for this method is the same as above, we want
        to provide apis for both "imgs" and "images".
        """
        imgs = [encodeValue(i) for i in imgs]
        self.images = imgs
        self.imgs = imgs

    def set_keywords(self, keywords):
        """
        Keys are stored in list format.
        """
        if not isinstance(keywords, list):
            raise Exception("Keyword input must be list!")
        if keywords:
            self.keywords = [encodeValue(k) for k in keywords[:self.config.MAX_KEYWORDS]]

    def set_authors(self, authors):
        """
        Authors are in ["firstName lastName", "firstName lastName"] format.
        """
        if not isinstance(authors, list):
            raise Exception("authors input must be list!")
        if authors:
            authors = authors[:self.config.MAX_AUTHORS]
            self.authors = [encodeValue(author) for author in authors]

    def set_summary(self, summary):
        """
        Summary is a paragraph of text from the title + body text.
        """
        summary = summary[:self.config.MAX_SUMMARY]
        self.summary = encodeValue(summary)

    def set_meta_language(self, meta_lang):
        """
        We are saving langauges in 2 char form, english = 'en'.
        """
        if meta_lang and len(meta_lang) >= 2:
            self.meta_lang = meta_lang[:2]

    def set_meta_keywords(self, meta_keywords):
        """
        Store the keys in list form.
        """
        self.meta_keywords = [k.strip() for k in meta_keywords.split(',')]

    def set_meta_favicon(self, meta_favicon):
        """
        """
        self.meta_favicon = meta_favicon

    def set_meta_description(self, meta_description):
        """
        """
        self.meta_description = meta_description

    def set_meta_data(self, meta_data):
        self.meta_data = meta_data

    def set_canonical_link(self, canonical_link):
        """
        """
        self.canonical_link = canonical_link

    def set_tags(self, tags):
        """
        """
        self.tags = tags

    def set_movies(self, movie_objects):
        """
        Trim goose's movie objects into just urls for us.
        """
        movie_urls = [o.src for o in movie_objects if o and o.src]
        self.movies = movie_urls
    
    def set_links(self, links):
        self.links = set(links)
        
    def set_outlinks(self, links):
        outlinks = []
        for url in links:
            link = Link(url)
            if link.is_valid():
                outlinks.append(link.url)
            #not stored
            #outlink["status"], outlink["code"], outlink["msg"], outlink["url"] = check_url(url)
            #if outlink["status"] is True:    
            #    outlinks.append(outlink["url"])
        self.outlinks = list(set(outlinks))

    def set_inlinks(self, links):
        inlinks = []
        for url in links:
            link = Link(url)
            if link.relative is True:
                if link.is_valid():
                    inlinks.append(link.url)
        self.inlinks = list(set(inlinks))

        #self.inlinks_err = [n for n in self.inlinks_err if n["url"] not in inlinks_err]

    def is_relevant(self, query):
        indexed = {"title":unicode(self.title), "content": unicode(self.text)}
        if query.match(indexed) is False:
            log = {"code": 800, "msg": "Not Relevant","status": False, "title": self.title, "content": self.text}
            raise ArticleException(self.url, log)
        return True

    def json(self):
        result = {}
        values = ['title', 'text', 'authors', 'keywords','tags', 'date', 'depth','outlinks', 'inlinks', 'source_url']
        for k,v in self.__dict__.items():
            if k in values and v is not None:
                if type(v) == set:
                    v = list(v)
                result[k] = v
        return result
    
    def json_simple(self):
        values = ['title', 'date', 'depth','outlinks', 'inlinks', 'source_url']
        for k,v in self.__dict__.items():
            if k in values and v is not None:
                if type(v) == set:
                    v = list(v)
                result[k] = v
        return result