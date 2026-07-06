#!/usr/bin/env python3
"""Génère les Progressions/*.html à partir des sources .tex (progtable.sty).

Ne fait pas tourner TeX : parse juste \\progheader{...}{...} et les blocs
\\seq{ID}{Titre}{Thème}{Objectif}{ \\item ... \\item ... } par un parseur de
groupes { } à profondeur, puis réémet le template HTML sobre du site.

Usage:
    python3 gen_html.py            # régénère tous les Progressions/*.tex
    python3 gen_html.py 6eme.tex    # ne régénère que ce fichier
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Progression {short} — Maths</title>
<style>
body{{font-family:monospace,sans-serif;color:#000;background:#fff;margin:2rem;}}
a{{color:#000;}}
a:hover{{text-decoration:underline;}}
h1{{font-size:1.1rem;margin:0 0 1rem 0;}}
table{{border-collapse:collapse;width:100%;}}
th,td{{border:1px solid #000;padding:.4rem .6rem;text-align:left;vertical-align:top;font-size:.85rem;}}
</style>
</head>
<body>
<a href="../index.html">← Retour</a>
<h1>Progression Maths — {long}</h1>
<table>
  <thead>
    <tr>
      <th>Séquence</th>
      <th>Titre</th>
      <th>Thème</th>
      <th>Compétences</th>
      <th>Objectif principal</th>
    </tr>
  </thead>
  <tbody>
{rows}
  </tbody>
</table>
</body>
</html>
"""

ROW_TEMPLATE = """    <tr>
      <td>{id}</td>
      <td>{titre}</td>
      <td>{theme}</td>
      <td>
        {items}
      </td>
      <td>{obj}</td>
    </tr>"""


def escape_html(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
    for m in re.finditer(r"\\seq\{", text):
        (id_, titre, theme, obj, items_body), _ = read_n_braced_args(text, m.end() - 1, 5)
        items = [it.strip() for it in items_body.split(r"\item") if it.strip()]
        rows.append({"id": id_, "titre": titre, "theme": theme, "obj": obj, "items": items})

    if not rows:
        raise ValueError(f"{path}: aucune séquence \\seq trouvée")

    return long_name, short_name, rows


def render(path):
    long_name, short_name, rows = parse_tex(path)
    rows_html = "\n".join(
        ROW_TEMPLATE.format(
            id=escape_html(r["id"]),
            titre=escape_html(r["titre"]),
            theme=escape_html(r["theme"]),
            obj=escape_html(r["obj"]),
            items="<br>\n        ".join(escape_html(it) for it in r["items"]),
        )
        for r in rows
    )
    html = HTML_TEMPLATE.format(
        short=escape_html(short_name), long=escape_html(long_name), rows=rows_html
    )
    out = path.with_suffix(".html")
    out.write_text(html, encoding="utf-8")
    print(f"{path.name} -> {out.name} ({len(rows)} séquences)")


def main():
    args = sys.argv[1:]
    paths = [Path(a) for a in args] if args else sorted(HERE.glob("*.tex"))
    if not paths:
        print("Aucun fichier .tex trouvé", file=sys.stderr)
        sys.exit(1)
    for p in paths:
        render(p)


if __name__ == "__main__":
    main()
