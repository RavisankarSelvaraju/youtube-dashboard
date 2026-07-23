#!/bin/sh

VENVNAME="dashboard"

if [ -f ./*/bin/activate ]; then
  echo "Virtual env already exists, i wont make a new one"
else
 if [ -f ./requirements.txt ]; then
  python3 -m venv $VENVNAME -r requirements.txt 
  echo "created a virtual env with name => $VENVNAME "
 else
  echo "Cannot find the requirements file"
 fi
fi
