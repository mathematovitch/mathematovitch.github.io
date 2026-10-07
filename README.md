# Cours de Maths

Site statique regroupant les cours, exercices et documents de mathématiques (collège), généré et publié via GitHub Pages.

**Voir le site en ligne : https://outerovitch-maths.github.io/**

## Architecture

Le site est une simple arborescence de fichiers (PDF, `.tex`, HTML) navigable via des pages d'index générées automatiquement. Chaque dossier contient un `index.html` produit par `build.py` (fil d'Ariane, séquences repliables, recherche, aperçu de la 1re page des PDF au survol).

```
.
├── index.html          # Page d'accueil (liste des sections)
├── Progressions        # Progressions annuelles par niveau (6e à Terminale)
├── Sixieme              # Cours/exercices de 6e, organisés par séquence (S01, S02, ...)
├── Quatrieme             # Cours/exercices de 4e, organisés par séquence (S01, S02, ...)
├── Utils                # Documents utilitaires (grilles, tables, suivi corrections, DNL)
├── thumbs               # Vignettes des PDF (générées par build.py)
├── build.py             # Construction du site : nettoyage, vignettes, index.html
├── legacy               # Ancien site « tree » (index seulement), généré par build.sh
├── build.sh             # Point d'entrée : build.py puis legacy/
└── favicon.ico
```

### Contenu par section

- **Progressions** : progressions pédagogiques annuelles (6e, 5e, 4e, 3e, Seconde, Première, Terminale) au format HTML/PDF.
- **Sixieme / Quatrieme** : une sous-page par séquence (`S01-...`, `S02-...`, ...), chacune contenant les fiches de cours (`Cours-...`), exercices (`Ex-...`) et devoirs surveillés (`DS-...`) au format PDF (sources `.tex` parfois incluses).
- **Utils** : documents transverses (grilles de multiplication à imprimer, suivi des corrections, dossier DNL en anglais).

### Génération des index

`./build.sh` (ou `python3 build.py` pour le nouveau site seul) :
1. supprime les fichiers indésirables générés par LaTeX (`.aux`, `.log`, `.toc`, ...) ;
2. nettoie les noms de fichiers/dossiers (accents, espaces, caractères spéciaux) ;
3. génère les vignettes des PDF dans `thumbs/` (nécessite `pdftoppm`, paquet poppler ; seuls les PDF nouveaux ou modifiés sont rendus) ;
4. recompile les progressions (`Progressions/NIVEAU.pdf`) si leur `.tex` a changé ;
5. régénère l'`index.html` de chaque dossier, l'accueil et la page 404 ;
6. (`build.sh` seulement) régénère l'ancien site `tree` dans `legacy/`, accessible sur `/legacy/`.

## Déploiement

Le site est servi directement depuis la branche `main` du dépôt via GitHub Pages (dépôt `outerovitch-maths/outerovitch-maths.github.io`).
