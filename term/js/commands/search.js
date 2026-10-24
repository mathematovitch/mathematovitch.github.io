// Recherche : find (noms), grep (contenu).
import { isDir, isText, globToRegExp, lookup, readText, walk, ERR } from "../fs.js";
import { entryPart, getopt, lines } from "./util.js";

export const find = {
  help: "cherche des fichiers par leur nom",
  usage: "find [chemin...] [-name motif] [-iname motif] [-type f|d] [-maxdepth n]",
  more: ["find / -iname '*angle*'      tout ce qui contient « angle »",
    "find . -name 'DS-*' -type f  les contrôles sous le dossier courant",
    "Mettre le motif entre guillemets, sinon le shell remplace * lui-même."],
  run(args, io) {
    const paths = [];
    let i = 0;
    for (; i < args.length && !args[i].startsWith("-"); i++) paths.push(args[i]);
    const tests = [];
    let maxDepth = Infinity;
    for (; i < args.length; i++) {
      const a = args[i], v = args[i + 1];
      if (["-name", "-iname", "-type", "-maxdepth"].includes(a) && v === undefined) {
        io.err(`find: argument manquant pour « ${a} »`); return 1;
      }
      if (a === "-name" || a === "-iname") {
        const re = globToRegExp(v, a === "-iname" ? "i" : "");
        tests.push((name) => re.test(name)); i++;
      } else if (a === "-type") {
        if (v !== "f" && v !== "d") { io.err(`find: type inconnu pour -type : ${v}`); return 1; }
        tests.push((name, node) => isDir(node) === (v === "d")); i++;
      } else if (a === "-maxdepth") {
        maxDepth = parseInt(v, 10); i++;
      } else { io.err(`find: prédicat inconnu « ${a} »`); return 1; }
    }
    let status = 0;
    for (const p of paths.length ? paths : ["."]) {
      const r = lookup(p);
      if (r.err) { io.err(`find: '${p}': ${ERR[r.err]}`); status = 1; continue; }
      const show = (segs, name, node) => {
        if (!tests.every(t => t(name, node))) return;
        const rel = segs.slice(r.segs.length).join("/");
        const shown = rel ? (p.endsWith("/") ? p + rel : `${p}/${rel}`) : p;
        io.out([entryPart(name, node, segs, shown)]);
      };
      show(r.segs, p.replace(/(.)\/+$/, "$1").split("/").pop() || "/", r.node);  // GNU : -name teste « . » tel quel
      walk(r.segs, r.node, show, 1, maxDepth);
    }
    return status;
  },
};

const GREP_MAX_FILES = 400;

export const grep = {
  help: "cherche un mot dans le contenu des fichiers texte",
  usage: "grep [-i] [-v] [-n] [-c] [-l] [-r] motif [fichier|dossier...]",
  more: ["-i  ignore majuscules/minuscules   -v  lignes qui ne correspondent PAS",
    "-n  numéros de ligne   -c  compte   -l  noms de fichiers seulement   -r  récursif",
    "ls | grep DS          filtre la sortie d'une autre commande",
    "grep -ri fraction /   cherche dans tous les fichiers texte (sources .tex : root seulement)"],
  async run(args, io) {
    const { opts, rest } = getopt(args, "ivnclrRhHwE");
    if (!rest.length) { io.err("grep: motif manquant (exemple : ls | grep Cours)"); return 2; }
    const [pat, ...files] = rest;
    let re;
    const word = s => (opts.w ? `\\b(?:${s})\\b` : s);
    try { re = new RegExp(word(pat), opts.i ? "gi" : "g"); }
    catch { re = new RegExp(word(pat.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")), opts.i ? "gi" : "g"); }
    const test = l => { re.lastIndex = 0; return re.test(l) !== !!opts.v; };
    const color = l => {
      if (opts.v || !io.tty) return [l];
      const parts = []; let last = 0;
      re.lastIndex = 0;
      for (const m of l.matchAll(re)) {
        if (!m[0]) continue;
        parts.push(l.slice(last, m.index), { t: m[0], cls: "hl" });
        last = m.index + m[0].length;
      }
      parts.push(l.slice(last));
      return parts;
    };

    // Liste des fichiers à lire (dossiers parcourus avec -r).
    const targets = [];
    let status = 1, errors = false;
    for (const f of files) {
      const r = lookup(f);
      if (r.err) { io.err(`grep: ${f}: ${ERR[r.err]}`); errors = true; continue; }
      if (!isDir(r.node)) { targets.push({ name: f, segs: r.segs }); continue; }
      if (!opts.r && !opts.R) { io.err(`grep: ${f}: ${ERR.EISDIR}`); errors = true; continue; }
      walk(r.segs, r.node, (segs, name, node) => {
        if (!isDir(node) && isText(name)) {
          const rel = segs.slice(r.segs.length).join("/");
          targets.push({ name: f === "." ? rel : `${f.replace(/\/$/, "")}/${rel}`, segs });
        }
      });
    }
    if (!files.length && (opts.r || opts.R)) return grep.run([...args, "."], io);
    const multi = (targets.length > 1 || opts.r || opts.R) && !opts.h || opts.H;

    const report = (name, text) => {
      const ls = lines(text);
      let n = 0;
      ls.forEach((l, k) => {
        if (!test(l)) return;
        n++;
        if (opts.l || opts.c) return;
        io.out([...(multi ? [{ t: name, cls: "t-html" }, ":"] : []), ...(opts.n ? [`${k + 1}:`] : []), ...color(l)]);
      });
      if (opts.c) io.out(multi ? `${name}:${n}` : `${n}`);
      else if (opts.l && n) io.out(name);
      if (n) status = 0;
    };

    if (!files.length) {
      if (io.stdin === null) { io.err("grep: rien à lire (exemple : ls | grep Cours, ou grep -r motif .)"); return 2; }
      report("(entrée standard)", io.stdin);
      return status;
    }
    if (targets.length > GREP_MAX_FILES) {
      io.err(`grep: ${targets.length} fichiers, seuls les ${GREP_MAX_FILES} premiers sont lus`);
      targets.length = GREP_MAX_FILES;
    }
    if (targets.length > 20 && io.tty) io.out(`(lecture de ${targets.length} fichiers...)`, "dim");
    // Lecture en parallèle par paquets, affichage dans l'ordre.
    for (let k = 0; k < targets.length; k += 8) {
      const batch = targets.slice(k, k + 8);
      const texts = await Promise.all(batch.map(t => (isText(t.name)
        ? readText(t.segs).catch(e => ({ e })) : Promise.resolve({ bin: true }))));
      batch.forEach((t, j) => {
        const x = texts[j];
        if (typeof x === "string") report(t.name, x);
        else if (x.bin) { /* binaire (PDF...) : ignoré, comme grep -I */ }
        else { io.err(`grep: ${t.name}: ${x.e.message}`); errors = true; }
      });
    }
    return errors && status ? 2 : status;
  },
};
