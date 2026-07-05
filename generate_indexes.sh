#!/bin/bash

unset -f cd

DIR=${1:-.}
MAX_DEPTH=5

########################################
# DELETE LATEX JUNK FILES
########################################

EXTENSIONS=("aux" "log" "out" "toc" "synctex.gz" "fls" "fdb_latexmk")

for ext in "${EXTENSIONS[@]}"; do
    find "$DIR" -type f -name "*.$ext" -delete
done

echo "Deleted junk files"

########################################
# CLEAN FILENAMES / DIRECTORY NAMES
########################################

rename_safe() {

    local path="$1"

    local dir
    dir="$(dirname "$path")"

    local file
    file="$(basename "$path")"

    # Convert accents -> ASCII
    local cleaned
    cleaned=$(echo "$file" \
        | iconv -f UTF-8 -t ASCII//TRANSLIT \
        | sed -E '
            s/[[:space:]]+/_/g;
            s/[^A-Za-z0-9._-]/_/g;
            s/_+/_/g;
            s/^_//;
            s/_$//
        ')

    if [[ "$file" != "$cleaned" ]]; then

        local target="$dir/$cleaned"

        if [[ ! -e "$target" ]]; then
            mv "$path" "$target"
            echo "Renamed:"
            echo "  $path"
            echo "  -> $target"
        else
            echo "Skipped (already exists): $target"
        fi
    fi
}

export -f rename_safe

########################################
# RENAME FILES
########################################

find "$DIR" -depth -maxdepth "$MAX_DEPTH" \( -type f -o -type d \) \
    | while read -r item; do
        rename_safe "$item"
    done

echo "Renaming finished"

########################################
# CREATE SUB INDEXES
########################################

dir_array=()

for dir in */; do
    dir_array+=("${dir%/}")
done

for dir in "${dir_array[@]}"; do

    cd "$dir" || continue

    tree -H './' \
         -L 2 \
         --noreport \
         --dirsfirst \
         -T "Cours de Maths/$dir" \
         --charset utf-8 \
         -I "index.html|*.tex" \
         -o index.html

    sed -i \
        's|<a href="././">.</a><br>|<a href="https://outerovitch-maths.github.io/">↰</a><br>|' \
        index.html

    sed -i '/<p class="VERSION">/,/<\/p>/d' index.html

    cd ../ || exit

    echo "Created index: $dir"
done

########################################
# CREATE TOP INDEX
########################################

tree -H './' \
     -L 1 \
     --noreport \
     -T 'Cours de Maths' \
     -d \
     --charset utf-8 \
     -o index.html

sed -i \
    's|<a href="./\([^"]*\)/">|<a href="./\1/index.html">|g' \
    index.html

sed -i \
    '/<head>/a<link rel="shortcut icon" type="image/x-icon" href="favicon.ico" />' \
    index.html

sed -i '/<p class="VERSION">/,/<\/p>/d' index.html

echo "Created general index"

echo "All indexes successfully created."
