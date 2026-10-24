# Cours de Maths

Site statique regroupant les cours, exercices et documents de mathématiques (collège), généré et publié via GitHub Pages.

**Voir le site en ligne : https://outerovitch-maths.github.io/**

## Architecture

Le site est une simple arborescence de fichiers (PDF, `.tex`, HTML) navigable via des pages d'index générées automatiquement. Chaque dossier contient un `index.html` produit par `build.py` (fil d'Ariane, séquences repliables, recherche, aperçu de la 1re page des PDF au survol).

```
.
├── index.html, 404.html # Accueil et page d'erreur (générés ; GitHub Pages les veut à la racine)
├── build.sh             # Point d'entrée unique : tools/build.py puis legacy/
├── Progressions         # Progressions annuelles par niveau (sources .tex → PDF + HTML)
├── Sixieme              # Cours/exercices de 6e, organisés par séquence (S01, S02, ...)
├── Quatrieme            # Cours/exercices de 4e, organisés par séquence (S01, S02, ...)
├── Utils                # Documents utilitaires (grilles, tables, suivi corrections, DNL)
├── assets               # Ressources du site : logo.svg, favicon.ico, icons/ (pixel W95), thumbs/ (vignettes générées)
├── credits              # Page crédits & liens (générée)
├── term                 # Terminal web (/term) : naviguer dans les cours avec ls, cd, open...
├── todo                 # Listes de tâches (/todo), page autonome
├── legacy               # Ancien site « tree » (index seulement), généré par build.sh
└── tools                # build.py (générateur), check_nomenclature.py, title.txt
```

Seuls les dossiers de cours (Progressions, niveaux, Utils) sont traités par le build :
nettoyage, renommage, vignettes, index, terminal. Le reste du dépôt n'est jamais modifié.

### Contenu par section

- **Progressions** : progressions pédagogiques annuelles (6e, 5e, 4e, 3e, Seconde, Première, Terminale) au format HTML/PDF.
- **Sixieme / Quatrieme** : une sous-page par séquence (`S01-...`, `S02-...`, ...), chacune contenant les fiches de cours (`Cours-...`), exercices (`Ex-...`) et devoirs surveillés (`DS-...`) au format PDF (sources `.tex` parfois incluses).
- **Utils** : documents transverses (grilles de multiplication à imprimer, suivi des corrections, dossier DNL en anglais).

### Génération des index

`./build.sh` (ou `python3 tools/build.py` pour le nouveau site seul) :
1. supprime les fichiers indésirables générés par LaTeX (`.aux`, `.log`, `.toc`, ...) ;
2. nettoie les noms de fichiers/dossiers (accents, espaces, caractères spéciaux) ;
3. génère les vignettes des PDF dans `assets/thumbs/` (nécessite `pdftoppm`, paquet poppler ; seuls les PDF nouveaux ou modifiés sont rendus) ;
4. recompile les progressions (`Progressions/NIVEAU.pdf`) si leur `.tex` a changé ;
5. régénère l'`index.html` de chaque dossier, l'accueil et la page 404, et `term/fs.json` (arborescence lue par le terminal web, voir `term/README.md`) ;
6. (`build.sh` seulement) régénère l'ancien site `tree` dans `legacy/`, accessible sur `/legacy/`.

## Déploiement

Le site est servi directement depuis la branche `main` du dépôt via GitHub Pages (dépôt `outerovitch-maths/outerovitch-maths.github.io`).
