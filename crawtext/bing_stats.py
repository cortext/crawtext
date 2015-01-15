from database import Database
def bing_stats(project_name):
    print project_name,";"
    db = Database(project_name)
    sources = db.use_coll('sources')
    for n in sources.find():
        if len(n["nb_results"]) > 5:
            print n["url"], n["nb"]

    # for n in [len(n["nb"]) :
    #     if n == 1:
    #         print n
        
    # print max_val
    # for n in sources.find():
    #     print len(n["nb"])

    # for n in sources.find({}, {"nb": {"$slice": -1}}).sort("nb"):
    #     print n["nb"][0], n["nb_results"][-1], n["url"]
  
              
        
bing_stats('pesticides3')
