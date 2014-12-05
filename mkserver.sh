#!/bin/bash

OUTDIR=$1
ARDIR=`dirname $0`

if [ ! -d "$OUTDIR" ]; then
    echo "Usage: mkserver.sh <output directory>" >&2
    exit 1
fi

OUTDIR=`realpath $OUTDIR`

FILES="autoreg/server.py
       autoreg/cli.py
       autoreg/__init__.py
       archeck
       archeck.py
       arhostadm
       arhostadm.py
       autoreg-srv.py
       gen-vbox-vms.py" 

(
    cd ${ARDIR}
    tar czvf ${OUTDIR}/ar-server.tgz $FILES
)