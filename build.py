#!/usr/bin/env python3
"""Construit le nouveau site en une passe (build.sh l'appelle, puis génère legacy/).

Usage : python3 build.py [racine]      (ou ./build.sh, qui fait aussi legacy/)

Stdlib uniquement (+ `pdftoppm` de poppler pour les vignettes, optionnel). Étapes :
1. crée les _Archive manquants des niveaux ;
2. supprime les fichiers temporaires LaTeX (.aux, .log, ...) ;
3. nettoie les noms de fichiers/dossiers (accents, espaces, caractères spéciaux) ;
4. génère les vignettes de la 1re page des PDF dans thumbs/ (cache : seuls les PDF
   nouveaux ou modifiés sont rendus, les vignettes orphelines sont supprimées) ;
5. réécrit l'index.html de chaque dossier :
   - accueil       : cartes par section (ouvertes dans un nouvel onglet) + récemment ajoutés
   - niveau        : séquences repliables, documents groupés par type, recherche
   - autre dossier : liste façon explorateur (dossiers puis fichiers)
"""

import html
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
SITE_TITLE = "Cours de Maths"
AUTHOR = "Colin Outerovitch"
SCHOOL = "Collège Jean Moulin"
LICENSE_URL = "https://creativecommons.org/publicdomain/zero/1.0/deed.fr"

EXCLUDE_DIRS = {"dev", "todo", ".git", ".scripts", "__pycache__", "thumbs", "legacy"}
HIDDEN_EXT = {".tex", ".sty", ".py", ".sh", ".org", ".md", ".odg", ".txt", ".ico"}
LEVELS = {"Sixieme": "Sixième", "Cinquieme": "Cinquième",
          "Quatrieme": "Quatrième", "Troisieme": "Troisième"}
NAMES = {**LEVELS, "Utils": "Utilitaires", "Progressions": "Progressions",
         "_Archive": "Archives"}
BLURBS = {"Progressions": "Progressions annuelles par niveau",
          "Utils": "Grilles, tables, fiches à imprimer"}
SECTION_ORDER = ["Progressions", "Sixieme", "Cinquieme", "Quatrieme", "Troisieme", "Utils"]

JUNK_EXT = (".aux", ".log", ".out", ".toc", ".synctex.gz", ".fls", ".fdb_latexmk")
THUMBS = ROOT / "thumbs"
THUMB_WIDTH = 240
PDFTOPPM = shutil.which("pdftoppm")

TYPES = [("Seq", "Séquence"), ("Prep", "Préparations"), ("Cours", "Cours"),
         ("Act", "Activités"), ("Ex", "Exercices"), ("DS", "Évaluations")]
DOC_RE = re.compile(r"^(Seq|Prep|Cours|Ex|Act|DS)-([2-6T])C(\d{2})(?:-([0-9]+[a-z]?))?-?(.*)$")
SEQ_RE = re.compile(r"^S(\d{2})-(.+)$")

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


def visible(p):
    if p.name.startswith(".") or p.name == "index.html":
        return False
    if p.is_dir():
        return p.name not in EXCLUDE_DIRS
    return p.suffix.lower() not in HIDDEN_EXT


def listdir(d):
    items = [p for p in d.iterdir() if visible(p)]
    dirs = sorted((p for p in items if p.is_dir()), key=lambda p: (p.name == "_Archive", p.name))
    files = sorted((p for p in items if p.is_file()), key=lambda p: p.name.lower())
    return dirs, files


def count_docs(d):
    return sum(1 for p in d.rglob("*") if p.is_file() and visible(p)
               and not any(part.startswith(".") for part in p.relative_to(d).parts))


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

def ensure_archives():
    for level in LEVELS:
        if (ROOT / level).is_dir():
            (ROOT / level / "_Archive").mkdir(exist_ok=True)


def delete_junk():
    n = 0
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [x for x in dirnames if x != ".git"]
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
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
        d = Path(dirpath)
        if ".git" in d.relative_to(ROOT).parts:
            continue
        for name in [*filenames, *dirnames]:
            if name in (".git", "_Archive"):
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

def compile_progressions():
    pdflatex = shutil.which("pdflatex")
    sty = PROG_DIR / "progtable.sty"
    for tex_name in PROG_FILES.values():
        tex = PROG_DIR / tex_name
        if not tex.is_file():
            continue
        pdf = tex.with_suffix(".pdf")
        newest = max(tex.stat().st_mtime, sty.stat().st_mtime if sty.is_file() else 0)
        if pdf.exists() and pdf.stat().st_mtime >= newest:
            continue
        if not pdflatex:
            print(f"pdflatex introuvable : {tex_name} non compilé")
            return
        # Date figée : même .tex => PDF identique à l'octet près, donc pas de faux
        # changement git si une recompilation se déclenche pour rien (mtime après un pull).
        env = {**os.environ, "SOURCE_DATE_EPOCH": "1767225600", "FORCE_SOURCE_DATE": "1"}
        # 2 passes : longtable a besoin de la 1re pour caler ses largeurs de colonnes.
        for _ in range(2):
            r = subprocess.run([pdflatex, "-interaction=nonstopmode", "-halt-on-error", tex_name],
                               cwd=PROG_DIR, capture_output=True, text=True, errors="replace",
                               env=env)
            if r.returncode:
                break
        if r.returncode:
            errors = [l for l in r.stdout.splitlines() if l.startswith("!")]
            print(f"Échec de compilation de {tex_name} : {' / '.join(errors[:3]) or 'voir pdflatex'}")
        else:
            print(f"Compilé : Progressions/{pdf.name}")
        for ext in (".aux", ".log", ".out"):  # nommément, pas de joker
            tex.with_suffix(ext).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Vignettes (1re page des PDF)

def thumb_path(pdf):
    return THUMBS / pdf.relative_to(ROOT).with_suffix(".jpg")


def site_pdfs():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        d = Path(dirpath)
        dirnames[:] = [x for x in dirnames if visible(d / x)]
        for f in filenames:
            if f.lower().endswith(".pdf") and not f.startswith("."):
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
:root{--bg:#fafaf9;--fg:#1c1c1a;--mut:#6b6b66;--line:#e4e3df;--card:#fff;
--acc:#2547d0;--hover:#f1f0ec;--pill:#efeee9;
--t-seq:#6a3fb5;--t-prep:#00707a;--t-cours:#2547d0;--t-act:#8a5a00;--t-ex:#1f7a4d;--t-ds:#b3261e;--t-res:#6b6b66}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#e9e8e4;--mut:#9a9993;
--line:#2c2c2a;--card:#1d1d1b;--acc:#8aa4ff;--hover:#252523;--pill:#2a2a28;
--t-seq:#c3a6ff;--t-prep:#5fd0d8;--t-cours:#8aa4ff;--t-act:#e0b45c;--t-ex:#6fcf9b;--t-ds:#ff8a80;--t-res:#9a9993}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);
font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:inherit;text-decoration:none}
.mono,code{font-family:ui-monospace,"JetBrains Mono",Menlo,Consolas,monospace}
.wrap{max-width:880px;margin:0 auto;padding:0 16px}
.wrap.wide{max-width:1200px}
header.top{border-bottom:1px solid var(--line);background:var(--bg);position:sticky;top:0;z-index:5}
header.top .wrap{display:flex;align-items:center;gap:12px;height:52px}
.crumbs{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:14px;color:var(--mut);min-width:0}
.crumbs a:hover{color:var(--fg)}
.crumbs .sep{opacity:.5}
.crumbs .cur{color:var(--fg);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.home{margin-left:auto;font-size:13px;color:var(--mut);border:1px solid var(--line);
border-radius:6px;padding:3px 9px;white-space:nowrap}
.home:hover{color:var(--fg);background:var(--hover)}
main{padding:28px 0 64px}
h1{font-size:26px;letter-spacing:-.01em;margin:0 0 4px}
.sub{color:var(--mut);margin:0 0 24px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);
font-weight:600;margin:36px 0 10px}
.banner{font-size:9px;line-height:1.15;color:var(--fg);margin:0 0 6px;overflow:hidden;white-space:pre}
/* cartes accueil */
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:16px 16px 14px;transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--acc);transform:translateY(-1px)}
.card .t{font-weight:600;font-size:17px;display:flex;justify-content:space-between;align-items:center}
.card .t .ext{color:var(--mut);font-size:13px;font-weight:400}
.card .d{color:var(--mut);font-size:13px;margin-top:4px}
/* listes */
.list{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
.row{display:flex;align-items:center;gap:12px;padding:9px 14px;border-top:1px solid var(--line)}
.row:first-child{border-top:0}
a.row:hover,.row a.main:hover{background:var(--hover)}
.row .ico{width:18px;flex:none;text-align:center;color:var(--mut)}
.row .name{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.row .meta{color:var(--mut);font-size:12.5px;white-space:nowrap}
.pill{font-size:11px;font-weight:600;padding:1px 7px;border-radius:99px;background:var(--pill);
white-space:nowrap;flex:none;min-width:44px;text-align:center}
/* séquences */
.tools{display:flex;gap:8px;margin:0 0 14px}
.tools input{flex:1;font:inherit;padding:8px 12px;border:1px solid var(--line);border-radius:8px;
background:var(--card);color:var(--fg);outline:none}
.tools input:focus{border-color:var(--acc)}
.tools button{font:inherit;font-size:13px;padding:0 12px;border:1px solid var(--line);
border-radius:8px;background:var(--card);color:var(--mut);cursor:pointer}
.tools button:hover,.tools .btn:hover{color:var(--fg);background:var(--hover)}
.tools .btn{display:flex;align-items:center;font-size:13px;padding:0 12px;border:1px solid var(--line);
border-radius:8px;background:var(--card);color:var(--mut);white-space:nowrap}
.doc.skill code{color:var(--mut);font-size:12px;flex:none;width:8em}
.godocs{display:block;padding:8px 14px 10px;font-size:13px;color:var(--acc);border-top:1px dashed var(--line)}
.godocs:hover{background:var(--hover)}
.meta.soon{font-style:italic}
.row a.main{padding:2px 0}
.row a.dl{border:1px solid var(--line);border-radius:6px;padding:1px 8px}
.row a.dl:hover{color:var(--fg);background:var(--hover)}
/* tableau de progression */
.tablewrap{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table.progtab{border-collapse:collapse;width:100%;min-width:760px;font-size:13.5px}
.progtab th{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;
color:var(--mut);font-weight:600;padding:10px 12px;border-bottom:1px solid var(--line);background:var(--bg)}
.progtab td{padding:10px 12px;border-top:1px solid var(--line);vertical-align:top}
.progtab tbody tr:first-child td{border-top:0}
.progtab tbody tr:not(.vacrow):hover td{background:var(--hover)}
.progtab td.id{color:var(--mut);font-size:12.5px;white-space:nowrap}
.progtab td.tt{font-weight:600;min-width:150px}
.progtab td.tt a:hover{color:var(--acc)}
.progtab td.tt .ext{color:var(--mut);font-weight:400;font-size:12px}
.progtab .cnt{font-weight:400;font-size:12px;color:var(--mut);margin-top:2px}
.progtab .cnt.soon{font-style:italic}
.progtab ul{list-style:none;margin:0;padding:0}
.progtab li{padding:1px 0}
.progtab li code{color:var(--mut);font-size:11.5px;margin-right:4px}
.progtab td.goal{color:var(--mut);font-style:italic;min-width:160px}
.progtab tr.vacrow td{text-align:center;font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;
color:var(--mut);background:var(--bg);padding:7px}
.progtab tr:target td{background:var(--hover)}
/* bouton « copier le lien » d'une séquence */
.lnk{font:inherit;font-size:13px;color:var(--mut);background:none;border:0;cursor:pointer;
padding:0 4px;border-radius:4px;opacity:0;transition:opacity .12s}
summary:hover .lnk,.lnk:focus-visible,.lnk.ok{opacity:1}
.lnk:hover{color:var(--fg);background:var(--pill)}
@media (hover:none){.lnk{opacity:1}}
@media print{.tablewrap{border:0;overflow:visible}table.progtab{min-width:0}header.top,.tools,.chev,.godocs,#pv{display:none!important}
body{background:#fff;color:#000;font-size:12px}main{padding:0}
details.seq{break-inside:avoid;border-color:#ccc}}
details.seq{background:var(--card);border:1px solid var(--line);border-radius:10px;margin-bottom:8px;overflow:hidden;scroll-margin-top:64px}
details.seq>summary{list-style:none;cursor:pointer;display:flex;align-items:center;gap:12px;padding:11px 14px;user-select:none}
details.seq>summary::-webkit-details-marker{display:none}
details.seq>summary:hover{background:var(--hover)}
details.seq>summary .num{color:var(--mut);font-size:13px;width:2.2em}
details.seq>summary .tt{flex:1;font-weight:600}
details.seq>summary .chev{color:var(--mut);transition:transform .15s}
details.seq[open]>summary .chev{transform:rotate(90deg)}
details.seq[open]>summary{border-bottom:1px solid var(--line)}
.grp{padding:6px 0 4px}
.grp+.grp{border-top:1px dashed var(--line)}
.grp h3{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;margin:6px 14px 2px;font-weight:600}
.doc{display:flex;align-items:center;gap:10px;padding:5px 14px 5px 14px}
.doc:hover{background:var(--hover)}
.doc .id{color:var(--mut);font-size:12.5px;width:2.6em;flex:none}
.doc .name{flex:1;min-width:0}
.doc .meta{color:var(--mut);font-size:12px}
.c-seq{color:var(--t-seq)}.c-prep{color:var(--t-prep)}.c-cours{color:var(--t-cours)}.c-act{color:var(--t-act)}.c-ex{color:var(--t-ex)}
.c-ds{color:var(--t-ds)}.c-res{color:var(--t-res)}
.seq.archive{opacity:.7}
.theme{font-size:10.5px;color:var(--mut);border:1px solid var(--line);border-radius:4px;padding:0 5px}
.seq.upcoming{display:flex;align-items:center;gap:12px;padding:9px 14px;margin-bottom:8px;
border:1px dashed var(--line);border-radius:10px;color:var(--mut)}
.seq.upcoming .num{font-size:13px;width:2.2em}
.seq.upcoming .tt{flex:1}
.seq.upcoming .meta{font-size:12px;font-style:italic}
.vac{display:flex;align-items:center;gap:10px;color:var(--mut);font-size:11.5px;
text-transform:uppercase;letter-spacing:.06em;margin:16px 2px}
.vac::before,.vac::after{content:"";flex:1;border-top:1px solid var(--line)}
.prog{padding:10px 14px 4px}
.prog .goal{margin:0;color:var(--mut);font-size:13.5px;font-style:italic}
details.skills{margin-top:4px}
details.skills>summary{cursor:pointer;font-size:12.5px;color:var(--acc);width:max-content}
details.skills ul{list-style:none;margin:6px 0 2px;padding:0}
details.skills li{display:flex;gap:10px;font-size:13.5px;padding:2px 0}
details.skills code{color:var(--mut);font-size:12px;flex:none;width:7.5em}
.hide{display:none!important}
#pv{position:fixed;z-index:20;width:240px;pointer-events:none;background:#fff;
border:1px solid var(--line);border-radius:6px;box-shadow:0 10px 30px rgba(0,0,0,.25);
opacity:0;transition:opacity .12s}
#pv.on{opacity:1}
footer{color:var(--mut);font-size:12px;line-height:1.5;padding:16px 0 24px;border-top:1px solid var(--line);text-align:right}
footer a{text-decoration:underline;text-underline-offset:2px}footer a:hover{color:var(--fg)}
@media (max-width:560px){.row .meta.sz,.doc .meta{display:none}h1{font-size:22px}}
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
addEventListener('beforeprint',()=>seqs.forEach(d=>d.open=true));
document.querySelectorAll('.lnk').forEach(b=>b.addEventListener('click',ev=>{
 ev.preventDefault();ev.stopPropagation();const id=b.closest('details').id;
 history.replaceState(null,'','#'+id);const url=location.href;
 const done=()=>{b.textContent='copié';b.classList.add('ok');
  setTimeout(()=>{b.textContent='#';b.classList.remove('ok')},1400)};
 navigator.clipboard?navigator.clipboard.writeText(url).then(done,done):done()}));
const norm=s=>s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
q.addEventListener('input',()=>{const v=norm(q.value.trim());
 seqs.forEach(d=>{let any=false;const title=norm(d.querySelector('summary').textContent);
  d.querySelectorAll('.doc').forEach(r=>{const hit=!v||title.includes(v)||norm(r.textContent).includes(v);
   r.classList.toggle('hide',!hit);any=any||hit});
  d.querySelectorAll('.grp').forEach(g=>g.classList.toggle('hide',!g.querySelector('.doc:not(.hide)')));
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


def page(d, title, body, script=False, here=None, extra_js="", wide=False, base=None):
    """`here` : page autre que l'index de `d` (le dossier devient alors un lien)."""
    crumbs = []
    chain = [d, *d.relative_to(ROOT).parents][:-1] if d != ROOT else []
    for p in reversed(chain):
        if p == d and not here:
            crumbs.append(f'<span class="cur">{e(label(p))}</span>')
        else:
            crumbs.append(f'<a href="{rel(d, p)}/index.html">{e(label(p))}</a>')
    if here:
        crumbs.append(f'<span class="cur">{e(here)}</span>')
    if d != ROOT or here:
        crumbs.insert(0, f'<a href="{rel(d, ROOT)}/index.html">{e(SITE_TITLE)}</a>')
        home = f'<a class="home" href="{rel(d, ROOT)}/index.html">⌂ Accueil</a>'
    else:
        crumbs = [f'<span class="cur">{e(SITE_TITLE)}</span>']
        home = ""
    sep = '<span class="sep">/</span>'
    favicon = rel(d, ROOT / "favicon.ico")
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
{f'<base href="{base}">' if base else ""}<link rel="icon" href="{favicon}">
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap{" wide" if wide else ""}"><nav class="crumbs">{sep.join(crumbs)}</nav>{home}</div></header>
<main><div class="wrap{" wide" if wide else ""}">
{body}
</div></main>
<footer><div class="wrap{" wide" if wide else ""}">
<a href="{LICENSE_URL}" target="_blank" rel="noopener license">CC0</a> · libre de tout usage, hors ressources tierces
</div></footer>
<script>{PREVIEW_JS}{JS if script else ""}{extra_js}</script>
</body>
</html>
"""


def ext_meta(p):
    return f'{p.suffix[1:].upper() or "—"} · {human_size(p.stat().st_size)}'


# ---------------------------------------------------------------------------
# Rendu des documents d'une séquence

def doc_rows(d, files):
    groups = {k: [] for k, _ in TYPES}
    groups["res"] = []
    for f in files:
        m = DOC_RE.match(f.stem)
        if m:
            kind, _lvl, _chap, item, name = m.groups()
            groups[kind].append((item or "", pretty(name) or kind, f))
        else:
            groups["res"].append(("", pretty(f.stem), f))
    out = []
    for kind, title in [*TYPES, ("res", "Ressources")]:
        if not groups[kind]:
            continue
        cls = "c-" + kind.lower()
        rows = []
        for item, name, f in sorted(groups[kind], key=lambda x: (x[0].zfill(4), x[1])):
            rows.append(
                f'<a class="doc" href="{rel(d, f)}" target="_blank" rel="noopener" title="{e(f.name)}"{thumb_attr(d, f)}>'
                f'<span class="id mono">{e(item)}</span><span class="name">{e(name)}</span>'
                f'<span class="meta mono">{e(ext_meta(f))}</span></a>')
        out.append(f'<div class="grp"><h3 class="{cls}">{title}</h3>{"".join(rows)}</div>')
    return "".join(out)


def subdir_rows(d, dirs):
    return "".join(
        f'<a class="doc" href="{rel(d, s)}/index.html">'
        f'<span class="id">▸</span><span class="name">{e(label(s))}/</span>'
        f'<span class="meta">{count_docs(s)} fichiers</span></a>' for s in dirs)


def skills_block(prog):
    """Objectif + compétences de la séquence, repris de la progression."""
    items = []
    for it in prog["items"]:
        code, _, text = it.partition(" — ")
        if not text:
            code, text = "", it
        items.append(f'<li><code>{e(code)}</code><span>{e(text)}</span></li>')
    return (f'<div class="prog"><p class="goal">{e(prog["obj"])}</p>'
            f'<details class="skills"><summary>Compétences · {len(items)}</summary>'
            f'<ul>{"".join(items)}</ul></details></div>')


def seq_block(level_dir, s, archive=False, prog=None):
    dirs, files = listdir(s)
    m = SEQ_RE.match(s.name)
    num, title = (m[1], pretty(m[2])) if m else ("", label(s))
    theme = ""
    inner = ""
    if prog:
        title = prog["titre"]
        theme = f'<span class="theme mono">{e(prog["theme"])}</span>'
        inner = skills_block(prog)
    inner += doc_rows(level_dir, files)
    if dirs:
        inner += f'<div class="grp"><h3 class="c-res">Dossiers</h3>{subdir_rows(level_dir, dirs)}</div>'
    n = count_docs(s)
    return (f'<details class="seq{" archive" if archive else ""}" id="{e(s.name)}">'
            f'<summary><span class="num mono">{e(num)}</span><span class="tt">{e(title)}</span>'
            f'{theme}<button class="lnk mono" type="button" title="Copier le lien vers cette séquence">#</button>'
            f'<span class="meta mono">{n}</span><span class="chev">›</span></summary>{inner}</details>')


def upcoming_block(prog):
    """Séquence prévue dans la progression mais sans dossier pour l'instant."""
    return (f'<div class="seq upcoming"><span class="num mono">{e(prog["id"][-2:])}</span>'
            f'<span class="tt">{e(prog["titre"])}</span>'
            f'<span class="theme mono">{e(prog["theme"])}</span><span class="meta">à venir</span></div>')


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
            blocks.append(f'<div class="vac">{e(r["vacances"])}</div>')
            continue
        num = r["id"][-2:]
        if num in by_num:
            blocks.append(seq_block(d, by_num[num], prog=r))
            done.add(by_num[num])
        elif int(num) < 90:  # 6C99 & co : « non traité cette année »
            blocks.append(upcoming_block(r))
    blocks += [seq_block(d, s) for s in seqs if s not in done]
    while blocks and blocks[-1].startswith('<div class="vac">'):
        blocks.pop()
    archive = d / "_Archive"
    arch = ""
    if archive.is_dir():
        adirs, _ = listdir(archive)
        if adirs:
            arch = ('<section class="arch"><h2>Archives</h2>'
                    + "".join(seq_block(d, s, archive=True,
                                        prog=progs.get(SEQ_RE.match(s.name)[1]) if SEQ_RE.match(s.name) else None)
                              for s in adirs) + "</section>")
    prog_html = PROG_DIR / PROG_FILES.get(d.name, "-")
    prog_btn = (f'<a class="btn" href="{rel(d, prog_html.with_suffix(".html"))}" target="_blank" '
                f'rel="noopener">Progression ↗</a>' if rows else "")
    loose = f'<h2>Autres fichiers</h2><div class="list">{file_rows(d, files)}</div>' if files else ""
    body = (f'<h1>{e(label(d))}</h1><p class="sub">{len(seqs)} séquences · {count_docs(d)} documents</p>'
            f'<div class="tools"><input id="q" type="search" placeholder="Rechercher un document…  ( / )" autocomplete="off">'
            f'<button id="all" type="button">Tout déplier</button>{prog_btn}</div>'
            + "".join(blocks) + arch + loose)
    return page(d, f"{label(d)} — {SITE_TITLE}", body, script=True)


ICONS = {".pdf": "◧", ".html": "◩", ".png": "▣", ".jpg": "▣"}


def file_rows(d, files):
    return "".join(
        f'<a class="row" href="{rel(d, f)}" target="_blank" rel="noopener"{thumb_attr(d, f)}>'
        f'<span class="ico">{ICONS.get(f.suffix.lower(), "□")}</span>'
        f'<span class="name">{e(f.name)}</span>'
        f'<span class="meta sz mono">{e(ext_meta(f))}</span></a>' for f in files)


def build_generic(d):
    dirs, files = listdir(d)
    rows = "".join(
        f'<a class="row" href="{rel(d, s)}/index.html"><span class="ico">▸</span>'
        f'<span class="name">{e(label(s))}/</span><span class="meta mono">{count_docs(s)} fichiers</span></a>'
        for s in dirs) + file_rows(d, files)
    body = (f'<h1>{e(label(d))}</h1><p class="sub">{len(dirs)} dossiers · {len(files)} fichiers</p>'
            f'<div class="list">{rows or "<div class=row><span class=name>Dossier vide</span></div>"}</div>')
    return page(d, f"{label(d)} — {SITE_TITLE}", body)


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
            title = (f'<a href="{rel(PROG_DIR, level_dir)}/index.html#{e(folder.name)}" target="_blank" '
                     f'rel="noopener" title="Documents de la séquence">{e(r["titre"])} <span class="ext">↗</span></a>'
                     f'<div class="cnt mono">{count_docs(folder)} docs{note}</div>')
        else:
            soon = "non traité" if int(num) >= 90 else "à venir"
            title = f'{e(r["titre"])}<div class="cnt soon">{soon}</div>'
        trs.append(f'<tr id="{e(r["id"])}"><td class="mono id">{e(r["id"])}</td><td class="tt">{title}</td>'
                   f'<td><span class="theme mono">{e(r["theme"])}</span></td>'
                   f'<td><ul>{"".join(skills)}</ul></td><td class="goal">{e(r["obj"])}</td></tr>')
    pdf = tex.with_suffix(".pdf")
    extra = ""
    if pdf.is_file():
        extra += f'<a class="btn" href="{pdf.name}" target="_blank" rel="noopener">PDF ↗</a>'
    if level_dir and level_dir.is_dir():
        extra += f'<a class="btn" href="{rel(PROG_DIR, level_dir)}/index.html" target="_blank" rel="noopener">Documents ↗</a>'
    body = (f'<h1>Progression — {e(long_name)}</h1>'
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
                    f'{thumb_attr(PROG_DIR, pdf)}>PDF ↗</a>' if pdf.is_file() else "")
        rows.append(f'<div class="row"><a class="name main" href="{html_f.name}">'
                    f'<b>{e(long_name)}</b></a><span class="meta">{nseq} séquences</span>{pdf_link}</div>')
    _, files = listdir(PROG_DIR)
    others = [f for f in files if f not in generated and f.stat().st_size > 0]
    body = (f'<h1>Progressions</h1><p class="sub">Progressions annuelles par niveau</p>'
            f'<div class="list">{"".join(rows)}</div>'
            + (f'<h2>Autres documents</h2><div class="list">{file_rows(PROG_DIR, others)}</div>' if others else ""))
    return page(PROG_DIR, f"Progressions — {SITE_TITLE}", body)


def build_progressions():
    for tex_name in PROG_FILES.values():
        tex = PROG_DIR / tex_name
        if parse_progression(tex):
            tex.with_suffix(".html").write_text(build_prog_page(tex), "utf-8")
    (PROG_DIR / "index.html").write_text(build_prog_index(), "utf-8")


def recent_files(n=8):
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "log", "--diff-filter=A", "--name-only",
                              "--format=@%cs", "-n", "60"], capture_output=True, text=True,
                             check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    seen, res, date = set(), [], ""
    for line in out.splitlines():
        if line.startswith("@"):
            date = line[1:]
        elif line:
            p = ROOT / line
            if p.is_file() and visible(p) and p.suffix == ".pdf" and p not in seen \
                    and p.relative_to(ROOT).parts[0] in LEVELS:
                seen.add(p)
                res.append((date, p))
    return res[:n]


def build_404():
    """404.html : servie par GitHub Pages à n'importe quelle profondeur, d'où <base href="/">."""
    dirs, _ = listdir(ROOT)
    dirs.sort(key=lambda p: SECTION_ORDER.index(p.name) if p.name in SECTION_ORDER else 99)
    cards = "".join(f'<a class="card" href="{s.name}/index.html"><div class="t">{e(label(s))}</div></a>'
                    for s in dirs)
    body = ('<h1>Page introuvable</h1>'
            '<p class="sub">Le document a peut-être été déplacé ou renommé : '
            '<code id="miss" class="mono"></code></p>'
            f'<div class="cards">{cards}</div>'
            '<script>document.getElementById("miss").textContent=decodeURIComponent(location.pathname)</script>')
    return page(ROOT, f"Page introuvable — {SITE_TITLE}", body, here="Page introuvable", base="/")


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
            desc = f"{nseq} séquences · {count_docs(s)} documents"
        else:
            desc = BLURBS.get(s.name, f"{count_docs(s)} fichiers")
        cards.append(f'<a class="card" href="{s.name}/index.html" target="_blank" rel="noopener">'
                     f'<div class="t">{e(label(s))}<span class="ext">↗</span></div>'
                     f'<div class="d">{e(desc)}</div></a>')
    banner_file = ROOT / ".scripts" / "title.txt"
    head = (f'<pre class="banner mono" aria-label="{e(SITE_TITLE)}">{e(banner_file.read_text("utf-8").rstrip())}</pre>'
            if banner_file.is_file() else f"<h1>{e(SITE_TITLE)}</h1>")
    recent = recent_files()
    rec = ""
    if recent:
        rows = []
        for date, p in recent:
            m = DOC_RE.match(p.stem)
            kind = m[1] if m else "res"
            name = pretty(m[5]) if m else pretty(p.stem)
            lvl = NAMES.get(p.relative_to(ROOT).parts[0], "")
            rows.append(f'<a class="row" href="{rel(ROOT, p)}" target="_blank" rel="noopener"{thumb_attr(ROOT, p)}>'
                        f'<span class="pill c-{kind.lower()}">{e(kind)}</span>'
                        f'<span class="name">{e(name)}</span>'
                        f'<span class="meta">{e(lvl)} · {e(label(p.parent))}</span>'
                        f'<span class="meta sz mono">{e(date)}</span></a>')
        rec = f'<h2>Récemment ajoutés</h2><div class="list">{"".join(rows)}</div>'
    body = (f'{head}<p class="sub">Cours de maths de {e(AUTHOR)} · {e(SCHOOL)} · année {school_year()}</p>'
            f'<h2>Sections</h2><div class="cards">{"".join(cards)}</div>{rec}')
    return page(ROOT, SITE_TITLE, body)


def main():
    ensure_archives()
    compile_progressions()
    print(f"{delete_junk()} fichiers temporaires LaTeX supprimés")
    rename_all()
    build_thumbs()
    build_progressions()
    n = 0
    (ROOT / "index.html").write_text(build_home(), "utf-8")
    (ROOT / "404.html").write_text(build_404(), "utf-8")
    (ROOT / ".nojekyll").touch()  # sinon GitHub Pages (Jekyll) ne publie pas les dossiers _Archive
    n += 1
    for dirpath, dirnames, _ in os.walk(ROOT):
        d = Path(dirpath)
        dirnames[:] = [x for x in dirnames if visible(d / x)]
        if d in (ROOT, PROG_DIR):  # PROG_DIR : fait par build_progressions()
            continue
        is_level = d.parent == ROOT and d.name in LEVELS
        (d / "index.html").write_text(build_level(d) if is_level else build_generic(d), "utf-8")
        n += 1
    print(f"{n} index.html générés")


if __name__ == "__main__":
    main()
