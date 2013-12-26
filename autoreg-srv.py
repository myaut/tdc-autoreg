#!/usr/bin/python -W ignore::DeprecationWarning

from autoreg.server import HostDBServer

# --------------------------------------------
# TDC hosts automatic registration v1.0
# 
# Main server module
# Copyright (c) Sergey Klyaus, 2011
# Published under GPLv2 LICENSE
#
# Version 0.5
# --------------------------------------------

SERVER_IPADDR = '0.0.0.0'
SERVER_PORT = 8765
SERVER_ADMINPASSWORD = 'default'
HOSTDB_NAME = 'hostsdb.dat'

if __name__ == '__main__':
	server = HostDBServer(HOSTDB_NAME, SERVER_ADMINPASSWORD)
	server.run(SERVER_IPADDR, SERVER_PORT)