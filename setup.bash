#!/bin/sh

VENVNAME="dashboard"

if [ -f ./*/bin/activate ]; then
  echo "========================================================"
  echo "[WARN] Virtual env already exists, i wont make a new one"
  echo "========================================================"
else
 if [ -f ./requirements.txt ]; then
  echo "============================================================="
  echo "[INFO] Creating a virtual env with name => $VENVNAME <= . . ."
  echo "============================================================="
  python3 -m venv $VENVNAME 
  echo "===================================================="
  echo "[INFO] Created a virtual env with name => $VENVNAME "
  echo "===================================================="
  source ./$VENVNAME/bin/activate
  pip install -r ./requirements.txt
  echo "===================================================="
  echo "[INFO] Installed the requirements in the virtual env"
  echo "===================================================="
 else
  echo "========================================"
  echo "[WARN] Cannot find the requirements file"
  echo "========================================"
 fi
fi

