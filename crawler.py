#!/usr/bin/env python
# -*- coding: utf-8 -*-


#from .newspaper import Article, build
import sys
from url import Link
import requests
# try:
# from newspaper import build
# from newspaper import Article
#from newspaper.api import build
from newspaper.article import Article
import Queue
from threading import Thread

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
                return (True, req.text)

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

    
def parse(url, html, query):
    log = dict()
    try:
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
                #here outlinks should be builtin
                # setattr(article, "outlinks", article.fetch_outlinks())
                setattr(article, "links", list(set([n for n in clean_links(article.outlinks)])))
                return (True,article)
        else:
            log["msg"] = "Article Build:Error"
            log["code"] = 700
            log["status"] = False
            return (False,log)
    except Exception as e:
        log["msg"] = "Article Parse:Error %s" %str(e)
        log["code"] = 700
        log["status"] = False
        return (False, log)


def next(article, depth):
    print article.__dict__["outlinks"]
    return [n for n in clean_outlinks(article.__dict__["outlinks"], depth)]
    

def export(article):
    return {"url":article.__dict__["url"],
             "url_info":Link(article.__dict__["url"]).json(), 
             "title": article.__dict__["title"], 
             "text":article.__dict__["text"], 
             "html":article.__dict__["html"], 
             "links":article.__dict__["links"],
             "outlinks":article.__dict__["outlinks"],
             #"links_info": [n for n in create_outlinks(article.__dict__["links"])],
             }

def clean_outlinks(urllist, depth):
    for n in set(urllist):
        if n != None and n != "" and n != "#" and n != "/":
            l = Link(n)
            if l.status is True:
                yield {"url":l.url, "depth":depth+1}

def clean_links(url):
    for link in url:
        link = Link(link)
        if link.status:
            yield link.url

def create_outlinks(url):
    for link in url:
        link = Link(link)
        if link.status:
            yield link.json()

    
# def put_to_queue(project_db):
'''
def put_to_seeds(project_db):
    print "Putting", len(project_db.sources.distinct("url")), "urls"
    for n in project_db.sources.find():
        if n not in project_db.queue.find({"url":n}):
            if n["status"][-1] is not False:
                project_db.queue.insert({"url":n, "depth":0})
'''
def put_to_seeds(project_db):
    queue = Queue.Queue()
    print "Putting", len(project_db.sources.distinct("url")), "urls"
    for n in project_db.sources.find():
        if n not in project_db.queue.find({"url":n["url"]}):
            if n["status"][-1] is not False:
                queue.put((n['url'], 0))
    if queue.empty() is False:
        return queue
    else:
        return False

def crawl_job(project_db, queue, query, max_depth):
    for i in range(4):
        t = Thread(target=run, args=(project_db, queue, query, max_depth))
        t.daemon = True
        t.start()

def process_data(queue, url, depth , query, max_depth):
    if depth >= max_depth:
        return
    if url is None:
        return

    ok, data = fetch(url)
    if ok:
        ok, log = parse(url, data, query)
        if ok:
            article = export(log)
            article["next_links"] = [n for n in clean_outlinks(article["links"], depth)]
            return (True, article)
        
    return (False, data)


def run(project_db, queue, query, max_depth):
    while queue.empty() is False:
        url, depth = queue.get()
        print "treating", url
        ok, data = process_data(queue, url,depth, query, max_depth)
        if ok:
            if data["url"] not in project_db.results.distinct("url"):
                project_db.results.insert(data)
                for n in data["next_links"]:
                    #print "Next round", n
                    queue.put(n)
        else:
            try:
                project_db.insert_log(url,data)
                print "log error", data["url"], data["msg"]
            except KeyError:
                pass
            
        
        
    queue.join()
    print "Terminated"
    return True
# def run(project_db, query, depth):
#     put_to_seeds(project_db)
#     while project_db.queue.count() != 0:
#         for n in project_db.queue.find():
#             for item in process_data(n["url"]["url"],n["depth"], query, depth):
#                 print item[1].keys()
#                 if item[0] == True:
#                     print "insert"
#                 else:
#                     print "False", item[1]["msg"]
#                 # if item[0]:
#                 #     print "inserting into results"
#                 #     project_db.results.insert(item[1])
#                 # else:
#                 #     print "inserting into logs"
#                 #     project_db.insert_log(n['url']["url"], item[1])
#                 # print "removing"
#             project_db.queue.remove({"url":n["url"]})
#     #project_db.drop("collection", "queue")
#     print "Terminated"
#     return True

def crawl(project_db, query, max_depth):
    queue = put_to_seeds(project_db)
    if queue is not False:
        if crawl_job(project_db,queue, query, max_depth):
            return True
        else:
            return False
