#!/usr/bin/env python2.7
from database import Database
from article import Article, Page


def crawl(db_name, query, directory, max_depth, debug=False):
    db = Database(db_name)
    db.create_colls()
    while db.queue.find() > 0:
        for item in db.queue.find():
            if item is not None:
            # if debug: print "find", item
            # if debug: print item["url"]
                if item["url"] not in db.logs.distinct("url") and item not in db.results.distinct("url"):
                    # if debug: print "item not in log or results"
                    p = Page(item["url"], item["source_url"], item["depth"], debug)
                    if debug: print "Page:"
                    if p.is_valid(max_depth) and p.fetch():
                        print "\t-fetched"
                        a = Article(p.url,p.html, p.source_url, p.depth, debug)
                        
                        if a.extract() and a.filter(query, directory):
                            if debug: print "\t-is relevant"                   
                            a.get_outlinks()
                            # if debug: print "nexts links: %d" %len(a.outlinks)
                            if len(a.outlinks) > 0:
                                if debug: print "\t-next pages: %d" %len(a.outlinks)
                                db.queue.insert(a.outlinks)
                            
                            if debug: print "\t-exported"
                            db.results.insert(a.export())
                            
                        else:
                            if debug: print "\t-not relevant"                   
                            db.insert_log(a.log())
                            
                    else:
                        print "\t-invalid"
                        db.insert_log(p.log())
                db.queue.remove(item)
            # if debug: print db.queue.count()
            if db.queue.count() == 0:
                break
        if db.queue.count() == 0:
            break
    return True
        
