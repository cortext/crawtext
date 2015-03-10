from datetime import datetime as dt
import os, sys, subprocess

def create_field(directory, format):
	print directory
	date = dt.now()
	date = dt.strftime(date, "%d-%m-%y_%H_%M")
	dict_values=dict()
	dict_values["sources"] = {
		"filename": os.path.join(directory, "sources_%s.%s") %(date, format),
		"format": format,
		"zip": os.path.join(directory,"sources.zip"),
		"fields": 'url,origin,status.status,date.date',
		}

	dict_values["logs"] = {
		"filename": os.path.join(directory, "logs_%s.%s") %(date, format),
		"format": format,
		"zip": os.path.join(directory,"logs.zip"),
		"fields": 'url,code,scope,statuss,msg',
		}
	dict_values["results"] = {
		"filename": os.path.join(directory, "results_%s.%s") %(date, format), 
		"format":format,
		"zip": os.path.join(directory,"results.zip"),
		"fields": 'url,domain,title,text,outlinks',
		}
	return dict_values


def export_all(name, directory, format):
	print "export all"
	dict_values = create_field(directory,format)
	
	filenames = []
	datasets = ['sources','results','logs']
	for n in datasets:
		field = dict_values[str(n)]["fields"]
		filename = dict_values[str(n)]["filename"]
		fzip = dict_values[str(n)]["zip"]
		if format == "csv":
			print ("- dataset '%s' in csv:") %n
			c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(name,n,field, filename)	
			
			filenames.append(filename)		
		else:
			print ("- dataset '%s' in json:") %n
			
			c = "mongoexport -d %s -c %s -o %s"%(name,n,filename)				
			filenames.append(filename)
		subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))	
		subprocess.call(["zip", fzip,filename], shell=False)

def export_one(name,directory, collection, format):
	print "export one"
	dict_values = create_field(directory,format)
	dict_values = dict_values[str(collection)]
	if format == "csv":
		print ("Exporting into csv")
		c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(name,collection,dict_values['fields'], dict_values['filename'])
	else:
		print ("Exporting into json")
		c = "mongoexport -d %s -c %s --jsonArray -o %s"%(name,colection,dict_values['filename'])				
	subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
	subprocess.call(["zip", dict_values['zip'], dict_values['filename']] )

def generate(name, task, directory):
	try:
		collection = task["data"]
	except KeyError, AttributeError:
		collection = None
	try:
		format = task["format"]
	except KeyError, AttributeError:
		format = "json"
	
	if collection is not None:
		return export_one(name, directory,collection, format)
	else:
		return export_all(name, directory, format)
