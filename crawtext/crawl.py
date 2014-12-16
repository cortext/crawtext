#!/usr/bin/env python2.7
from database import Database
from article import Article, Page

def crawl(db_name, query, directory):
    db = Database(db_name)
    db.create_colls()
    while db.queue.find() > 0:
        for item in db.queue.find():
            if item["url"] not in db.logs.distinct("url") and item not in db.results.distinct("url"):
                print "item not in log or results"
                p = Page(item["url"], item["source_url"], item["depth"],False)
                if p.is_valid() and p.fetch():
                    p = p.export()
                    a = Article(p["url"],p["html"], p["source_url"], p["depth"], False)
                    if a.extract() and a.filter(query, directory):
                        db.results.insert(a.export())
                        db.queue.insert(a.get_outlinks())
                    else:
                        db.insert_log(a.log())
                        db.queue.remove(item)
                else:
                    db.insert_logs(p.log())
                    db.queue.remove(item)
            print db.queue.count()
            if db.queue.count() == 0:
                break
        if db.queue.count() == 0:
            break
    return True
        
