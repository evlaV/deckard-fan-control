#! /bin/bash

watch -n 1 "head -n 1 /var/log/deckard-fan-control.log && tail -n 20 /var/log/deckard-fan-control.log"
