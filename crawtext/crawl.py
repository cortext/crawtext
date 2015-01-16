#!/usr/bin/env python2.7
from database import Database
from article import Article, Page
from datetime import datetime

def crawl(db_name, query, directory, max_depth, debug=True):
    db = Database(db_name)
    db.create_colls()
    datenow = datetime.now()
    treated = [n for n in db.results.find()]
    if debug: print len(treated), "already in results"
    while db.queue.find() > 0:
        if debug: print "\nCrawling ..."
        for item in db.queue.find():
            if item["url"] in treated:
                if debug: print "treated"
                exists = db.results.find_one({"url":item["url"]})
                if exists is None:
                    if debug: print "Not found item"
                    db.queue.remove(item)
                else:
                    if debug: print "found item"
                    db.results.update({"url": item["url"]}, {"$push":  {"date":datenow}, "$inc": {"crawl_nb":+1}})
                    next_urls = []
                    for url in exists["cited_links"]:
                        if url not in db.queue.distinct("url"):
                            next_urls.append({"url": url, "source_url":exists["url"]})
                    db.queue.insert(next_urls)
            else:
                if debug: print "new item"
                try:
                    p = Page(item["url"], item["source_url"],item["depth"], debug)
                except KeyError:
                    p = Page(item["url"])
                if p.download(max_depth):
                    if debug: print "downloaded"
                    a = Article(p.url,p.html, p.source_url, p.depth, debug)
                    if a.extract() and a.filter(query, directory):
                        a.date = datenow
                        if debug is True: print "\t-is relevant"
                        if debug : print "D", item["depth"], "Max D", max_depth
                        if item["depth"] < max_depth:
                            if debug: print "Next" 
                            a.fetch_links()
                            if debug is True: print "nexts links: %d" %len(a.links)    
                            if len(a.links) > 0:
                                print a.links
                                if debug is True: print "\t-next pages: %d" %len(a.links)
                                db.queue.insert(a.links)

                        else:    
                            if debug: print "max_depth exceeded %d"(self.depth)
                        if debug: print a.export()
                        db.insert_result(a.export())
                        
            treated.append(item["url"])
            db.queue.remove(item)          
            if debug:
                print "To treat", len([n for n in db.queue.distinct("url") if n not in treated])
            if db.queue.count() == 0:
                break
            
        if db.queue.count() == 0:
            break
    return True
       
