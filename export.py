def create_collection(format, directory):
	date = dt.now()
	date = dt.strftime(date, "%d-%m-%y_%H:%M")
	dict_values=dict()
	dict_values["sources"] = {
		"filename": "%s/sources_%s.%s" %(directory, date, format),
		"format": format,
		"fields": 'url,origin,date.date',
		}
	dict_values["logs"] = {
		"filename": "%s/logs_%s.%s" %(directory, date, format), 
		"format":format,
		"fields": 'url,code,scope,status,msg',
		}
	dict_values["results"] = {
		"filename": "%s/results_%s.%s" %(directory,date, format), 
		"format":format,
		"fields": 'url,domain,title,text,outlinks',
		}
	return dict_values
		
def export_all(name, format, dict_values):
	datasets = ['sources', 'results', 'logs']
	filenames = []
	for n in datasets:
		dict_values = dict_values[str(n)]
		if format == "csv":
			print ("- dataset '%s' in csv:") %n
			c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(name,n,dict_values['fields'], dict_values['filename'])	
			filenames.append(dict_values['filename'])		
		else:
			print ("- dataset '%s' in json:") %n
			c = "mongoexport -d %s -c %s -o %s"%(name,n,dict_values['filename'])				
			filenames.append(dict_values['filename'])
		subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
def export_one(name, format, collection, dict_values):
	dict_values = self.dict_values[str(collection)]
	if self.format == "csv":
		print ("Exporting into csv")
		c = "mongoexport -d %s -c %s --csv -f %s -o %s"%(name,collection,dict_values['fields'], dict_values['filename'])
	else:
		print ("Exporting into json")
		c = "mongoexport -d %s -c %s --jsonArray -o %s"%(name,colection,dict_values['filename'])				
subprocess.call(c.split(" "), stdout=open(os.devnull, 'wb'))
def generate(name, directory):
	try:
		collection = task["data"]
	except KeyError, AttributeError:
		collection = None
	try:
		format = task["format"]
	except KeyError, AttributeError:
		format = "json"
	
	f_dict = create_collection(directory, format)
	if collection is not None:
		return export_one(name, format,f_dict)
	else:
		return export_all(name, format,f_dict)