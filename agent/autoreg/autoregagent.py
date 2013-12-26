#!/usr/bin/python

# --------------------------------------------
# TDC hosts automatic registration v1.0
# 
# XML-RPC common agent functions
# Copyright (c) Sergey Klyaus, 2011
# Published under GPLv2 LICENSE
#
# Version 0.5
# --------------------------------------------

import xmlrpclib
import time
from datetime import datetime
import socket
import os

POLLTIME	= 15

class HostRowID:
	HostName = 0
	IPAddress = 1
	ExtraVars = 2
	State = 3
	
class HostState:
	New = 'N'
	Registered = 'R'
	Configured = 'C'

class HostServerError(Exception):
	pass

class HostAlreadyConfigured(Exception):
	pass

class HostAgent:
	def __init__(self, server, port):
		try:
			self.proxy = xmlrpclib.ServerProxy("http://%s:%s" % (server, port))
		except (socket.error, xmlrpclib.ProtocolError):
			raise HostServerError
		
	def register(self, hostid, ipaddr):
		while True:
			state = self.proxy.register(hostid, ipaddr)
			
			if state == HostState.New:
				# Waiting for configuration on HostDBServer	
				time.sleep(POLLTIME)
			elif state == HostState.Registered:
				# Found configuration!
				if not os.path.exists('/etc/autoreg.lock'):
					# Create lock file
					lkfile = file('/etc/autoreg.lock', 'w')
					lkfile.write(datetime.now().strftime('%Y.%m.%d.%H.%M'))
					
					# Than return host's data
					return self.proxy.get_host_info(hostid)
				else:
					# Remove lockfile first
					
					raise HostAlreadyConfigured
			elif state == HostState.Configured:
				raise HostAlreadyConfigured
			else:
				raise HostServerError
		
	def configure(self, hostid):
		self.proxy.configure(hostid)