#!/usr/bin/env python3
"""Construit le nouveau site en une passe (build.sh l'appelle, puis génère legacy/).

Usage : python3 tools/build.py [racine]      (ou ./build.sh, qui fait aussi legacy/)

Seuls les dossiers de cours (SECTION_ORDER : Progressions, niveaux, Utils) sont nettoyés,
renommés, indexés et listés ; le reste du dépôt (assets/, term/, todo/, tools/...) n'est
jamais touché. Stdlib uniquement (+ `pdftoppm` de poppler pour les vignettes). Étapes :
1. crée les _Archive manquants des niveaux ;
2. supprime les fichiers temporaires LaTeX (.aux, .log, ...) ;
3. nettoie les noms de fichiers/dossiers (accents, espaces, caractères spéciaux) ;
4. génère les vignettes de la 1re page des PDF dans assets/thumbs/ (cache : seuls les PDF
   nouveaux ou modifiés sont rendus, les vignettes orphelines sont supprimées) ;
5. réécrit l'index.html de chaque dossier :
   - accueil       : cartes par section (ouvertes dans un nouvel onglet) + récemment ajoutés
   - niveau        : séquences repliables, documents groupés par type, recherche
   - autre dossier : liste façon explorateur (dossiers puis fichiers)
6. écrit la page crédits (credits/), la 404 et term/fs.json (arborescence du terminal /term).
"""

import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import profkey  # documents prof : règles (is_secret) et chiffrement (X.enc)

ROOT = (Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent).resolve()
SITE_TITLE = "Cours de Maths"
AUTHOR = "M. Outerovitch"
SCHOOL = "Collège Jean Moulin"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/deed.fr"

# Sous-dossiers ignorés à l'intérieur des sections (figures sources, caches).
EXCLUDE_DIRS = {"images", "__pycache__"}
HIDDEN_EXT = {".tex", ".sty", ".py", ".sh", ".org", ".md", ".odg", ".txt", ".ico"}
LEVELS = {"Sixieme": "Sixième", "Cinquieme": "Cinquième",
          "Quatrieme": "Quatrième", "Troisieme": "Troisième"}
NAMES = {**LEVELS, "Utils": "Utilitaires", "Progressions": "Progressions",
         "_Archive": "Archives", "credits": "Crédits & liens"}
BLURBS = {"Progressions": "Progressions annuelles par niveau",
          "Utils": "Grilles, tables, fiches à imprimer"}
SECTION_ORDER = ["Progressions", "Sixieme", "Cinquieme", "Quatrieme", "Troisieme", "Utils"]

ASSETS = ROOT / "assets"          # ressources du site (pas du contenu de cours)
ICON_DIR = ASSETS / "icons"
LOGO = ASSETS / "logo.svg"
LOGO_ICON = ASSETS / "calculatrice.svg"  # logotype à gauche du titre (pixel W95, 22×28)
FAVICON = ASSETS / "favicon.ico"        # secours (16/32/64 px)
FAVICON_SVG = ASSETS / "favicon.svg"    # π pixel W95, net à toutes les tailles
CREDITS_DIR = ROOT / "credits"

JUNK_EXT = (".aux", ".log", ".out", ".toc", ".synctex.gz", ".fls", ".fdb_latexmk")
THUMBS = ASSETS / "thumbs"
THUMB_WIDTH = 240
PDFTOPPM = shutil.which("pdftoppm")

TYPES = [("Seq", "Séquence"), ("Prep", "Préparations"), ("Cours", "Cours"),
         ("Act", "Activités"), ("Ex", "Exercices"), ("DS", "Évaluations")]
# Corrigé d'un Ex/Act/DS : son nom + -Corr (Ex-6C04-01-Nom-Corr.pdf, profkey.CORR), affiché sous lui.
DOC_RE = re.compile(r"^(Seq|Prep|Cours|Ex|Act|DS)-([2-6T])C(\d{2})(?:-([0-9]+[a-z]?))?-?(.*)$")
SEQ_RE = re.compile(r"^S(\d{2})-(.+)$")
# Mode prof (clic sur la calculatrice de l'accueil, ou sudo du terminal) : ces types et les
# archives ne sont visibles qu'en mode prof, et publiés seulement chiffrés (X.enc, tools/profkey.py),
# déchiffrés dans le navigateur par assets/prof.js.
PROF_TYPES = profkey.PROF_TYPES
PROF_KEY = "mathematovitch-prof"   # localStorage : session prof, partagée avec term/ (assets/prof.js)
PROF_JS = ASSETS / "prof.js"

# Accents perdus par le nettoyage des noms de fichiers (rename_all)
ACCENTS = {
    "Decimaux": "Décimaux", "Decimale": "Décimale", "Decimales": "Décimales",
    "Egales": "Égales", "Entiere": "Entière", "Entieres": "Entières",
    "Mediatrices": "Médiatrices", "Perimetre": "Périmètre",
    "Perimetres": "Périmètres", "Probabilites": "Probabilités",
    "Proportionnalite": "Proportionnalité", "Donnees": "Données",
    "Operations": "Opérations", "Numeration": "Numération",
    "Satistiques": "Statistiques", "Statistiques": "Statistiques",
    "reciproque": "réciproque", "litteral": "littéral", "Geometrie": "Géométrie",
    "Evaluation": "Évaluation", "Hypotenuse": "Hypoténuse",
    "Paralleles": "Parallèles", "Unite": "Unité", "lUnite": "l'Unité",
    "Graduee": "Graduée", "Graduees": "Graduées", "Consecutifs": "Consécutifs",
    "Decomposition": "Décomposition", "Decomposer": "Décomposer",
    "Problemes": "Problèmes", "Repere": "Repère", "Symetrie": "Symétrie",
}


PROG_FILES = {"Sixieme": "6eme.tex", "Cinquieme": "5eme.tex",
              "Quatrieme": "4eme.tex", "Troisieme": "3eme.tex"}


PROG_DIR = ROOT / "Progressions"
_parse_tex = None


def parse_progression(tex):
    """(nom long, nom court, lignes) de Progressions/NIVEAU.tex, via gen_html.parse_tex."""
    global _parse_tex
    gen = PROG_DIR / "gen_html.py"
    if not (tex.is_file() and gen.is_file()):
        return None
    if _parse_tex is None:
        sys.dont_write_bytecode = True  # pas de Progressions/__pycache__
        spec = importlib.util.spec_from_file_location("gen_html", gen)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _parse_tex = mod.parse_tex
    try:
        return _parse_tex(tex)
    except ValueError as err:
        print(f"Progression ignorée : {err}")
        return None


def load_progression(level):
    """Lignes (séquences et vacances) de la progression d'un niveau."""
    parsed = parse_progression(PROG_DIR / PROG_FILES.get(level, "-"))
    return parsed[2] if parsed else []


def pretty(s):
    words = re.split(r"[-_ ]+", s.strip("-_ "))
    return " ".join(ACCENTS.get(w, w) for w in words if w)


def human_size(n):
    for unit in ("o", "Ko", "Mo"):
        if n < 1024:
            return f"{n:.0f} {unit}"
        n /= 1024
    return f"{n:.1f} Go"


def e(s):
    return html.escape(str(s), quote=True)


_tex = {}


def secret(p):
    """Document prof en clair (profkey.is_secret) : jamais listé ni commité, seul X.enc l'est."""
    def text():
        k = (p, p.stat().st_mtime)
        if k not in _tex:
            _tex[k] = p.read_text("utf-8", "replace")
        return _tex[k]
    return profkey.is_secret(p.relative_to(ROOT).as_posix(), text)


def base(p):
    """Fichier d'origine d'un chiffré : DS-….pdf.enc -> DS-….pdf (sinon p lui-même)."""
    return p.with_suffix("") if p.suffix == profkey.ENC else p


def visible(p):
    if p.name.startswith(".") or p.name == "index.html":
        return False
    if p.parent == ROOT:  # à la racine, seules les sections de cours existent pour le build
        return p.is_dir() and p.name in SECTION_ORDER
    if p.is_dir():
        return p.name not in EXCLUDE_DIRS
    if p.suffix != profkey.ENC and secret(p):
        return False
    return base(p).suffix.lower() not in HIDDEN_EXT


def listdir(d):
    items = [p for p in d.iterdir() if visible(p)]
    dirs = sorted((p for p in items if p.is_dir()), key=lambda p: (p.name == "_Archive", p.name))
    files = sorted((p for p in items if p.is_file()), key=lambda p: p.name.lower())
    return dirs, files


def is_prof(p):
    m = DOC_RE.match(base(p).stem)
    return ("_Archive" in p.relative_to(ROOT).parts or profkey.is_corr(base(p).name)
            or (bool(m) and m[1] in PROF_TYPES))


def enc_attr(f):
    """Lien vers un chiffré : assets/prof.js intercepte le clic et ouvre le document déchiffré."""
    return f' data-enc="{e(base(f).name)}"' if f.suffix == profkey.ENC else ""


def count_docs(d, prof=True):
    return sum(1 for p in d.rglob("*") if p.is_file() and visible(p) and (prof or not is_prof(p))
               and not any(part.startswith(".") for part in p.relative_to(d).parts))


def ndocs(d):
    """Nombre de documents de `d` en HTML : compte élève, et compte prof s'il diffère
    (le CSS n'affiche que celui du mode courant)."""
    a, b = count_docs(d, prof=False), count_docs(d)
    return str(a) if a == b else f'<span class="eleve">{a}</span><span class="prof">{b}</span>'


def rel(from_dir, to):
    return os.path.relpath(to, from_dir).replace(os.sep, "/")


def label(p):
    if p == ROOT:
        return SITE_TITLE
    m = SEQ_RE.match(p.name)
    if m:
        return f"S{m[1]} · {pretty(m[2])}"
    return NAMES.get(p.name, pretty(p.name))


# ---------------------------------------------------------------------------
# Nettoyage

def sections():
    """Dossiers de cours présents, dans l'ordre d'affichage."""
    return [ROOT / s for s in SECTION_ORDER if (ROOT / s).is_dir()]


def ensure_archives():
    for level in LEVELS:
        if (ROOT / level).is_dir():
            (ROOT / level / "_Archive").mkdir(exist_ok=True)


def delete_junk():
    n = 0
    for dirpath, dirnames, filenames in (w for s in sections() for w in os.walk(s)):
        for f in filenames:
            if f.endswith(JUNK_EXT):
                (Path(dirpath) / f).unlink()
                n += 1
    return n


def clean_name(name):
    s = name.replace("œ", "oe").replace("Œ", "OE").replace("æ", "ae").replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9._-]", "_", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")


def rename_all():
    # De bas en haut : les enfants sont renommés avant leur dossier parent.
    for dirpath, dirnames, filenames in (w for s in sections() for w in os.walk(s, topdown=False)):
        d = Path(dirpath)
        for name in [*filenames, *dirnames]:
            if name == "_Archive":
                continue
            cleaned = clean_name(name)
            if not cleaned or cleaned == name:
                continue
            src, dst = d / name, d / cleaned
            if dst.exists():
                print(f"Ignoré (existe déjà) : {dst.relative_to(ROOT)}")
            else:
                src.rename(dst)
                print(f"Renommé : {src.relative_to(ROOT)} -> {cleaned}")


# ---------------------------------------------------------------------------
# Progressions : recompilation PDF si le .tex (ou progtable.sty) a changé

PDFLATEX = shutil.which("pdflatex")
# Date figée : même .tex => PDF identique à l'octet près, donc pas de faux changement git
# si une recompilation se déclenche pour rien (mtime après un pull).
TEX_ENV = {**os.environ, "SOURCE_DATE_EPOCH": "1767225600", "FORCE_SOURCE_DATE": "1"}


def pdflatex(tex, job=None, pre="", passes=2):
    """Compile `tex` dans son dossier (`job` : nom du PDF produit, `pre` : code TeX lu avant
    le fichier), puis supprime nommément les .aux/.log/.out. Renvoie True si tout va bien."""
    job = job or tex.stem
    cmd = [PDFLATEX, "-interaction=nonstopmode", "-halt-on-error", f"-jobname={job}",
           f"{pre}\\input{{{tex.name}}}" if pre else tex.name]
    for _ in range(passes):
        r = subprocess.run(cmd, cwd=tex.parent, capture_output=True, text=True, errors="replace",
                           env=TEX_ENV)
        if r.returncode:
            break
    if r.returncode:
        errors = [l for l in r.stdout.splitlines() if l.startswith("!")]
        print(f"Échec de compilation de {tex.relative_to(ROOT)} ({job}) : "
              f"{' / '.join(errors[:3]) or 'voir pdflatex'}")
    for ext in (".aux", ".log", ".out"):  # nommément, pas de joker
        (tex.parent / f"{job}{ext}").unlink(missing_ok=True)
    return r.returncode == 0


def compile_progressions():
    sty = PROG_DIR / "progtable.sty"
    for tex_name in PROG_FILES.values():
        tex = PROG_DIR / tex_name
        if not tex.is_file():
            continue
        pdf = tex.with_suffix(".pdf")
        newest = max(tex.stat().st_mtime, sty.stat().st_mtime if sty.is_file() else 0)
        if pdf.exists() and pdf.stat().st_mtime >= newest:
            continue
        if not PDFLATEX:
            print(f"pdflatex introuvable : {tex_name} non compilé")
            return
        # 2 passes : longtable a besoin de la 1re pour caler ses largeurs de colonnes.
        if pdflatex(tex):
            print(f"Compilé : Progressions/{pdf.name}")


def corr_of(p):
    """Corrigé associé à un sujet : Ex-6C04-01-Nom.pdf -> Ex-6C04-01-Nom-Corr.pdf."""
    return p.with_name(p.stem + profkey.CORR + p.suffix)


def compile_corriges():
    """Sources à corrigé (\\ifcorrige) : le sujet, puis le corrigé …-Corr.pdf compilé avec
    \\aveccorrige défini. Seulement si le .tex est plus récent que l'un des deux PDF."""
    for lvl in LEVELS:
        if not (ROOT / lvl).is_dir():
            continue
        for tex in sorted((ROOT / lvl).rglob("*.tex")):
            m = DOC_RE.match(tex.stem)
            if not m or m[1] not in ("Ex", "Act", "DS") or "\\ifcorrige" not in tex.read_text("utf-8", "replace"):
                continue
            corr = corr_of(tex.with_suffix(".pdf"))
            todo = [(job, pre) for job, pre in ((tex.stem, ""), (corr.stem, "\\def\\aveccorrige{}"))
                    if not (tex.parent / f"{job}.pdf").exists()
                    or (tex.parent / f"{job}.pdf").stat().st_mtime < tex.stat().st_mtime]
            if todo and not PDFLATEX:
                print(f"pdflatex introuvable : {tex.name} non compilé")
                return
            for job, pre in todo:
                if pdflatex(tex, job, pre):
                    print(f"Compilé : {(tex.parent / job).relative_to(ROOT)}.pdf")


# ---------------------------------------------------------------------------
# Documents prof : chiffrés (X.enc), jamais commités en clair

GITIGNORE = ROOT / ".gitignore"
GI_BEGIN = "# >>> documents prof en clair : seul X.enc est commité (généré par tools/build.py) >>>"
GI_END = "# <<< documents prof en clair <<<"


def encrypt_secrets():
    """Pour chaque document prof en clair (profkey.is_secret), X.enc à jour, puis la liste des X
    dans .gitignore. Sans clé (dev/prof.key), rien n'est chiffré : avertissement seulement.
    Un .enc orphelin n'est supprimé que si son dossier contient des documents prof en clair
    (sur un clone neuf, qui n'a que des .enc, on ne touche à rien)."""
    key = profkey.load_key()
    plain, made, todo = [], 0, 0
    for lvl in LEVELS:
        for p in sorted((ROOT / lvl).rglob("*")) if (ROOT / lvl).is_dir() else []:
            if not p.is_file() or p.suffix == profkey.ENC or not secret(p):
                continue
            plain.append(p)
            enc = p.with_name(p.name + profkey.ENC)
            if enc.exists() and enc.stat().st_mtime >= p.stat().st_mtime:
                continue
            if not key:
                todo += 1
                continue
            data = profkey.encrypt(key, p.relative_to(ROOT).as_posix(), p.read_bytes())
            if enc.exists() and enc.read_bytes() == data:
                os.utime(enc)  # même contenu (mtime seul changé) : pas de faux diff
            else:
                enc.write_bytes(data)
                made += 1
    dirs = {p.parent for p in plain}
    removed, kept = 0, []
    for lvl in LEVELS:
        for x in sorted((ROOT / lvl).rglob("*" + profkey.ENC)) if (ROOT / lvl).is_dir() else []:
            if base(x).exists():
                continue
            if x.parent in dirs:
                x.unlink()
                removed += 1
            else:
                kept.append(x)
    write_gitignore(plain)
    print(f"Documents prof : {len(plain)} en clair (ignorés par git), {made} chiffrés, {removed} .enc orphelins supprimés")
    if todo:
        print(f"  {todo} non chiffrés : pas de clé sur cette machine "
              "(python3 tools/profkey.py init, ou restore avec le mot de passe)")
    for x in kept:
        print(f"  .enc sans fichier en clair, gardé : {x.relative_to(ROOT)}")


def write_gitignore(plain):
    """Bloc généré de .gitignore : motifs fixes (types prof, archives) et chemin exact de chaque
    document prof en clair (les .tex à corrigé ne se reconnaissent qu'à leur contenu)."""
    esc = lambda r: re.sub(r"([*?\[\\])", r"\\\1", r)
    lines = []
    for lvl in LEVELS:
        lines += [f"/{lvl}/**/_Archive/**", f"!/{lvl}/**/_Archive/**/"]
        lines += [f"/{lvl}/**/{t}-*" for t in PROF_TYPES] + [f"/{lvl}/**/*{profkey.CORR}.*"]
    lines += [f"!*{profkey.ENC}", "!index.html"]
    # en clair présents, ou connus par leur .enc : même bloc sur un clone qui n'a que les .enc
    names = {p.relative_to(ROOT).as_posix() for p in plain}
    names |= {base(x).relative_to(ROOT).as_posix() for lvl in LEVELS if (ROOT / lvl).is_dir()
              for x in (ROOT / lvl).rglob("*" + profkey.ENC)}
    lines += sorted("/" + esc(n) for n in names)
    block = "\n".join([GI_BEGIN, *lines, GI_END]) + "\n"
    old = GITIGNORE.read_text("utf-8") if GITIGNORE.exists() else ""
    if GI_BEGIN in old and GI_END in old:
        new = old[:old.index(GI_BEGIN)] + block + old[old.index(GI_END) + len(GI_END) + 1:]
    else:
        new = old.rstrip("\n") + "\n\n" + block
    if new != old:
        GITIGNORE.write_text(new, "utf-8")


# ---------------------------------------------------------------------------
# Vignettes (1re page des PDF)

def thumb_path(pdf):
    return THUMBS / pdf.relative_to(ROOT).with_suffix(".jpg")


def site_pdfs():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        d = Path(dirpath)
        dirnames[:] = [x for x in dirnames if visible(d / x)]
        for f in filenames:
            if f.lower().endswith(".pdf") and not f.startswith(".") and not secret(d / f):
                yield d / f


def build_thumbs():
    if not PDFTOPPM:
        print("pdftoppm introuvable : vignettes non générées (paquet poppler)")
        return
    made, wanted = 0, set()
    for pdf in site_pdfs():
        t = thumb_path(pdf)
        wanted.add(t)
        if t.exists() and t.stat().st_mtime >= pdf.stat().st_mtime:
            continue
        t.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([PDFTOPPM, "-f", "1", "-l", "1", "-singlefile", "-jpeg",
                            "-jpegopt", "quality=70", "-scale-to-x", str(THUMB_WIDTH),
                            "-scale-to-y", "-1", str(pdf), str(t.with_suffix(""))],
                           capture_output=True)
        if r.returncode == 0:
            made += 1
        else:
            print(f"Vignette impossible : {pdf.relative_to(ROOT)}")
    removed = 0
    if THUMBS.is_dir():
        for t in list(THUMBS.rglob("*.jpg")):
            if t not in wanted:
                t.unlink()
                removed += 1
        for dirpath, _, _ in sorted(os.walk(THUMBS), key=lambda x: -len(x[0])):
            if dirpath != str(THUMBS) and not os.listdir(dirpath):
                os.rmdir(dirpath)
    print(f"Vignettes : {made} générées, {removed} supprimées, {len(wanted)} au total")


def thumb_attr(d, f):
    if f.suffix.lower() != ".pdf":
        return ""
    t = thumb_path(f)
    return f' data-thumb="{rel(d, t)}"' if t.exists() else ""


# ---------------------------------------------------------------------------
# Gabarit commun

CSS = """
:root{color-scheme:light;--bg:#fff;--fg:#000;--mut:#555;--line:#000;--soft:#999;--card:#fff;
--acc:#0000ee;--vis:#551a8b;--hover:#ffffcc;--pill:#fff;--navy:#23255f;--orange:#e8590c;
--t-seq:#800080;--t-prep:#007070;--t-cours:#0000a0;--t-act:#806000;--t-ex:#006000;--t-ds:#c00000;--t-res:#555}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 "Times New Roman",Times,serif}
a{color:var(--acc);text-decoration:underline}
a:visited{color:var(--vis)}
a:hover{background:var(--hover)}
.mono,code{font-family:"Courier New",Courier,monospace}
.wrap{max-width:880px;margin:0 auto;padding:0 16px}
.wrap.wide{max-width:1200px}
header.top{border-bottom:1px solid var(--line);background:var(--bg)}
header.top .wrap{display:flex;align-items:center;gap:12px;min-height:40px;padding-top:6px;padding-bottom:6px}
.crumbs{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-family:"Courier New",Courier,monospace;font-size:14px;min-width:0}
.crumbs .sep{color:var(--mut)}
.crumbs .cur{font-weight:bold;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.home{margin-left:auto;font-family:"Courier New",Courier,monospace;font-size:14px;white-space:nowrap}
main{padding:56px 0 64px}
header.top+main{padding-top:24px}
h1{font-size:28px;margin:0 0 4px}
.sub{color:var(--mut);margin:0 0 20px;font-style:italic}
h2{font-size:20px;margin:28px 0 8px;padding-bottom:2px;border-bottom:1px solid var(--line)}
.logo{display:block;width:100%;max-width:640px;height:auto;margin:8px 0 10px;image-rendering:pixelated}
.brand{display:flex;align-items:flex-end;gap:2%;max-width:720px;margin:8px 0 10px}
.brand img{display:block;height:auto;image-rendering:pixelated}
/* calculatrice (22×28) haute comme le M ombre comprise (y 48→144 sur 120 du logo) : 7.62 % ≈ 0.98 × r/(1+r), r = 0.8·120/894·22/28 */
.brand .calc{flex:0 0 7.62%}
.brand .logo{flex:1;min-width:0;max-width:none;margin:0}
/* cartes accueil : simple liste */
.cards{display:block;margin:0;padding:0}
.card{display:block;padding:2px 0}
.card .t{display:inline;font-weight:bold;font-size:18px}
.card .t .ext{color:var(--mut);font-weight:normal;font-size:14px;margin-left:4px;text-decoration:none}
.card .d{display:inline;color:var(--mut);font-size:15px;margin-left:8px}
.card .d::before{content:"— "}
.card:visited .t{color:var(--vis)}
/* listes */
.list{border:1px solid var(--line)}
.row{display:flex;align-items:center;gap:12px;padding:4px 8px;border-top:1px solid var(--soft)}
.row:first-child{border-top:0}
a.row{color:var(--fg);text-decoration:none}
a.row .name{color:var(--acc);text-decoration:underline}
a.row:visited .name{color:var(--vis)}
a.row:hover,.row a.main:hover{background:var(--hover)}
.row .ico{width:18px;flex:none;text-align:center;color:var(--mut)}
.row .name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .meta{color:var(--mut);font-size:13px;white-space:nowrap;font-family:"Courier New",Courier,monospace}
.pill{font-family:"Courier New",Courier,monospace;font-size:12px;font-weight:bold;white-space:nowrap;flex:none;min-width:52px}
.pill::before{content:"["}.pill::after{content:"]"}
/* séquences */
.tools{display:flex;gap:8px;margin:0 0 12px}
.tools input{flex:1;font:inherit;font-family:"Courier New",Courier,monospace;font-size:14px;padding:3px 6px;
border:2px inset #ccc;background:#fff;color:var(--fg)}
.tools button,.tools .btn{font:13px Arial,Helvetica,sans-serif;padding:3px 10px;border:2px outset #ddd;
background:#e0e0e0;color:#000;cursor:pointer;white-space:nowrap;text-decoration:none;display:flex;align-items:center}
.tools button:active,.tools .btn:active{border-style:inset}
.tools .btn:visited{color:#000}
.doc.skill code{color:var(--mut);font-size:12px;flex:none;width:8em}
.godocs{display:block;padding:4px 10px 6px;font-size:14px;border-top:1px dashed var(--soft)}
.meta.soon{font-style:italic}
.row a.main{padding:2px 0}
.row a.dl{font-family:"Courier New",Courier,monospace;font-size:13px}
/* tableau de progression */
.tablewrap{overflow-x:auto}
table.progtab{border-collapse:collapse;width:100%;min-width:760px;font-size:14.5px;border:1px solid var(--line)}
.progtab th{text-align:left;font-weight:bold;padding:4px 8px;border:1px solid var(--line);background:#e0e0e0}
.progtab td{padding:6px 8px;border:1px solid var(--line);vertical-align:top}
.progtab tbody tr:not(.vacrow):hover td{background:var(--hover)}
.progtab td.id{font-family:"Courier New",Courier,monospace;font-size:13px;white-space:nowrap}
.progtab td.tt{font-weight:bold;min-width:150px}
.progtab td.tt .ext{color:var(--mut);font-weight:normal;font-size:12px}
.progtab .cnt{font-weight:normal;font-size:13px;color:var(--mut);margin-top:2px}
.progtab .cnt.soon{font-style:italic}
.progtab ul{margin:0;padding:0 0 0 16px}
.progtab li{padding:0}
.progtab li code{color:var(--mut);font-size:12px;margin-right:4px}
.progtab td.goal{font-style:italic;min-width:160px}
.progtab tr.vacrow td{text-align:center;font-weight:bold;background:#e0e0e0;padding:3px}
.progtab tr:target td{background:var(--hover)}
/* lien « # » d'une séquence : ouvre sa page et copie son adresse */
a.lnk,a.lnk:visited{font:13px "Courier New",Courier,monospace;color:var(--mut);text-decoration:none;padding:0 4px}
a.lnk:hover{color:var(--acc);text-decoration:underline}
details.seq{border:1px solid var(--line);margin-bottom:-1px;scroll-margin-top:16px}
details.seq>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:10px;padding:5px 8px;user-select:none;background:#f0f0f0}
details.seq>summary::-webkit-details-marker{display:none}
details.seq>summary:hover{background:var(--hover)}
details.seq>summary .num{font-family:"Courier New",Courier,monospace;font-size:14px;width:2.6em}
details.seq>summary .tt{flex:1;font-weight:bold}
details.seq>summary .chev{font-family:"Courier New",Courier,monospace;color:var(--fg)}
details.seq>summary .chev{font-size:0}details.seq>summary .chev::after{content:"[+]";font-size:14px}
details.seq[open]>summary .chev::after{content:"[−]"}
details.seq[open]>summary{border-bottom:1px solid var(--line)}
.grp{padding:4px 0}
.grp+.grp{border-top:1px dashed var(--soft)}
.grp h3{font-size:14px;margin:4px 10px 2px;font-weight:bold;text-decoration:underline}
.doc{display:flex;align-items:center;gap:10px;padding:2px 10px 2px 22px}
.doc:hover{background:var(--hover)}
.doc .id{font-family:"Courier New",Courier,monospace;font-size:13px;width:2.8em;flex:none;color:var(--mut)}
.doc .name{flex:1;min-width:0}
.doc .meta{color:var(--mut);font-size:12.5px;font-family:"Courier New",Courier,monospace}
.c-seq{color:var(--t-seq)}.c-prep{color:var(--t-prep)}.c-cours{color:var(--t-cours)}.c-act{color:var(--t-act)}.c-ex{color:var(--t-ex)}
.c-ds,.c-corr{color:var(--t-ds)}.c-res{color:var(--t-res)}
.seq.archive{opacity:.75}
.theme{font-family:"Courier New",Courier,monospace;font-size:12px;color:var(--mut)}
.theme::before{content:"("}.theme::after{content:")"}
.seq.upcoming{display:flex;align-items:center;gap:10px;padding:5px 8px;margin-bottom:-1px;
border:1px dashed var(--soft);color:var(--mut)}
.seq.upcoming .num{font-family:"Courier New",Courier,monospace;font-size:14px;width:2.6em}
.seq.upcoming .tt{flex:1}
.seq.upcoming .meta{font-size:13px;font-style:italic}
.vac{text-align:center;font-weight:bold;margin:14px 0 13px;font-family:"Courier New",Courier,monospace;font-size:14px}
.vac::before{content:"~~~~~~ "}.vac::after{content:" ~~~~~~"}
.prog{padding:6px 10px 2px}
.prog .goal{margin:0;font-size:15px;font-style:italic}
details.skills{margin-top:2px}
details.skills>summary{cursor:pointer;font-size:14px;color:var(--acc);text-decoration:underline;width:max-content}
details.skills ul{margin:4px 0 2px;padding:0 0 0 18px}
details.skills li{font-size:14.5px;padding:1px 0}
details.skills code{color:var(--mut);font-size:12.5px;margin-right:8px}
.i{image-rendering:pixelated;vertical-align:middle;flex:none;border:0}
.i32{margin-right:8px;position:relative;top:-2px}
.i16{image-rendering:auto;margin-right:5px;position:relative;top:-1px}
h3 .i32{margin-right:6px}
.home .i16,.btn .i16{margin-right:4px}
.vac .i16{margin:0 6px 0 0}
.seq.upcoming .meta .i16{opacity:.8}
.hide{display:none!important}
/* mode prof : documents prof (Seq, Prep, DS, corrigés, archives) masqués sinon ; fond rosé + bandeau pour savoir où on en est */
html:not(.prof) .prof,html.prof .eleve{display:none!important}
html.prof body{background:#ffe4e4}
html.prof details.seq>summary,html.prof .seq.upcoming,html.prof .progtab th,html.prof .progtab tr.vacrow td{background:#f4d0d0}
.doc.corr{padding-left:38px}.doc.corr .id{width:1.6em}.doc.corr .name{color:var(--t-ds)}
#profbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;justify-content:center;gap:12px;
padding:3px 8px;background:#c00000;color:#fff;font:bold 13px "Courier New",Courier,monospace}
#profbar button,#login button{font:13px Arial,Helvetica,sans-serif;padding:2px 10px;border:2px outset #ddd;background:#e0e0e0;color:#000;cursor:pointer}
#profbar button:active,#login button:active{border-style:inset}
#login{padding:0;border:2px outset #ddd;background:#e0e0e0;color:#000;font:13px Arial,Helvetica,sans-serif;width:300px}
#login::backdrop{background:rgba(0,0,0,.25)}
#login .tb{background:#000080;color:#fff;font-weight:bold;padding:3px 6px}
#login form{padding:10px;display:grid;gap:8px}
#login input{font:14px "Courier New",Courier,monospace;padding:3px 6px;border:2px inset #ccc;background:#fff}
#login .err{color:#c00000;min-height:1em;margin:0}
#login .bt{display:flex;justify-content:flex-end;gap:8px}
#pv{position:fixed;z-index:20;width:240px;pointer-events:none;background:#fff;border:1px solid #000;
box-shadow:4px 4px 0 #000;opacity:0}
#pv.on{opacity:1}
footer{color:var(--mut);font-size:13px;padding:10px 0 24px;border-top:1px solid var(--line);text-align:center;font-style:italic}
/* impression : noir et blanc, sans boutons ni icônes, tout déplié (PRINT_JS), adresse de la page en tête */
@media print{@page{margin:12mm}
*{color:#000!important;background:none!important;box-shadow:none!important}
body{font-size:11pt}main{padding:0}.wrap,.wrap.wide{max-width:none;padding:0}a{text-decoration:none}
header.top,.tools,.chev,.lnk,.godocs,#pv,.i,footer a,.card .ext,#profbar{display:none!important}
main::before{content:attr(data-url);display:block;font:9pt "Courier New",Courier,monospace;margin-bottom:6pt}
.tablewrap{overflow:visible}table.progtab{min-width:0}
details.seq>summary{border-bottom:1px solid #000}details.seq>summary .meta{display:none}
.grp,.prog,.row,.doc{break-inside:avoid}h2,h3,details.seq>summary{break-after:avoid}
.doc{padding-left:10px}.doc .name::after{content:"  " attr(title);font:8.5pt "Courier New",Courier,monospace}
.row .name{white-space:normal}.seq.archive{opacity:1}footer{padding:6pt 0 0;font-size:9pt}}
@media (max-width:560px){.row .meta.sz,.doc .meta{display:none}h1{font-size:22px}.card .d{display:block;margin-left:0}.card .d::before{content:""}}
"""

PREVIEW_JS = """
(()=>{
if(!matchMedia('(hover:hover)').matches)return;
const pv=document.createElement('img');pv.id='pv';pv.alt='';document.body.append(pv);
let cur=null,mx=0;
// À droite de la liste si la place le permet, sinon près du curseur ; centré sur la ligne.
const place=()=>{if(!cur)return;const w=240,m=16,r=cur.getBoundingClientRect();
 const h=pv.complete&&pv.naturalWidth?pv.offsetHeight:340;
 let x=r.right+m;if(x+w+m>innerWidth)x=mx+w+40<innerWidth?mx+24:mx-w-24;
 const y=Math.max(m,Math.min(r.top+r.height/2-h/2,innerHeight-h-m));
 pv.style.left=x+'px';pv.style.top=y+'px'};
pv.addEventListener('load',place);
document.addEventListener('mouseover',ev=>{const a=ev.target.closest('[data-thumb]');
 mx=ev.clientX;if(a===cur)return;cur=a;
 if(!a){pv.classList.remove('on');return}
 pv.src=a.dataset.thumb;pv.classList.add('on');place()});
addEventListener('scroll',()=>{cur=null;pv.classList.remove('on')},{passive:true});
})();
"""

PROG_JS = """
(()=>{
const q=document.getElementById('q');if(!q)return;
const norm=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const rows=[...document.querySelectorAll('.progtab tbody tr')];
q.addEventListener('input',()=>{const v=norm(q.value.trim());
 rows.forEach(r=>r.classList.toggle('hide',!!v&&(r.classList.contains('vacrow')||!norm(r.textContent).includes(v))))});
addEventListener('keydown',ev=>{if(ev.key==='/'&&document.activeElement!==q){ev.preventDefault();q.focus()}
 if(ev.key==='Escape'){q.value='';q.dispatchEvent(new Event('input'));q.blur()}});
})();
"""

PRINT_JS = """
// Impression : adresse de la page en tête, tout déplier (séquences, compétences) puis remettre comme avant.
(()=>{let shut=[];const m=document.querySelector('main');
if(m)m.dataset.url=location.href.replace(/#.*$/,'').replace(/index\\.html$/,'');
addEventListener('beforeprint',()=>{shut=[...document.querySelectorAll('details:not([open])')];shut.forEach(d=>d.open=true)});
addEventListener('afterprint',()=>{shut.forEach(d=>d.open=false);shut=[]});
})();
"""

LINK_JS = """
// « # » d'une séquence : le lien ouvre sa page (nouvel onglet) et copie son adresse au passage ;
// sur la page de la séquence elle-même, il copie seulement.
const here=location.href.replace(/[#?].*$/,'').replace(/index\\.html$/,'');
document.querySelectorAll('a.lnk').forEach(a=>a.addEventListener('click',ev=>{
 const url=a.href.replace(/index\\.html$/,'');if(url===here)ev.preventDefault();
 const done=()=>{a.textContent='copié';setTimeout(()=>{a.textContent='#'},1400)};
 navigator.clipboard?navigator.clipboard.writeText(url).then(done,()=>{}):0}));
"""

JS = """
(()=>{
const q=document.getElementById('q');if(!q)return;
const seqs=[...document.querySelectorAll('details.seq')];
const key='open:'+location.pathname;
let saved=[];try{saved=JSON.parse(localStorage.getItem(key)||'[]')}catch(_){}
seqs.forEach(d=>{if(saved.includes(d.id))d.open=true;
 d.addEventListener('toggle',()=>{if(q.value)return;
  try{localStorage.setItem(key,JSON.stringify(seqs.filter(x=>x.open).map(x=>x.id)))}catch(_){}})});
// Lien direct vers une séquence : page.html#S03-Fractions-Egales
const target=location.hash&&document.getElementById(decodeURIComponent(location.hash.slice(1)));
if(target&&target.matches('details.seq')){target.open=true;target.scrollIntoView({block:'start'})}
const norm=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
q.addEventListener('input',()=>{const v=norm(q.value.trim());
 seqs.forEach(d=>{let any=false;const title=norm(d.querySelector('summary').textContent);
  d.querySelectorAll(document.documentElement.classList.contains('prof')?'.doc':'.doc:not(.prof)').forEach(r=>{const hit=!v||title.includes(v)||norm(r.textContent).includes(v);
   r.classList.toggle('hide',!hit);any=any||hit});
  d.querySelectorAll('.grp').forEach(g=>g.classList.toggle('hide',!g.querySelector('.doc:not(.hide)')&&!g.matches('.prof')));
  d.classList.toggle('hide',!any);if(v)d.open=any;});
 document.querySelectorAll('.vac,.seq.upcoming').forEach(x=>x.classList.toggle('hide',!!v));
 document.querySelectorAll('section.arch').forEach(a=>a.classList.toggle('hide',!a.querySelector('details.seq:not(.hide)')));
 if(!v)seqs.forEach(d=>d.open=saved.includes(d.id));});
document.getElementById('all').addEventListener('click',()=>{
 const open=!seqs.every(d=>d.open);seqs.forEach(d=>d.open=open)});
addEventListener('keydown',ev=>{if(ev.key==='/'&&document.activeElement!==q){ev.preventDefault();q.focus()}
 if(ev.key==='Escape'){q.value='';q.dispatchEvent(new Event('input'));q.blur()}});
})();
"""


# Dans <head>, avant tout affichage (pas de clignotement) : html.prof si la session prof
# (assets/prof.js) n'a pas expiré. Le reste (liens chiffrés, « Quitter », connexion) : prof.js.
PROF_HEAD_JS = f"""
(()=>{{const k='{PROF_KEY}',h=document.documentElement;
const on=()=>{{try{{const s=JSON.parse(localStorage.getItem(k)||'null');if(s&&s.k&&s.until>Date.now())return true}}catch(_){{}}return false}};
h.classList.toggle('prof',on());
addEventListener('storage',ev=>{{if(ev.key===k||ev.key===null)h.classList.toggle('prof',on())}});
setInterval(()=>h.classList.toggle('prof',on()),60000);
}})();
"""


LOGIN_HTML = ('<dialog id="login"><div class="tb">Mode professeur</div><form>'
              '<label for="pw">Mot de passe :</label><input id="pw" type="password" autocomplete="current-password">'
              '<p class="err"></p><div class="bt"><button type="submit">OK</button>'
              '<button type="button" class="no">Annuler</button></div></form></dialog>')


def module_path(d, p):
    """Chemin d'import d'un module ES : « assets/x.js » tout court serait un nom de paquet
    (refusé par le navigateur), il faut « ./assets/x.js »."""
    r = rel(d, p)
    return r if r.startswith(".") else "./" + r


def bust(p):
    """Suffixe ?v=<empreinte> : les navigateurs gardent le favicon en cache tant que l'URL ne change pas."""
    return f"?v={hashlib.md5(p.read_bytes()).hexdigest()[:8]}" if p.is_file() else ""


def page(d, title, body, script=False, here=None, extra_js="", wide=False, base=None):
    """`here` : page autre que l'index de `d` (le dossier devient alors un lien).
    Pas de barre du haut sur l'accueil (choix de l'utilisateur) : fil d'Ariane ailleurs."""
    top = ""
    if d != ROOT or here:
        crumbs = [f'<a href="{rel(d, ROOT)}/index.html">{e(SITE_TITLE)}</a>']
        chain = [d, *d.relative_to(ROOT).parents][:-1] if d != ROOT else []
        for p in reversed(chain):
            if p == d and not here:
                crumbs.append(f'<span class="cur">{e(label(p))}</span>')
            else:
                crumbs.append(f'<a href="{rel(d, p)}/index.html">{e(label(p))}</a>')
        if here:
            crumbs.append(f'<span class="cur">{e(here)}</span>')
        home = f'<a class="home" href="{rel(d, ROOT)}/index.html">{icon(d, "accueil", 16)} Accueil</a>'
        top = (f'<header class="top"><div class="wrap{" wide" if wide else ""}"><nav class="crumbs">'
               f'{"<span class=sep>/</span>".join(crumbs)}</nav>{home}</div></header>\n')
    favicon = (f'<link rel="icon" href="{rel(d, FAVICON)}{bust(FAVICON)}" sizes="any">'
               f'<link rel="icon" href="{rel(d, FAVICON_SVG)}{bust(FAVICON_SVG)}" type="image/svg+xml">')
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
{f'<base href="{base}">' if base else ""}{favicon}
<style>{CSS}</style>
<script>{PROF_HEAD_JS}</script>
</head>
<body>
<div id="profbar" class="prof">MODE PROF · évaluations et corrigés visibles <button id="profquit" type="button">Quitter</button></div>
{top}<main><div class="wrap{" wide" if wide else ""}">
{body}
</div></main>
<footer><div class="wrap{" wide" if wide else ""}">
<a href="{LICENSE_URL}" target="_blank" rel="noopener license">CC0</a> · libre de tout usage, hors ressources tierces
· <a href="{rel(d, CREDITS_DIR)}/index.html">crédits &amp; liens</a>{f" · mis à jour le {up}" if (up := updated(d)) else ""}
</div></footer>
<script>{PREVIEW_JS}{PRINT_JS}{JS if script else ""}{extra_js}</script>
<script type="module">import {{wire}} from "{module_path(d, PROF_JS)}{bust(PROF_JS)}";wire();</script>
</body>
</html>
"""


SECTION_ICONS = {"Progressions": "progressions", "Sixieme": "sixieme", "Quatrieme": "quatrieme",
                 "Utils": "utils", "_Archive": "archives"}
FILE_ICONS = {".pdf": "pdf", ".html": "html", ".png": "image", ".jpg": "image"}


def icon(d, name, size=32):
    """Icône pixel 32×32 de assets/icons/ (pack rétro), affichée en 32 ou réduite en 16."""
    f = ICON_DIR / f"{name}.png"
    return (f'<img class="i i{size}" src="{rel(d, f)}" alt="" width="{size}" height="{size}">'
            if f.is_file() else "")


def dir_icon(d, p, size=32):
    return icon(d, SECTION_ICONS.get(p.name) or ("niveau" if p.name in LEVELS else "dossier"), size)


def ext_meta(p):
    return f'{base(p).suffix[1:].upper() or "—"} · {human_size(p.stat().st_size)}'


# ---------------------------------------------------------------------------
# Rendu des documents d'une séquence

def doc_row(d, f, item, name, cls=""):
    return (f'<a class="doc{cls}" href="{rel(d, f)}" target="_blank" rel="noopener" title="{e(base(f).name)}"'
            f'{thumb_attr(d, f)}{enc_attr(f)}>'
            f'<span class="id mono">{e(item)}</span><span class="name">{e(name)}</span>'
            f'<span class="meta mono">{e(ext_meta(f))}</span></a>')


def doc_rows(d, files):
    """Documents groupés par type ; chaque corrigé (mode prof) juste sous son sujet."""
    groups = {k: [] for k, _ in TYPES}
    groups["res"] = []
    corrs = {}
    for f in files:
        b = base(f)
        m = DOC_RE.match(b.stem)
        if profkey.is_corr(b.name):
            corrs[b.stem.removesuffix(profkey.CORR)] = f
        elif m:
            kind, _lvl, _chap, item, name = m.groups()
            groups[kind].append((item or "", pretty(name) or kind, f))
        else:
            groups["res"].append(("", pretty(b.stem), f))
    out = []
    for kind, title in [*TYPES, ("res", "Ressources")]:
        if not groups[kind]:
            continue
        cls = "c-" + kind.lower()
        rows = []
        for item, name, f in sorted(groups[kind], key=lambda x: (x[0].zfill(4), x[1])):
            rows.append(doc_row(d, f, item, name, " prof" if kind in PROF_TYPES else ""))
            if kind in ("Ex", "Act", "DS") and (c := corrs.pop(base(f).stem, None)):
                rows.append(doc_row(d, c, "↳", "Corrigé", " corr prof"))
        prof = " prof" if kind in PROF_TYPES else ""
        out.append(f'<div class="grp{prof}"><h3 class="{cls}">{icon(d, kind.lower())}{title}</h3>{"".join(rows)}</div>')
    if corrs:  # corrigé sans sujet (sujet pas encore déposé)
        rows = [doc_row(d, c, (m[4] or "") if m else "", pretty(m[5] if m else s) + " (corrigé)", " prof")
                for s, c in sorted(corrs.items()) for m in [DOC_RE.match(s)]]
        out.append(f'<div class="grp prof"><h3 class="c-ds">{icon(d, "ds")}Corrigés</h3>{"".join(rows)}</div>')
    return "".join(out)


def subdir_rows(d, dirs):
    return "".join(
        f'<a class="doc" href="{rel(d, s)}/index.html">'
        f'<span class="id">{icon(d, "dossier", 16)}</span><span class="name">{e(label(s))}/</span>'
        f'<span class="meta">{ndocs(s)} fichiers</span></a>' for s in dirs)


def skills_block(prog, open_=False):
    """Objectif + compétences de la séquence, repris de la progression."""
    items = []
    for it in prog["items"]:
        code, _, text = it.partition(" — ")
        if not text:
            code, text = "", it
        items.append(f'<li><code>{e(code)}</code><span>{e(text)}</span></li>')
    return (f'<div class="prog"><p class="goal">{e(prog["obj"])}</p>'
            f'<details class="skills"{" open" if open_ else ""}><summary>Compétences · {len(items)}</summary>'
            f'<ul>{"".join(items)}</ul></details></div>')


def seq_block(level_dir, s, archive=False, prog=None, open_=False):
    """Bloc dépliable d'une séquence ; `level_dir` est le dossier de la page qui l'affiche
    (page de niveau, ou la séquence elle-même pour sa propre page, alors dépliée)."""
    dirs, files = listdir(s)
    m = SEQ_RE.match(s.name)
    num, title = (m[1], pretty(m[2])) if m else ("", label(s))
    theme = ""
    inner = ""
    if prog:
        title = prog["titre"]
        theme = f'<span class="theme mono">{e(prog["theme"])}</span>'
        inner = skills_block(prog, open_)
    inner += doc_rows(level_dir, files)
    if dirs:
        inner += f'<div class="grp"><h3 class="c-res">{icon(level_dir, "dossier")}Dossiers</h3>{subdir_rows(level_dir, dirs)}</div>'
    n = ndocs(s)
    link = ('<a class="lnk mono" href="./index.html" title="Copier l\'adresse de cette page">#</a>'
            if level_dir == s else
            f'<a class="lnk mono" href="{rel(level_dir, s)}/index.html" target="_blank" rel="noopener" '
            f'title="Ouvrir la page de la séquence (l\'adresse est copiée)">#</a>')
    return (f'<details class="seq{" archive" if archive else ""}" id="{e(s.name)}"{" open" if open_ else ""}>'
            f'<summary><span class="num mono">{e(num)}</span><span class="tt">{e(title)}</span>'
            f'{theme}{link}<span class="meta mono">{n}</span><span class="chev">›</span></summary>{inner}</details>')


def upcoming_block(d, prog):
    """Séquence prévue dans la progression mais sans dossier pour l'instant."""
    return (f'<div class="seq upcoming"><span class="num mono">{e(prog["id"][-2:])}</span>'
            f'<span class="tt">{e(prog["titre"])}</span>'
            f'<span class="theme mono">{e(prog["theme"])}</span><span class="meta">{icon(d, "a-venir", 16)}à venir</span></div>')


# ---------------------------------------------------------------------------
# Pages

def build_level(d):
    dirs, files = listdir(d)
    seqs = [s for s in dirs if s.name != "_Archive"]
    by_num = {m[1]: s for s in seqs if (m := SEQ_RE.match(s.name))}
    rows = load_progression(d.name)
    progs = {r["id"][-2:]: r for r in rows if "id" in r}
    # Ordre de la progression (avec les vacances), puis les dossiers qu'elle ne cite pas.
    blocks, done = [], set()
    for r in rows:
        if "vacances" in r:
            blocks.append(f'<div class="vac">{icon(d, "vacances", 16)}{e(r["vacances"])}</div>')
            continue
        num = r["id"][-2:]
        if num in by_num:
            blocks.append(seq_block(d, by_num[num], prog=r))
            done.add(by_num[num])
        elif int(num) < 90:  # 6C99 & co : « non traité cette année »
            blocks.append(upcoming_block(d, r))
    blocks += [seq_block(d, s) for s in seqs if s not in done]
    while blocks and blocks[-1].startswith('<div class="vac">'):
        blocks.pop()
    archive = d / "_Archive"
    arch = ""
    if archive.is_dir():
        adirs, _ = listdir(archive)
        if adirs:
            arch = (f'<section class="arch prof"><h2>{icon(d, "archives")}Archives</h2>'
                    + "".join(seq_block(d, s, archive=True,
                                        prog=progs.get(SEQ_RE.match(s.name)[1]) if SEQ_RE.match(s.name) else None)
                              for s in adirs) + "</section>")
    prog_html = PROG_DIR / PROG_FILES.get(d.name, "-")
    prog_btn = (f'<a class="btn" href="{rel(d, prog_html.with_suffix(".html"))}" target="_blank" '
                f'rel="noopener">{icon(d, "progressions", 16)}Progression ↗</a>' if rows else "")
    loose = f'<h2>Autres fichiers</h2><div class="list">{file_rows(d, files)}</div>' if files else ""
    body = (f'<h1>{dir_icon(d, d)}{e(label(d))}</h1><p class="sub">{len(seqs)} séquences · {ndocs(d)} documents</p>'
            f'<div class="tools"><input id="q" type="search" placeholder="Rechercher un document…  ( / )" autocomplete="off">'
            f'<button id="all" type="button">Tout déplier</button>{prog_btn}</div>'
            + "".join(blocks) + arch + loose)
    return page(d, f"{label(d)} — {SITE_TITLE}", body, script=True, extra_js=LINK_JS)


def seq_level(d):
    """Niveau d'un dossier de séquence (Sixieme/S04-…, Sixieme/_Archive/S98-…), sinon None."""
    if not SEQ_RE.match(d.name):
        return None
    up = d.parent.parent if d.parent.name == "_Archive" else d.parent
    return up.name if up.parent == ROOT and up.name in LEVELS else None


def build_seq(d, level):
    """Page propre d'une séquence : son seul bloc, déplié, compétences comprises."""
    num = SEQ_RE.match(d.name)[1]
    prog = next((r for r in load_progression(level) if r.get("id", "")[-2:] == num), None)
    archive = d.parent.name == "_Archive"
    title = prog["titre"] if prog else pretty(SEQ_RE.match(d.name)[2])
    sub = f"{LEVELS[level]} · séquence {num}{' (archive)' if archive else ''}"
    body = (f'<h1>{icon(d, "dossier-ouvert")}{e(title)}</h1><p class="sub">{e(sub)} · {ndocs(d)} documents</p>'
            + seq_block(d, d, archive=archive, prog=prog, open_=True))
    return page(d, f"{title} — {LEVELS[level]} — {SITE_TITLE}", reserved(d, body), extra_js=LINK_JS)


def reserved(d, body):
    """Pages d'archives : contenu visible en mode prof seulement."""
    if "_Archive" not in d.relative_to(ROOT).parts:
        return body
    return f'<p class="eleve sub">Réservé au professeur.</p><div class="prof">{body}</div>'


def file_rows(d, files):
    return "".join(
        f'<a class="row{" prof" if is_prof(f) else ""}" href="{rel(d, f)}" target="_blank" rel="noopener"'
        f'{thumb_attr(d, f)}{enc_attr(f)}><span class="ico">{icon(d, FILE_ICONS.get(base(f).suffix.lower(), "res"), 16)}</span>'
        f'<span class="name">{e(base(f).name)}</span>'
        f'<span class="meta sz mono">{e(ext_meta(f))}</span></a>' for f in files)


def build_generic(d):
    dirs, files = listdir(d)
    rows = "".join(
        f'<a class="row" href="{rel(d, s)}/index.html"><span class="ico">{icon(d, "dossier", 16)}</span>'
        f'<span class="name">{e(label(s))}/</span><span class="meta mono">{ndocs(s)} fichiers</span></a>'
        for s in dirs) + file_rows(d, files)
    body = (f'<h1>{dir_icon(d, d) if d.name in SECTION_ICONS else icon(d, "dossier-ouvert")}{e(label(d))}</h1><p class="sub">{len(dirs)} dossiers · {len(files)} fichiers</p>'
            f'<div class="list">{rows or "<div class=row><span class=name>Dossier vide</span></div>"}</div>')
    return page(d, f"{label(d)} — {SITE_TITLE}", reserved(d, body))


def level_of_prog(tex_name):
    return next((lvl for lvl, t in PROG_FILES.items() if t == tex_name), None)


def build_prog_page(tex):
    long_name, _short, rows = parse_progression(tex)
    level = level_of_prog(tex.name)
    level_dir = ROOT / level if level else None
    folders, archived = {}, {}
    if level_dir and level_dir.is_dir():
        folders = {m[1]: s for s in listdir(level_dir)[0] if (m := SEQ_RE.match(s.name))}
        if (level_dir / "_Archive").is_dir():
            archived = {m[1]: s for s in listdir(level_dir / "_Archive")[0]
                        if (m := SEQ_RE.match(s.name))}
    trs, nseq, nvac = [], 0, 0
    for r in rows:
        if "vacances" in r:
            nvac += 1
            trs.append(f'<tr class="vacrow"><td colspan="5">{e(r["vacances"])}</td></tr>')
            continue
        nseq += 1
        num = r["id"][-2:]
        skills = []
        for it in r["items"]:
            code, _, text = it.partition(" — ")
            if not text:
                code, text = "", it
            skills.append(f'<li><code>{e(code)}</code> {e(text)}</li>')
        folder = folders.get(num) or archived.get(num)
        if folder:
            note = " · archivé" if num not in folders else ""
            title = (f'<a href="{rel(PROG_DIR, folder)}/index.html" target="_blank" '
                     f'rel="noopener" title="Page de la séquence">{e(r["titre"])} <span class="ext">↗</span></a>'
                     f'<div class="cnt mono">{ndocs(folder)} docs{note}</div>')
        else:
            soon = "non traité" if int(num) >= 90 else "à venir"
            title = f'{e(r["titre"])}<div class="cnt soon">{soon}</div>'
        trs.append(f'<tr id="{e(r["id"])}"><td class="mono id">{e(r["id"])}</td><td class="tt">{title}</td>'
                   f'<td><span class="theme mono">{e(r["theme"])}</span></td>'
                   f'<td><ul>{"".join(skills)}</ul></td><td class="goal">{e(r["obj"])}</td></tr>')
    pdf = tex.with_suffix(".pdf")
    extra = ""
    if pdf.is_file():
        extra += f'<a class="btn" href="{pdf.name}" target="_blank" rel="noopener">{icon(PROG_DIR, "disquette", 16)}PDF ↗</a>'
    if level_dir and level_dir.is_dir():
        extra += f'<a class="btn" href="{rel(PROG_DIR, level_dir)}/index.html" target="_blank" rel="noopener">{dir_icon(PROG_DIR, level_dir, 16)}Documents ↗</a>'
    body = (f'<h1>{icon(PROG_DIR, "progressions")}Progression — {e(long_name)}</h1>'
            f'<p class="sub">{nseq} séquences · {nvac} périodes de vacances</p>'
            f'<div class="tools"><input id="q" type="search" placeholder="Filtrer…  ( / )" autocomplete="off">{extra}</div>'
            f'<div class="tablewrap"><table class="progtab"><thead><tr><th>Séquence</th><th>Titre</th>'
            f'<th>Thème</th><th>Compétences</th><th>Objectif principal</th></tr></thead>'
            f'<tbody>{"".join(trs)}</tbody></table></div>')
    return page(PROG_DIR, f"Progression {long_name} — {SITE_TITLE}", body, extra_js=PROG_JS,
                here=f"Progression {long_name}", wide=True)


def build_prog_index():
    rows, generated = [], set()
    for tex_name in PROG_FILES.values():
        tex = PROG_DIR / tex_name
        parsed = parse_progression(tex)
        if not parsed:
            continue
        long_name, _, prows = parsed
        html_f, pdf = tex.with_suffix(".html"), tex.with_suffix(".pdf")
        generated |= {html_f, pdf}
        nseq = sum("id" in r for r in prows)
        pdf_link = (f'<a class="meta mono dl" href="{pdf.name}" target="_blank" rel="noopener"'
                    f'{thumb_attr(PROG_DIR, pdf)}>{icon(PROG_DIR, "disquette", 16)}PDF ↗</a>' if pdf.is_file() else "")
        rows.append(f'<div class="row"><span class="ico">{icon(PROG_DIR, "progressions", 16)}</span><a class="name main" href="{html_f.name}">'
                    f'<b>{e(long_name)}</b></a><span class="meta">{nseq} séquences</span>{pdf_link}</div>')
    _, files = listdir(PROG_DIR)
    others = [f for f in files if f not in generated and f.stat().st_size > 0]
    body = (f'<h1>{icon(PROG_DIR, "progressions")}Progressions</h1><p class="sub">Progressions annuelles par niveau</p>'
            f'<div class="list">{"".join(rows)}</div>'
            + (f'<h2>Autres documents</h2><div class="list">{file_rows(PROG_DIR, others)}</div>' if others else ""))
    return page(PROG_DIR, f"Progressions — {SITE_TITLE}", body)


def build_progressions():
    for tex_name in PROG_FILES.values():
        tex = PROG_DIR / tex_name
        if parse_progression(tex):
            tex.with_suffix(".html").write_text(build_prog_page(tex), "utf-8")
    (PROG_DIR / "index.html").write_text(build_prog_index(), "utf-8")


MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
_dates = None


def updated(d):
    """« 25 octobre 2026 » : dernière modification du contenu de `d` (dernier commit, ou aujourd'hui
    si des fichiers ne sont pas committés). Les pages générées sont ignorées : relancer le build
    ne change pas la date, donc pas de faux diff."""
    global _dates
    if _dates is None:
        _dates = {}
        secs = [str(p.relative_to(ROOT)) for p in sections()]
        try:
            git = lambda *a: subprocess.run(["git", "-C", str(ROOT), *a, "--", *secs],
                                            capture_output=True, text=True, check=True).stdout
            log, status = git("log", "--format=@%cs", "--name-only"), git("status", "--porcelain", "-uall")
        except (OSError, subprocess.CalledProcessError):
            return None

        def add(path, day):
            p = ROOT / path
            if p.name == "index.html" or (p.parent == PROG_DIR and p.suffix == ".html"):
                return
            for a in p.parents:
                if _dates.get(a, "") < day:
                    _dates[a] = day
        day = ""
        for line in log.splitlines():
            if line.startswith("@"):
                day = line[1:]
            elif line:
                add(line, day)
        for line in status.splitlines():
            add(line[3:].split(" -> ")[-1].strip('"'), date.today().isoformat())
    day = _dates.get(d)
    if not day:
        return None
    y, m, j = map(int, day.split("-"))
    return f"{j} {MOIS[m - 1]} {y}"


def recent_files(n=8):
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "--diff-filter=A", "--name-only",
                              "--format=@%cs", "-n", "60"], capture_output=True, text=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    # n documents élève, et au plus n documents prof (masqués aux élèves) intercalés
    seen, res, date, count = set(), [], "", {False: 0, True: 0}
    for line in out.splitlines():
        if count[False] >= n:
            break
        if line.startswith("@"):
            date = line[1:]
        elif line:
            p = ROOT / line
            if p.is_file() and visible(p) and base(p).suffix == ".pdf" and p not in seen \
                    and p.relative_to(ROOT).parts[0] in LEVELS and count[is_prof(p)] < n:
                seen.add(p)
                count[is_prof(p)] += 1
                res.append((date, p))
    return res


def build_404():
    """404.html : servie par GitHub Pages à n'importe quelle profondeur, d'où <base href="/">."""
    dirs, _ = listdir(ROOT)
    dirs.sort(key=lambda p: SECTION_ORDER.index(p.name) if p.name in SECTION_ORDER else 99)
    cards = "".join(f'<a class="card" href="{s.name}/index.html"><div class="t">{dir_icon(ROOT, s)}{e(label(s))}</div></a>'
                    for s in dirs)
    body = (f'<h1>{icon(ROOT, "erreur")}Page introuvable</h1>'
            '<p class="sub">Le document a peut-être été déplacé ou renommé : '
            '<code id="miss" class="mono"></code></p>'
            f'<div class="cards">{cards}</div>'
            '<script>document.getElementById("miss").textContent=decodeURIComponent(location.pathname)</script>')
    return page(ROOT, f"Page introuvable — {SITE_TITLE}", body, here="Page introuvable", base="/")


CREDITS = [
    ("Ressources tierces utilisées sur ce site", [
        ("Retro Computer Icons Set (110 icons)", "https://gdainti.itch.io/retro-computer-icons-set-110-icons",
         "icônes pixel du site, par gdainti"),
        ("Sésamath", "https://www.sesamath.net", "manuels et figures (fichiers Sesa-…)"),
        ("Mathsenligne", "https://mathsenligne.net", "fiches d'exercices (dossiers mathsenligne/)"),
        ("Police figlet « Doh »", "http://www.figlet.org/", "chiffres de la commande clock du terminal, par Curtis Wanner"),
    ]),
    ("Liens utiles", [
        ("m@ths et tiques", "https://www.maths-et-tiques.fr", "cours, exercices et vidéos d'Yvan Monka"),
    ]),
]


def build_credits():
    body = ['<h1>Crédits &amp; liens</h1><p class="sub">Les ressources tierces restent sous la licence '
            'de leurs auteurs (elles ne sont pas couvertes par la CC0 du site).</p>']
    for title, links in CREDITS:
        body.append(f'<h2>{e(title)}</h2><ul>')
        body += [f'<li><a href="{url}" target="_blank" rel="noopener">{e(name)}</a> — {e(desc)}</li>'
                 for name, url, desc in links]
        body.append('</ul>')
    return page(CREDITS_DIR, f"Crédits & liens — {SITE_TITLE}", "".join(body))


def term_tree(d):
    """Arborescence pour le terminal web (term/) : dossier -> dict, fichier -> taille en octets.
    Racine : sections de cours seulement. Les fichiers HIDDEN_EXT sont inclus : le terminal
    ne les montre qu'en mode sudo. Les documents prof y sont sous leur nom d'origine (X), le
    terminal va chercher X.enc (liste « enc » de fs.json)."""
    out = {}
    for p in sorted(d.iterdir(), key=lambda p: p.name):
        if p.name.startswith(".") or p.name == "index.html" or p.is_symlink():
            continue
        if d == ROOT and p.name not in SECTION_ORDER:
            continue
        if p.is_dir():
            if p.name not in EXCLUDE_DIRS:
                out[p.name] = term_tree(p)
        elif p.suffix == profkey.ENC:
            out[p.name[:-len(profkey.ENC)]] = p.stat().st_size  # sous son nom d'origine
        elif not secret(p):
            out[p.name] = p.stat().st_size
    return out


def build_term_fs():
    """term/fs.json : seule source de données du terminal (pas d'API, site statique)."""
    if not (ROOT / "term").is_dir():
        return
    data = {"title": SITE_TITLE, "author": AUTHOR, "school": SCHOOL, "year": school_year(),
            "hidden": sorted(HIDDEN_EXT), "prof": [f"{t}-" for t in PROF_TYPES] + ["_Archive"], "prof_suffix": [profkey.CORR],
            "enc": sorted(base(x).relative_to(ROOT).as_posix() for lvl in LEVELS if (ROOT / lvl).is_dir()
                          for x in (ROOT / lvl).rglob("*" + profkey.ENC)),
            "tree": term_tree(ROOT)}
    (ROOT / "term" / "fs.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), "utf-8")


def school_year():
    """Année scolaire en cours, basculée au 1er août : « 2026-2027 »."""
    today = date.today()
    start = today.year if today.month >= 8 else today.year - 1
    return f"{start}-{start + 1}"


def build_home():
    dirs, _ = listdir(ROOT)
    dirs.sort(key=lambda p: SECTION_ORDER.index(p.name) if p.name in SECTION_ORDER else 99)
    cards = []
    for s in dirs:
        sub_dirs, _ = listdir(s)
        if s.name in LEVELS:
            nseq = len([x for x in sub_dirs if SEQ_RE.match(x.name)])
            desc = f"{nseq} séquences · {ndocs(s)} documents"
        else:
            desc = e(BLURBS.get(s.name, "")) or f"{ndocs(s)} fichiers"
        cards.append(f'<a class="card" href="{s.name}/index.html" target="_blank" rel="noopener">'
                     f'<div class="t">{dir_icon(ROOT, s)}{e(label(s))}<span class="ext">↗</span></div>'
                     f'<div class="d">{desc}</div></a>')
    head = (f'<h1><img class="logo" src="{rel(ROOT, LOGO)}" alt="Mathématovitch" width="894" height="120"></h1>'
            if LOGO.is_file() else f"<h1>{e(SITE_TITLE)}</h1>")
    if LOGO.is_file() and LOGO_ICON.is_file():
        # largeurs en % de la ligne pour que calculatrice et titre gardent la même hauteur
        head = (f'<h1 class="brand"><img class="calc" src="{rel(ROOT, LOGO_ICON)}" alt="" width="22" height="28">'
                f'<img class="logo" src="{rel(ROOT, LOGO)}" alt="Mathématovitch" width="894" height="120"></h1>')
    recent = recent_files()
    rec = ""
    if recent:
        rows = []
        for date, p in recent:
            m = DOC_RE.match(base(p).stem)
            kind = "Corr" if profkey.is_corr(base(p).name) else m[1] if m else "res"
            name = pretty(m[5]) if m else pretty(base(p).stem)
            lvl = NAMES.get(p.relative_to(ROOT).parts[0], "")
            rows.append(f'<a class="row{" prof" if is_prof(p) else ""}" href="{rel(ROOT, p)}" target="_blank" rel="noopener"{thumb_attr(ROOT, p)}{enc_attr(p)}>'
                        f'<span class="pill c-{kind.lower()}">{e(kind)}</span>'
                        f'<span class="name">{e(name)}</span>'
                        f'<span class="meta">{e(lvl)} · {e(label(p.parent))}</span>'
                        f'<span class="meta sz mono">{e(date)}</span></a>')
        rec = f'<h2>{icon(ROOT, "recent")}Récemment ajoutés</h2><div class="list">{"".join(rows)}</div>'
    body = (f'{head}<p class="sub">Cours de {e(AUTHOR)} · {e(SCHOOL)} · année {school_year()}</p>'
            f'<h2>{icon(ROOT, "dossier")}Sections</h2><div class="cards">{"".join(cards)}</div>{rec}')
    return page(ROOT, SITE_TITLE, body + LOGIN_HTML)


def main():
    ensure_archives()
    compile_progressions()
    compile_corriges()
    print(f"{delete_junk()} fichiers temporaires LaTeX supprimés")
    rename_all()
    encrypt_secrets()
    build_thumbs()
    build_progressions()
    n = 0
    (ROOT / "index.html").write_text(build_home(), "utf-8")
    (ROOT / "404.html").write_text(build_404(), "utf-8")
    CREDITS_DIR.mkdir(exist_ok=True)
    (CREDITS_DIR / "index.html").write_text(build_credits(), "utf-8")
    build_term_fs()
    # Pages a beau masquer les documents prof, les moteurs suivraient quand même les liens.
    (ROOT / "robots.txt").write_text("User-agent: *\n" + "".join(f"Disallow: /*/{t}-\n" for t in PROF_TYPES)
                                     + f"Disallow: /*{profkey.CORR}.\nDisallow: /*/_Archive/\nDisallow: /*.enc$\n", "utf-8")
    (ROOT / ".nojekyll").touch()  # sinon GitHub Pages (Jekyll) ne publie pas les dossiers _Archive
    n += 1
    for dirpath, dirnames, _ in os.walk(ROOT):
        d = Path(dirpath)
        dirnames[:] = [x for x in dirnames if visible(d / x)]
        if d in (ROOT, PROG_DIR):  # PROG_DIR : fait par build_progressions()
            continue
        is_level = d.parent == ROOT and d.name in LEVELS
        level = seq_level(d)
        (d / "index.html").write_text(build_level(d) if is_level else build_seq(d, level) if level
                                      else build_generic(d), "utf-8")
        n += 1
    print(f"{n} index.html générés")


if __name__ == "__main__":
    main()
