import threading
import time
from database import *
from wk import Worker
from job import *
#http://code.activestate.com/recipes/65222-run-a-task-every-few-seconds/
class TaskThread(threading.Thread):
    """Thread that executes a task every N seconds"""
    
    def __init__(self):
		threading.Thread.__init__(self)
		self._finished = threading.Event()
		self._interval = 15.0
		DB = Database(TASK_MANAGER_NAME)
		self.COLL = DB.use_coll(TASK_COLL)
		self.tasks_list = list(self.COLL.find())
    def setInterval(self, interval):
        """Set the number of seconds we sleep between executing our task"""
        self._interval = interval
    
    def shutdown(self):
        """Stop this thread"""
        self._finished.set()
    
    def run(self):
        while 1:
            if self._finished.isSet(): return
            self.task()
            
            # sleep for interval or until shutdown
            self._finished.wait(self._interval)
    
    def task(self):
		for n in self.tasks_list:
			_class = str(n["action"]).capitalize()+str("Job")
			
			job = globals()[_class](n)
			print job
			status = job.run_job()
			
			if status is True:	
				self.COLL.update({"_id": n["_id"]},{"$inc":{"nb_run": +1},"$set":{"last_run":datetime.today()}})
				ExportJob(job.name)
			else:
				self.COLL.update({"_id": n["_id"]},{"$inc":{"nb_run": +1},"$set":{job.status}})
			ReportJob(job.name)
			
		return self.shutdown()	
			#if self.next_run == self.now# toutes les minutes
			#self.last_run = self.next_run
			#self.next_run = udpate(self.last_run+self.repeat)
				#~ print self.COLL.update({"_id": n["_id"]},{"$inc":{"nb_run": +1},"$set":{"last_run":datetime.today()}})
			#~ else:
				#~ print self.COLL.update({"_id": n["_id"]},{"$set":job.status})
        
        

            
if __name__ == '__main__':
	tt = TaskThread()
	tt.setInterval(3)
	print 'starting'
	tt.start()
	
	#print 'killing the thread'
	#tt.shutdown()
	#print 'killed and done'
