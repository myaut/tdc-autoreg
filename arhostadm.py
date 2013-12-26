#!/usr/bin/python

import autoreg
from autoreg.cli import print_usage, parse_options
import getopt
import xmlrpclib
import socket
import sys
import md5

usagestring = """Usage:\tarhostadm [-s server[:port]] [-p password] <subcommand> [-?] [options]"""

subcommands = {
	'list' 	: ('list [-h]', 'Shows list of all registered hosts'),
	'info' 	: ('info <hostid>', 'Shows information on desired host by its HostID'),
	'create': ('create <hostid> <hostname>', 'Creates new host in host database'),
	'update': ('update <hostid> [-h hostname] [extraarg1=extraval1] [extraarg2=extraval2]	...', 
					'Updates database'),
	'delete': ('delete <hostid>', 'Delete entry in host database'),
	'register': ('register <hostid>', 'Change hostid state to registered'),
	'unconfigure': ('unconfigure <hostid>', 'Change hostid state to new')
	}

def print_list(data, header):
    fmtstr = '%20s %20s %16s %5s\n'
    if header:
		hostlist  = fmtstr % ('HOSTID', 'HOSTNAME', 'IPADDR', 'STATE')
		hostlist += fmtstr % ('-'*20, '-'*20, '-'*16, '-'*5)
    else:
		hostlist = ''
    
    for hostid in data:	
		hostlist += fmtstr % (hostid, data[hostid][autoreg.HostRowID.HostName],
								data[hostid][autoreg.HostRowID.IPAddress],
								data[hostid][autoreg.HostRowID.State])
	
    print hostlist

def print_info(hostid, hostdata):	
    hostinfo  = 'HostID: ' 	+ hostid + '\n'
    hostinfo += 'Hostname: ' 	+ hostdata[autoreg.HostRowID.HostName] + '\n'
    hostinfo += 'IP Address: ' 	+ hostdata[autoreg.HostRowID.IPAddress] + '\n'
    
    hostinfo += 'Extra Variables:\n'
    
    extravars = hostdata[autoreg.HostRowID.ExtraVars]
    for hostvar in extravars:
		hostinfo += "\t%s: %s\n" % (hostvar, extravars[hostvar])
	
    print hostinfo   

## -------------------
## MAIN 
## --------------------

(server, port, password, command, commandargs) = parse_options(usagestring, subcommands, 'list')
adminhash = md5.new(password).hexdigest()

try:
	proxy = xmlrpclib.ServerProxy("http://%s:%s" % (server, port))
except socket.error, err:
	print >> sys.stderr, err
	sys.exit(1)

try:
	if command == 'list':
		hostdata = proxy.get_host_list()
		
		if len(hostdata) == 0:
			print >> sys.stderr, "No hosts in database"
			sys.exit(1)
		else:
			# if -h in command options, shall print without headers
			print_list(hostdata, '-h' not in commandargs)
	else:
		# all other options have argument 'hostid'
		if len(commandargs) < 1:
			print_usage(command, usagestring, subcommands)
			sys.exit(1)
		
		hostid = commandargs[0]
		commandargs = commandargs[1:]
		
		if command == 'info':
			print_info(hostid, proxy.get_host_info(hostid))
		elif command == 'create':
			if len(commandargs) < 1:
				print_usage(command, usagestring, subcommands)
				sys.exit(1)
		
			hostname = commandargs[0]
			proxy.create_host(adminhash, hostid, hostname)
		elif command == 'delete':	
			proxy.delete_host(adminhash, hostid)
		elif command == 'update':
			(uopt, uargs) = getopt.getopt(commandargs, 'h:')
			uopt = dict(uopt)
			
			if '-h' in uopt.keys():
				proxy.set_hostname(adminhash, hostid, uopt['-h'])
				
			for uarg in uargs:
				if ';' in uarg:
					print >> sys.stderr, "Note: arguments couldn't include semicolons"
					sys.exit(1)
			
			for uarg in uargs:
				extravar = uarg.split('=', 1)
				if '=' in uarg:
					proxy.update_host(adminhash, hostid, extravar[0], extravar[1])
				else:
					print >> sys.stderr, "Wrong update argument %s" % uarg
		elif command == 'register':	
			if proxy.get_state(hostid) == autoreg.HostState.New:
				proxy.set_state(adminhash, hostid, autoreg.HostState.Registered)
			else:
				print >> sys.stderr, "Wrong state!"
		elif command == 'unconfigure':	
			if proxy.get_state(hostid) in [autoreg.HostState.Configured, 
						autoreg.HostState.Registered]:
				proxy.set_state(adminhash, hostid, autoreg.HostState.New)
			else:
				print >> sys.stderr, "Wrong state!"
			
except xmlrpclib.ProtocolError:
	print >> sys.stderr, "Internal server error"
	sys.exit(1)
	
except xmlrpclib.Fault, fault:
	print >> sys.stderr, fault.faultString
	sys.exit(1)