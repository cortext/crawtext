#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Utils to run crawl on a regular basis

from datetime import datetime
from database import TaskDB
from wk import Worker

def run():
    tk = TaskDB()
    now = datetime.today()
    day = (now.day, now.month, now.year)


    for n in tk.coll.find():
        try:
            next = n["next"]
            date = (next.day, next.month, next.year)
            print date
            if day == date:
                print "Start", n["project_name"]
                #wk = Worker(str(n["project_name"]))
                #wk.start({})
            # print n["project_name"]
            # print n["date"][-1].day, n["date"][-1].month
            
        except KeyError:
            pass

run()