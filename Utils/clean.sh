#!/bin/bash

## DELETE JUNK FILES ##

# Define the directory to start searching from (default is the current directory)
DIR=${1:-.}

# List of extensions considered as junk files
EXTENSIONS=("aux" "log" "out" "toc" "synctex.gz" "fls" "fdb_latexmk")

declare -i count=0

# Loop through each extension and delete the files
for ext in "${EXTENSIONS[@]}"; do
    # Count the files before deleting them
    files_deleted=$(find "$DIR" -type f -name "*.$ext" -print -delete | wc -l)
    # Add the number of deleted files to the total count
    count=$((count + files_deleted))
done

echo "Deleted $count junk files"
