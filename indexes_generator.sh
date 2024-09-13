#!/bin/bash

# Array of French educational levels
dirnames=("06.sixieme" "05.cinquieme" "04.quatrieme" "03.troisieme" "02.seconde" "01.premiere" "00.terminale")
levels=("Sixieme" "Cinquieme" "Quatrieme" "Troisieme" "Seconde" "Premiere" "Terminale")
numbers=("00" "01" "02" "03" "04" "05" "06" )

# Create index for each level
for dir in "${levels[@]}"; do
    cd "$dir"
    tree -H '.' -L 2 --noreport --dirsfirst -T "Cours de Maths/$dir" --charset utf-8 -I "index.html" -o index.html
    cd ../
    echo "Created index: $dir"
done

tree -H '.' -L 1 --noreport --dirsfirst -T 'Cours de Maths/Choix du niveau' -d --charset utf-8 -I "index.html" -o index.html
# sed -i 's|<a href="./\([^"]*\)/">|\<a href="./\1/index.html">|g' index.html

echo "All indexes created successfully."
