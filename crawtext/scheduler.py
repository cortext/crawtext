#!/usr/bin/env python
# -*- coding: utf-8 -*-
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
from database import Database
from config import config
from celery import Celery

app = Celery('tasks', broker='amqp://guest@localhost//')


def get_tasks():
    cfg = config()
    task_db = Database(cfg["default"]["db_name"])
    coll = task_db.use_coll("job")
    return [{"name":n["name"]} for n in coll.find()]

@app.task
def add(data):
    return Crawtext()

class Scheduler(object):
    pass
'''
name,
{u'status': [True], 
u'filter_lang': u'fr', 
u'file': False, 
u'task': None, 
u'name': u'mottanai_test5', 
u'url': False, 
u'project_path': u'/home/c24b/projets/crawtext-latest/crawtext/projects/mottanai_test5',
u'msg': [u'ok'], 
u'search_nb': 5, 
u'next': False, 
u'filter': True, 
u'directory': u'/home/c24b/projets/crawtext-latest/crawtext/projects', 
u'step': [u'create'], 
u'repeat': False, 
u'key': u'J8zQNrEwAJ2u3VcMykpouyPf4nvA6Wre1019v/dIT0o', 
u'date': datetime.datetime(2015, 10, 26, 18, 32), 
u'query': u'(mottainai) OR (motainai) OR (mota\xefna\xef)', 
u'_id': ObjectId('562e63a2dabe6e30beeb19a1'), 
u'max_depth': 2, 
u'history': [datetime.datetime(2015, 10, 26, 18, 32)]}
'''
