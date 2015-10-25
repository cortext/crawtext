import unittest
from config import config

class TestMethods(unittest.TestCase):
    '''testing the config implementation'''
    
    
        
    
    def load_file(self):
        self.newf ="./file.test"
        test = config(self.nwf)
        self.assertEqual(config(), test)
    #~ def load_file(self):
        #~ element = config["defautl"]
        #~ self.assertEqual(element, 'Je tres clair, Luc')
#~ 
    #~ def yaml(self):
        #~ print(config("config.yml"))
        #~ 
#~ 
    #~ def json(self):
        #~ pass
#~ 
    #~ def load_into_crawtext(self):
        #~ pass
    

if __name__ == '__main__':
    unittest.main()
    

