// Navigation : ls, cd, pwd, tree.
import { state } from "../state.js";
import { absPath, entries, isDir, isHidden, humanSize, duSize, walk, lookup, ERR } from "../fs.js";
import { entryPart, getopt } from "./util.js";

function longLine(name, node, segs) {
  const perm = isDir(node) ? "drwxr-xr-x" : isHidden(name) ? "-rw-------" : "-rw-r--r--";
  const owner = isHidden(name) ? "root" : "prof";
  return [`${perm} ${owner.padEnd(4)} ${humanSize(duSize(node)).padStart(5)}  `, entryPart(name, node, segs)];
}

export const ls = {
  help: "liste le contenu d'un dossier",
  usage: "ls [-l] [-a] [-1] [-R] [-d] [chemin...]",
  more: ["-l  format long (droits, taille)", "-1  un nom par ligne", "-R  récursif",
    "-d  le dossier lui-même, pas son contenu", "-a  tout afficher (sources visibles en root seulement)",
    "Dossiers d'abord, _Archive en dernier, tri naturel (S2 avant S10)."],
  async run(args, io) {
    const { opts, rest } = getopt(args, "laAh1Rd");
    const show = (segs, node) => {
      const items = entries(node);
      if (!items.length) return;
      if (opts.l) items.forEach(([n, c]) => io.out(longLine(n, c, [...segs, n])));
      else if (opts["1"]) items.forEach(([n, c]) => io.out([entryPart(n, c, [...segs, n])]));
      else io.cols(items.map(([n, c]) => [entryPart(n, c, [...segs, n])]));
    };
    let status = 0;
    const targets = [];
    for (const p of rest.length ? rest : ["."]) {
      const r = lookup(p);
      if (r.err) { io.err(`ls: impossible d'accéder à '${p}': ${ERR[r.err]}`); status = 2; continue; }
      targets.push({ p, ...r });
    }
    const files = targets.filter(t => opts.d || !isDir(t.node));
    const dirs = targets.filter(t => !opts.d && isDir(t.node));
    if (files.length) {
      const parts = files.map(t => entryPart(t.segs[t.segs.length - 1] ?? "/", t.node, t.segs, t.p));
      if (opts.l) files.forEach((t, i) => io.out([longLine(t.p, t.node, t.segs)[0], parts[i]]));
      else io.cols(parts.map(p => [p]));
    }
    const headers = rest.length > 1 || opts.R;
    dirs.forEach((t, i) => {
      if (headers) { if (i || files.length) io.out(""); io.out(`${t.p}:`); }
      show(t.segs, t.node);
      if (opts.R) walk(t.segs, t.node, (segs, name, node) => {
        if (!isDir(node)) return;
        io.out(""); io.out(`${t.p === "." ? "." : t.p.replace(/\/$/, "")}/${segs.slice(t.segs.length).join("/")}:`);
        show(segs, node);
      });
    });
    return status;
  },
};

export const cd = {
  help: "change de dossier",
  usage: "cd [chemin]",
  more: ["cd ..   remonte d'un niveau", "cd /    ou  cd  : revient à la racine du site",
    "cd -    revient au dossier précédent", "cd S04-Angles/images, cd ../../Quatrieme : chemins relatifs ou absolus"],
  run(args, io) {
    if (args.length > 1) { io.err("bash: cd: trop d'arguments"); return 1; }
    let p = args[0] ?? "/";
    if (p === "-") {
      if (!state.oldpwd) { io.err("bash: cd: « OLDPWD » non défini"); return 1; }
      p = absPath(state.oldpwd);
      io.out(p);
    }
    const r = lookup(p);
    if (!r.err && !isDir(r.node)) r.err = "ENOTDIR";
    if (r.err) { io.err(`bash: cd: ${args[0]}: ${ERR[r.err]}`); return 1; }
    state.oldpwd = state.cwd;
    state.cwd = r.segs;
    return 0;
  },
};

export const pwd = {
  help: "affiche le chemin du dossier courant",
  usage: "pwd",
  run(args, io) { io.out(absPath(state.cwd)); },
};

export const tree = {
  help: "affiche l'arborescence",
  usage: "tree [-d] [-L niveau] [chemin]",
  more: ["-d  dossiers seulement", "-L n  descend au plus de n niveaux (ex. tree -L 2 /)"],
  run(args, io) {
    const { opts, rest } = getopt(args, "daL", "L");
    const max = opts.L ? parseInt(opts.L, 10) : Infinity;
    if (opts.L && !(max > 0)) { io.err("tree: niveau invalide, doit être supérieur à 0."); return 1; }
    let status = 0;
    for (const p of rest.length ? rest : ["."]) {
      const r = lookup(p);
      if (r.err || !isDir(r.node)) {
        io.out([{ t: p, cls: "t-dir" }, ` [erreur à l'ouverture du dossier]`]);
        status = 2;
        continue;
      }
      let nd = 0, nf = 0;
      io.out([{ t: p, cls: "t-dir" }]);
      const rec = (segs, node, prefix, depth) => {
        const items = entries(node).filter(([, c]) => !opts.d || isDir(c));
        items.forEach(([name, child], i) => {
          const last = i === items.length - 1;
          isDir(child) ? nd++ : nf++;
          io.out([prefix + (last ? "└── " : "├── "), entryPart(name, child, [...segs, name], name)]);
          if (isDir(child) && depth < max) rec([...segs, name], child, prefix + (last ? "    " : "│   "), depth + 1);
        });
      };
      rec(r.segs, r.node, "", 1);
      io.out("");
      io.out(`${nd} dossier${nd > 1 ? "s" : ""}` + (opts.d ? "" : `, ${nf} fichier${nf > 1 ? "s" : ""}`));
    }
    return status;
  },
};
