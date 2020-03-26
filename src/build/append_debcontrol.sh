#!/bin/sh

# Appends to debian/control file.

# $1 -- Package path
# $2 -- File to append
# $3 -- Output path

# Print commands
set -x

rm -rf "$3"
dpkg-deb -R "$1" "$3"
cat "$2" >> "$3"/DEBIAN/control
dpkg-deb -b "$3"
