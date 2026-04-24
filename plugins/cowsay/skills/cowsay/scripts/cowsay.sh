#!/bin/bash
set -e
# Run cowsay with custom text. Usage: cowsay.sh "message"
# Uses uvx so the cowsay package is run without installing or conflicting with a local cowsay/ dir.
MSG="${1:-Hello!}"
uvx cowsay -t "$MSG"
