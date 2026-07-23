#!/bin/sh

if [ -f ./*/bin/activate ]; then
 source ./*/bin/activate
 python3 run.py
else
 echo"Virtual env does not exists, Run `bash setup.bash` first"
fi	
