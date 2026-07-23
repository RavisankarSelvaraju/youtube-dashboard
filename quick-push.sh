#!/bin/bash

git add -A

if [ "$#" -gt 0 ]; then
    git commit -m "[quick-commit] $*"
else
    git commit -m "[quick-commit] update"
fi

git push
