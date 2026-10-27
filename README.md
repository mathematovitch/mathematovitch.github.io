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
| Terminal | `/term/` | naviguer dans les cours avec `ls`, `cd`, `open`… ; dépôt à part [`mathematovitch/term`](https://github.com/mathematovitch/term), qui lit `assets/fs.json` |
| CV | `/cv/` | CV de l'auteur ; dépôt à part [`mathematovitch/cv`](https://github.com/mathematovitch/cv), lien depuis le nom de l'auteur sur l'accueil |
| Todo | `/todo/` | listes de tâches façon org-mode, synchronisées par un Gist GitHub (jeton stocké dans le navigateur) |
| Ancien site | `/legacy/` | la version d'origine, pages `tree -H`, gardée active (sans les documents du mode prof) |

### Mode élève / mode prof

Par défaut, le site est en **mode élève** : cours, activités, exercices,
ressources. Un clic sur la **calculatrice** de l'accueil, ou **`C-x C-x`**
(Ctrl+X deux fois, comme sous Emacs) depuis n'importe quelle page, demande le mot de
passe (le même que le `sudo` du terminal) et passe en **mode prof** pour 2 h,
sur toutes les pages : fond rosé, bandeau rouge « MODE PROF » avec un bouton
« Quitter » (recliquer la calculatrice ou refaire `C-x C-x` quitte aussi). S'affichent alors en
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
├── assets/              # logo.svg, calculatrice.svg, favicon, icons/ (pixel W95), thumbs/ (vignettes générées), fs.json (terminal)
├── credits/             # Page crédits (générée)
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
   et `assets/fs.json` (arborescence lue par le terminal `/term`).

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

## Sites liés (`/term`, `/cv`)

Le terminal web et le CV sont des **dépôts à part** de l'organisation,
servis par GitHub Pages sous le même domaine (sites de projet) :
[`mathematovitch/term`](https://github.com/mathematovitch/term) → `/term/`,
[`mathematovitch/cv`](https://github.com/mathematovitch/cv) → `/cv/`. Même
origine : ils utilisent `assets/` (favicon, `prof.js`, `prof.json`) et la
session du mode prof. Le terminal lit `assets/fs.json`, généré par
`build_term_fs()` de `tools/build.py` : à committer ici. Aperçu local : liens
symboliques `term` et `cv` vers `~/code/04-web/…` à la racine (ignorés par
git), puis `python3 -m http.server`.

---

## Déploiement

Servi directement depuis la branche `main` du dépôt
`mathematovitch/mathematovitch.github.io` via GitHub Pages. Pages ne lance
pas le build : les fichiers générés (`index.html`, vignettes, `assets/fs.json`,
PDF des progressions, `legacy/`) sont committés.

---

## 🛣️ Roadmap

Numérotée par endroit du site à modifier : `1.1` = 1er chantier des pages de
séquence, etc.

### 1. Pages de séquence (`/Sixieme/S04-Angles/`…)

- [ ] **1.1 QR code par séquence**, généré au build, affiché sur la page de la
  séquence et imprimable (à coller dans le cahier).
- [ ] **1.2 Fiche récap imprimable** : une page A4 par séquence pour l'élève
  (compétences, liste des fiches, cases « fait / revu »).
- [ ] **1.3 « Pour réviser le DS »** : sur la page de séquence, un bloc qui
  regroupe le cours et les fiches de la compétence évaluée (déduit des codes
  `6C04-…`).
- [ ] **1.4 Une adresse par compétence** : chaque code (ex. `6C04-GEO02`) a sa
  propre adresse et mène aux fiches qui la travaillent.

### 2. Contenu de cours (`Progressions/`, niveaux)

- [ ] **2.1 Séquences « à venir »** de 6e à créer : 6C09, 6C15 à 6C18 (la 4e
  est complète).
- [ ] **2.2 Vacances** à placer dans les progressions de 5e et 3e ; placement
  proposé en 4e à valider.
- [ ] **2.3 Cinquième et Troisième** (si repris) : progressions prêtes, créer
  `Cinquieme/` et `Troisieme/` (déjà prévus par `build.sh`).
- [ ] **2.4 Lycée** (Seconde, Première, Terminale) : pages vides, hors périmètre.
- [ ] **2.5 Séquences à compléter** (avec `/sequence`) : seule S04-Angles suit
  tout le modèle. 6e : S11 et S12 n'ont qu'une fiche chacune, sans cours ;
  S10 sans cours ; S08 et S13 sans DS. 4e : S06 et S10 sans cours ; S09 sans
  DS ; S04 et S05 n'ont que 3 ou 4 fiches.
- [ ] **2.6 Plans de séquence (`Seq`) et préparations (`Prep`)** sur le modèle
  de S04 (avec `/sequence`), en 6e puis en 4e (aucun pour l'instant).
- [ ] **2.7 Calcul mental** : une série de diaporamas `Act` par séquence, comme
  `Act-6C04-03`.
- [ ] **2.8 Faute de frappe** : `Quatrieme/S06-Satistiques` → `Statistiques`.
  Un `git mv` casserait les QR codes et liens déjà imprimés : ajouter une
  redirection, ou garder le nom.
- [ ] **2.9 Doublons** : fichiers de probabilités identiques entre
  `Quatrieme/S12-Probabilites` et `Sixieme/S14-Probabilites` ; décider
  (garder les deux, ou un lien).

### 3. Outillage (`tools/`)

- [ ] **3.1 Changer la clé prof** (`profkey.py rotate`) : nouvelle clé maître,
  tous les `.enc` rechiffrés ; procédure documentée si le mot de passe fuite.

### 4. Navigation et accessibilité (toutes les pages)

- [ ] **4.1 Raccourcis clavier** façon Emacs, sur toute page, à côté de
  `C-x C-x` (mode prof) : `C-x t` ouvre le terminal, `C-x m` la musique,
  etc. ; liste affichée par `C-x ?` ou sur la page crédits.
- [ ] **4.2 Vérifier l'accessibilité** : textes alternatifs des icônes,
  contrastes, navigation au clavier.

Roadmaps du terminal et du CV : dans leurs dépôts.

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
- [x] Terminal (`/term`) et CV (`/cv`) sortis dans leurs propres dépôts

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
