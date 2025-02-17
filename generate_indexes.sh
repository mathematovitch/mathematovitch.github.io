#!/bin/bash

## DELETE JUNK FILES ##

# Define the directory to start searching from (default is the current directory)
DIR=${1:-.}

# List of extensions considered as junk files
EXTENSIONS=("aux" "log" "out" "toc" "synctex.gz" "fls" "fdb_latexmk")

# Loop through each extension and delete the files
for ext in "${EXTENSIONS[@]}"; do
    find "$DIR" -type f -name "*.$ext" -exec rm -f {} +
done

echo "Deleted junk files"

## CREATE SUB-LEVELS INDEXES ##

# Initialize an empty array
dir_array=()

# Loop through all directories in the current directory and append to array
for dir in */; do
    # Remove the trailing slash from directory name
    dir_array+=("${dir%/}")
done

# Create index for each level
for dir in "${dir_array[@]}"; do
    cd "$dir"
    tree -H '.' -L 2 --noreport --dirsfirst -T "Cours de Maths/$dir" --charset utf-8 -I "index.html" -I "*.tex" -o index.html # Tree make sub-levels indexes
    sleep 0.25
    sed -i 's|<a href="././">.</a><br>|<a href="https://outerovitch-maths.github.io/">↰</a><br>|' index.html # Make href .. point to top-level index
    sed -i '/<p class="VERSION">/,/<\/p>/d' index.html # Remove the version information block
    cd ..
    echo "Created index: $dir"
done

## CREATE TOP-LEVEL INDEX ##

tree -H '.' -L 1 --noreport -T 'Cours de Maths' -d --charset utf-8 -o index.html # Tree make top-level index
sleep 0.25
sed -i 's|<a href="./\([^"]*\)/">|\<a href="./\1/index.html">|g' index.html # Make href point to sub-indexes
sleep 0.25
sed -i '/<head>/a<link rel="shortcut icon" type="image/x-icon" href="favicon.ico" />' index.html # Add the sum icon to HTML head
sed -i '/<p class="VERSION">/,/<\/p>/d' index.html # Remove the version information block
echo "Created general index"

echo "All indexes successfully created."
