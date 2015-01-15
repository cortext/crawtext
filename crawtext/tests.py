from config import Config
from wk import Worker
import re

def test_bing(project_name, key="", query=""):
    key = "J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o"
    w = Worker(project_name)
    if w.exists() is False:
        query = re.sub("2", "", project_name)
        query = re.sub("_", " ", project_name)
        w.create({"--query": query, "--key": key})
    cfg = Config(project_name, 'crawl', debug=False)
    cfg.setup()
    return 

def test_export(project_name, query=""):
    key = "J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o"
    w = Worker(project_name)
    if w.exists() is False:
        query = re.sub("_", " ", project_name)
        w.create({"--query": query, "--key": key})
    w.start({})
    return 

# test_export("chemtraces")
from link import Link

def test_link(url):
    l = Link(url)
    print l.url
from article import Page, Article

def test_page(url):
    p = Page(url)
    p.fetch()
    p.export()
    a = Article(p.url, p.html)
    a.extract()
    for n in a.domains:
        print n
        
from crawl import crawl

def test_crawl(name):
    cfg = Config(name, "crawl")
    cfg.setup()

    print "Now crawl"
    crawl(cfg.project_name, cfg.query, cfg.directory, cfg.max_depth, True)

def test_schedule(name):
    wk = Worker(name)
    wk.schedule("{}")

# test_export("pesticides5", "pesticides and DDT")
test_schedule("chemtraces")

# test_bing("jesuischarlie", key="J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o", query="#jesuischarlie")
# test_crawl("jesuischarlie")
# def test_schedule(name):
    
    # cfg = Config(name, "crawl")
    # cfg.setup()
    # cfg.crawl_setup()
    
    #crawl(cfg.project_name, cfg.query, cfg.directory, cfg.max_depth, True)

#test_link('http://www.psy.be/divers/fr/interviews/francois-damiens.htm')
# test_page('http://www.psy.be/divers/fr/interviews/francois-damiens.htm')
# test_bing('ebola')
# test_bing('pesticides3')
# test_bing('ebola3')
# test_bing('vache_folle3')
# test_bing('pesticides3')
# test_bing('ebola3')
# test_bing('vache_folle3')
# test_bing('pesticides3')
# test_bing('ebola3')
# test_bing('vache_folle3')
# test_bing('pesticides3')
# test_bing('ebola3')


