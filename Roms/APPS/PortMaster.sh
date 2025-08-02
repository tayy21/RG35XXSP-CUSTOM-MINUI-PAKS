#!/bin/bash

progdir=$(cd $(dirname "$0"); pwd)

program="python3 ${progdir}/port_master/main.py"
log_file="${progdir}/port_master/log.txt"

$program > "$log_file" 2>&1