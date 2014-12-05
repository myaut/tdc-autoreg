AutoReg
=======

How to Use
----------

This set of scripts is used to automatically configure Virtual Machines, cloned from OVA in VirtualBox.
Every cloned VM registers within AutoReg server to save it's IP address and takes it's hostname from server.

* You create OVA file with all needed software and AutoReg agent (note that server address is hardcoded on this step)
* VMs are cloned from OVA using gen-vbox-vms script:

```
# /opt/autoreg/gen-vbox-vms.py -i <path to ova> 	\
      -n <vm name prefix> -c <count> 			\
      -p <base port number for VRDE> 			\
      -s <server:port>
```

* When VM starts, and agent is run, it polls server, until it would be registered (done automatically by gen-vbox-vms). Also, agent updates hosts database with IP address that was assigned to VM by DHCP.
* Agent updates host configuration
	* Writes hostname
	* Creates file /etc/autoreg.lock that disables agent
	* Reboots VM
* You may reconfigure VM:

```
	$ arhostadm unconfigure 080027C91726
	$ arhostadm ... (reconfigure entry)
	$ arhostadm register 080027C91726
```

You may use extra vars 	to do additional configuration steps. Agent supports CentOS and Solaris 11.
	
How To Install
--------------

Edit run-autoreg.py and autoreg-srv.py (change listening address, server address, port, etc.)
Create distros (mkagent.sh and mkserver.sh) and upload them to Server and Master VM.

Install and run server
```
$ cd autoreg
$ tar xzvf ar-server.tar 
$ touch hostsdb.dat
$ ./autoreg-srv.py &
```

Check that autoreg is running
```
$ export PATH=$PATH:<autoreg path>
$ archeck
Server is alive
$ arhostadm list
No hosts in database
```

Install agent into VM
```
# mkdir -p /opt/autoreg
# cd /opt/autoreg
# tar xzvf ar-agent.tgz
```

On Solaris create startup script link:
```
# ln -s /opt/autoreg/S99autoreg /etc/rc3.d/
```

On Linux (RHEL-like) with SysVInit, register startup script with chkconfig:
```
# ln -s /opt/autoreg/autoreg /etc/init.d
# chkconfig --add autoreg
# chkconfig autoreg on
```

On Linux systems with systemd, register it:
```
# cp /opt/autoreg/autoreg.conf /etc/systemd/system/autoreg.service
# systemctl enable autoreg.conf
```
To start it immediately, run `systemd enable`:
```
# systemctl enable autoreg.service
```

Run VM and check that it receives state 'C' (configured) and adds its IP to database.
```
$ arhostadm list
              HOSTID             HOSTNAME           IPADDR STATE
-------------------- -------------------- ---------------- -----
        0800276823F8               java-1   192.168.50.185     C
        080027AFC52F               java-5   192.168.50.177     C
        080027BAFE62               java-4   192.168.50.186     C
        08002751F252          java-test-1   192.168.50.188     C

```

License
-------

GPLv2
