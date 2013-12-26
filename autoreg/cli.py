#!/usr/bin/python

import getopt
import sys

# --------------------------------------------
# TDC hosts automatic registration v1.0
# 
# CLI Tools
# Copyright (c) Sergey Klyaus, 2011
# Published under GPLv2 LICENSE
#
# Version 0.5
# --------------------------------------------

def print_usage(command, usagestring, subcommands):
	print >> sys.stderr, usagestring
	if command:
		print >> sys.stderr, '\t', subcommands[command][0]
		print >> sys.stderr, "\t%s" % (subcommands[command][1])
	else:
		print >> sys.stderr, "Where subcommand is:"
		for cmd in subcommands:
			print >> sys.stderr, "\t%s\t- %s" % (cmd, subcommands[cmd][1])
		

def parse_options(usagestring, subcommands, defaultcmd):
	"""
	Each cli utility has syntax:
	arcliutil [-s server[:port]] [-p password] <subcommand> [-?] [options]
	parse_options parses sys.argv[1:] using getopt according this command line.
	
	usagestring - simple string used in help
	defaultcmd - subcommand used if no subcommand specified
	
	subcommands is a dictionary:
	{Subcommand name: (Usage string, Help), ...}
	
	e.g.:
	{'list' : ('list [-h]', 'Shows list of all registered hosts')}
	
	default values:
	server = localhost
	port = 8765
	password = default
	"""
	
	(options, args) = getopt.getopt(sys.argv[1:], '?s:p:')
	options = dict(options)
	
	if '-?' in options.keys():
		print_usage(None, usagestring, subcommands)
		sys.exit(0)
	
	port = 8765
	if '-s' not in options.keys():
		server = 'localhost'
	else:
		server = options['-s']
	
	if '-p' not in options.keys():
		password = 'default'
	else:
		password = options['-p']
	
	if ':' in server:
		server_port = server.split(':', 1)
		server = server_port[0]
		port = int(server_port[1])
	
	if port == 0:
		print >> sys.stderr, "You specified wrong port"
		print_usage(None, usagestring, subcommands)
		sys.exit(1)
	
	if len(args) < 1:
		command = defaultcmd
	else:
		command = args[0]
	
	if command not in subcommands:
		print >> sys.stderr, "Incorrect subcommand"
		print_usage(None, usagestring, subcommands)
		sys.exit(1)
		
	commandargs = args[1:]
	
	if '-?' in commandargs or '--help' in commandargs:
		print_usage(command, usagestring, subcommands)
		sys.exit(0)
		
	return (server, port, password, command, commandargs)