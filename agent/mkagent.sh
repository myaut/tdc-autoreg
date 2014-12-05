#!/bin/bash

OUTDIR=$1
ARDIR=`dirname $0`

if [ ! -d "$OUTDIR" ]; then
    echo "Usage: mkagent.sh <output directory>" >&2
    exit 1
fi

OUTDIR=`realpath $OUTDIR`

FILES="autoreg/autoregagent.py
       autoreg/run-autoreg.py
       autoreg/S99autoreg
       autoreg/autoreg
       autoreg/autoreg.conf" 

(
    cd ${ARDIR}
    tar czvf ${OUTDIR}/ar-agent.tgz $FILES
)