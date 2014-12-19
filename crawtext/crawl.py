#!/usr/bin/env python2.7
from database import Database
from article import Article, Page


def crawl(db_name, query, directory, max_depth, debug=False):
    debug = False
    db = Database(db_name)
    db.create_colls()
    treated = set()

    while db.queue.find() > 0:
        print "\nCrawling ..."
        
        for item in db.queue.find():
            print "T", len(treated)
            if item["url"] not in treated and item["url"] not in db.results.distinct("url") and item["url"] not in db.logs.distinct("url") :
                p = Page(item["url"], item["source_url"], item["depth"], debug)
                if debug is True: print "Page:"
                if p.is_valid(max_depth) and p.fetch():
                    if debug is True: print "\t-fetched"
                    a = Article(p.url,p.html, p.source_url, p.depth, debug)
                    print p.depth
                    if a.extract() and a.filter(query, directory):
                        if debug is True: print "\t-is relevant"                   
                        a.get_outlinks()
                        if debug is True: print "nexts links: %d" %len(a.outlinks)
                        if len(a.outlinks) > 0:
                            if debug is True: print "\t-next pages: %d" %len(a.outlinks)

                            db.queue.insert(a.outlinks)
                        
                        if debug is True: print "\t-exported"
                        db.results.insert(a.export())
                        
                    else:
                        if debug is True: print "\t-not relevant"                   
                        db.insert_log(a.log())
                        
                
                treated.add(p.url)
            db.queue.remove(item)
            
            
            # if debug: 
            print db.queue.count()
            if db.queue.count() == 0:
                break
        if db.queue.count() == 0:
            break
        treated = {}
    return True
        
