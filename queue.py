import threading
import Queue
import requests
import time, random
from database import Database


DB = Database('mottanai')
logs = DB.use_coll('logs')
results = DB.use_coll('results')
sources = DB.use_coll('sources')


WORKERS = 4

def insert_log(url, log):
    print "insert into log %s" %url
    if url not in sources.distinct("url"):
        if url not in log.distinct("url"):
            log.insert({url:"url","msg":[log["msg"]], "status":[log["status"]], "code": log["code"]})
        else:
            exists = log.find_one({"url":url})
            log.update({"_id":exists["_id"]}, {"$push": log})
    else:
        exists = sources.find_one({"url":url})
        sources.update({"_id":exists["_id"]}, {"$push": log})
    return     

def control(req):
    '''Bool control the result if text/html or if content available'''
    #Content-type is not html 
    try:
        # req.headers['content-type']
        if 'text/html' not in req.headers['content-type']:
            log["msg"]="Control: Content type is not TEXT/HTML"
            log["code"] = 404
            log["status"] = False
            return log
        #Error on ressource or on server
        elif req.status_code in range(400,520):
            log["code"] = req.status_code
            log["msg"]="Control: Request error on connexion no ressources or not able to reach server"
            log["status"] = False
            return log
        #Redirect
        #~ elif len(self.req.history) > 0 | self.req.status_code in range(300,320): 
            #~ self.error_type="Redirection"
            #~ self.bad_status()
            #~ return False
        else:
            log["code"] = 200
            log["msg"]="Ok"
            log["status"] = True            
            return log
    #Headers problems        
    except Exception as e:
        log["msg"]="Control: Request headers were not found"
        log["code"] = 403
        log["status"] = False
        return log
            

def get(url):
    '''Bool request a webpage: return boolean and update raw_html'''
    log = dict()
    try:
        requests.adapters.DEFAULT_RETRIES = 2
        #user_agents = [u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1', u'Mozilla/5.0 (Windows NT 6.1; rv:15.0) Gecko/20120716 Firefox/15.0a2', u'Mozilla/5.0 (compatible; MSIE 10.6; Windows NT 6.1; Trident/5.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727) 3gpp-gba UNTRUSTED/1.0', u'Opera/9.80 (Windows NT 6.1; U; es-ES) Presto/2.9.181 Version/12.00']
        #headers = {'User-Agent': choice(user_agents),}
        #proxies = {"https":"77.120.126.35:3128", "https":'88.165.134.24:3128', }
        try:

            # req = requests.get((self.url), headers = headers ,allow_redirects=True, proxies=None, timeout=5)
            req = requests.get(url, allow_redirects=True, timeout=5)
            req.raise_for_status()
            try:
                log["doc"] = req.txt
                log["msg"] = "Ok"
                log["code"] = 200
                log["status"] = True
                return log
                # if control(req)[0] is True:
                #     return (True, req.text)
                # else:
                #     return control(req)

            except Exception as e:
                log["msg"] = "Requests: answer was not understood %s" %e
                log["code"] = 400
                log["status"] = False
                return log

        except Exception as e:
            log["msg"] = "Requests: "+str(e.args)
            log["code"] = req.status_code
            log["status"] = False
            return log

#    except requests.exceptions.MissingSchema:
#        log["msg"] = "Request: Incorrect url - Missing sheme for : %s" %url
#        log["code"] = 406
#        log["status"] = False
#        return log    

    except Exception as e:
        log["msg"] = "Requests: %s " %(e)
        log["code"] = 204
        log["status"] = False
        return log



class RequestWorker(threading.Thread):
    
    def __init__(self, queueA, queueB):
        self.__queue = queueA
        self.__queueB = queueB
        threading.Thread.__init__(self)

    def run(self):
        while 1:
            item = self.__queue.get()
            if item is None:
                break # reached end of queue
            
            #main action
            doc = get(item)
            if doc["status"] is True:
            # if doc[0] is not False:
                self.__queueB.put(doc["doc"])
            else:
                 insert_log(item, doc)

class ExtractWorker(threading.Thread):
    #from extractor.article import Article
    def __init__(self, queue):
        self.__queue = queue
        threading.Thread.__init__(self)

    def run(self):
        while 1:
            item = self.__queue.get()
            if item is None:     
                break # reached end of queue

            # pretend we're doing something that takes 10-100 ms
            print "Extraction"
            print item
            
            #time.sleep(random.randint(10, 100) / 1000.0)

            
        
queueA = Queue.Queue()
queueB = Queue.Queue()



for i in range(WORKERS):
    RequestWorker(queueA, queueB).start() # start a worker



db = Database('mottanai')
sources = db.use_coll('sources')

for row in sources.find():
    
    if row['status'][-1] is True:
        #print "push", row['url']
        queueA.put(row['url'])

for i in range(WORKERS):
    queueA.put(None) # add end-of-queue markers
    ExtractWorker(queueB).start()    

    