#!/bin/sh
# Starts the core. The data folder is the volume /var/lib/salvia-vpn.
# The first start opens the panel and the proxy to the network
# (salvia-vpn-core -setup-server) and prints the logins.
set -eu

data=/var/lib/salvia-vpn
mkdir -p "$data"
if [ ! -f "$data/config.json" ]; then
  salvia-vpn-core -data-dir "$data" -setup-server=-
fi
exec salvia-vpn-core -plain -data-dir "$data"
