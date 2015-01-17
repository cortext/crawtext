#!/usr/bin/env python2.7
from database import Database
from article import Article, Page
from datetime import datetime

def crawl(db_name, query, directory, max_depth, debug=True):
    db = Database(db_name)
    db.results = db.use_coll("results")
    db.sources = db.use_coll("sources")
    db.queue = db.use_coll("queue")
    db.logs = db.use_coll("logs")
    treated = db.results.distinct("url")
    print len(treated)
    for n in db.logs.distinct("url"):
        treated.append(n)

    if debug: print len(treated), "already in results"
    while db.queue.count() > 0:
        if debug: print "\nCrawling ..."
        for item in db.queue.find():
            if debug:
                print "\nTreating", db.queue.count(), "pages \n"
                print item["url"]
            if item["url"] in treated:
                print "treated"
                if update_result(db,treated, item, debug) is False:
                    item['msg'] = "Result not found but treated"

                db.queue.remove(item) 
            else:
                print "new"
                resp, data = create_result(db, treated, item,query, directory, max_depth, debug)
                if resp is False:
                    try:    
                        db.insert_log(data)
                    except:
                        pass
                db.queue.remove(item)
            if db.queue.count() == 0:
                break
            print "Results", db.results.count()
            if db.results.count() > 200000:
                for n in db.results.find({"depth":max(db.results.distinct("depth"))}):
                    db.results.remove({"_id":n["_id"]})
                print db.results.count()
                db.queue.drop()
                break
        if db.queue.count() == 0:
            break
    return True
       
def update_result(db,treated, item, debug):
    print "update"
    print db.update_result(item)
    
    exists = db.results.find_one({"url":item["url"]})
    if exists is not None :
        next_urls = []
        try:
            next = [n for n in exists["cited_links"] if n not in treated]
            if len(next) > 0:
                
        # print exists['cited_links']
                for url in exists["cited_links"]:
                    next_urls.append({"url": url, "source_url":item["url"], "depth": item["depth"]+1, "date": item["date"]})
                if len(next_urls) > 0:
                    db.queue.insert(next_urls)
                    print ">>inserted", len(next_urls)
                    return True
            
            else:
                return  True
        except KeyError:
            return True
    else:
        return False

def create_result(db, treated, item, query, directory,max_depth, debug):
    
    p = Page(item["url"], item["source_url"],item["depth"], item["date"], debug)
    if p.download():
        if debug: print ">Page downloaded"
        a = Article(p.url,p.html, p.source_url, p.depth,p.date, debug)
        if a.extract() and a.filter(query, directory):
            if debug is True: print "\t-is relevant"
            if a.check_depth(max_depth):
                if debug: print "\t-page depth:", item["depth"],"<", max_depth
                a.fetch_links()
                if len(a.links) > 0:
                    if debug is True: print "\t-next pages: %d" %len(a.links)
                    db.queue.insert([{"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date} for url, domain in zip(a.links, a.domains)])
                    print "\t-inserted %d nexts url" %len(a.links)
                # else:
                #     if debug: print "\t-page depth:", item['depth'],"<", max_depth

            db.insert_result(a.export())
            treated.append(item["url"])
            return (True, "")
        else:
            return (False, a.log())        
    else:
        treated.append(item["url"])
        return (False, p.log())
    
    