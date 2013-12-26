#!/usr/bin/python -W ignore::DeprecationWarning

# --------------------------------------------
# TDC hosts automatic registration v1.0
# 
# XML-RPC Host database Server
# Copyright (c) Sergey Klyaus, 2011
# Published under GPLv2 LICENSE
#
# Version 0.5
# --------------------------------------------

from autoreg import *

from SimpleXMLRPCServer import SimpleXMLRPCServer
import os, fcntl
import md5
import time
import shutil
import sys

import traceback

import csv

# Some Variables
DB_NOTICE = True
DB_DEBUG = True

# Some hostid checker Decorators
def host_checker(func, cond, error):
	def wrapper(self, data, hostid, *args, **kwargs):
		if cond(hostid, data):
			return func(self, data, hostid, *args, **kwargs)
		else:
			raise error(hostid)
	return wrapper
	
def host_exists_checker(func):
	return host_checker(func, 
					lambda hostid, data: hostid in data.keys(), 
					HostNotFoundError)

def host_notexists_checker(func):
	return host_checker(func, 
					lambda hostid, data: hostid not in data.keys(), 
					HostAlreadyExistsError)

class HostsDB:
	"""DB is simple csv, format
	hostid(it's macaddress),vmname,public ipaddr,extra config string,state
	where extra config string is semicolon separated nv list for additional arguments:
	
	e.g.: 
	00:1D:09:46:28:08,java-1,192.168.50.155,e1000g2=192.168.100.1;hosts=hosts_java,R
	
	On read operations, file opens with shared filesystem lock (fcntl.LOCK_SH), and entire database is read into dictionary:
		{hostid: [hostname, ipaddr, extravarstr, state]}
	
	On update operations, HostsDB read full database at first, make proper modifications in dictionary, then writes it using csv.writer, file opens with shared filesystem lock (fcntl.LOCK_SH),
	
	WARNING: In this implementation, transactions are not supported, so this code is not atomic:
		mydata = hostsdb.select('0011223344FF')
		if mydata[HostRowID.HostName] != '':
			hostsdb.set_state('0011223344FF', HostState.Configured)"""
	def debug(self, doprint, fmtstr, *args):
		if doprint:
			print >> sys.stderr, ("HostsDB: " + fmtstr) % args
		
	def extravar_split(self, extravarstr):
		# ExtraVar Helper
		# Split extra variables string 'var1=1;var2=str' into {var1: 1, var2: str}
		return dict([tuple(pair.split('=', 1)) 
				for pair 
				in extravarstr.split(';')
				if '=' in pair])
	
	def extravar_join(self, extravars):
		return ';'.join([item[0] + '=' + item[1] for item in extravars.items()])

	def __init__(self, hostsdb_fn):
		shutil.copy(hostsdb_fn, hostsdb_fn+'.old')
		self.debug(DB_NOTICE, 'Backing up %s to %s', hostsdb_fn, hostsdb_fn)
		self.hostsdb_fn = hostsdb_fn;
	
	def read(self):
		"""Reads entire dictionary from hostdb
		and returns empty dictionary or:
		{hostid: [hostname, ipaddr, extravarstr, state]}
		
		For field numbers use constants from autoreg.HostRowID"""
		if not os.path.exists(self.hostsdb_fn):
			return {}
		
		hostsdb = open(self.hostsdb_fn, 'r')
		fcntl.lockf(hostsdb.fileno(), fcntl.LOCK_SH)
		hostsdb_data = {}
		
		try:
			for host in csv.reader(hostsdb):
				hostsdb_data[host[0]] = host[1:]
		except EOFError:
			return dict()
		finally:
			fcntl.lockf(hostsdb.fileno(), fcntl.LOCK_UN)
			hostsdb.close()
		
		self.debug(DB_DEBUG, "Read full database")
		return hostsdb_data
	
	def select(self, hostid):
		"""Reads single entry from database
		
		NOTE: in select function ExtraVar string is parsed into dictionary
		
		returnvalue: [hostname, ipaddr, {evname1: evval1, evname2: evval2, ...}, state]"""
		data = self.read()
		
		if hostid in data.keys():
			self.debug(DB_DEBUG, "Select %s successful", hostid)
			row = data[hostid];
			row[HostRowID.ExtraVars] = self.extravar_split(row[HostRowID.ExtraVars])
			return row;
		else:
			self.debug(DB_NOTICE, "Select %s failed", hostid)
			raise HostNotFoundError(hostid)
	
	def update_decorator(func):
		def update_wrapper(self, *args, **kwargs):
			try:
				# Open for update in executive mode
				data = self.read();
				hostsdb = open(self.hostsdb_fn, 'w')
				fcntl.lockf(hostsdb.fileno(), fcntl.LOCK_EX)
				newdata = data.copy()
				
				func(self, newdata, *args, **kwargs)
				
				# If no error returned, write new data
				self.debug(DB_DEBUG, "Update sucessfully commited")
				data = newdata
			finally:
				# commit data to file
				self.debug(DB_DEBUG, "Update finished")
				writer = csv.writer(hostsdb);
				for hostid in data:
					writer.writerow([hostid] + data[hostid]);
				
				fcntl.lockf(hostsdb.fileno(), fcntl.LOCK_UN)
				hostsdb.close()	  
				
		return update_wrapper
	
	@update_decorator
	@host_notexists_checker
	def create(self, data, hostid, hostname):
		""" Creates new hostid-hostname pair in DB
		
		If hostid already exists, raises HostAlreadyExistsError"""
		data[hostid] = [hostname, '', '', HostState.New]
		self.debug(DB_NOTICE, "New entry %s - %s created", hostid, hostname);
		
		return data

	# update variable
	@update_decorator
	@host_exists_checker
	def set_ipaddr(self, data, hostid, ipaddr):
		"""Changes IP address
		
		If hostid not exists, raises HostNotFoundError"""
		data[hostid][HostRowID.IPAddress] = ipaddr;
		self.debug(DB_DEBUG, "%s.ipaddr=%s", hostid, ipaddr)
		
		return data

	@update_decorator
	@host_exists_checker
	def set_hostname(self, data, hostid, hostname):
		""" Changes IP address
		
		If hostid not exists, raises HostNotFoundError"""
		data[hostid][HostRowID.HostName] = hostname;
		self.debug(DB_DEBUG, "%s.hostname=%s", hostid, hostname)
		
		return data

	@update_decorator
	@host_exists_checker
	def set_state(self, data, hostid, state):
		# TODO: Check is have valid value
		"""
		Set state for hostid
		
		NOTE: use autoreg.HostState constants
		
		If hostid not exists, raises HostNotFoundError
		"""
		data[hostid][HostRowID.State] = state;
		self.debug(DB_NOTICE, "%s transtitioned to state %s", hostid, state)
		return data
	
	@update_decorator
	@host_exists_checker
	def update(self, data, hostid, varname, varvalue):
		"""
		Update extra variable for host
		
		If hostid not exists, raises HostNotFoundError
		"""
		extravars = self.extravar_split(data[hostid][HostRowID.ExtraVars]);
		extravars[varname] = varvalue;
		#  Convert it back
		data[hostid][HostRowID.ExtraVars] = self.extravar_join(extravars);
		return data

	# delete entry
	@update_decorator
	@host_exists_checker
	def delete(self, data, hostid):
		"""
		Removes entry
		
		If hostid not exists, raises HostNotFoundError
		"""
		self.debug(DB_NOTICE, "%s removed", hostid)
		del data[hostid]
		return data
		
# XML RPC Server
class HostDBDispatcher:
	"""
	Host dispatcher registers XML-RPC function and dispatches it
	on remote call. Replaces default SimpleXMLRPCDispatcher for two reasons:
		* Provides additional tracing for exception 
		* Managed function registration
	"""
	def __init__(self):
		self.rpcfunctions = {}
	
	def register(self, func, funcname = None):
		"""
		Registers function in dispatcher.
		If funcname is not specified, uses default function name provided by __name__ variable (this doesn't work with decorators)
		"""
		if not funcname:
			funcname = func.__name__
			
		self.rpcfunctions[funcname] = func
		print "Registered", funcname
	
	def _dispatch(self, method, params):
		try:
			if method in self.rpcfunctions:
				return self.rpcfunctions[method](*params)
		except (HostError, ServerNoAccess):
			raise
		except:
			print "Internal error (uncaught exception)"
			traceback.print_exc()
			raise
		

class HostDBServer:
	"""
	Main XML-RPC Server for host database handling
	"""
	def checkadmin(self, adminhash):
		return md5.new(self.admin_password).hexdigest() == adminhash
	
	def dbadmin_operation(self, func):
		def dbadmin_wrapper(adminhash, hostid, *args, **kwargs):
			if self.checkadmin(adminhash):
				return func(self.hostdb, hostid, *args, **kwargs)
			else:
				raise ServerNoAccess
		return dbadmin_wrapper
	
	# end admin stript functions
	
	def __init__(self, hostsdb_fn, admin_password, logfile = sys.stderr):
		"""
		Creates new instance of Server
		
		hostsdb_fn - path to hostdb database
		admin_password - administrator password (cleartext)
		logfile (default sys.stderr) - file descriptor for logging
		
		Server logic is simple each host represented as FSM:
		
			  
		NEW ---------> REGISTERED ---------> CONFIGURED
		 ^                                      |
		 |                                      |
		 +---------------------------------------
		 
		Host can register himself via register call or administrator can call "arhostadm create". State is set to New
		Then administrator configures host (set's it's extravars, hostname) and set state to Registered.
		 
		On host agent is run which constantly checks host state, when it sees that state of host is registered, it applies configuration and sets state to Configured, so on next boot it will not apply configuration until we have not reset FSM via unconfigure/register
		 
		RPC functions:
		 
		Available to all:
		check() - returns True (used for checking XML-RPC connection)
		get_host_list() - wrapper for HostsDB.read()
		get_host_info(hostid) - wrapper for HostsDB.select()
		get_state(hostid) - returns state of host
		 
		Administrator functions (have adminhash param, which must contain correct administrator password hash):
		create_host(adminhash, hostid, hostname) - wrapper for HostsDB.create
		set_hostname(adminhash, hostid, hostname) - wrapper for HostsDB.set_hostname
		set_state(adminhash, hostid, state) - wrapper for  HostsDB.set_state
		update_host(adminhash, hostid, varname, varval) - wrapper for HostsDB.update 
		delete_host(adminhash, hostid) - wrapper for HostsDB.delete
		
		Agent-specific functions:
		register(hostid, ipaddr) - registers new host if needed and returns it's state in database
		configure(hostid) - tells us that host has configured itself
		"""
		self.hostdb = HostsDB(hostsdb_fn)
		self.dispatcher = HostDBDispatcher()
		self.admin_password = admin_password
		self.logfile = logfile
		
		# Register functions
		self.dispatcher.register(self.check)
		
		self.dispatcher.register(self.get_host_list)
		self.dispatcher.register(self.get_host_info)
		self.dispatcher.register(self.get_state)
		
		self.dispatcher.register(self.register)
		self.dispatcher.register(self.configure)
		
		dbadminfuncs = {'create_host': HostsDB.create, 
						'set_hostname': HostsDB.set_hostname, 
						'set_state':   HostsDB.set_state, 
						'update_host': HostsDB.update, 
						'delete_host': HostsDB.delete }
		for funcname in dbadminfuncs:
			self.dispatcher.register(self.dbadmin_operation(dbadminfuncs[funcname]), funcname)
	
	def log(self, formatstr, *args):
		print >> self.logfile, formatstr % args
		
	def check(self):
		return True
	
	def get_host_list(self):
		return self.hostdb.read()
	
	def get_host_info(self, hostid):
		return self.hostdb.select(hostid)
		
	def get_state(self, hostid):
		return self.hostdb.select(hostid)[HostRowID.State]

	def register(self, hostid, ipaddr):
		try:
			hostdata = self.hostdb.select(hostid)
			
			if hostdata[HostRowID.IPAddress] != ipaddr:
				self.log("Host %s has changed ip address" % (ipaddr))
				self.hostdb.set_ipaddr(hostid, ipaddr);
				self.hostdb.set_state(hostid, HostState.Registered);
			
			# OK, it is known host, return it's data
			return hostdata[HostRowID.State]
		except HostNotFoundError:
			# It is first attempt to register host, 
			# return None and add hostdata to DB
			self.log("Host %s is fresh host, hostname %s" % (hostid, ipaddr))
			self.hostdb.create(hostid, '');
			self.hostdb.set_ipaddr(hostid, ipaddr);
			
			return HostState.New;
	
	def configure(self, hostid):
		self.hostdb.set_state(hostid, HostState.Configured);
	
	def run(self, ipaddr, port):
		self.server = SimpleXMLRPCServer((ipaddr, port), logRequests=False, allow_none=True);
		self.server.register_instance(self.dispatcher)
		self.server.serve_forever()
		
		