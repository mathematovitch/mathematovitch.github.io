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
- **`Progressions/gen_html.py`** : désormais **parseur seul** (`parse_tex`,
  stdlib, pas de TeX exécuté) : `\progheader`, `\vacances` et blocs
  `\seq{...}{...}{...}{...}{...}` via un parseur de groupes `{ }` à
  profondeur (pas de regex naïve), 5e argument découpé sur `\item`. Le
  rendu HTML est fait par `../build.py` : **tableau** (l'utilisateur ne veut
  pas de dépliement pour les progressions, il veut tout voir d'un coup), aux
  couleurs du site (sombre/clair), titre de séquence lié à
  `Sixieme/index.html#S{NN}-…`. Lancé directement, il relance `build.py`.
- L'accueil affiche sous le bandeau ASCII l'auteur, le collège (`AUTHOR`,
  `SCHOOL`) et l'année scolaire (calculée, bascule au 1er août) ; toutes les
  pages portent la licence **CC0 1.0** en pied de page (choix de l'utilisateur : le plus ouvert
  possible), avec exclusion explicite des ressources tierces.
- **Compilation automatique** : à chaque run, `build.py` recompile
  `NIVEAU.pdf` (2 passes `pdflatex`, longtable) si `NIVEAU.tex` ou
  `progtable.sty` est plus récent que le PDF, puis supprime nommément
  `.aux/.log/.out`. `SOURCE_DATE_EPOCH` figé : même source ⇒ PDF identique
  à l'octet (pas de faux diff git après un pull qui touche les mtimes).
- Vacances : `\vacances{...}` présents en 6e et 4e (placement 4e proposé
  par Claude, 3/3/2/2/2 séquences, à ajuster) ; absents en 5e/3e.

### Workflow

```
# éditer Progressions/NIVEAU.tex sous Emacs (AUCTeX), puis :
./build.sh             # nouveau site + legacy/ (ou python3 build.py : nouveau site seul)
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

- `build.py` masque `*.tex`, `*.sty`, `*.py`… des index générés
  (`HIDDEN_EXT`) — ne pas retirer `.tex`/`.sty` de ce filtre.
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
  surveillé/évaluation). Côté enseignant : `Seq` (plan de séquence : séances,
  documents, toutes les évaluations y compris hors papier, ex. Capytale) et
  `Prep` (préparation de séance) ; `build.py` les affiche en tête de séquence. Anciens codes obsolètes rencontrés et convertis :
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

## Préférences pédagogiques (fiches, contrôles, séances)

Élèves de 6e en **REP+** : tout doit rester simple et court.

- **Énoncés courts** : une ligne de consigne par exercice. Les procédures de
  manipulation (pliage, etc.) sont expliquées à l'oral, jamais rédigées sur la
  fiche élève. Préférer des pointillés à compléter (ex. `<`, `>`, `=`) et plus
  d'items plutôt que du texte.
- **Fiches d'exercices** : une fiche = une compétence. Page 1 : sujet avec
  rappel de leçon + exercice traité (exemple grisé) ; page 2 : la même feuille
  avec les réponses en rouge (`\feuille` imprimée deux fois, `\ifcorrige`).
  Même principe pour un diaporama de calcul mental.
- **Contrôles (`DS`)** : recto-verso, deux compétences par contrôle (une par
  face), 35 min, noté sur 40. En haut : en-tête avec la note, **grille de
  compétences juste dessous**, puis la consigne ; bandeau « Compétence … » en
  tête de chaque face. Le PDF publié est le sujet seul (corrigé : passer
  `\corrigefalse` à `\corrigetrue`). Modèle : `Sixieme/S04-Angles/DS-6C04-0[1-3]-*.tex`.
- **Grille de compétences** : Insuffisant / Fragile / Satisfaisant / Très
  satisfaisant (vocabulaire BO, jamais « Expert ») — macro `\competences` de
  `~/texmf/tex/latex/Mathdoc/mathdoc.sty`.
- **Angles** : les angles droits sont toujours codés (petit carré) ; pas
  d'exercice « vérifie à l'équerre ». L'angle **nul** fait partie des angles
  particuliers enseignés en 6e (avec aigu, droit, obtus, plat). Figures à
  mesurer en vraie grandeur (imprimer à 100 %).
- **Séances (`Prep`)** : pas d'ardoise, tout se fait dans le cahier
  d'exercices (calcul mental, activités, exercices). La trace écrite est
  **écrite au tableau et copiée** par les élèves (jamais projetée) : prévoir
  du temps (~15 min). Pas de « ticket de sortie ».

## Conventions générales

- Ne jamais committer sans demande explicite de l'utilisateur.
- Toujours utiliser des chemins/suppressions nommés explicitement plutôt que
  des jokers larges (`rm -f *.ext`) dans un dossier contenant des fichiers
  suivis par git.
- Point d'entrée : **`./build.sh`** (ex-`update_site.sh`, renommé à la
  demande de l'utilisateur). Il lance `build.py` (nouveau site, à la racine),
  puis régénère **l'ancien site `tree` dans `legacy/`**
  (`outerovitch-maths.github.io/legacy/`), que l'utilisateur veut garder
  actif. `legacy/` ne contient que des `index.html` : `tree -H "/SECTION"`
  produit des liens absolus vers les vrais fichiers (pas de duplication), et
  les `sed` corrigent les liens (`/Sixieme./` → `/Sixieme/`, `../X/` →
  `./X/index.html`, « . » → `↰` vers `/legacy/index.html`). `legacy` et
  `thumbs` sont exclus des deux générateurs.
- `build.py` (Python stdlib, + `pdftoppm` pour les vignettes, `pdflatex`
  pour les progressions), en une passe : `_Archive` manquants, suppression des
  fichiers temporaires LaTeX, nettoyage des noms (accents/espaces),
  vignettes de la 1re page des PDF dans `thumbs/` (cache par mtime,
  orphelines supprimées — `thumbs/` est généré, ne pas l'éditer), puis un
  `index.html` stylé par dossier (plus de `tree`). L'accueil ouvre chaque
  section dans un nouvel onglet (choix voulu de l'utilisateur). La table
  `ACCENTS` de `build.py` recolle les accents perdus dans les titres
  affichés : y ajouter les mots manquants plutôt que renommer. Les pages de
  niveau suivent `Progressions/NIVEAU.tex` (lu via `gen_html.parse_tex`, sans
  dupliquer le parseur) : ordre et titres accentués de la progression,
  thème, objectif et compétences par séquence, séparateurs de vacances,
  séquences sans dossier affichées « à venir » (sauf `C9x`). Le lien se fait
  par le numéro : dossier `S{NN}-…` ↔ `\seq{6C{NN}}`. Les anciens scripts
  redondants sous `Utils/` (`autogit.sh`, `clean.sh`, `copy_template.sh`,
  `generate_indexes.sh`, `goto_dir.sh`, `new_chapter.sh`) ont été supprimés
  car obsolètes — ne pas les recréer.
