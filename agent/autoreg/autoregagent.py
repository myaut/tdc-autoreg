#!/usr/bin/python

# --------------------------------------------
# TDC hosts automatic registration v1.0
# 
# XML-RPC common agent functions
# Copyright (c) Sergey Klyaus, 2011
# Published under GPLv2 LICENSE
#
# Version 0.6
# --------------------------------------------

import xmlrpclib
import time
from datetime import datetime
import socket
import os
import sys

AR_LOCK_FILE = '/etc/autoreg.lock'
POLLTIME    = 15

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
        self.proxy = xmlrpclib.ServerProxy("http://%s:%s" % (server, port))
        
    def register(self, hostid, ipaddr):
        failed_print = False
        
        while True:
            try:
                state = self.proxy.register(hostid, ipaddr)
            except socket.error as e:
                if not failed_print:
                    print >> sys.stderr, "Cannot connect to server, will retry in %ds: %s" % (POLLTIME, e)
                    failed_print = True
                time.sleep(POLLTIME)
                continue
            except xmlrpclib.ProtocolError as e:
                raise HostServerError("Protocol error: %s" % e)
            
            if state == HostState.New:
                # Waiting for configuration on HostDBServer
                time.sleep(POLLTIME)
            elif state == HostState.Registered:
                # Found configuration!
                if not os.path.exists(AR_LOCK_FILE):
                    # Create lock file
                    lkfile = file(AR_LOCK_FILE, 'w')
                    lkfile.write(datetime.now().strftime('%Y.%m.%d.%H.%M'))
                    
                    # Than return host's data
                    return self.proxy.get_host_info(hostid)
                else:
                    # To reconfigure, let user remove lockfile first
                    
                    raise HostAlreadyConfigured("Host is already configured")
            elif state == HostState.Configured:
                raise HostAlreadyConfigured("Host is already configured")
            else:
                raise HostServerError("Internal server error")
        
    def configure(self, hostid):
        self.proxy.configure(hostid)