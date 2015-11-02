import redis
#r = redis.StrictRedis()
taskdb = redis.Redis('localhost')
def create_task():
    taskdb.sadd("cles", "valeur")
