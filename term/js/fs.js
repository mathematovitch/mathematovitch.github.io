// Système de fichiers virtuel, en lecture seule, construit depuis fs.json (généré par build.py).
// Un dossier est un objet { nom: enfant }, un fichier est sa taille en octets.
import { SITE } from "./config.js";
import { state, isRoot } from "./state.js";

export let META = { hidden: [], prof: [], tree: {} };

export async function loadFS() {
  const r = await fetch("fs.json", { cache: "no-cache" });
  if (!r.ok) throw new Error(`fs.json : erreur HTTP ${r.status}`);
  META = await r.json();
}

// Messages d'erreur POSIX, tels que les affiche un système en français.
export const ERR = {
  ENOENT: "Aucun fichier ou dossier de ce type",
  ENOTDIR: "N'est pas un dossier",
  EISDIR: "est un dossier",
  EACCES: "Permission non accordée",
  EROFS: "Système de fichiers accessible en lecture seule",
};

export const isDir = n => n !== null && typeof n === "object";
export const ext = name => { const i = name.lastIndexOf("."); return i > 0 ? name.slice(i).toLowerCase() : ""; };

/** Fichier masqué du site (sources .tex, scripts..., et documents du mode prof : Corr-, DS-...) :
 *  visible seulement en root. */
export const isHidden = name => META.hidden.includes(ext(name)) || (META.prof || []).some(p => name.startsWith(p));
export const canSee = name => isRoot() || !isHidden(name);

export const TEXT_EXT = [".tex", ".sty", ".cls", ".bib", ".txt", ".md", ".org", ".html", ".htm", ".css",
  ".js", ".json", ".py", ".sh", ".csv", ".svg", ".xml"];
export const IMG_EXT = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"];
export const isText = name => TEXT_EXT.includes(ext(name));

/** Classe CSS de couleur selon le type (façon dircolors). */
export function typeClass(name, node) {
  if (isDir(node)) return "t-dir";
  const e = ext(name);
  if (isHidden(name)) return "t-src";
  if (e === ".pdf") return "t-pdf";
  if (IMG_EXT.includes(e)) return "t-img";
  if (e === ".html" || e === ".htm") return "t-html";
  return "";
}

const collator = new Intl.Collator("fr", { numeric: true, sensitivity: "base" });

/** Contenu visible d'un dossier, rangé : dossiers d'abord (_Archive en dernier), tri naturel. */
export function entries(dir) {
  return Object.keys(dir).filter(canSee).map(name => [name, dir[name]]).sort(([a, x], [b, y]) =>
    (isDir(y) - isDir(x)) || ((a === "_Archive") - (b === "_Archive")) || collator.compare(a, b));
}

export const nodeAt = segs => segs.reduce((n, s) => (isDir(n) ? n[s] : undefined), META.tree);

/**
 * Résout un chemin (absolu, relatif, ~, ., ..) en vérifiant chaque étape comme le noyau :
 * renvoie { segs, node } ou { err: "ENOENT" | "ENOTDIR" | "EACCES" }.
 */
export function lookup(path, cwd = state.cwd) {
  const tilde = path === "~" || path.startsWith("~/");
  let segs = path.startsWith("/") || tilde ? [] : [...cwd];
  let node = nodeAt(segs);
  const parts = (tilde ? path.slice(1) : path).split("/");
  const trailing = parts.length > 1 && parts[parts.length - 1] === "";
  for (const p of parts) {
    if (p === "" || p === ".") continue;
    if (!isDir(node)) return { err: "ENOTDIR" };
    if (p === "..") { segs.pop(); node = nodeAt(segs); continue; }
    if (!Object.hasOwn(node, p)) return { err: "ENOENT" };
    if (!canSee(p)) return { err: "EACCES" };
    segs.push(p);
    node = node[p];
  }
  if (trailing && !isDir(node)) return { err: "ENOTDIR" };
  return { segs, node };
}

export const absPath = segs => "/" + segs.join("/");

/** Chemin le plus court à afficher/retaper : relatif au dossier courant si possible. */
export function shortPath(segs) {
  const c = state.cwd;
  if (c.every((s, i) => segs[i] === s)) return segs.slice(c.length).join("/") || ".";
  return absPath(segs);
}

/** URL publique d'un fichier (ou de l'index d'un dossier) sur le site. */
export function urlOf(segs, node) {
  const path = segs.map(encodeURIComponent).join("/");
  if (isDir(node)) return `${SITE}/${path ? path + "/" : ""}index.html`;
  return `${SITE}/${path}`;
}

const textCache = new Map();
export async function readText(segs) {
  const url = urlOf(segs, 0);
  if (!textCache.has(url)) {
    textCache.set(url, fetch(url).then(r => {
      if (!r.ok) throw new Error(`erreur HTTP ${r.status}`);
      return r.text();
    }).catch(e => { textCache.delete(url); throw e; }));
  }
  return textCache.get(url);
}

/** Parcours récursif : appelle fn(segs, name, node, depth) pour chaque entrée visible. */
export function walk(segs, node, fn, depth = 1, maxDepth = Infinity) {
  if (!isDir(node) || depth > maxDepth) return;
  for (const [name, child] of entries(node)) {
    const s = [...segs, name];
    fn(s, name, child, depth);
    walk(s, child, fn, depth + 1, maxDepth);
  }
}

export function humanSize(n) {
  if (n < 1024) return `${n}`;
  const u = ["K", "M", "G"];
  let i = -1;
  do { n /= 1024; i++; } while (n >= 1024 && i < u.length - 1);
  return `${n < 10 ? n.toFixed(1).replace(".", ",") : Math.round(n)}${u[i]}`;
}

export function duSize(node) {
  if (!isDir(node)) return node;
  return entries(node).reduce((t, [, c]) => t + duSize(c), 0);
}

// --- Jokers du shell (*, ?, [...]) ---------------------------------------

// Dans un motif, « \x » est le caractère x littéral (partie entre guillemets dans le shell).
export const escapeGlob = s => s.replace(/[\\*?[]/g, "\\$&");
const unescapeGlob = s => s.replace(/\\(.)/g, "$1");
export const hasGlob = s => /(^|[^\\])(\\\\)*[*?[]/.test(s);

export function globToRegExp(glob, flags = "") {
  const lit = c => c.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&");
  let re = "";
  for (let i = 0; i < glob.length; i++) {
    const c = glob[i];
    if (c === "\\") re += lit(glob[++i] ?? "\\");
    else if (c === "*") re += ".*";
    else if (c === "?") re += ".";
    else if (c === "[") {
      const j = glob.indexOf("]", i + 2);
      if (j < 0) { re += "\\["; continue; }
      re += "[" + glob.slice(i + 1, j).replace(/^!/, "^").replace(/\\/g, "\\\\") + "]";
      i = j;
    } else re += lit(c);
  }
  return new RegExp(`^${re}$`, flags);
}

/** Développe un motif (échappé, voir escapeGlob) ; sans correspondance, le motif est rendu tel quel (bash). */
export function expandGlob(word) {
  if (!hasGlob(word)) return [word];
  const abs = word.startsWith("/");
  const tilde = word === "~" || word.startsWith("~/");
  const parts = word.split("/");
  let found = [{ segs: abs || tilde ? [] : [...state.cwd], text: abs ? "" : tilde ? "~" : null }];
  parts.forEach((p, i) => {
    if (i === 0 && (abs || tilde)) return;
    const last = i === parts.length - 1;
    const next = [];
    for (const f of found) {
      const join = name => (f.text === null ? name : `${f.text}/${name}`);
      const node = nodeAt(f.segs);
      // Slash final (« */ ») : seuls les dossiers conviennent.
      if (p === "" && last) { if (isDir(node)) next.push({ ...f, text: (f.text ?? "") + "/" }); continue; }
      if (!hasGlob(p)) {
        const name = unescapeGlob(p);
        const r = lookup(name, f.segs);
        if (name.includes("/") || r.err) continue;
        next.push({ segs: r.segs, text: join(name) });
        continue;
      }
      if (!isDir(node)) continue;
      const re = globToRegExp(p);
      for (const [name] of entries(node))
        if (re.test(name) && (p.startsWith(".") || !name.startsWith(".")))
          next.push({ segs: [...f.segs, name], text: join(name) });
    }
    found = next;
  });
  return found.length ? found.map(f => f.text) : [word];
}
