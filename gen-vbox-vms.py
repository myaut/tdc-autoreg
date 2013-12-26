#!/usr/bin/python

# Generate VBox things

from optparse import OptionParser
import sys
import subprocess
import re

class InternalErrorException:
	pass

def do_call(cmd):
	print "Executing %s" % cmd
	ret = subprocess.call(cmd, shell=True)
	if ret != 0:
		raise InternalErrorException

def get_vbox_macaddress(vmname):
	vbox = subprocess.Popen('VBoxManage showvminfo %s' % vmname, shell=True, stdout=subprocess.PIPE)
	vboxlines = vbox.stdout.readlines()
	
	for line in vboxlines:
		if 'NIC 1' in line:
			return re.findall('MAC:\s+([0-9A-Z]+),', line)[0]
            
optparser = OptionParser()

# Basic Options
optparser.add_option("-i", "--image", dest="image", metavar="IMAGE", 
			help=".ova image to import")
optparser.add_option("-n", "--name", dest="name", metavar="NAME", 
			help="VM's name prefix")
optparser.add_option("-c", "--count", dest="count", metavar="N", 
			default='1', help="VM's count")	
optparser.add_option("-p", "--portbase", dest="portbase", metavar="PORT", 
			default='4000', help="VM's VRDE base port")				
optparser.add_option("-s", "--server", dest="server", metavar="SERVER:PORT", 
            default='localhost:8765', help="Autoreg server")             
			
(opts, args) = optparser.parse_args()

if not opts.image or not opts.name:
	print >> sys.stderr, 'Wrong syntax'
	optparser.print_help()
	sys.exit(1)

do_call('archeck -s %s' % opts.server)

for i in range(1, int(opts.count) + 1):
	vmname = "%s-%s" % (opts.name, i)
	vrdeport = int(opts.portbase) + i
	
	print "Configuring %s (vrdeport: %s)" % (vmname, vrdeport)
	
	do_call("VBoxManage import %s --vsys 0 --vmname %s" % (opts.image, vmname))
	do_call("VBoxManage modifyvm %s --macaddress1 auto" % (vmname, ))
	do_call("VBoxManage modifyvm %s --vrdeport %d" % (vmname, vrdeport, ))
	do_call("VBoxManage modifyvm %s --vrde on" % (vmname, ))
	
	hostid = get_vbox_macaddress(vmname)
	do_call("arhostadm -s %s create %s %s" % (opts.server, hostid, vmname))
	do_call("arhostadm -s %s update %s vrdeport=%d" % (opts.server, hostid, vrdeport))
	do_call("arhostadm -s %s register %s" % (opts.server, hostid))