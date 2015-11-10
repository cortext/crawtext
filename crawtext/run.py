#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Usage: run.py (<db> <coll>| --db=<db> --coll=<col>)

Options:
    db     run the scheduled crawtext project from a given database
"""
def get_tasks(db_name, coll_name):
    db = Database(db_name)
    coll = db.use_coll(coll_name)
    return [n for n in coll.find()]
        

def run_now(last_run, interval ="day"):
    '''interval default 1 day or 1 week or 1 month'''
    try:
        
        today = datetime.datetime.today().isocalendar()
        if interval == "day":
            run = last_run.isocalendar()+datetime.timedelta(days=1)
        elif interval == "week":
            run = last_run.isocalendar()+datetime.timedelta(days=7)
            
        elif interval == "month":
            run = last_run.isocalendar()+ datetime.timedelta(days=21)
        else:
            run = last_run.isocalendar()
            
            
        return bool(run == today)
    except TypeError:
        return False


if __name__ == '__main__':
    import docopt
    
    from database import Database
    from celery import Celery
    from crawler import Crawtext
    import datetime
    db_name = docopt.docopt(__doc__)['<db>']
    coll_name = docopt.docopt(__doc__)['<coll>']
    app = Celery('tasks', broker='mongodb://localhost:27017/%s' %db_name)
    
        
    @app.task(name='tasks.crawl')
    def add(data):
        
        return Crawtext(data)
    
    # Parse arguments, use file docstring as a parameter definition
    
    for n in get_tasks(db_name, coll_name):
        print "Adding", n["name"]
        add(n)
        
    
    


    
        #~ from scheduler import Scheduler
        #~ s = Scheduler()
        #~ #two config options
        #~ #with config.json
        #~ #c = Crawtext()
        #~ #with task info for scheduler
        #~ #c = Crawtext(task_cfg = {"name":"cop21-now", "db_name" :"scheduler", "dirname":"project_tester"})
#~ 
#~ 
