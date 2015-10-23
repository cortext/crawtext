from crawtext.database import Database

db = Database("RRI")

for n in db.data.find({},{"url":1, "cited_links_ids":1, "title":1}):
    print(n)
