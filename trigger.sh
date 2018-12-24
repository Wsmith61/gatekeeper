#!/bin/bash
/usr/bin/curl http://192.168.1.154/control?cmd=GPIO,4,1
sleep 1
/usr/bin/curl http://192.168.1.154/control?cmd=GPIO,4,0
