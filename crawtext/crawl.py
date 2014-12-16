#!/usr/bin/env python2.7

def crawl(db_name, query, directory):
    while self.db.queue.find() > 0: 
       for item in self.db.queue.find():
            if item["url"] not in self.db.logs.distinct("url") and item not in self.db.results.distinct("url"):
                p = Page(item["url"], item["source_url"], item["depth"],False)
                if p.is_valid() and  p.fetch():
                    p = p.export()
                    a = Article(p["url"],p["html"], p["source_url"], p["depth"], False)
                    if a.extract() and a.filter(self.query, self.directory):
                        print "Insert", a.export()
                        self.db.results.insert(a.export())
                    else:
                        self.db.insert_log(a.log())
                else:
                    self.db.insert_logs(p.log())
            self.db.queue.remove(item)
            if self.db.queue.count() < 0:
                break
        if self.db.queue.count() < 0:
                break
