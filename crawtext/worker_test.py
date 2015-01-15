#Project management tests
class Worker(object):
    def __init__(self, name):
        self.name = name

    def check_user_input(self, u_input):
        #u_input is a docopt dict but could be other thing
        if u_input["<name>"]:
            self.name = u_input["<name>"]
        else:
            self.params = u_input   
    
    def exists(self, name):
        db = TaskDB()
        project = db.coll.find({"name":name})
        if project is None:
            return False
        else:
            self.project = project
            return True

    def show_or_create_project(self):
        print len(self.params), self.params


if __name__== "main":
    w = Worker("test_1")
    w = 