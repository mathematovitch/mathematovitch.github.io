#!/bin/sh

filesToPush=$(git status --porcelain | sed "s/^...//")

if [ "$1" = "a" ]; then
    git add .
    git commit -m "adding $file ✓"
    git push
elif [ "$1" = "m" ]; then
    git add .
    git commit -m "modifying $file ✓"
    git push
elif [ "$1" = "d" ]; then
    git add .
    git commit -m "deleting $file ✓"
    git push
elif [ -z "$1" ]; then
    git add .
    git commit -m "adding all"
    git push
else
    printf "Invalid argument: Use 'a' for adding, 'm' for modifying, 'd' for deleting.\n" >&2
    exit 1
fi
