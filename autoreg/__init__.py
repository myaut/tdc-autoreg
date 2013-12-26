#!/usr/bin/python -W ignore::DeprecationWarning

# Host DB declarations

class HostRowID:
	HostName = 0
	IPAddress = 1
	ExtraVars = 2
	State = 3
	
class HostState:
	New = 'N'
	Registered = 'R'
	Configured = 'C'

class HostError(Exception):
	pass

class HostNotFoundError(HostError):
	def __init__(self, hostid):
		Exception.__init__(self, "Host %s not found in database" % (hostid, ))

class HostAlreadyExistsError(HostError):
	def __init__(self, hostid):
		Exception.__init__(self, "Host %s already exists" % (hostid, ))
		
class ServerNoAccess(Exception):
	def __init__(self):
		Exception.__init__(self, "Host doesn't have admin privileges")
		
class InternalError(Exception):
	def __init__(self, *args):
		self.excdata = args