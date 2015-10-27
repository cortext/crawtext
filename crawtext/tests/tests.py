import unittest
from config import config

class TestConfigMethods(unittest.TestCase):
    '''testing the config implementation'''
    def load_file(self):
        print(config)
        pass

    def yaml(self):
        pass

    def json(self):
        pass

    def load_into_crawtext(self):
        pass
    
class TestStartMethods(unittest.TestCase):
    def start(self):
        pass
    def load_project(self):
        pass
    def load_source(self):
        pass
    def load_queue(self):
        pass
    

if __name__ == '__main__':
    unittest.main()
