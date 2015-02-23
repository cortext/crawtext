#!/usr/bin/env python2.7
from database import Database
from article import Article, Page
from datetime import datetime
#Logs
import logging
logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="crawtext.log", format=FORMAT, level=logging.DEBUG)

logging.info("Runnning crawl")
import sys
sys.setrecursionlimit(10000)

def uniq(seq):
    checked = []
    for e in seq:
        if e not in checked:
            checked.append(e)
    return checked

def clean_queue(db):
    treated = uniq(db.results.distinct("url"))
    treated.extend(db.logs.distinct("url"))
    logging.info("Already treated %i urls in results and logs" %len(treated))
    logging.info("Queue contains %i urls" %db.queue.count())
    update_urls(db.queue.find(), db)
    logging.info("After cleaning: Q contains %i urls" %db.queue.count())
    return treated

def remove_last_level(db):
    logging.info("Remove last crawl depth")
    for n in db.results.find({"depth":max(db.results.distinct("depth"))}, timeout=False):
        db.results.remove({"_id":n["_id"]})
    logging.info("Now results are %i" %db.results.count())
    db.queue.drop()
    return 

def crawl(db_name, query, directory, max_depth, debug=True):
    logging.info("Running crawl")
    db = Database(db_name)
    db.results = db.use_coll("results")
    db.sources = db.use_coll("sources")
    db.queue = db.use_coll("queue")
    db.logs = db.use_coll("logs")
    logging.info("Database initiated")
    treated = clean_queue(db)
    logging.info("Queue is clean!")
    
    logging.info("%i Q" %db.queue.count())
    while db.queue.count() > 0:
        logging.info("Begin crawl")
        for item in db.queue.find(timeout=False):
            if item not in treated:
                logging.info("%s:%s" %(item['url'], item["depth"]))
                # if item["url"] not in clean_queue(db):     
                resp, data = create_result(item, db, query, directory, max_depth, debug)
                logging.info("Creating results")
                if resp is True:
                    db.results.insert(data)
                elif resp is False:
                    db.logs.insert(data)
                else:
                    pass  
                db.queue.remove({"url": item["url"]})
                
                if db.queue.count() == 0:
                    break
                if db.results.count() > 200000:
                    remove_last_level(db)
            else:
                update(url,db)
                treated.append(url)

        logging.info("Nb queue: %i" %db.queue.count())
        logging.info("Nb Results: %i" %db.results.count())
        if db.queue.count() == 0:
            break
    return True
def update_urls(list, db):
    for item in list:
        if update(item['url'], db) is True:
            try:
                return update_urls(item['cited_link'], db)
            except KeyError:
                return db.queue.find()
    return db.queue.find()

def update(url, db):
    #In results
    exists = db.results.find_one({"url":url}, timeout=False)
    if exists is not None:
        db.results.update({"url":exists["url"]}, {"$push": {"date":datetime.today()},"$set":{"crawl_nb": int(exists["crawl_nb"]+1)}})
        db.queue.remove({"url":exists["url"]})
        # for u in exists['cited_links']:
        #     update(u, db)
        return True
    else:
        exists = db.logs.find_one({"url":url}, timeout=False)
        if exists is not None:
            db.queue.remove({"url":url})
        return False


def update_url(db, treated, url):
    logging.info("Update")
    exists = db.results.find_one({"url":url}, timeout=False)
    if exists is not None:
        logging.info("found treated url in results")
        db.results.update({"url":exists["url"]}, {"$push": {"date":datetime.today()},"$set":{"crawl_nb": int(exists["crawl_nb"]+1)}})
        db.queue.remove({"url":exists["url"]})
        logging.info("Updating and removing from queue")
        try:
            logging.info("Cited link %s" %str(url))
            for u in exists["cited_links"]:
                if u in treated:
                    update_url(db, treated, u)                    
            return  
        except Exception as e:
            logging.info(e)
            logging.warning("Url has no cited links: %s" %url)
            return

    else:
        exists = db.logs.find_one({"url":url}, timeout=False)
        if exists is not None:
            # logging.info("Url found in logs with error: %s" %exists['msg'])
            db.logs.update({"_id":exists["_id"]}, {"$set": {"nb_crawl":2}})
            db.queue.remove({"url": url})
        else:
            logging.warning("Url not found in logs and results")
        return

def update_result(db,treated, item, debug):
    if debug:print "update", item["url"]
    exists = db.results.find_one({"url":item["url"]}, timeout=False)
    if exists is not None:
        if debug: print "Already treated"
        next_urls = []    
        
        next = [n for n in exists["cited_links"] if n not in treated]
        if len(next) > 0:
            for url in exists["cited_links"]: 
                if url not in db.queue.distinct("url"):
                    next_urls.append({"url": url, "source_url":item["url"], "depth": item["depth"]+1, "date": item["date"]})
            if len(next_urls) > 0:
                db.queue.insert(next_urls)
                print ">>inserted", len(next_urls)
        
        if type(exists["date"]) == list:
            last = exists['date'][-1]
        else:
            last = exists['date']
        try:
            day = (last.day, last.month, last.year)
        except TypeError:
            db.update_result(item)
            return True

        now = datetime.now()
        n_day = (now.day, now.month, now.year)
        if n_day != day:
            db.update_result(item)
        return True
    return False

def create_result(item, db, query, directory,max_depth, debug):
    if item is not None:
        try:
            if item["url"] is not None or item["url"] is not False:
                p = Page(item["url"], item["source_url"],item["depth"], item["date"], debug)
                if p.download():
                    logging.info(">Page downloaded")
                    a = Article(p.url,p.html, p.source_url, p.depth,p.date, debug)
                    if a.extract():
                        if a.filter(query, directory):
                            logging.info("Page is relevant")
                            if a.check_depth(max_depth):
                                logging.info("Depth is inferior to maximum")
                                a.fetch_links()
                                if len(a.links) > 0:
                                    db.queue.insert([{"url": url, "source_url": item['url'], "depth": int(item['depth'])+1, "domain": domain, "date": a.date} for url, domain in zip(a.links, a.domains)])
                                    logging.info("\t-inserted %d nexts url" %len(a.links))
                            return (True, a.export())
                        else:
                            return (False, a.log())        
                    else:
                        return (False, p.log())
                else:                    
                    return (False, p.log())
        except Exception, e:
            return (False, {"url":item["url"], "status": False, "msg":str(e), "code": 001})
    else:
        return (None, '')
    