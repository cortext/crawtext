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

