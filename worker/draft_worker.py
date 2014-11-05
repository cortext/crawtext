def dispatch(self):		
		if self.is_valid_name() is False:
			return self.log.push()
		
		if self.exists() :
			if self.has_params():
				if self.has_action():
					if self.debug:
						print "Has action %s" %self.action
						print "Running %s project: %s" %(self.type, self.name)
						self.params['type'] = self.type
						print "Parameters =", self.params
					return self.dispatch()
					
				else:
					if self.debug:
						print "No action"
						print "Updating %s project: %s" %(self.type, self.name)
					return self.update()
			else:
				if self.debug:
					print "Showing %s project: %s" %(self.type, self.name)
				self.action = "show"
				return self.start_action()	
		else:
			if self.has_params():
				if self.debug:
					print "creating a complete %s project" %(self.type)
				if self.set_action():
					if self.debug:
						print "Before starting project create it"
					action = self.params['action']
					del self.params['action']
					self.create()
					self.params['action'] = action
					if self.debug:
						print "Running it"
					return self.dipatch()

				return self.create()
			else:
				self.action = "create"
				if self.debug:
					print "creating a defaut %s" %(self.type)
				return self.create(mode="default")	

#JOB

# def start(self):
	# 	_class = (self.type).capitalize
	# 	instance = globals()[_class]	
	# 	print instance
	# 	job = instance(self._doc, self.debug)
	# 	start = getattr(job, str(self.action))
	# 	return start()