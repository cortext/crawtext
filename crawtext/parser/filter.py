from adblockparser import AdblockRules
import os
PKG_DIR = os.path.dirname(os.path.realpath(__file__))
#PKG_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'packages')
class Filter(object):
    def __init__(self, filename):
        self.rules = []
        with open(filename, "r") as blacklist:
            for line in blacklist.xreadlines():
                if line.startswith('!'):
                    continue
                if '##' in line: # HTML rule
                    continue
                else:
                    self.rules.append(line)
        #, supported_options=['script', 'domain']
        self.adblock = AdblockRules(self.rules, supported_options=['script', 'domain'])
        
    def match(self, url, options=None):
        return self.adblock.should_block(url)
    
            
filter = Filter(os.path.join(PKG_DIR, "complete-list.txt"))

#"complete-list.txt"


