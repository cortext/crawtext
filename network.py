import threading
import Queue
import requests
from urls import Link
from database import Database
import re
#from article import Article
from query import Query
from newspaper.api import build
from newspaper.article import Article

WORKERS = 4

def control(log, headers,status_code):
    '''Bool control the result if text/html or if content available'''
    #Content-type is not html 
    try:
        # req.headers['content-type']
        if 'text/html' not in headers['content-type']:
            log["msg"]="Control: Content type is not TEXT/HTML"
            log["code"] = 404
            log["status"] = False
            return (False,log)
        #Error on ressource or on server
        elif status_code in range(400,520):
            log["code"] = req.status_code
            log["msg"]="Control: Request error on connexion no ressources or not able to reach server"
            log["status"] = False
            return (False,log)
        #Redirect
        #~ elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
            #~ self.error_type="Redirection"
            #~ self.bad_status()
            #~ return False
        else:
            return (True, log)
    #Headers problems        
    except Exception as e:
        log["msg"]="Control: Request headers were not found"
        log["code"] = 403
        log["status"] = False
        return (False, log)
            

def download(url):
    '''Bool request a webpage: return boolean and update raw_html'''
    
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
            return control(log, req.headers, req.status_code)
            # if control(req)[0] is True:
            #     return (True, req.text)
            # else:
            #     return control(req)

        except Exception as e:
            log["msg"] = "Requests: answer was not understood %s" %e
            log["code"] = 400
            log["status"] = False
            return (True,log)

    except Exception as e:
        log["msg"] = "Requests: "+str(e.args)
        log["code"] = 500
        log["status"] = False
        return (False,log)

#    except requests.exceptions.MissingSchema:
#        log["msg"] = "Request: Incorrect url - Missing sheme for : %s" %url
#        log["code"] = 406
#        log["status"] = False
#        return log    

    except Exception as e:
        log["msg"] = "Requests: %s " %(e)
        log["code"] = 204
        log["status"] = False
        return (False,log)

def create(url, html, query):
    print "create", url
    article = Article(url)
    regex = re.compile("<.*?>")
    log = dict()
    log["url"] = url
    try:
        if article.build(html) is True:
            if article.text == "":
                log['code'] = 700
                log['msg'] = "Text is empty"
                article.text = BeautifulSoup(html).get_text()
                
            elif re.match(regex, article.text):
                log['code'] = 700
                log['msg'] = "Text is not clean"
                article.text = BeautifulSoup(html).get_text()
                
            if article.is_relevant(query) is False:
                log['code'] = 800
                log['msg'] = "Article is not relevant"
                return (False, log)
            # self.feeds = [n for n in self.next.feed]
            return (True, export(article))
        else:
            log["code"] = 700
            log["msg"] = "Parsing error"
            return (False, log)
            
    except AttributeError,e:
        log["code"] = 700
        log["msg"] = "Parsing error: %s" %str(e)
        return (False,log)

def export(article):
    print "export", article.url
    next = build(article.url,article.html)
    outlinks = [n.url for n in next.articles]
    return {"url":article.url, "title": article.title, "text":article.text, "html":article.html, "outlinks":outlinks}


class RequestWorker(threading.Thread):
    
    def __init__(self, queue, queueB, query, db):
        self.download_queue = queue
        self.extract_queue = queueB
        threading.Thread.__init__(self)     
        self.query = Query(query)
        self.db = db
    
    def run(self):
        while 1:
            item = self.download_queue.get()
            if item is None:
                break
            url,depth = item
            if depth > 10:
                log["msg"] = "Depth crawl is limited to 10. depth value is: %d" %depth
                log["code"] = 900
                log["status"] = False
                self.db.insert_log(url, log)
                
            if url is None:
                break # reached end of queue            
            
            ok, data = download(url)
            
            if ok:
                self.extract_queue.put((data["url"], data["html"], depth))
                self.extract()
            else:
                self.db.insert_log(url, data)
                

    def extract(self):

        doc = self.extract_queue.get()
        url, html, depth = doc
        ok, data = create(url, html, self.query)
        if ok:
            #print len(data["outlinks"])
            for url in data['outlinks']:
                self.download_queue.put((url, depth+1))
            self.db.insert_result(data)
        else:
            self.db.insert_log(url, data)
            
'''
queue = Queue.Queue()
queueB = Queue.Queue()

#initialize

for row in sources.find():
    if row['status'][-1] is True:
        if row["depth"] > 10:
            pass
        print row['url']
        queue.put((row['url'],row["depth"]))


for i in range(WORKERS):
    RequestWorker(queue, queueB, query).start() # start a worker

for i in range(WORKERS):
    queue.put(None) # add end-of-queue markers
#    RequestWorker(queueB).start()    

''' 