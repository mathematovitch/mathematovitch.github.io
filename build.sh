#!/bin/bash
# Construit les deux versions du site :
# 1. le nouveau site (racine) : build.py — nettoyage LaTeX, noms de fichiers,
#    vignettes PDF, progressions (PDF + HTML), index.html stylés ;
# 2. l'ancien site « tree » dans legacy/ (outerovitch-maths.github.io/legacy/).
#    Seuls ses index sont dans legacy/ : leurs liens pointent (en absolu, /Sixieme/...)
#    vers les mêmes fichiers que le nouveau site, rien n'est dupliqué.

unset -f cd
cd "$(dirname "$0")" || exit 1

python3 build.py "$@" || exit 1

LEGACY=legacy
EXCLUDE="dev|todo|legacy|thumbs"

########################################
# INDEX DES SECTIONS (legacy/SECTION/index.html)
########################################

sections=()
for dir in */; do
    name="${dir%/}"
    [[ "|$EXCLUDE|" == *"|$name|"* ]] && continue
    sections+=("$name")
done

for name in "${sections[@]}"; do
    out="$LEGACY/$name/index.html"
    mkdir -p "$LEGACY/$name"

    (cd "$name" && tree -H "/$name" \
         --noreport \
         --dirsfirst \
         -T "Cours de Maths/$name" \
         --charset utf-8 \
         -I "index.html|*.tex|*.sty" \
         -o "../$out")

    # tree colle le « . » du dossier courant au préfixe : /Sixieme./x -> /Sixieme/x
    sed -i "s|href=\"/$name\./|href=\"/$name/|g" "$out"

    # Lien racine « . » -> retour à l'accueil legacy
    sed -i \
        "s|<a href=\"/$name/\">.</a><br>|<a href=\"/$LEGACY/index.html\">↰</a><br>|" \
        "$out"

    sed -i '/<p class="VERSION">/,/<\/p>/d' "$out"

    # _Archive reste listé, mais sans son contenu
    sed -i "\|href=\"/$name/_Archive/[^\"]|d" "$out"

    echo "Index legacy : $name"
done

########################################
# INDEX RACINE (legacy/index.html)
########################################

tree -H '.' \
     -L 1 \
     --noreport \
     -T 'Cours de Maths' \
     -d \
     --charset utf-8 \
     -I "$EXCLUDE" \
     -o "$LEGACY/index.html"

# tree écrit les liens relativement au fichier de sortie (../Sixieme/) :
# on les redirige vers les index legacy (./Sixieme/index.html), « . » vers le nouveau site.
sed -i \
    -e 's|<a href="\.\./">\.</a>|<a href="/index.html">.</a>|' \
    -e 's|<a href="\.\./\([^"]*\)/">|<a href="./\1/index.html">|g' \
    "$LEGACY/index.html"

sed -i \
    '/<head>/a<link rel="shortcut icon" type="image/x-icon" href="/favicon.ico" />' \
    "$LEGACY/index.html"

sed -i '/<p class="VERSION">/,/<\/p>/d' "$LEGACY/index.html"

# Remplace le <h1> par défaut par le bandeau ASCII de .scripts/title.txt
if [[ -f .scripts/title.txt ]]; then
    python3 - "$LEGACY/index.html" <<'PYEOF'
import sys
path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    html = f.read()
with open('.scripts/title.txt', encoding='utf-8') as f:
    banner = f.read().rstrip('\n')
html = html.replace('<h1>Cours de Maths</h1>', f'<pre>\n{banner}\n</pre>')
with open(path, 'w', encoding='utf-8') as f:
    f.write(html)
PYEOF
fi

echo "Site legacy généré dans $LEGACY/"
