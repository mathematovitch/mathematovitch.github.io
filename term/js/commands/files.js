// Fichiers : cat, open, et filtres de texte (head, tail, wc, sort).
import { ext, isDir, isText, isEnc, IMG_EXT, readText, urlOf, lookup, ERR } from "../fs.js";
import { openEnc } from "../../../assets/prof.js";
import { getopt, lines, quote } from "./util.js";

/**
 * Contenu texte des opérandes, ou de l'entrée standard s'il n'y en a pas.
 * Appelle fn(texte, nom) ; renvoie le code de retour.
 */
async function eachText(io, files, fn) {
  if (!files.length) {
    if (io.stdin === null) { io.err(`${io.name}: aucun fichier (exemple : ${io.name} fichier.tex, ou ls | ${io.name})`); return 1; }
    await fn(io.stdin, "-");
    return 0;
  }
  let status = 0;
  for (const f of files) {
    const r = lookup(f);
    if (r.err) { io.err(`${io.name}: ${f}: ${ERR[r.err]}`); status = 1; continue; }
    if (isDir(r.node)) { io.err(`${io.name}: ${f}: ${ERR.EISDIR}`); status = 1; continue; }
    if (!isText(f)) { io.err(`${io.name}: ${f}: fichier binaire — essayez : open ${quote(f)}`); status = 1; continue; }
    try { await fn(await readText(r.segs), f); } catch (e) { io.err(`${io.name}: ${f}: ${e.message}`); status = 1; }
  }
  return status;
}

export const cat = {
  help: "affiche le contenu d'un fichier texte",
  usage: "cat [-n] fichier...",
  more: ["-n  numérote les lignes", "Les PDF et images ne sont pas du texte : utilisez open."],
  async run(args, io) {
    const { opts, rest } = getopt(args, "n");
    let k = 0;
    return eachText(io, rest, text => {
      for (const l of lines(text)) io.out(opts.n ? `${String(++k).padStart(6)}  ${l}` : l);
    });
  },
};

export const open = {
  help: "ouvre un fichier (PDF, page, image) ou un dossier sur le site",
  usage: "open fichier|dossier...",
  more: ["PDF et pages HTML : nouvel onglet", "image : aperçu dans le terminal",
    "fichier texte : affiché comme avec cat", "dossier : sa page sur le site (open . pour le dossier courant)"],
  async run(args, io) {
    if (!args.length) { io.err("open: fichier manquant (exemple : open Cours-6C01-Fractions.pdf)"); return 1; }
    let status = 0;
    for (const f of args) {
      const r = lookup(f);
      if (r.err) { io.err(`open: ${f}: ${ERR[r.err]}`); status = 1; continue; }
      const url = urlOf(r.segs, r.node);
      const e = ext(f);
      if (!isDir(r.node) && isEnc(r.segs) && !isText(f)) {
        // Document prof chiffré (lisible seulement en sudo, sinon lookup a refusé) : déchiffré ici.
        const name = r.segs[r.segs.length - 1];
        if (io.tty) {
          try { await openEnc(url, name); } catch (err) { io.err(`open: ${f}: ${err.message}`); status = 1; continue; }
        }
        io.out(`Ouverture dans un nouvel onglet : ${name} (déchiffré)`);
      } else if (!isDir(r.node) && IMG_EXT.includes(e) && io.tty) {
        const img = document.createElement("img");
        img.className = "preview"; img.src = url; img.alt = f; img.loading = "lazy";
        io.node(img);
        io.out([{ t: url, href: url }]);
      } else if (!isDir(r.node) && isText(f) && e !== ".html" && e !== ".htm") {
        status |= await cat.run([f], io);
      } else {
        if (io.tty) window.open(url, "_blank", "noopener");
        io.out(["Ouverture dans un nouvel onglet : ", { t: url, href: url }]);
      }
    }
    return status;
  },
};

export const head = {
  help: "affiche le début d'un texte",
  usage: "head [-n N] [fichier...]",
  more: ["10 lignes par défaut ; ls | head -n 3"],
  async run(args, io) {
    const { opts, rest } = getopt(args, "n#", "n");
    const n = parseInt(opts.n ?? "10", 10);
    return eachText(io, rest, (text, f) => {
      if (rest.length > 1) io.out(`==> ${f} <==`);
      lines(text).slice(0, n).forEach(l => io.out(l));
    });
  },
};

export const tail = {
  help: "affiche la fin d'un texte",
  usage: "tail [-n N|+N] [fichier...]",
  more: ["-n +N  à partir de la ligne N"],
  async run(args, io) {
    const { opts, rest } = getopt(args, "n#", "n");
    const from = String(opts.n ?? "").startsWith("+");
    const n = parseInt(opts.n ?? "10", 10);
    return eachText(io, rest, (text, f) => {
      if (rest.length > 1) io.out(`==> ${f} <==`);
      const ls = lines(text);
      (from ? ls.slice(Math.max(0, n - 1)) : n > 0 ? ls.slice(-n) : []).forEach(l => io.out(l));
    });
  },
};

export const wc = {
  help: "compte lignes, mots et caractères",
  usage: "wc [-l] [-w] [-c] [fichier...]",
  more: ["ls | wc -l   compte les fichiers du dossier"],
  async run(args, io) {
    const { opts, rest } = getopt(args, "lwcm");
    const all = !opts.l && !opts.w && !opts.c && !opts.m;
    return eachText(io, rest, (text, f) => {
      const v = [];
      if (all || opts.l) v.push(lines(text).length);
      if (all || opts.w) v.push(text.split(/\s+/).filter(Boolean).length);
      if (all || opts.c || opts.m) v.push(opts.c ? new TextEncoder().encode(text).length : [...text].length);
      io.out(v.map(x => String(x).padStart(v.length > 1 ? 7 : 0)).join(" ") + (f === "-" ? "" : ` ${f}`));
    });
  },
};

export const sort = {
  help: "trie les lignes",
  usage: "sort [-r] [-n] [-u] [fichier...]",
  async run(args, io) {
    const { opts, rest } = getopt(args, "rnu");
    const coll = new Intl.Collator("fr", { numeric: !!opts.n });
    let all = [];
    const status = await eachText(io, rest, text => { all.push(...lines(text)); });
    all.sort(coll.compare);
    if (opts.r) all.reverse();
    if (opts.u) all = all.filter((l, i) => i === 0 || l !== all[i - 1]);
    all.forEach(l => io.out(l));
    return status;
  },
};
