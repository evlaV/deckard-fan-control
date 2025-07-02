#! /bin/bash
# systemctl stop fancontrol
fanspeed 80
systemctl stop deckard-fan-control
systemctl daemon-reload
systemctl enable --now deckard-fan-control
journalctl -u deckard-fan-control -f
