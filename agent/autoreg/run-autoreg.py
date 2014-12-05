#!/usr/bin/python

# --------------------------------------------
# TDC hosts automatic registration v1.1
# 
# Basic Solaris 11 / Linux agent for VirtualBox
# Copyright (c) Sergey Klyaus, 2011, 2014
# Published under GPLv2 LICENSE
# --------------------------------------------

import os
import sys
import re
import subprocess
import shutil

import autoregagent
import select

SERVER_IPADDR = 'r520.tdc'
SERVER_PORT = 8765
AR_SUFFIX='.ar_orig'

def log(fmtstr, *args):
    subprocess.call(["logger", "-p", "daemon.notice", "TDC Autoreg: " + (fmtstr % args)])       

def backup_config(path):
    if not os.path.exists(path + AR_SUFFIX):
        shutil.copy(path, path + AR_SUFFIX)
    
def get_info():
    if sys.platform == 'sunos5':
        ethname = 'net0'
        ifcfg = subprocess.Popen(("/usr/sbin/ifconfig", ethname), 
                                 stdout=subprocess.PIPE)    
    elif sys.platform == 'linux2':
        ethname = 'eth0'
        ifcfg = subprocess.Popen(("ip", "addr", "show", "dev", ethname), 
                                 stdout=subprocess.PIPE)
    
    ifcfg_out = ifcfg.stdout.read()
    
    ipaddr = re.findall( "inet\s+([0-9.]+)", ifcfg_out)[0]
    hostid = re.findall( "ether\s+([0-9a-f:]+)", ifcfg_out)[0]
    
    # Convert mac address
    hostid = ''.join(["%02X" % int(tetr, 16) for tetr in hostid.split(':')])
    
    return (hostid, ipaddr)

def update_hostname(hostname):
    if sys.platform == 'sunos5':
        hosts_path = '/etc/inet/hosts'
        
        nf = file('/etc/nodename', 'w')
        nf.truncate()
        print >> nf, hostname
        
        # Also update SMF on solaris 11
        svccfg = subprocess.call(('svccfg', '-s', 'node', 
                                  'setprop', 'config/nodename', 
                                  '=', '"%s"' % hostname))     
        svcadm = subprocess.call(('svcadm', 'refresh', 'node'))
    elif sys.platform == 'linux2':
        hosts_path = '/etc/hosts'
        
        if os.stat('/usr/bin/hostnamectl'):
            # RHEL/CentOS 7 are using systemd - so call hostnamectl directly
            
            hostnamectl = subprocess.call(('hostnamectl', 'set-hostname', hostname))
        else:            
            # On RHEL we update /etc/sysconfig/network
            path = '/etc/sysconfig/network'
            
            backup_config(path)
            orig_netcfg = file(path + AR_SUFFIX)
            netcfg = file(path, 'w')
            
            for l in orig_netcfg:
                if l.startswith('HOSTNAME'):
                    print >> netcfg, 'HOSTNAME=' + hostname
                else:
                    netcfg.write(l)
    
    hnlist = [hostname, hostname + '.local', 'localhost', 'loghost']
    
    # Save original host file
    backup_config(hosts_path)
    
    hf = file(hosts_path, 'w')
    hf.truncate()
    print >> hf, "# Automatically created by autoreg"
    print >> hf, '::1\t\t' + '\t'.join(hnlist)
    print >> hf, '127.0.0.1\t\t' + '\t'.join(hnlist)

def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError, e:
        print >> sys.stderr, str(e)
        sys.exit(1)
    
def reboot():
    if sys.platform == 'sunos5':
        subprocess.call('shutdown -i6 -y', shell=True)
    else:
        subprocess.call('reboot')
        
(hostid, ipaddr) = get_info()
agent = autoregagent.HostAgent(SERVER_IPADDR, SERVER_PORT)

daemonize()

try:    
    data = agent.register(hostid, ipaddr)
    update_hostname(data[autoregagent.HostRowID.HostName])
    agent.configure(hostid)
    log("Configured hostname %s, restarting", data[autoregagent.HostRowID.HostName])
    reboot()
except autoregagent.HostAlreadyConfigured:
    log("Already configured")
    
    # Eternally sleep
    select.select([], [], [])