# CLAUDE.md

Site statique de cours de maths (collège), servi via GitHub Pages depuis `main`
(dépôt `mathematovitch/mathematovitch.github.io`, organisation créée le
2026-10-24 ; l'ancienne adresse `outerovitch-maths.github.io` est un dépôt
séparé du compte personnel qui ne fait que rediriger chaque chemin vers la
nouvelle, via `index.html` + `404.html` : les QR codes déjà imprimés restent
valables, ne pas supprimer ce dépôt). Voir `README.md` pour
la vue d'ensemble de l'arborescence (`Progressions/`, `Sixieme/`, `Quatrieme/`,
`Utils/`).

## Organisation du dépôt (rangée le 2026-10-24, demande de l'utilisateur)

Racine minimale : `index.html` et `404.html` (générés ; **GitHub Pages impose
la racine**, ne pas les déplacer), `.nojekyll`, `build.sh` (seul point
d'entrée), README/CLAUDE.md. Ensuite :

- **Cours** : `Progressions/`, `Sixieme/`, `Quatrieme/`, `Utils/` — les
  **seuls** dossiers que le build touche (`SECTION_ORDER` / `sections()` de
  `tools/build.py`, `SECTIONS` de `build.sh`) : nettoyage, renommage,
  vignettes, index, legacy, `term/fs.json`. Tout autre dossier racine est
  invisible pour le build (`visible()` filtre la racine) : pas besoin de
  l'ajouter à une liste d'exclusion.
- `assets/` : `favicon.svg` + `favicon.ico` (16/32/64, secours), π pixel W95
  de `dev/pi.svg` ; `calculatrice.svg` (de `dev/calculatrice.svg`, viewBox
  recadré `5 2 22 28`) affichée à gauche du titre de l'accueil (`.brand`) ;
  `logo.svg`, `icons/`, `thumbs/` (généré). `todo/` garde son icône `todo.png`.
- `credits/index.html` (généré, URL `/credits/`).
- `term/`, `todo/`, `legacy/` : URLs publiques inchangées (`/term`, `/todo`,
  `/legacy`).
- `tools/` : `build.py`, `profkey.py` (clé du mode prof), `hooks/pre-commit`, `check_nomenclature.py` et `check_links.py` (lancés en fin de `build.sh`, avertissement seulement), `title.txt` (bandeau ASCII
  du legacy). `build.py` calcule `ROOT` depuis son propre emplacement
  (`tools/..`).
- Non suivis (`.gitignore`) : `dev/`, et les fichiers vides que le sandbox de
  Claude Code crée à la racine (`.bashrc`, `.gitconfig`, `.idea`, `.claude/`…)
  — l'auto-commit « adding all » les avait poussés une fois.

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
  rendu HTML est fait par `../tools/build.py` : **tableau** (l'utilisateur ne veut
  pas de dépliement pour les progressions, il veut tout voir d'un coup), aux
  couleurs du site (thème clair), titre de séquence lié à
  `Sixieme/index.html#S{NN}-…`. Lancé directement, il relance `tools/build.py`.
- L'accueil affiche le logo `assets/logo.svg` (pixel-art « Mathématovitch »
  version Windows 95 : bleu marine/rouge, ombre tramée ; source
  `dev/mathematovitch-win95-clair.svg`, viewBox recadré au plus serré sur les
  pixels hors `<defs>` → `12 24 894 120` ; remplace l'ancien bandeau ASCII
  `tools/title.txt`), puis l'auteur, le collège (`AUTHOR`,
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
./build.sh             # nouveau site + legacy/ (ou python3 tools/build.py : nouveau site seul)
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
  `Prep` (préparation de séance) ; `build.py` les affiche en tête de séquence.
  Corrigé d'un `Ex`/`Act`/`DS` : **nom du sujet + `-Corr`**
  (`Ex-6C04-01-Nom.pdf` ↔ `Ex-6C04-01-Nom-Corr.pdf` ; choix de l'utilisateur,
  qui a remplacé l'ancien préfixe `Corr-`), affiché juste sous son sujet
  (`profkey.CORR`, `is_corr()`) ; `check_nomenclature.py` signale un corrigé
  sans sujet. Sujet et corrigé sont **toujours deux PDF
  séparés** (demande de l'utilisateur, 2026-10-27, pour imprimer). Anciens codes obsolètes rencontrés et convertis :
  `FA-` (fiche d'activité) → `Ex`, `FM-` (fiche méthode) → `Cours`.
- **Niveau** : un seul caractère — `6`/`5`/`4`/`3` pour le collège,
  `2`/`1`/`T` pour le lycée (Seconde/Première/Terminale).
- **`C{NN}`** : numéro de chapitre à deux chiffres, aligné sur le dossier
  parent `S{NN}-Nom/`.
- **Item** (optionnel) : suffixe séparé par un tiret pour désambiguïser
  plusieurs fichiers du même type/chapitre (ex. `Ex-6C09-16-Coefficient.pdf`,
  `Ex-4C02-4a-...`).
- Renommage effectué avec `git mv` (pas `mv`) pour préserver l'historique.

**Figures sources** : sous-dossier `images/` d'une séquence (exclu des index
via `EXCLUDE_DIRS` de `build.py`). Ex. `S04-Angles/images/Sesa-*-nb.pdf` :
figures Sésamath découpées (vectoriel, niveaux de gris via ghostscript) dans
`_Archive/pg_94.pdf`.

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
- **Fiches d'exercices** : une fiche = une compétence. Sujet avec rappel de
  leçon + exercice traité (exemple grisé) ; corrigé = la même feuille avec les
  réponses en rouge, dans un PDF à part. Convention des sources : `\feuille`
  écrite une fois, corps du document
  `\ifdefined\aveccorrige\corrigetrue\else\corrigefalse\fi \feuille` ;
  `compile_corriges()` de `build.py` compile `Ex-….pdf` (sujet) et
  `Ex-…-Corr.pdf` (avec `\def\aveccorrige{}`) quand le `.tex` est plus récent.
  Exception : le diaporama de calcul mental `Act-6C04-03` (sujet et corrigé
  alternés, projeté) n'est pas découpé.
- **Contrôles (`DS`)** : recto-verso, deux compétences par contrôle (une par
  face), 35 min, noté sur 40. En haut : en-tête avec la note, **grille de
  compétences juste dessous**, puis la consigne ; bandeau « Compétence … » en
  tête de chaque face. Même convention que les fiches : `DS-….pdf` (sujet) et
  `DS-…-Corr.pdf` compilés par le build. Modèle : `Sixieme/S04-Angles/DS-6C04-0[1-3]-*.tex`.
- **Grille de compétences** : Insuffisant / Fragile / Satisfaisant / Très
  satisfaisant (vocabulaire BO, jamais « Expert ») — macro `\competences` de
  `~/texmf/tex/latex/Mathdoc/mathdoc.sty`.
- **Angles** : les angles droits sont toujours codés (petit carré) ; pas
  d'exercice « vérifie à l'équerre ». L'angle **nul** fait partie des angles
  particuliers enseignés en 6e (avec aigu, droit, obtus, plat). Figures à
  mesurer en vraie grandeur (imprimer à 100 %).
- **Séances (`Prep`)** : pas d'ardoise, tout se fait dans le cahier
  d'exercices (calcul mental, activités, exercices). Les corrections (activités,
  exercices) ne sont **jamais projetées** : le professeur corrige au tableau et
  les élèves prennent la correction (pas d'autocorrection avec corrigé distribué). La trace écrite est
  **écrite au tableau et copiée** par les élèves (jamais projetée) : prévoir
  du temps (~15 min). Pas de « ticket de sortie ».

## Terminal web `term/` (`/term`, branche `termjs`)

Émulateur de shell en JS pur (modules ES, aucune dépendance) pour naviguer
dans les cours : reprise du side-project GitLab `dev/termjs/` (ignoré par git),
dont la roadmap est entièrement implémentée. Doc complète : section
« Terminal web » du `README.md` racine (l'ancien `term/README.md` y a été
fusionné le 2026-10-25, avec la roadmap du site). Alias dans `term/aliases.sh`
(syntaxe bash restreinte, lue par `js/aliases.js`).

- Seule source de données : **`term/fs.json`**, écrit par `build_term_fs()` de
  `build.py` (dossier → objet, fichier → taille ; `HIDDEN_EXT` inclus, que le
  terminal ne montre qu'en `sudo`). Généré, mais à committer (Pages ne lance
  pas le build). Pas d'API GitHub (quota de 60 req/h sans jeton).
- `term/` n'est pas une section de cours : ni index généré, ni listé dans
  le site, ni dans `fs.json` (qui ne contient que les sections).
- `sudo` : mot de passe du mode prof, vérifié par `unlock()` de
  `assets/prof.js` (voir « Mode élève / mode prof ») ; `open`/`cat` déchiffrent
  les chemins de la liste `enc` de `fs.json`.
- Messages d'erreur au format GNU en locale française (`Aucun fichier ou
  dossier de ce type`…). Tout texte affiché passe par `textContent`.
- Tests : Chromium ne tourne pas dans le sandbox (sockets interdits) ; la
  logique se teste sous Deno (`--location http://127.0.0.1:PORT/term/`), avec
  le serveur HTTP lancé **dans la même commande** (réseau non partagé entre
  commandes) et `--reload` (Deno met les imports HTTP en cache).

## Page CV `cv/` (`/cv/`, 2026-10-27)

`cv/index.html` écrit **à la main** (hors build, comme `term/`), thème
[Minimal](https://github.com/mathematovitch/minimal) (fork d'orderedlist/minimal) : `cv/stylesheets/styles.css`
copié tel quel (**CC BY-SA 3.0**, pas CC0 ; crédité dans `CREDITS` et en pied de page)
+ ajouts en fin de fichier (sections `<details>` dépliables) ; colonne de gauche
volontairement sobre (avatar, nom, poste, un lien vers les cours, sommaire en liste `ul.sommaire`). Mail seulement en pied de
page, non cliquable (`[at]`/`[dot]`) ; `<meta name="robots" content="noindex">`.
Sources : `~/work/08.Autre/Inspection-2026/CV-Colin-Outerovitch.tex` (dates de
référence) et le rapport DNL (`~/work/08.Autre/DNL/`). **Données perso : mail
seulement** (ni téléphone, ni adresse, ni date de naissance) ; pas de mention de la
certification DNL (choix de l'utilisateur). Lien depuis l'auteur de l'accueil
(`CV_DIR` de `build.py`). Avatar `cv/avatar.svg` : grille pixel 5×5 symétrique aux
couleurs du logo, fond transparent (variantes dans `dev/avatars/`).

## Mode élève / mode prof, documents prof chiffrés (2026-10-27)

Par défaut mode élève. **Documents prof** (`profkey.is_secret()` de
`tools/profkey.py`) : types `Seq`, `Prep`, `DS` (`PROF_TYPES`, toute
extension), les corrigés `…-Corr.*`, tout ce qui est sous un `_Archive/`, et les `.tex` contenant
`\ifcorrige`. Ils ne sont publiés que **chiffrés** (`X.enc`), à la demande de
l'utilisateur (le masquage seul ne lui suffisait pas) :

- Clé maître K dans `dev/prof.key` (local, jamais commitée) ; `assets/prof.json`
  (public) = K chiffrée en AES-GCM par PBKDF2-SHA256(mot de passe, 600 000).
  `X.enc` = `MVCH1` + IV + AES-GCM(K, X), IV = HMAC(K, chemin, sha256) ⇒
  déterministe (pas de faux diff). `python3 tools/profkey.py init|passwd|restore`
  (interactif : à faire lancer par l'utilisateur avec `!`). Plus de
  `SUDO_SALT`/`SUDO_HASH` ni de `term/passwd.py` (un hachage rapide public
  aurait permis la force brute).
- `build.py` : `encrypt_secrets()` (après `rename_all()`) chiffre ce qui a
  changé, supprime les `.enc` orphelins seulement dans un dossier qui a des
  documents prof en clair (clone neuf : rien), et réécrit le bloc généré de
  `.gitignore` (motifs fixes + chemin exact de chaque document prof). Le site
  liste `X.enc` sous le nom `X` (`base()`, `enc_attr()` → `data-enc`) ; un
  clone sans clé se construit à l'identique. Pas de vignette pour un document
  prof. Hook `tools/hooks/pre-commit` (`git config core.hooksPath tools/hooks`)
  : refuse un document prof en clair dans l'index — garde-fou pour `ag`.
- Navigateur : `assets/prof.js` (module ES, importé par chaque page via
  `wire()` et par le terminal) : `unlock()` (session
  `localStorage["mathematovitch-prof"]` = `{until, k}`, 2 h), `openEnc()`
  (onglet ouvert pendant le clic, puis URL `blob:` révoquée au bout d'1 min,
  demande de l'utilisateur : PC partagés), `decryptText()`, `quit()`
  (coupe aussi le sudo du terminal). `PROF_HEAD_JS` (dans `<head>`) pose
  `html.prof` ; `.prof` masqué sinon, `.eleve` masqué en mode prof (compteurs
  `ndocs()`). Fond rosé + bandeau `#profbar`. Archives : section `prof`, pages
  `_Archive/…` « Réservé au professeur » (`reserved()`).
- Exclus aussi du legacy (`tree -I`), `Disallow` dans `robots.txt` ; dans le
  terminal, préfixes `prof` de `fs.json` (dont `_Archive`) traités comme
  `HIDDEN_EXT`. Comme un vrai shell (demande de l'utilisateur, 2026-10-27) : `sudo cmd` =
  une commande en root ; `chroot` (ou `su`, `sudo -s`) = shell root (`state.root`,
  invite `root@` rouge) jusqu'à `exit`. La session prof sert de cache du mot de
  passe (pas redemandé pendant 2 h) mais ne rend pas root à elle seule ;
  `isRoot()` = `elevated || (root && active())`. Tab complète après `sudo`.
- **Ne jamais committer un document prof en clair.** L'historique a été purgé
  des versions en clair (2026-10-27, `git filter-branch`, sauvegarde
  `dev/backup-2026-10-27.git`).

## Design du site (`CSS` de `tools/build.py`)

Choix de l'utilisateur (2026-10-24) : **thème clair uniquement** (plus de mode
sombre), DA « brute old school » à la `tree -H` / web 1998, pas « vibe coded » :
Times, liens bleus soulignés (violets visités), traits noirs 1 px, pas
d'arrondis ni d'ombres douces, types en `[Cours]`, séquences `[+]`/`[−]`,
boutons gris en relief. Pas de barre du haut **sur l'accueil seulement**
(marge haute généreuse pour que la page respire) ; les autres pages gardent
le fil d'Ariane et le bouton « Accueil », que l'utilisateur aime bien. Icônes pixel Windows 95 dans `assets/icons/` (32×32,
renommées par usage : `cours.png`, `ds.png`, `dossier.png`…) via `icon(d, nom, taille)` : 32 px net (`pixelated`), 16 px lissé.
Source : pack itch.io de gdainti (zip dans `dev/`, numéroté ligne par ligne,
11 colonnes). Page `credits/` (liste `CREDITS` de `tools/build.py`, liée en pied de page) : y ajouter toute
nouvelle ressource tierce. Pied de page « mis à jour le … » : `updated(d)`, date git du
dernier commit touchant le contenu du dossier (pages générées exclues, sinon chaque build
changerait toutes les pages). Impression : bloc `@media print` du `CSS` + `PRINT_JS`
(déplie tous les `<details>` sur `beforeprint`, referme sur `afterprint`).

## Conventions générales

- Ne jamais committer sans demande explicite de l'utilisateur.
- Toujours utiliser des chemins/suppressions nommés explicitement plutôt que
  des jokers larges (`rm -f *.ext`) dans un dossier contenant des fichiers
  suivis par git.
- Point d'entrée : **`./build.sh`** (ex-`update_site.sh`, renommé à la
  demande de l'utilisateur). Il lance `tools/build.py` (nouveau site, à la racine),
  puis régénère **l'ancien site `tree` dans `legacy/`**
  (`mathematovitch.github.io/legacy/`), que l'utilisateur veut garder
  actif. `legacy/` ne contient que des `index.html` : `tree -H "/SECTION"`
  produit des liens absolus vers les vrais fichiers (pas de duplication), et
  les `sed` corrigent les liens (`/Sixieme./` → `/Sixieme/`, `../X/` →
  `./X/index.html`, « . » → `↰` vers `/legacy/index.html`). Les deux
  générateurs ne parcourent que les sections de cours.
- `tools/build.py` (Python stdlib, + `pdftoppm` pour les vignettes, `pdflatex`
  pour les progressions), en une passe : `_Archive` manquants, suppression des
  fichiers temporaires LaTeX, nettoyage des noms (accents/espaces),
  vignettes de la 1re page des PDF dans `assets/thumbs/` (cache par mtime,
  orphelines supprimées — `assets/thumbs/` est généré, ne pas l'éditer), puis un
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
