// Complétion (Tab) des commandes et des chemins.
import { entries, isDir, lookup } from "./fs.js";
import { COMMANDS, ALIASES } from "./commands/index.js";

export function commonPrefix(list) {
  if (!list.length) return "";
  let p = list[0];
  for (const s of list) while (!s.startsWith(p)) p = p.slice(0, -1);
  return p;
}

/**
 * Complète le mot sous le curseur. Renvoie null, ou { value, caret, choices } :
 * value/caret : nouvelle ligne et position du curseur ; choices : candidats à afficher (plusieurs).
 */
export function complete(value, caret) {
  const before = value.slice(0, caret), after = value.slice(caret);
  const m = /(\S*)$/.exec(before);
  const word = m[1], start = caret - word.length;
  const prev = before.slice(0, start).trim().split(/\s+/).filter(Boolean);
  const isCmd = !prev.length || /^(\||;|&&|\|\||sudo)$/.test(prev[prev.length - 1]) || /[|;&]$/.test(prev[prev.length - 1]);
  // Commande de la dernière partie de la ligne (après |, ;, &&, ||), sudo sauté.
  const seg = before.slice(0, start).split(/\|\||&&|[|;]/).pop().trim().split(/\s+/).filter(Boolean);
  const cmdName = seg.filter(w => w !== "sudo")[0];

  let cands;   // [texte inséré, libellé affiché]
  let base;    // partie du mot conservée devant le candidat
  let stem;    // partie du mot à compléter
  if (isCmd) {
    base = ""; stem = word;
    cands = [...Object.keys(COMMANDS).filter(c => !COMMANDS[c].hidden), ...Object.keys(ALIASES)]
      .filter(c => c.startsWith(word)).sort().map(c => [c + " ", c]);
  } else {
    if (word.startsWith("-")) return null;
    const slash = word.lastIndexOf("/");
    base = word.slice(0, slash + 1); stem = word.slice(slash + 1);
    const r = lookup(base || ".");
    if (r.err || !isDir(r.node)) return null;
    const dirsOnly = cmdName === "cd" || cmdName === "tree";
    cands = entries(r.node)
      .filter(([n, c]) => n.startsWith(stem) && (!dirsOnly || isDir(c)))
      .map(([n, c]) => (isDir(c) ? [n + "/", n + "/"] : [n + " ", n]));
    if (!stem && !base && cands.length === 0) return null;
  }
  if (!cands.length) return null;
  const set = text => ({ value: value.slice(0, start) + text + after, caret: start + text.length });
  if (cands.length === 1) return { ...set(base + cands[0][0]), choices: [] };
  const pref = commonPrefix(cands.map(c => c[1]));
  if (pref.length > stem.length) return { ...set(base + pref), choices: [] };
  return { ...set(word), choices: cands.map(c => c[1]) };
}
