#!/usr/bin/env python3
"""Vérifie la cohérence Sixieme//Quatrieme/ <-> Progressions/{6eme,4eme}.tex.

Deux contrôles, stdlib-only (pas de dépendance externe) :

1. Nomenclature : chaque fichier/dossier posé directement dans un dossier
   de séquence `S{NN}-Nom/` doit suivre le format
   `{Type}-{Niveau}C{NN}[-Item]-Nom-Descriptif[.ext]` avec
   Type in {Cours, Ex, Act, DS}. Les dossiers/fichiers cachés (préfixe
   `.`, ex. `.data`, `.figures`) et le contenu tiers reconnu (mathsenligne/,
   Sesa-*, pg_NN.pdf, Chapitre_N_-_Nom.pdf) sont ignorés, comme dans
   update_site.sh.

2. Couverture : croise les séquences `S{NN}-...` présentes sur le disque
   avec les `\\seq{NiveauCNN}` déclarés dans Progressions/{6eme,4eme}.tex,
   pour repérer les trous dans un sens ou dans l'autre.

Usage:
    python3 .scripts/check_nomenclature.py
Code de sortie : 0 si rien à signaler, 1 sinon.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NIVEAUX = {"Sixieme": "6", "Quatrieme": "4"}

SEQ_RE = re.compile(r"^S(\d{2})-")
ITEM_RE = re.compile(r"^(Cours|Ex|Act|DS)-([1-6T])C(\d{2})-\S+$")

THIRD_PARTY_FILES = (
    re.compile(r"^Sesa-\d+", re.IGNORECASE),
    re.compile(r"^pg_\d+\.pdf$"),
    re.compile(r"^Chapitre_\d+_-_.+\.pdf$"),
    re.compile(r"^grille_multiplication_"),
    re.compile(r"^regles_multiplication_"),
    re.compile(r"^\d[a-z]\d_"),  # export mathsenligne, ex. 6n1_..., 6n3_...
)
THIRD_PARTY_DIRS = {"mathsenligne"}

# Artefacts d'éditeur / scratch connus, à laisser tels quels (voir CLAUDE.md).
KNOWN_SCRATCH = {
    "region_.tex",
    "Cours-S04-test.tex",
    "Cours-S08-help.tex",
}


def is_third_party(name, is_dir):
    if name in KNOWN_SCRATCH:
        return True
    if is_dir:
        return name in THIRD_PARTY_DIRS
    return any(p.match(name) for p in THIRD_PARTY_FILES)


def check_nomenclature():
    problems = []
    for folder, niveau in NIVEAUX.items():
        base = ROOT / folder
        if not base.is_dir():
            continue
        for seq_dir in sorted(base.iterdir()):
            if not seq_dir.is_dir() or seq_dir.name.startswith("."):
                continue
            m = SEQ_RE.match(seq_dir.name)
            if not m:
                problems.append(f"{seq_dir.relative_to(ROOT)}: nom de dossier hors convention S{{NN}}-Nom")
                continue
            nn = m.group(1)
            for item in sorted(seq_dir.iterdir()):
                if item.name.startswith(".") or item.name == "index.html":
                    continue
                if is_third_party(item.name, item.is_dir()):
                    continue
                im = ITEM_RE.match(item.name)
                if not im:
                    problems.append(f"{item.relative_to(ROOT)}: ne suit pas {{Type}}-{{Niveau}}C{{NN}}-Nom")
                    continue
                _, item_niveau, item_nn = im.groups()
                if item_niveau != niveau:
                    problems.append(
                        f"{item.relative_to(ROOT)}: niveau {item_niveau} attendu {niveau} (dossier {folder})"
                    )
                if item_nn != nn:
                    problems.append(
                        f"{item.relative_to(ROOT)}: chapitre C{item_nn} attendu C{nn} (dossier {seq_dir.name})"
                    )
    return problems


def parse_seq_ids(tex_path):
    text = tex_path.read_text(encoding="utf-8")
    ids = []
    for m in re.finditer(r"\\seq\{([^}]+)\}", text):
        ids.append(m.group(1).strip())
    return ids


def check_coverage():
    problems = []
    tex_by_niveau = {"6": ROOT / "Progressions" / "6eme.tex", "4": ROOT / "Progressions" / "4eme.tex"}
    for folder, niveau in NIVEAUX.items():
        base = ROOT / folder
        tex_path = tex_by_niveau[niveau]
        if not base.is_dir() or not tex_path.is_file():
            continue

        disk_nn = set()
        for seq_dir in base.iterdir():
            if seq_dir.is_dir():
                m = SEQ_RE.match(seq_dir.name)
                if m:
                    disk_nn.add(m.group(1))

        declared_ids = parse_seq_ids(tex_path)
        declared_nn = set()
        for id_ in declared_ids:
            dm = re.match(rf"^{niveau}C(\d{{2}})$", id_)
            if dm:
                declared_nn.add(dm.group(1))
            else:
                problems.append(f"{tex_path.name}: \\seq{{{id_}}} ne suit pas {niveau}C{{NN}}")

        for nn in sorted(disk_nn - declared_nn):
            problems.append(f"{folder}/S{nn}-... : présent sur le disque mais absent de {tex_path.name}")
        for nn in sorted(declared_nn - disk_nn):
            problems.append(f"{tex_path.name}: {niveau}C{nn} déclaré mais aucun dossier {folder}/S{nn}-...")

    return problems


def main():
    problems = check_nomenclature() + check_coverage()
    if not problems:
        print("OK : rien à signaler.")
        return 0
    print(f"{len(problems)} point(s) à vérifier :")
    for p in problems:
        print(f"  - {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
