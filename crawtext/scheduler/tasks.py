
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
        
def get_tasks(db_name):
    task_db = Database(db_name)
    coll = task_db.use_coll("job")
    for n in coll.find():
        if n["next"] is not False:
            if run_now(data["last"]):
                database.objects(newid=id).save()
                yield {"name":n["name"],"db_name":db_name, "dirname":n["directory"], "next": n["next"], "last":n["history"][-1]}
