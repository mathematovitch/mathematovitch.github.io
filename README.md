# Mathématovitch — Cours de Maths

Site statique regroupant les cours, exercices et documents de mathématiques
(collège), généré par un script Python et publié via GitHub Pages.

**Voir le site en ligne : https://mathematovitch.github.io/**

---

## Ce que contient le site

| Page | Adresse | Rôle |
|---|---|---|
| Accueil | `/` | logo pixel W95, auteur, collège, année scolaire ; une carte par section (ouverte dans un nouvel onglet) ; « Récemment ajoutés » |
| Pages de niveau | `/Sixieme/`, `/Quatrieme/` | séquences repliables `[+]`/`[−]` dans l'ordre de la progression, avec thème, objectif et compétences ; documents groupés par type (`[Cours]`, `[Ex]`, `[DS]`…) ; recherche ; séparateurs de vacances ; séquences sans dossier affichées « à venir » ; `#` de chaque séquence : ouvre sa page et copie son adresse |
| Pages de séquence | `/Sixieme/S04-Angles/`… | la séquence seule, dépliée, compétences comprises, même style que la page de niveau (archives comprises) |
| Progressions | `/Progressions/` | progressions annuelles 6e, 5e, 4e, 3e en tableau HTML + PDF, générées depuis LaTeX |
| Autres dossiers | `…/index.html` | liste façon explorateur (dossiers puis fichiers), fil d'Ariane, bouton « Accueil » |
| Vignettes | (survol) | aperçu de la 1re page de chaque PDF |
| Crédits | `/credits/` | ressources tierces utilisées (icônes, police figlet…) |
| 404 | (toute adresse inconnue) | page d'erreur aux couleurs du site |
| Terminal | `/term/` | naviguer dans les cours avec `ls`, `cd`, `open`… (voir plus bas) |
| CV | `/cv/` | CV de l'auteur (thème [Minimal](https://github.com/mathematovitch/minimal), CC BY-SA 3.0), page écrite à la main ; lien depuis le nom de l'auteur sur l'accueil ; non indexé par les moteurs (`noindex`), mail en clair non cliquable |
| Todo | `/todo/` | listes de tâches façon org-mode, synchronisées par un Gist GitHub (jeton stocké dans le navigateur) |
| Ancien site | `/legacy/` | la version d'origine, pages `tree -H`, gardée active (sans les documents du mode prof) |

### Mode élève / mode prof

Par défaut, le site est en **mode élève** : cours, activités, exercices,
ressources. Un clic sur la **calculatrice** de l'accueil demande le mot de
passe (le même que le `sudo` du terminal) et passe en **mode prof** pour 2 h,
sur toutes les pages : fond rosé, bandeau rouge « MODE PROF » avec un bouton
« Quitter » (recliquer la calculatrice quitte aussi). S'affichent alors en
plus les évaluations (`DS`), les plans de séquence (`Seq`), les préparations
(`Prep`), les **corrigés** (`…-Corr.pdf`), chacun juste sous son exercice, son
activité ou son DS, et les **archives**. Le terminal suit le même mode : un
`sudo`/`chroot` réussi l'active, `sudo -k` ou « Quitter » le coupent.

**Documents prof chiffrés** : le dépôt public ne contient ces documents (et
les sources `.tex` à corrigé) que chiffrés, `X.enc` (AES-256-GCM). Le
navigateur les déchiffre lui-même au clic, une fois le mot de passe saisi
(`assets/prof.js`, WebCrypto) : pas de serveur, et aucune clé dans le code.
La clé des documents est dans `assets/prof.json`, chiffrée par le mot de
passe (PBKDF2, 600 000 itérations) : **tout repose sur le mot de passe**, à
choisir solide. Chez soi, les fichiers restent en clair (on les édite et
compile comme avant) : `build.sh` les chiffre et les liste dans `.gitignore`,
et un hook `pre-commit` (`tools/hooks/`) refuse tout commit qui en contiendrait
un en clair.

#### Mot de passe prof : un seul pour tout

Il n'y a **qu'un mot de passe** : celui du mode prof du site, du `sudo` du
terminal et du chiffrement des PDF prof, c'est le même. Derrière, deux
éléments :

- la **clé** K (32 octets aléatoires) qui chiffre réellement les documents :
  `dev/prof.key`, sur l'ordinateur seulement (`dev/` n'est pas dans git) ;
- `assets/prof.json` (public, commité) : cette clé chiffrée par le mot de
  passe. Changer le mot de passe ne réécrit que ce fichier : les `.enc` ne
  changent pas.

Commandes (interactives : à lancer soi-même dans un terminal, ou avec `!`
dans Claude Code) ; il faut le module Python `cryptography`
(paquet `python-cryptography`) :

```
python3 tools/profkey.py init      # une seule fois : crée la clé et choisit le mot de passe
python3 tools/profkey.py passwd    # changer le mot de passe
python3 tools/profkey.py restore   # autre ordinateur : clone + mot de passe = clé retrouvée
git config core.hooksPath tools/hooks   # active le garde-fou, dans chaque clone
```

Procédures :

1. **Changer le mot de passe** : `passwd` (ne demande pas l'ancien si
   `dev/prof.key` est présent), puis commit de `assets/prof.json` et push. L'ancien mot de passe ne
   marche plus dès que Pages a publié ; une session prof déjà ouverte dans un
   navigateur reste valable jusqu'à son expiration (2 h) ou « Quitter ».
2. **Nouvel ordinateur** : cloner, `restore` (demande le mot de passe et
   recrée `dev/prof.key`), `git config core.hooksPath tools/hooks`. Les
   documents prof en clair n'étant pas dans git, les recopier depuis l'ancien
   ordinateur pour les éditer (ou les ouvrir déchiffrés depuis le site).
3. **Mot de passe oublié** : tant que `dev/prof.key` existe sur l'ordinateur,
   `passwd` en pose un nouveau sans l'ancien. Sans ce fichier **et** sans le
   mot de passe, les `.enc` du dépôt sont perdus (seuls les originaux en
   clair de l'ordinateur restent) : **sauvegarder `dev/prof.key`** hors du
   dépôt (clé USB, gestionnaire de mots de passe).
4. **Ajouter un document prof** : le nommer selon la nomenclature (`DS-`,
   `Seq-`, `Prep-`, `…-Corr`) ou le ranger dans `_Archive/`, puis
   `./build.sh` : il est chiffré en `X.enc` et ajouté au `.gitignore` ; on
   commite le `.enc`, jamais l'original (le hook le refuse).

Toutes les pages portent la licence **CC0 1.0** en pied de page (ressources
tierces exclues, voir `/credits/`).

**Ancienne adresse** : `outerovitch-maths.github.io` est un dépôt séparé
(compte personnel) qui redirige chaque chemin vers la nouvelle adresse
(`index.html` + `404.html`) : les QR codes déjà imprimés restent valables.

### Design

Thème clair uniquement, style « web 1998 » assumé : Times, liens bleus
soulignés (violets une fois visités), traits noirs de 1 px, pas d'arrondis ni
d'ombres douces, boutons gris en relief, icônes pixel Windows 95
(`assets/icons/`). Pas de barre du haut sur l'accueil ; fil d'Ariane et bouton
« Accueil » sur les autres pages.

---

## Arborescence

```
.
├── index.html, 404.html # Accueil et page d'erreur (générés ; GitHub Pages les veut à la racine)
├── build.sh             # Point d'entrée unique : tools/build.py puis legacy/
├── Progressions/        # Progressions annuelles (sources .tex → PDF + HTML)
├── Sixieme/             # Cours de 6e, une séquence par dossier (S01-…, S02-…)
├── Quatrieme/           # Cours de 4e, idem
├── Utils/               # Documents transverses (grilles, tables, suivi des corrections, DNL)
├── assets/              # logo.svg, calculatrice.svg, favicon, icons/ (pixel W95), thumbs/ (vignettes générées)
├── credits/             # Page crédits (générée)
├── cv/                  # CV (/cv/), écrit à la main, hors build
├── term/                # Terminal web (/term)
├── todo/                # Listes de tâches (/todo), page autonome
├── legacy/              # Ancien site « tree » (index seulement), généré par build.sh
└── tools/               # build.py (générateur), check_nomenclature.py, check_links.py, title.txt
```

Seules les **sections de cours** (`Progressions`, niveaux, `Utils`) sont
traitées par le build : nettoyage, renommage, vignettes, index, terminal. Le
reste du dépôt n'est jamais modifié.

### Contenu par section

- **Progressions** : une source `NIVEAU.tex` par niveau (texte UTF-8, macros
  de `progtable.sty`) → `NIVEAU.pdf` (pdflatex) et `NIVEAU.html` (tableau).
  Elles pilotent aussi l'ordre et les titres des pages de niveau.
- **Sixieme / Quatrieme** : un dossier par séquence (`S04-Angles/`…) avec les
  fiches au format `{Type}-{Niveau}C{NN}[-Item]-{Nom}.pdf`, sources `.tex`
  à côté. Types : `Cours`, `Ex`, `Act`, `DS` ; côté enseignant `Seq` (plan de
  séquence) et `Prep` (préparation de séance), affichés en tête de séquence ;
  corrigé : nom du sujet suivi de `-Corr` (`Ex-6C04-01-Nom.pdf` ↔
  `Ex-6C04-01-Nom-Corr.pdf`). Sujet et corrigé sont toujours deux PDF séparés.
  Une source `.tex` à `\ifcorrige` donne le sujet ; `build.py` compile en plus
  le corrigé (`\aveccorrige` défini) dès que le `.tex` change.
  Figures sources dans `images/`, anciens documents dans `_Archive/`.
- **Utils** : grilles de multiplication à imprimer, suivi des corrections,
  dossier DNL en anglais.

---

## Construire le site

```
./build.sh               # nouveau site + legacy/
python3 tools/build.py   # nouveau site seul
python3 tools/check_nomenclature.py   # noms de fichiers ↔ progressions
python3 tools/check_links.py          # liens cassés des pages générées
```

Prérequis : Python 3 (stdlib seulement), `pdftoppm` (poppler) pour les
vignettes, `pdflatex` pour les progressions, `tree` pour `legacy/`.

`tools/build.py`, en une passe :
1. crée les `_Archive/` manquants des niveaux ;
2. supprime les fichiers temporaires LaTeX (`.aux`, `.log`, `.toc`…) ;
3. nettoie les noms de fichiers/dossiers (accents, espaces, caractères spéciaux) ;
4. génère les vignettes des PDF dans `assets/thumbs/` (seuls les PDF nouveaux
   ou modifiés sont rendus, les vignettes orphelines sont supprimées) ;
5. recompile `Progressions/NIVEAU.pdf` si le `.tex` a changé (PDF
   reproductible à l'octet : pas de faux diff git) ;
6. régénère l'`index.html` de chaque dossier, l'accueil, la 404, `credits/`
   et `term/fs.json`.

`build.sh` régénère ensuite l'ancien site dans `legacy/` : uniquement des
`index.html` produits par `tree -H`, dont les liens pointent vers les vrais
fichiers (rien n'est dupliqué).

Enfin, `build.sh` lance deux vérifications, en avertissement seulement (le
build ne s'arrête pas) :

- `check_nomenclature.py` vérifie que chaque fichier de séquence suit la
  nomenclature, et croise les dossiers `S{NN}-…` (archives comprises) avec les
  `\seq` des progressions ; les séquences « à venir » sont rappelées sur une
  ligne, sans compter comme un problème ;
- `check_links.py` suit chaque lien interne (`href`, `src`) des pages
  générées (nouveau site, progressions et `legacy/`) et signale les fichiers
  ou dossiers disparus et les ancres `#…` absentes.

---

## Terminal web (`/term`)

Mini terminal interactif pour naviguer dans les cours et ouvrir les fichiers
(PDF surtout) depuis le navigateur, comme dans un shell Unix. JavaScript pur
(modules ES, aucune dépendance). Reprise du projet GitLab Pages `termjs`
(ancien dépôt `colinouterovitch/my-page` sur forge.apps.education.fr) :
l'API GitLab est remplacée par **`term/fs.json`**, l'arborescence des
sections générée à chaque build. Aucune requête d'API, pas de quota,
fonctionne aussi en local.

```
cd /Sixieme/S04-Angles      # Tab complète les noms
ls -l                       # cliquer sur un nom l'ouvre (dossier : cd, fichier : open)
open Cours-6C04-Les-Angles.pdf
find / -iname '*angle*'
ls | grep DS
help ls                     # aide détaillée de chaque commande
```

L'URL suit le dossier courant : `/term/#/Sixieme/S04-Angles` ouvre le
terminal directement dans la séquence (lien à donner aux élèves).

### Commandes

| Commande | Rôle |
|---|---|
| `help [cmd]`, `man` | liste des commandes, aide détaillée |
| `ls [-l] [-1] [-R] [-d]`, `ll` | contenu d'un dossier, en colonnes, couleurs par type |
| `cd [chemin]` | `..`, `/`, `~`, `-`, chemins relatifs/absolus ; liste le dossier ensuite (alias) |
| `pwd` | dossier courant |
| `tree [-d] [-L n]` | arborescence |
| `open fichier\|dossier`, `pdf` | PDF/HTML : nouvel onglet ; image : aperçu ; texte : affiché ; dossier : sa page du site |
| `cat [-n]`, `head`, `tail`, `wc`, `sort` | lecture et filtres de texte |
| `find [chemin] -name/-iname/-type/-maxdepth` | recherche par nom |
| `grep [-ivnclrw] motif [fichiers]` | recherche dans le contenu (ou filtre d'un pipe) |
| `history`, `!!`, `!n`, `!préfixe` | historique |
| `clock [-s]` | l'heure en grand pour un contrôle : plein écran, police figlet « doh » (comme `termdown -z -f doh`), « : » qui clignotent, écran sans veille ; Échap ou Ctrl+C pour quitter |
| `echo`, `whoami`, `date`, `clear` (`c`), `theme` | divers (`theme vert\|ambre\|gris\|clair`) |
| `alias`, `source` (`s`, `.`), `builtin` | alias de `term/aliases.sh` (ci-dessous) |
| `chroot`, `sudo cmd`, `sudo -s`, `su`, `exit` | mode professeur (ci-dessous) |

Shell : guillemets `'…'` `"…"`, `\`, variables (`$PWD`, `$?`, `$HOME`,
`$USER`, `$OLDPWD`), jokers `* ? […]`, enchaînements `|`, `;`, `&&`, `||`.
Clavier : Tab, ↑/↓, Ctrl+C, Ctrl+L, Ctrl+U, Ctrl+K, Ctrl+A, Ctrl+E, Ctrl+W.
Messages d'erreur au format GNU en français, codes de retour dans `$?`.

Le système de fichiers est en lecture seule : `rm`, `mkdir`, `touch`, `cp`,
`mv`, `nano`, `vim`, `>`… existent mais échouent avec l'erreur POSIX
`Système de fichiers accessible en lecture seule`.

### Alias (`term/aliases.sh`)

Joue le rôle du `~/.bash_aliases` (copie de ceux de l'auteur), lu au
démarrage. Syntaxe bash restreinte : `alias nom="commande"` et fonctions
`nom() { … "$@" … }`. Le corps est une vraie ligne du shell (`&&`, `|`…),
sans récursion : `builtin cd` court-circuite la fonction `cd`.

- `cd` ⇒ `builtin cd "$@" && ll` (liste le dossier après chaque `cd`) ;
- `s` ⇒ `source ~/.bashrc` : relit `aliases.sh`, efface l'écran et
  réaffiche l'accueil, sans changer de dossier ;
- `c` ⇒ `clear` ;
- `pdf` ⇒ `open` (`pdf Cours-6C04-Les-Angles.pdf`).

### Mode sudo

Les fichiers masqués sur le site (`.tex`, `.sty`, `.py`, `.sh`, `.md`… :
`HIDDEN_EXT` de `tools/build.py`), les documents du mode prof (`DS-`,
`Seq-`, `Prep-`, `…-Corr`) et les archives sont invisibles pour l'élève
(`Permission non accordée`). Comme dans un vrai shell :
`sudo commande` lance **une** commande en root (`sudo open DS-…`), et
`chroot` (ou `su`, `sudo -s`) ouvre un **shell root** : invite
`root@mathematovitch#` en rouge, tout visible et complété par Tab, documents
prof déchiffrés à la volée (`open`, `cat`, `grep`), jusqu'à `exit`. Mot de
passe : celui du mode prof (3 essais), pas redemandé tant que le mode prof
du site est actif (2 h, il sert de cache) ; `sudo -k` ou « Quitter » le
coupent. Tab complète aussi après `sudo`, avant le mot de passe. Ex. :
`chroot` puis `grep -ri "angle nul" .` cherche dans les sources LaTeX. Mot de passe :
`python3 tools/profkey.py passwd` (voir le mode prof, plus haut).

### Fichiers

```
term/
├── index.html        page, touches tactiles (Tab, ↑, ↓, cd .., ls, ^C)
├── term.css          thèmes (variables CSS), couleurs façon dircolors, mobile
├── fs.json           GÉNÉRÉ par tools/build.py (ne pas éditer, mais committer)
├── aliases.sh        alias et fonctions du shell (cd → cd && ll, s, c, pdf)
└── js/
    ├── main.js       affichage, prompt, clavier, historique, démarrage
    ├── shell.js      parseur : guillemets, variables, jokers, | ; && ||, alias
    ├── fs.js         système de fichiers virtuel, chemins, erreurs POSIX
    ├── aliases.js    lecture de aliases.sh
    ├── complete.js   complétion Tab
    ├── state.js      état + sauvegarde localStorage
    ├── config.js     hôte, utilisateur
    └── commands/     une commande = { help, usage, more, run(args, io) }
```

Tester en local (les modules ES et `fetch` ne marchent pas en `file://`) :

```
python3 -m http.server   # à la racine du site, puis http://localhost:8000/term/
```

---

## Déploiement

Servi directement depuis la branche `main` du dépôt
`mathematovitch/mathematovitch.github.io` via GitHub Pages. Pages ne lance
pas le build : les fichiers générés (`index.html`, vignettes, `fs.json`,
PDF des progressions, `legacy/`) sont committés.

---

## 🛣️ Roadmap

Numérotée par endroit du site à modifier : `1.1` = 1er chantier des pages de
séquence, etc.

### 1. Pages de séquence (`/Sixieme/S04-Angles/`…)

- [ ] **1.1 QR code par séquence**, généré au build, affiché sur la page de la
  séquence et imprimable (à coller dans le cahier).

### 2. Contenu de cours (`Progressions/`, niveaux)

- [ ] **2.1 Séquences « à venir »** de 6e à créer : 6C09, 6C15 à 6C18 (la 4e
  est complète).
- [ ] **2.2 Vacances** à placer dans les progressions de 5e et 3e ; placement
  proposé en 4e à valider.
- [ ] **2.3 Cinquième et Troisième** (si repris) : progressions prêtes, créer
  `Cinquieme/` et `Troisieme/` (déjà prévus par `build.sh`).
- [ ] **2.4 Lycée** (Seconde, Première, Terminale) : pages vides, hors périmètre.

### 3. Terminal (`/term`)

- [ ] **3.1 Tutoriel intégré** (`tuto`), plus tard : quelques défis du type
  « trouve le DS sur les angles » pour apprendre les bases du terminal.

### 4. CV (`/cv`)

- [ ] **4.1 Actualiser le CV** d'après le dossier I-Prof (postes, dates,
  formations continues suivies, missions) ; vérifier le niveau d'anglais
  (B2 BULATS, attestation non retrouvée). Source actuelle : CV de
  l'inspection 2026 et rapport DNL.

<details>
<summary>Déjà fait</summary>

**Site**
- [x] Générateur `tools/build.py` (stdlib) remplaçant les index `tree` ; ancien site gardé dans `/legacy/`
- [x] Progressions en LaTeX → PDF + HTML, qui pilotent les pages de niveau (ordre, titres, compétences, vacances, séquences « à venir »)
- [x] Nomenclature unifiée des fichiers + `check_nomenclature.py`
- [x] Vignettes des PDF au survol, « Récemment ajoutés », recherche sur les pages de niveau
- [x] Design old school : thème clair, icônes pixel W95, logo et favicon pixel
- [x] Page crédits, page 404, licence CC0
- [x] Organisation GitHub `mathematovitch` + redirection de l'ancienne adresse (QR codes)
- [x] Page `/todo` synchronisée par Gist
- [x] Une page par séquence (`/Sixieme/S04-Angles/`) : son bloc seul, déplié, compétences comprises ; le `#` de chaque séquence ouvre sa page et copie son adresse ; les progressions y renvoient
- [x] Mode impression (toutes les pages) : noir et blanc, tout déplié, adresse de la page et noms de fichiers
- [x] Pied de page « mis à jour le … » (date git du dernier commit touchant le contenu)
- [x] Mode élève / mode prof (calculatrice de l'accueil, mot de passe du sudo) : DS, Seq, Prep, corrigés et archives réservés au prof, corrigés séparés des sujets et affichés sous eux
- [x] Documents prof chiffrés dans le dépôt (AES-256-GCM, clé protégée par le mot de passe), déchiffrés dans le navigateur ; historique git purgé des versions en clair
- [x] Page CV `/cv/` (thème Minimal forké sous `mathematovitch/minimal`, avatar pixel, sections dépliables, `noindex`)
- [x] `build.sh` vérifie la nomenclature (`check_nomenclature.py`) et les liens cassés (`check_links.py`), en avertissement seulement

**Terminal**
- [x] `ls`, `cd`, `open`, historique clavier, complétion Tab
- [x] `cd ..`, `/`, `~`, `-`, `../../x` ; messages d'erreur POSIX et codes de retour
- [x] `open` intelligent (PDF, images, HTML, texte, dossiers), `tree`, `cat`
- [x] CSS : scroll, sélection, focus, thèmes
- [x] Mode sudo (même mot de passe que le mode prof, vérifié par déchiffrement de la clé)
- [x] Tri des dossiers (dossiers d'abord, `_Archive` en dernier, tri naturel)
- [x] Recherche (`find`, `grep`), pipes et filtres de texte
- [x] Sauvegarde de l'état (localStorage : dossier, historique, thème)
- [x] Support mobile (touches tactiles, clavier virtuel, noms cliquables)
- [x] `clock` plein écran pour les contrôles
- [x] Alias façon `~/.bash_aliases` (`cd && ll`, `s`, `c`, `pdf`)

</details>

---

## 🎓 Objectif pédagogique

- Donner aux élèves un accès structuré aux ressources
- Habituer à la navigation arborescente
- Introduire les bases du terminal Unix
- Centraliser les supports de cours de manière élégante

## 🧑‍🏫 Auteur

Projet développé par **M. Outerovitch**, professeur de mathématiques ([CV](https://mathematovitch.github.io/cv/)).

## 📜 Licence

[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/deed.fr) : le
contenu original du site est placé dans le domaine public. Les ressources
tierces (Sésamath, mathsenligne, icônes…) restent sous leur propre licence,
voir `/credits/`.
