---
name: sequence
description: Mettre à niveau une séquence de cours (Sixieme/, Quatrieme/…) selon les règles du site — état des lieux par compétence, puis cours, fiches d'exercices, activités, DS et plan de séquence en LaTeX, sur le modèle de Sixieme/S04-Angles. À utiliser quand l'utilisateur dit « on s'occupe de la S06 en 6e », « /sequence 6 S06 », « mets à niveau la séquence … ».
argument-hint: "<niveau> <séquence>, ex. 6 S06"
---

# Mettre à niveau une séquence

Argument : niveau + numéro (`6 S06`, `4 07`, `6C09`). Si absent, demander.

Les règles générales (nomenclature, documents prof chiffrés, préférences
pédagogiques, `-Corr`, `\feuille`/`\aveccorrige`) sont dans le `CLAUDE.md` du
dépôt : elles priment. Ce skill dit **dans quel ordre** travailler.

## 1. État des lieux (toujours, avant de produire quoi que ce soit)

```
python3 tools/seq_status.py <niveau> <NN>
```

Il liste, par compétence de `Progressions/{niveau}.tex`, les `Act`/`Ex`/`DS`
rattachés (le `.tex` cite le code), les documents de séquence (`Seq`, `Prep`,
`Cours`), les documents **non rattachés** (pas de code dans le source, ou PDF
sans source) et ce qui manque.

Puis **ouvrir** ce qui existe pour le juger, en priorité les non rattachés :
lire les `.tex` ; pour un PDF sans source, `pdftotext -layout` (et
`pdftoppm -png -r 60 -f 1 -l 1` + Read si c'est une figure). Le cours existant
(`Cours-…tex`) fixe le vocabulaire et les notations à reprendre.

Présenter à l'utilisateur un **bilan court**, un tableau par compétence :

| Compétence | Existant | Verdict | Proposé |
|---|---|---|---|
| GEO18 Tracer un cercle | Ex-6C06-04, -05 (PDF seuls) | à refaire en `.tex` (pas de source, pas de corrigé) | Ex-6C06-01 |

Verdicts : **garder** (déjà conforme : ajouter juste `%% Compétence :`),
**reprendre** (source `.tex` à adapter), **refaire** (PDF seul, trop long,
plusieurs compétences mélangées…), **archiver** (doublon, hors progression).
Signaler les compétences de la progression qui semblent hors de portée ou mal
découpées, sans modifier la progression d'office.

**Attendre la validation** du bilan (l'utilisateur peut rayer, réordonner,
dire « seulement GEO18 à GEO20 aujourd'hui ») avant d'écrire.

## 2. Ce qu'on produit, et dans quel ordre

1. **`Seq-{N}C{NN}-Plan-de-Sequence.tex`** d'abord (il fixe la numérotation
   des documents). Modèle : `Sixieme/S04-Angles/Seq-6C04-Plan-de-Sequence.tex`
   (tableau objectif/programme/compétences/prérequis/fil rouge, déroulement
   séance par séance avec documents, tableau des évaluations). L'utilisateur le
   lit en diagonale : rester sur une page si possible.
   Séances de 55 min, découpées par semaine : voir « Volume horaire » ci-dessous.
2. **`Cours-{N}C{NN}-Nom.tex`** : une partie (I, II…) par compétence ou groupe
   de compétences, court (trace écrite copiée au tableau, ~15 min par partie).
   Reprendre l'existant s'il est bon.
3. **`Ex-{N}C{NN}-{KK}-Nom.tex`** : **une fiche = une compétence**, KK = rang
   de la fiche dans la séquence (01, 02…), dans l'ordre du plan. Modèle :
   `Sixieme/S04-Angles/Ex-6C04-01-Nommer-un-Angle.tex` (rappel de leçon
   encadré, exemple traité grisé `\fait`, réponses `\rep` en pointillés sur le
   sujet et en rouge sur le corrigé, une ligne de consigne par exercice).
4. **`Act-{N}C{NN}-{KK}-Nom.tex`** : activités de découverte / manipulation
   prévues par le plan (modèles `Act-6C04-01`, `-02`) ; calcul mental en
   diaporama comme `Act-6C04-03` si le plan en prévoit un.
5. **`DS-{N}C{NN}-{KK}-Nom.tex`** : **deux compétences par DS, une par
   face** (recto-verso, 35 min, sur 40, grille `\competences` juste sous
   l'en-tête, bandeau « Compétence … » en tête de face). KK = rang du DS.
   Modèle : `Sixieme/S04-Angles/DS-6C04-01-Nommer-Sommet-et-Cotes.tex`.
   Nombre impair de compétences : le dernier DS a une face d'une compétence
   et l'autre de réinvestissement, ou on demande.
6. **`Prep-…`** : seulement si l'utilisateur le demande (séance observée…).
   Modèle `Prep-6C04-01`.

Pour chaque document :

- Première ligne : `%% Compétence : 6C06-GEO18` (plusieurs codes pour un DS ou
  une activité : `%% Compétences : 6C06-GEO18, 6C06-GEO19`). C'est ce qui
  permet à `seq_status.py` de rattacher le document. L'ajouter aussi aux
  `.tex` existants gardés.
- Copier les macros du modèle (`\rep`, `\entoure`, `\fait`, `\ifcorrige`…)
  plutôt que d'en inventer ; corps du document :
  `\ifdefined\aveccorrige\corrigetrue\else\corrigefalse\fi \feuille`.
- `\renewcommand{\centerhead}{S{NN} - Titre court}`.
- Figures TikZ en vraie grandeur pour tout ce qui se mesure (imprimer à 100 %) ;
  angles droits toujours codés.

## 3. Ce qu'on fait de l'existant

- Fichier remplacé par une nouvelle version : `git mv` vers `_Archive/` du
  dossier de séquence (pas de suppression). Le build chiffre ce qui est sous
  `_Archive/`.
- Fichier gardé mais renuméroté : `git mv` (préserve l'historique), et
  mettre à jour les références dans le `Seq`.
- Contenu tiers (`Sesa-*`, `pg_NN.pdf`, `Chapitre_N_-_Nom.pdf`,
  `mathsenligne/`) : ne jamais renommer ; peut servir de source d'exercices.
- Ne pas toucher aux autres séquences.

## 4. Vérifier

1. Compiler chaque `.tex` modifié dans un dossier temporaire
   (`pdflatex -interaction=nonstopmode -output-directory "$TMPDIR/…"`), sujet
   **et** corrigé (`pdflatex '\def\aveccorrige{}\input{X.tex}'`), corriger
   les erreurs, regarder la page 1 (et 2 pour un DS) en PNG : mise en page,
   une feuille par fiche, recto-verso pour le DS.
2. `./build.sh` : compile les PDF dans le dépôt, chiffre les documents prof
   (DS, Seq, Prep, `-Corr`, `_Archive/`), régénère les pages. Lire les
   avertissements de `check_nomenclature.py` et `check_links.py`.
3. `python3 tools/seq_status.py <niveau> <NN>` : plus de « Manquant » ni de
   non rattaché (sauf ce que l'utilisateur a choisi de laisser).
4. `git status` : aucun document prof en clair indexé (le hook pre-commit le
   refuse de toute façon). **Ne pas committer** : l'utilisateur committe.

Finir par un récapitulatif : documents créés / repris / archivés, ce qui reste
(ex. activité Capytale à préparer sur l'ENT, figures à scanner).

## Volume horaire et rythme des séances (2026-2027, donné par l'utilisateur)

| Niveau | Séances fixes | Séance particulière |
|---|---|---|
| **6e** (6e D, 22 élèves, REP+) | **4 h par semaine** | + 1 h une semaine sur deux |
| **4e** | **3 h par semaine** | + 1 h **en demi-groupe** une semaine sur deux |

Le plan de séquence s'articule **par semaine** : 4 séances (6e) ou
3 séances (4e) qui font avancer la séquence, plus **une séance
particulière** une semaine sur deux, qui ne porte pas de nouvelle notion (la
classe entière n'y est pas en 4e, et elle n'a lieu qu'une semaine sur deux) :

- salle informatique (Capytale, permis rapporteur…), manipulation,
  travail en petit groupe, oral, remédiation ou approfondissement de la
  compétence en cours ;
- dans le tableau du `Seq` : une colonne ou une ligne distincte « Séance
  particulière » par quinzaine, hors numérotation des séances de la classe,
  pour que le plan reste juste si cette séance saute.

Ordre de grandeur : une séquence de 6e = 2 à 3 semaines (8 à 12 séances + 1
séance particulière) ; en 4e = 3 à 4 semaines (9 à 12 séances + 2 séances
particulières). Un DS prend une séance (35 min + reprise). Calendrier : les
séparateurs `\vacances` de la progression.
