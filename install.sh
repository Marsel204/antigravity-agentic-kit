#!/bin/sh
# Installs tools/skills; projects opt in with aek init.
set -eu
kit_dir=$(CDPATH= cd "$(dirname "$0")" && pwd)
exec python3 "$kit_dir/scripts/aek.py" install "$@"
