#import pytest

import py.test
from ..config import config
class TestConfig:    
    def test_wrongf(self):
        '''testing the config implementation'''
        from config import config
        #self.newf ="./file.test"
        new_conf = config("afile.json")
        assert type(new_conf) is dict
    
    def test_yaml(self):
        from config import config
        #self.newf ="./file.test"
        new_conf = config("config.yaml")
        print(new_conf)

    def test_json(self):
        
        #self.newf ="./file.test"
        new_conf = config("config.json")
        assert new_conf["name"] == "test_app_crawl"
    def test_load(self):
        #self.newf ="./file.test"
        new_conf = config("config.json")
        print(new_conf)
        c= Crawtext()
        assert c.name == new_conf["name"]
        

class TestCrawtext:
    def test_create(self):
        from crawtext import Crawtext
        pass
    def test_update(self):
        from crawtext import Crawtext
        pass
    def test_article(self):
        from article import Page
        pass
        
from ..article import Page

p = Page({"url": self.url, "source_url": "url", "depth": 0}, self.task)
p.process(False)

