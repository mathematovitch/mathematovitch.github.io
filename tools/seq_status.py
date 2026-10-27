#!/usr/bin/env python3
"""État d'une séquence : ce qui existe, ce qui manque, par compétence.

Lit les compétences de la séquence dans Progressions/{niveau}.tex (via
gen_html.parse_tex) et les documents du dossier `S{NN}-…/`. Un document est
rattaché à une compétence si son source `.tex` cite son code (`6C04-GEO10`
ou `GEO10`) ; sinon il est listé « non rattaché ». Les documents prof ne sont
lus qu'en clair (sur la machine du prof) ; un `.enc` seul compte comme présent.

Attendu par compétence (règles du CLAUDE.md) : une fiche `Ex` (sujet +
`-Corr`), une face de `DS` (deux compétences par DS, sujet + `-Corr`).
Par séquence : un `Cours`, un `Seq` (plan de séquence).

Usage:
    python3 tools/seq_status.py 6 06      # ou : 6 S06, 6C06
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True  # pas de Progressions/__pycache__
sys.path.insert(0, str(ROOT / "Progressions"))
from gen_html import parse_tex  # noqa: E402

LEVELS = {"6": ("Sixieme", "6eme"), "5": ("Cinquieme", "5eme"),
          "4": ("Quatrieme", "4eme"), "3": ("Troisieme", "3eme")}
TYPES = ("Seq", "Prep", "Cours", "Act", "Ex", "DS")
NAME_RE = re.compile(r"^(Seq|Prep|Cours|Ex|Act|DS)-[1-6T]C\d{2}(?:-(\d+[a-z]?))?-")


def parse_args(argv):
    joined = "".join(argv).upper().replace(" ", "")
    m = re.fullmatch(r"([6543])(?:C|S|-S)?(\d{1,2})", joined)
    if not m:
        sys.exit(__doc__)
    return m.group(1), f"{int(m.group(2)):02d}"


def stem(name):
    """Nom du sujet : sans .enc, sans extension, sans -Corr."""
    name = name.removesuffix(".enc")
    name = name.rsplit(".", 1)[0] if "." in name else name
    return name.removesuffix("-Corr")


def collect(folder):
    """{stem: {"exts": {...}, "corr": bool, "tex": Path|None}} des documents nommés."""
    docs = {}
    for f in sorted(folder.iterdir()):
        if not f.is_file() or not NAME_RE.match(f.name):
            continue
        d = docs.setdefault(stem(f.name), {"exts": set(), "corr": False, "tex": None})
        plain = f.name.removesuffix(".enc")
        if stem(plain) + "-Corr" in plain:
            d["corr"] = True
            continue
        ext = plain.rsplit(".", 1)[-1]
        d["exts"].add(ext)
        if ext == "tex" and not f.name.endswith(".enc"):
            d["tex"] = f
    return docs


def main():
    lvl, nn = parse_args(sys.argv[1:])
    dirname, texname = LEVELS[lvl]
    _, _, rows = parse_tex(ROOT / "Progressions" / f"{texname}.tex")
    seq = next((r for r in rows if r.get("id") == f"{lvl}C{nn}"), None)
    if seq is None:
        sys.exit(f"{lvl}C{nn} absente de Progressions/{texname}.tex")

    comps = []  # (code complet, code court, intitulé)
    for it in seq["items"]:
        code, _, label = it.partition("—")
        code = code.strip()
        comps.append((code, code.split("-", 1)[-1], label.strip()))

    print(f"{lvl}C{nn} — {seq['titre']} ({seq['theme']}) : {seq['obj']}")
    folders = sorted((ROOT / dirname).glob(f"S{nn}-*"))
    if not folders:
        print(f"\nPas de dossier {dirname}/S{nn}-… : séquence à créer.")
        print("Compétences :")
        for code, _, label in comps:
            print(f"  {code} — {label}")
        return 0
    folder = folders[0]
    print(f"Dossier : {folder.relative_to(ROOT)}/\n")

    docs = collect(folder)
    linked = {}  # stem -> codes courts cités
    for s, d in docs.items():
        text = d["tex"].read_text(encoding="utf-8", errors="replace") if d["tex"] else ""
        linked[s] = {short for _, short, _ in comps if re.search(rf"\b{short}\b", text)}

    def describe(s):
        d = docs[s]
        bits = ["/".join(sorted(d["exts"])) or "?"]
        if s.split("-", 1)[0] in ("Ex", "Act", "DS"):
            bits.append("corrigé" if d["corr"] else "SANS corrigé")
        if "tex" not in d["exts"]:
            bits.append("pas de source")
        return f"{s}  [{', '.join(bits)}]"

    print("Par compétence :")
    todo = []
    for code, short, label in comps:
        print(f"  {code} — {label}")
        for t in ("Act", "Ex", "DS"):
            hits = [s for s in docs if s.startswith(t + "-") and short in linked[s]]
            for s in hits:
                print(f"      {t:5} {describe(s)}")
            if t in ("Ex", "DS") and not hits:
                print(f"      {t:5} —")
                todo.append(f"{t} pour {code}")

    print("\nDocuments de séquence :")
    for t in ("Seq", "Prep", "Cours"):
        hits = [s for s in docs if s.startswith(t + "-")]
        for s in hits:
            print(f"  {t:5} {describe(s)}")
        if not hits and t != "Prep":
            print(f"  {t:5} —")
            todo.append(f"{t}-{lvl}C{nn}")

    orphans = [s for s in docs if s.split("-", 1)[0] in ("Act", "Ex", "DS") and not linked[s]]
    if orphans:
        print("\nNon rattachés (aucun code de compétence dans le source, ou pas de source) :")
        for s in orphans:
            print(f"  {describe(s)}")

    visible = [f for f in folder.iterdir() if not f.name.startswith(".")]
    others = sorted(f.name for f in visible
                    if f.is_file() and not NAME_RE.match(f.name) and f.name != "index.html")
    subdirs = sorted(f.name + "/" for f in visible if f.is_dir())
    if others or subdirs:
        print("\nAutres (tiers, brouillons, sous-dossiers) :")
        for n in subdirs + others:
            print(f"  {n}")

    if todo:
        print("\nManquant (avant rattachement des documents ci-dessus) :")
        for t in todo:
            print(f"  - {t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
