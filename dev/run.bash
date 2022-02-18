#!/bin/bash
## we're at /app
## code is edited live at "app/mount/"
# cd /app/sdk
## install backend - without dependencies: they have been installed at
## image creation
# pip3 install --no-dependencies -e .
## run the app
printf "\nRunning pub/sub sample application...\n"
## https://github.com/gorakhargosh/watchdog#shell-utilities
watchmedo auto-restart -d /app --patterns="*.py;*.crt;*.key;*.pem" \
--recursive -- python3 /app/common/basicPubSub.py \
-e a20qyadf9v1i2e-ats.iot.us-west-2.amazonaws.com -r /app/cert/root-CA.crt \
-c /app/cert/thing1.cert.pem -k /app/cert/thing1.private.key
