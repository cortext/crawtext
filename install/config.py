
from corbot import Crawtext

def config():
	import yaml
	yaml_f = open("../conf/defauts.yaml", "r")
	data =  yaml.load(yaml_f)
	print data
	c = Crawtext(data["name"], data["parameters"], False)
	c.show()
	sys.exit()
	
	
	
if __name__== "__main__":		
	config()
	
