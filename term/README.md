# Terminal web – Cours de Maths

Mini terminal web interactif pour naviguer dans les cours du site
(`mathematovitch.github.io/term/`) et ouvrir les fichiers (PDF surtout)
depuis le navigateur, comme dans un shell Unix (`ls`, `cd`, `open`…).

Reprise du projet GitLab Pages `termjs` (ancien dépôt
`colinouterovitch/my-page` sur forge.apps.education.fr), adapté au site
GitHub Pages : l'API GitLab est remplacée par **`fs.json`**, l'arborescence du
site générée par `tools/build.py` à chaque build (sections de cours seulement). Plus aucune requête d'API, pas de
quota, fonctionne aussi en local.

---

## Utilisation

```
cd /Sixieme/S04-Angles      # Tab complète les noms
ls -l                       # cliquer sur un nom l'ouvre (dossier : cd, fichier : open)
open Cours-6C04-Les-Angles.pdf
find / -iname '*angle*'
ls | grep DS
help ls                     # aide détaillée de chaque commande
```

L'URL suit le dossier courant : `/term/#/Sixieme/S04-Angles` ouvre le terminal
directement dans la séquence (lien à donner aux élèves).

## Commandes

| Commande | Rôle |
|---|---|
| `help [cmd]`, `man` | liste des commandes, aide détaillée |
| `ls [-l] [-1] [-R] [-d]`, `ll` | contenu d'un dossier, en colonnes, couleurs par type |
| `cd [chemin]` | `..`, `/`, `~`, `-`, chemins relatifs/absolus |
| `pwd` | dossier courant |
| `tree [-d] [-L n]` | arborescence |
| `open fichier\|dossier` | PDF/HTML : nouvel onglet ; image : aperçu ; texte : affiché ; dossier : sa page du site |
| `cat [-n]`, `head`, `tail`, `wc`, `sort` | lecture et filtres de texte |
| `find [chemin] -name/-iname/-type/-maxdepth` | recherche par nom |
| `grep [-ivnclrw] motif [fichiers]` | recherche dans le contenu (ou filtre d'un pipe) |
| `history`, `!!`, `!n`, `!préfixe` | historique |
| `clock [-s]` | l'heure en grand pour un contrôle : plein écran, police figlet « doh » (comme `termdown -z -f doh`), « : » qui clignotent, écran sans veille ; Échap ou Ctrl+C pour quitter |
| `echo`, `whoami`, `date`, `clear`, `theme` | divers (`theme vert\|ambre\|gris\|clair`) |
| `alias`, `source`/`.`, `builtin` | alias de `aliases.sh` (ci-dessous) |
| `sudo cmd`, `sudo -s`, `su`, `exit` | mode professeur (voir ci-dessous) |

Shell : guillemets `'…'` `"…"`, `\`, variables (`$PWD`, `$?`, `$HOME`, `$USER`,
`$OLDPWD`), jokers `* ? […]`, enchaînements `|`, `;`, `&&`, `||`.
Clavier : Tab, ↑/↓, Ctrl+C, Ctrl+L, Ctrl+U, Ctrl+K, Ctrl+A, Ctrl+E, Ctrl+W.

Le système de fichiers est en lecture seule : `rm`, `mkdir`, `touch`, `cp`,
`mv`, `nano`, `vim`, `>`… existent mais échouent avec l'erreur POSIX
`Système de fichiers accessible en lecture seule`.

## Alias (`aliases.sh`)

`term/aliases.sh` joue le rôle du `~/.bash_aliases` (copie de ceux de l'auteur),
lu au démarrage. Syntaxe bash restreinte : `alias nom="commande"` et fonctions
`nom() { … "$@" … }`. Le corps est une vraie ligne du shell (`&&`, `|`…),
sans récursion : `builtin cd` court-circuite la fonction `cd`.

- `cd` ⇒ `builtin cd "$@" && ll` (liste le dossier après chaque `cd`) ;
- `s` ⇒ `source ~/.bashrc` : relit `aliases.sh`, efface l'écran et
  réaffiche l'accueil, sans changer de dossier ;
- `c` ⇒ `clear`.

## Mode sudo

Les fichiers masqués sur le site (`.tex`, `.sty`, `.py`, `.sh`, `.md`… :
`HIDDEN_EXT` de `tools/build.py`) sont invisibles pour l'élève (`Permission non
accordée`). `sudo` (mot de passe vérifié par SHA-256 salé, gardé 15 min comme
le vrai sudo, 3 essais) les rend visibles : `sudo -s` puis `grep -ri "angle
nul" .` cherche dans les sources LaTeX.

**Ce n'est pas une protection** : le site est statique et public, les sources
sont de toute façon dans le dépôt GitHub. C'est un mode d'affichage.

Changer le mot de passe :

```
python3 term/passwd.py
```

## Fichiers

```
term/
├── index.html        page, touches tactiles (Tab, ↑, ↓, cd .., ls, ^C)
├── term.css          thèmes (variables CSS), couleurs façon dircolors, mobile
├── fs.json           GÉNÉRÉ par tools/build.py (ne pas éditer)
├── passwd.py         change le mot de passe sudo
├── aliases.sh        alias et fonctions du shell (cd → cd && ll, s, c)
└── js/
    ├── main.js       affichage, prompt, clavier, historique, démarrage
    ├── shell.js      parseur : guillemets, variables, jokers, | ; && ||
    ├── fs.js         système de fichiers virtuel, chemins, erreurs POSIX
    ├── aliases.js    lecture de aliases.sh
    ├── complete.js   complétion Tab
    ├── state.js      état + sauvegarde localStorage
    ├── config.js     hôte, utilisateur, hash sudo
    └── commands/     une commande = { help, usage, more, run(args, io) }
```

Tester en local (les modules ES et `fetch` ne marchent pas en `file://`) :

```
python3 -m http.server   # à la racine du site, puis http://localhost:8000/term/
```

---

## 🛣️ Roadmap

### Court terme
- [x] `ls`, `cd`, `open`
- [x] Historique clavier
- [x] Autocomplétion (Tab) pour commandes et chemins
- [x] Gestion correcte de `cd ..` (et `/`, `~`, `-`, `../../x`, vérification de chaque étape)
- [x] Messages d'erreur POSIX (`Aucun fichier ou dossier de ce type`, `N'est pas un dossier`, `commande introuvable`…, codes de retour dans `$?`)

### Moyen terme
- [x] `open` intelligent (PDF, images, HTML, texte, dossiers)
- [x] Commande `tree`
- [x] Commande `cat` (lecture texte)
- [x] Amélioration CSS (scroll, sélection, focus, thèmes)

### Long terme
- [x] Mode sudo avec mdp hash SHA256 salted
- [x] Rangement des dossiers (dossiers d'abord, `_Archive` en dernier, tri naturel)
- [x] Recherche (`find`, `grep`)
- [x] Sauvegarde de l'état (localStorage : dossier, historique, thème, sudo)
- [x] Support mobile (touches tactiles, clavier virtuel, noms cliquables)

---

## 🎓 Objectif pédagogique

- Donner aux élèves un accès structuré aux ressources
- Habituer à la navigation arborescente
- Introduire les bases du terminal Unix
- Centraliser les supports de cours de manière élégante

## 🧑‍🏫 Auteur

Projet développé par **M. Outerovitch**, professeur de mathématiques.

## 📜 Licence

CC0 1.0, comme le reste du site.
