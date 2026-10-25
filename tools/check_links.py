#!/usr/bin/env python3
"""Vérifie les liens internes des pages générées (nouveau site et legacy/).

Parcourt tous les `index.html` des sections, l'accueil, la 404, credits/,
legacy/ et les pages Progressions/*.html, et signale chaque `href`/`src`
interne qui mène à un fichier ou dossier disparu, ou à une ancre `#id`
absente de la page visée (ex. une séquence renommée). Liens externes
(http:, mailto:…) ignorés ; `<base href>` respecté (404).

Usage:
    python3 tools/check_links.py
Code de sortie : 0 si tout est bon, 1 sinon (build.sh l'ignore : simple avertissement).
"""
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SECTIONS = ["Progressions", "Sixieme", "Cinquieme", "Quatrieme", "Troisieme", "Utils", "credits", "legacy"]


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.ids, self.base = [], set(), None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "base" and a.get("href"):
            self.base = a["href"]
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key])


_cache = {}


def parse(f):
    if f not in _cache:
        p = Page()
        p.feed(f.read_text("utf-8", errors="replace"))
        _cache[f] = p
    return _cache[f]


def pages():
    yield from (ROOT / n for n in ("index.html", "404.html"))
    for s in SECTIONS:
        d = ROOT / s
        if d.is_dir():
            yield from sorted(d.rglob("index.html"))
    yield from sorted((ROOT / "Progressions").glob("*.html"))


def check(f):
    problems = []
    p = parse(f)
    for link in p.links:
        u = urlsplit(link)
        if u.scheme or u.netloc or link.startswith(("data:", "javascript:")):
            continue
        path = unquote(u.path)
        if not path:
            target = f
        else:
            if path.startswith("/"):
                target = ROOT / path.lstrip("/")
            else:
                base = f.parent if not p.base else (ROOT / p.base.lstrip("/") if p.base.startswith("/") else f.parent / p.base)
                target = base / path
            target = target.resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                problems.append(f"{f.relative_to(ROOT)} → {link} : introuvable")
                continue
        if u.fragment and target.suffix == ".html" and unquote(u.fragment) not in parse(target).ids:
            problems.append(f"{f.relative_to(ROOT)} → {link} : ancre #{u.fragment} absente")
    return problems


def main():
    files = [f for f in pages() if f.is_file()]
    problems = [x for f in files for x in check(f)]
    if not problems:
        print(f"Liens OK : {len(files)} pages vérifiées.")
        return 0
    print(f"{len(problems)} lien(s) cassé(s) sur {len(files)} pages :")
    for x in problems:
        print(f"  - {x}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
