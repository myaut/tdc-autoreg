#!/usr/bin/python

import autoreg
from autoreg.cli import print_usage, parse_options
import xmlrpclib
import socket
import sys

usagestring = """Usage:\tarcheck [-s server[:port]]"""

subcommands = {
	'check' 	: ('check', 'Checks server is alive')
	}  

## -------------------
## MAIN 
## --------------------

(server, port, password, command, commandargs) = parse_options(usagestring, subcommands, 'check')

try:
	proxy = xmlrpclib.ServerProxy("http://%s:%s" % (server, port))
	if proxy.check() == True:
		print >> sys.stderr, "Server is alive"
		sys.exit(0)
	else:
		print >> sys.stderr, "Server fails own check"
		sys.exit(1)
except (xmlrpclib.Fault, xmlrpclib.ProtocolError, socket.error), err:
	print >> sys.stderr, err
	sys.exit(1)