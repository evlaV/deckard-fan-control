#! /bin/bash
systemctl stop fancontrol
fanspeed 80
systemctl stop jupiter-fan-control
systemctl daemon-reload
systemctl enable --now jupiter-fan-control
journalctl -u jupiter-fan-control -f
