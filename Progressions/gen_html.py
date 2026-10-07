#!/usr/bin/env python3
"""Parseur des sources Progressions/*.tex (progtable.sty), utilisé par ../build.py.

Ne fait pas tourner TeX : parse juste \\progheader{...}{...}, \\vacances{...} et les
blocs \\seq{ID}{Titre}{Thème}{Objectif}{ \\item ... \\item ... } par un parseur de
groupes { } à profondeur (les arguments peuvent contenir des accolades).

Le rendu HTML (et la compilation PDF si le .tex a changé) est fait par build.py,
pour que les progressions aient le même style que le reste du site. Lancer ce
fichier directement relance simplement build.py :
    python3 Progressions/gen_html.py
"""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_braced_arg(text, pos):
    """text[pos] doit être '{'. Renvoie (contenu, position juste après le '}')."""
    if text[pos] != "{":
        raise ValueError(f"'{{' attendu à la position {pos}, trouvé {text[pos]!r}")
    depth = 0
    start = pos + 1
    i = pos
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    raise ValueError("accolade non fermée")


def read_n_braced_args(text, pos, n):
    args = []
    for _ in range(n):
        while text[pos].isspace():
            pos += 1
        arg, pos = read_braced_arg(text, pos)
        args.append(arg.strip())
    return args, pos


def parse_tex(path):
    text = path.read_text(encoding="utf-8")

    m = re.search(r"\\progheader\{", text)
    if not m:
        raise ValueError(f"{path}: \\progheader introuvable")
    (long_name, short_name), _ = read_n_braced_args(text, m.end() - 1, 2)

    rows = []
    for m in re.finditer(r"\\(seq|vacances)\{", text):
        if m.group(1) == "vacances":
            (nom,), _ = read_n_braced_args(text, m.end() - 1, 1)
            rows.append({"vacances": nom})
            continue
        (id_, titre, theme, obj, items_body), _ = read_n_braced_args(text, m.end() - 1, 5)
        items = [it.strip() for it in items_body.split(r"\item") if it.strip()]
        rows.append({"id": id_, "titre": titre, "theme": theme, "obj": obj, "items": items})

    if not any("id" in r for r in rows):
        raise ValueError(f"{path}: aucune séquence \\seq trouvée")

    return long_name, short_name, rows


if __name__ == "__main__":
    sys.exit(subprocess.run([sys.executable, str(HERE.parent / "build.py")]).returncode)
