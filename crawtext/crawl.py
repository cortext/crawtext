#!/usr/bin/env python2.7
from database import Database
from article import Article, Page
from datetime import datetime

def crawl(db_name, query, directory, max_depth, debug=True):
    db = Database(db_name)
    db.create_colls()
    datenow = datetime.now()
    treated = db.results.find()
    print len(treated)
    while db.queue.find() > 0:
        if debug: print "\nCrawling ..."
        for item in db.queue.find():
            if item["url"] in treated:
                if debug: print "treated"
                exists = db.results.find_one({"url":item["url"]})
                if exists is None:
                    db.queue.remove(item)
                else:
                    db.results.update({"url": item["url"]}, {"$push":  {"date":datenow}, "$inc": {"crawl_nb":+1}})
                    next_urls = []
                    for url in exists["cited_links"]:
                        if url not in db.distinct("url"):
                            next_urls.append({"url": url, "source_url":exists["url"]})
                    db.queue.insert(next_urls)
            else:
                try:
                    p = Page(item["url"], item["source_url"],item["depth"], debug)
                except KeyError:
                    p = Page(item["url"])
                if p.download(max_depth):
                    a = Article(p.url,p.html, p.source_url, p.depth, debug)
                    if a.extract() and a.filter(query, directory):
                        a.date = datenow
                        if debug is True: print "\t-is relevant"
                        # print item["depth"], max_depth
                        if item["depth"] < max_depth:
                            if debug:print "Next" 

                            a.fetch_links()
                            if debug is True: print "nexts links: %d" %len(a.outlinks)    
                            if len(a.outlinks) > 0:
                                if debug is True: print "\t-next pages: %d" %len(a.outlinks)
                                db.queue.insert(a.outlinks)

                        else:    
                            if debug: print "max_depth exceeded %d"(self.depth)

                        db.insert_results(a.export())
                        
            treated.append(item["url"])
            db.queue.remove(item)          
            if debug:
                print db.queue.count()
            if db.queue.count() == 0:
                break
            
        if db.queue.count() == 0:
            break
    return True
       
