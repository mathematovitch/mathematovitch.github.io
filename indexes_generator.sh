#!/bin/bash

# Initialize an empty array
dir_array=()

# Loop through all directories in the current directory and append to array
for dir in */; do
    # Remove the trailing slash from directory name
    dir_array+=("${dir%/}")
done

# Define the directory to start searching from (default is the current directory)
DIR=${1:-.}

# List of extensions you consider as "junk" files
EXTENSIONS=("aux" "log" "out" "toc" "synctex.gz" "fls" "fdb_latexmk")

# Loop through each extension and delete the files
for ext in "${EXTENSIONS[@]}"; do
    find "$DIR" -type f -name "*.$ext" -exec rm -f {} +
done

echo "Deleted junk files!"

# Create index for each level
for dir in "${dir_array[@]}"; do
    cd "$dir"
    tree -H '.' -L 2 --noreport --dirsfirst -T "Cours de Maths/$dir" --charset utf-8 -I "index.html" -I "*.tex" -o index.html
    cd ../
    echo "Created index: $dir"
done

tree -H '.' -L 1 --noreport --dirsfirst -T 'Cours de Maths/Choix du niveau' -d --charset utf-8 -I "index.html" -o index.html
# sed -i 's|<a href="./\([^"]*\)/">|\<a href="./\1/index.html">|g' index.html
echo "Created general index"


echo "All indexes created successfully."
