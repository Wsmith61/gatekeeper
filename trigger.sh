#!/bin/bash
/usr/bin/curl http://192.168.1.154/control?cmd=GPIO,4,1
sleep 1
/usr/bin/curl http://192.168.1.154/control?cmd=GPIO,4,0
/usr/bin/curl -i -XPOST 'http://192.168.1.16:8086/write?db=collectdb' --data-binary 'gate_opened value=1'
