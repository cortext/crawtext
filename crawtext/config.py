#usr/bin python env
import os

def config(afile="config.json"):
    '''load config given a YAML or a JSON file'''
    if afile.endswith("json"):
        import json
        curr_dir = os.path.join(os.getcwd(), "crawtext")
        afile = os.path.join(curr_dir, afile)
        with open(afile) as json_f:
            try:
                config = json.load(json_f)
            except ValueError as e:
                sys.exit("Error parsing config.json file: %s" %e)
        return config
        
        
    elif afile.endswith("yml"):
        import yaml
        
        curr_dir = os.path.join(os.getcwd(), "crawtext")
        afile = os.path.join(curr_dir, afile)
        try:
            with open(afile, 'r') as ymlfile:
                try:
                    config = yaml.load(ymlfile.read())
                except ValueError as e:
                    sys.exit("Error parsing config.yml file: %s" %e)
            return config
        except IOError, e:
            sys.exit("File not found: config.yml")
    else:
        sys.exit("No config file found")

