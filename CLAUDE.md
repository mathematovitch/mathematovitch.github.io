# CLAUDE.md

Site statique de cours de maths (collège), servi via GitHub Pages depuis `main`
(dépôt `outerovitch-maths/outerovitch-maths.github.io`). Voir `README.md` pour
la vue d'ensemble de l'arborescence (`Progressions/`, `Sixieme/`, `Quatrieme/`,
`Utils/`).

## Sous-système `Progressions/` : source LaTeX → HTML généré

Les pages `Progressions/{6eme,5eme,4eme,3eme}.html` ne sont plus éditées à la
main : elles sont **générées** depuis des sources `.tex` du même nom, pour
éviter d'éditer du HTML brut avec entités (`&eacute;`...) sous Emacs.

- **`Progressions/progtable.sty`** : package LaTeX autonome (pas de
  dépendance externe type pandoc/make4ht — non installés sur cette machine,
  seul `pdflatex` l'est). Fournit `\progheader{Nom long}{Label court}`,
  l'environnement `proglist` (table `longtable`), et la macro
  `\seq{ID}{Titre}{Thème}{Objectif}{ \item ... \item ... }` qui construit
  **toute une ligne de tableau en un seul appel de macro**.
- **`Progressions/{niveau}.tex`** : une source par niveau, texte UTF-8 réel
  (é, è, —, …, ℕ, ℤ, ×, −, ² écrits directement, pas d'entités HTML/LaTeX).
  Codes de compétence uniques au format `{niveau}C{NN}-{THEME}{NN}`
  (ex. `6C01-NUM01`), numérotation continue par thème sur tout le niveau.
- **`Progressions/gen_html.py`** : script Python 3 stdlib-only (pas de TeX
  exécuté) qui parse `\progheader{...}` et les blocs `\seq{...}{...}{...}{...}{...}`
  par un parseur de groupes `{ }` à profondeur (pas de regex naïve, les
  arguments peuvent contenir des accolades), découpe le 5e argument sur
  `\item`, et réémet le HTML avec le template sobre (mono, noir/blanc) déjà
  utilisé par 6e/4e. Idempotent.

### Workflow

```
# éditer Progressions/NIVEAU.tex sous Emacs (AUCTeX), puis :
python3 Progressions/gen_html.py            # régénère tous les NIVEAU.html
python3 Progressions/gen_html.py 6eme.tex   # ou un seul niveau
pdflatex Progressions/NIVEAU.tex            # optionnel : PDF imprimable
```

### Pièges LaTeX rencontrés (`progtable.sty`)

- `\newcommand{\endseq}` est **toujours illégal** en LaTeX : le préfixe
  `\end...` est réservé, même sans environnement `seq` déclaré.
- Dans un `\newenvironment`, le code de fin n'a **pas accès direct** aux
  `#n` du code de début — il faut stocker via `\def` dans le begin-code.
- Plus fondamental : avec des colonnes `p{}` dans un `longtable`, **une
  même ligne de tableau ne peut pas être construite par deux appels de
  macro séparés** (`\halign` ne le supporte pas). D'où le choix final :
  `\seq` est une simple `\newcommand` à 5 arguments qui émet toute la
  ligne (`&`, `\\`, `\hline` compris) d'un coup — pas d'environnement.
- `\DeclareUnicodeCharacter` (dans `progtable.sty`) mappe les caractères
  Unicode bruts non couverts par `utf8.def` (ℕ U+2115, ℤ U+2124, − U+2212)
  vers leur rendu LaTeX, pour que le même texte source compile avec
  `pdflatex` **et** soit recopié tel quel par `gen_html.py`.

### Points d'attention

- `update_site.sh` exclut `*.tex` et `*.sty` de l'index `tree` généré
  (`-I "index.html|*.tex|*.sty"`) — ne pas retirer ce filtre.
- Compiler avec `pdflatex` produit des `.aux`/`.log`/`.pdf` dans
  `Progressions/` ; seul `Progression_6eme_2025_2.pdf` (fichier suivi,
  préexistant) est un livrable voulu. Ne pas supprimer avec un joker large
  (`rm -f *.pdf`) : ça a déjà effacé ce fichier par erreur une fois (récupéré
  via `git restore`). Nettoyer nommément les artefacts de test.
- `premiere.html`, `seconde.html`, `terminale.html` restent vides
  volontairement (hors périmètre, pas de dossiers de cours correspondants).
- `5eme.tex`/`3eme.tex` ont été renumérotés (`5C0N`/`3C0N`) par rapport à
  l'ancien template coloré (codes non uniques) ; `6eme.tex`/`4eme.tex`
  reprennent tels quels les codes déjà en usage dans `Sixieme/`, `Quatrieme/`.

## Nomenclature des fichiers de cours (`Sixieme/`, `Quatrieme/`)

Tous les fichiers de cours suivent le format
`{Type}-{Niveau}C{NN}[-{Item}]-{Nom-Descriptif}.ext` (ex. `Cours-6C01-...`,
`Ex-4C02-1a-Calcul.pdf`, `DS-6C05-1-...`).

- **Type** : `Cours` (leçon), `Ex` (exercice), `Act` (activité), `DS` (devoir
  surveillé/évaluation). Anciens codes obsolètes rencontrés et convertis :
  `FA-` (fiche d'activité) → `Ex`, `FM-` (fiche méthode) → `Cours`.
- **Niveau** : un seul caractère — `6`/`5`/`4`/`3` pour le collège,
  `2`/`1`/`T` pour le lycée (Seconde/Première/Terminale).
- **`C{NN}`** : numéro de chapitre à deux chiffres, aligné sur le dossier
  parent `S{NN}-Nom/`.
- **Item** (optionnel) : suffixe séparé par un tiret pour désambiguïser
  plusieurs fichiers du même type/chapitre (ex. `Ex-6C09-16-Coefficient.pdf`,
  `Ex-4C02-4a-...`).
- Renommage effectué avec `git mv` (pas `mv`) pour préserver l'historique.

**Contenu tiers à ne jamais renommer** (reconnaissable à ces motifs) :
`mathsenligne/*`, `Sesa-NN-*` (ressources Sésamath), `pg_NN.pdf` (pages de
manuel scanné), `Chapitre_N_-_Nom.pdf` (extraits de manuel). Les fichiers
manifestement vides ou artefacts d'éditeur (ex. `region_.tex`, cache de
TeXstudio) sont aussi à laisser tels quels.

Point d'attention : du contenu peut être dupliqué à l'identique (vérifié
byte-à-byte via `md5sum`) entre deux niveaux différents — constaté entre
`Quatrieme/S12-Probabilites` et `Sixieme/S14-Probabilites`. Renommer selon
le niveau du dossier où le fichier se trouve réellement ; ne pas tenter de
dédupliquer sans consulter l'utilisateur.

## Conventions générales

- Ne jamais committer sans demande explicite de l'utilisateur.
- Toujours utiliser des chemins/suppressions nommés explicitement plutôt que
  des jokers larges (`rm -f *.ext`) dans un dossier contenant des fichiers
  suivis par git.
- Le script actif de génération des index est `update_site.sh` à la racine
  du dépôt (renommé depuis `generate_indexes.sh` car il fait bien plus que
  générer des index : nettoyage LaTeX, renommage de fichiers, index ; pas
  de `sleep` : `tree -o` et `sed -i` sont synchrones). Les anciens scripts
  redondants sous `Utils/` (`autogit.sh`, `clean.sh`, `copy_template.sh`,
  `generate_indexes.sh`, `goto_dir.sh`, `new_chapter.sh`) ont été supprimés
  car obsolètes — ne pas les recréer.
