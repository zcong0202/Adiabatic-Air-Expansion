#!/bin/bash
foam_command=("$@")
set --
source /usr/lib/openfoam/openfoam2506/etc/bashrc
set -e
exec "${foam_command[@]}"
