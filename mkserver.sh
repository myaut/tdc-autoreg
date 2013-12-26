#!/bin/bash

FILES="autoreg/server.py
       autoreg/cli.py
       autoreg/__init__.py
       archeck
       archeck.py
       arhostadm
       arhostadm.py
       gen-vbox-vms.py" 

tar czvf ar-server.tgz $FILES