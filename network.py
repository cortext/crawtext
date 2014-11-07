#!/usr/bin/env python
# -*- coding: utf-8 -*-


#from .newspaper import Article, build
import sys
from query import Query
from url import Link
# try:
from newspaper import build
from newspaper import Article
    
        
def fetch(url):
    log = dict()
    log["url"] = url
    try:
        # req = requests.get((self.url), headers = headers ,allow_redirects=True, proxies=None, timeout=5)
        req = requests.get(url, allow_redirects=True, timeout=5)
        req.raise_for_status()
        try:
            log["html"] = req.text
            log["msg"] = "Ok"
            log["code"] = 200
            log["status"] = True
            if 'text/html' not in req.headers['content-type']:
                log["msg"]="Control: Content type is not TEXT/HTML"
                log["code"] = 404
                log["status"] = False
                return (False,log)
        #Error on ressource or on server
            elif req.status_code in range(400,520):
                log["code"] = req.status_code
                log["msg"]="Control: Request error on connexion no ressources or not able to reach server"
                log["status"] = False
                return (False,log)
            
            else:
                return (True, (url,req.text))

        except Exception as e:
            log["msg"] = "Requests: answer was not understood %s" %e
            log["code"] = 400
            log["status"] = False
            return (False,log)

    except Exception as e:
        log["msg"] = "Requests: "+str(e.args)
        log["code"] = 500
        log["status"] = False
        return (False,log)

    
def parse(url, html):
    article = Article(url)
    if article.build(html):
        if article.text == "":
            log['code'] = 700
            log['msg'] = "Text is empty"
            return (False, log)
        if article.is_relevant(query) is False:
            log['code'] = 800
            log['msg'] = "Article is not relevant"
            return (False, log)
        else:
            
            links = set(article.fetch_outlinks())
            return (True,article, links)
    else:
        log["msg"] = "Article Build:Error" %e
        log["code"] = 700
        log["status"] = False
        return (False,log)



def export(article, links, depth):
    return {"url":article.url,
            "url_info":Link(article.url).json(), 
            "title": article.title, 
            "text":article.text, 
            "html":article.html, 
            "links":[clean_outlinks(links, depth)], 
            "outlinks": [n for n in create_outlinks(links)]
            }

def clean_outlinks(urllist, depth):
    for n in urllist:
        l = Link(n)
        if l.status:
            yield {"url":l.url, "depth":depth+1}

def create_outlinks(url):
    for link in url:
        link = Link(link)
        if link.status:
            yield link.json()

def process_data(n, query, db):
   
    query = Query(query)
    url, depth = n["url"], n["depth"]
    if depth <= 10:
        ok, data = fetch(url)
        if ok:
            print "fetched"
            ok, data, links = parse(data[0], data[1])
            if ok:
                data = export(data, links, depth)
                yield(data)
            print "False"
    
        db.insert_log(url, data)
    