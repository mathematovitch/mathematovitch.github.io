// Interprète de lignes de commande : guillemets, variables, jokers, |, ;, &&.
import { USER } from "./config.js";
import { state, save } from "./state.js";
import { absPath, expandGlob, escapeGlob, hasGlob, ERR } from "./fs.js";
import { COMMANDS, ALIASES } from "./commands/index.js";
import { USER_ALIASES, FUNCS } from "./aliases.js";

/**
 * Découpe la ligne en mots et opérateurs. Un mot est une liste de morceaux :
 * { text, q } (q : entre guillemets, donc pas de jokers) ou { name, q } pour une variable,
 * résolue seulement à l'exécution (« cd x && echo $PWD » voit le nouveau dossier).
 */
export function tokenize(line) {
  const toks = [];
  let cur = null, i = 0;
  const word = () => (cur ??= { parts: [] });
  const flush = () => { if (cur) toks.push(cur); cur = null; };
  const add = (text, q) => word().parts.push({ text, q });
  const dollar = q => {
    const m = /^\$(\?|\{(\w+)\}|(\w+))/.exec(line.slice(i));
    if (!m) return false;
    i += m[0].length;
    word().parts.push({ name: m[2] || m[3] || m[1], q });
    return true;
  };
  while (i < line.length) {
    const c = line[i];
    if (/\s/.test(c)) { flush(); i++; continue; }
    const op = /^(\|\||&&|>>|[|;<>&])/.exec(line.slice(i));
    if (op) { flush(); toks.push({ op: op[0] }); i += op[0].length; continue; }
    if (c === "'") {
      const j = line.indexOf("'", i + 1);
      if (j < 0) throw new SyntaxError("guillemet ' non fermé");
      add(line.slice(i + 1, j), true); i = j + 1;
    } else if (c === '"') {
      i++;
      add("", true);   // "" est un mot vide, pas une absence de mot
      while (i < line.length && line[i] !== '"') {
        if (line[i] === "\\" && /["\\$]/.test(line[i + 1] ?? "")) { add(line[i + 1], true); i += 2; }
        else if (line[i] === "$" && dollar(true)) { /* variable */ }
        else add(line[i++], true);
      }
      if (i >= line.length) throw new SyntaxError('guillemet " non fermé');
      i++;
    } else if (c === "\\") {
      add(line[i + 1] ?? "", true); i += 2;
    } else if (c === "$" && dollar(false)) {
      /* variable */
    } else { add(c, false); i++; }
  }
  flush();
  return toks;
}

const vars = () => ({ "?": String(state.status), PWD: absPath(state.cwd), HOME: "/", USER,
  OLDPWD: state.oldpwd ? absPath(state.oldpwd) : "" });

/** Mots d'un étage de pipeline → arguments : variables résolues, jokers développés hors guillemets. */
export function argv(words) {
  const v = vars(), out = [];
  for (const w of words) {
    let text = "", pat = "";
    for (const p of w.parts) {
      const val = p.name !== undefined ? (Object.hasOwn(v, p.name) ? v[p.name] : "") : p.text;
      text += val;
      pat += p.q ? escapeGlob(val) : val;
    }
    if (!text && w.parts.every(p => p.name !== undefined && !p.q)) continue;  // $VIDE disparaît
    if (!hasGlob(pat)) { out.push(text); continue; }
    const exp = expandGlob(pat);
    out.push(...(exp.length === 1 && exp[0] === pat ? [text] : exp));
  }
  return out;
}

/** Entrées/sorties d'une commande : vers le terminal, ou capturées pour le pipe suivant. */
function makeIO(ui, name, stdin, tty) {
  const buf = [];
  const text = c => (typeof c === "string" ? c : c.map(p => (typeof p === "string" ? p : p.t)).join(""));
  return {
    name, stdin, tty, ui,
    out(content, cls) { tty ? ui.print(content, cls) : buf.push(text(content)); },
    cols(items) { tty ? ui.cols(items) : items.forEach(it => buf.push(text(it))); },
    err(msg) { ui.print(msg, "err"); },
    node(el) { if (tty) ui.node(el); },
    captured: () => (buf.length ? buf.join("\n") + "\n" : ""),
  };
}

/** Commande inconnue : suggère la plus proche (distance d'édition ≤ 2). */
function suggest(name) {
  const d = (a, b) => {
    const m = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
    for (let j = 1; j <= b.length; j++) m[0][j] = j;
    for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++)
      m[i][j] = Math.min(m[i - 1][j] + 1, m[i][j - 1] + 1, m[i - 1][j - 1] + (a[i - 1] !== b[j - 1]));
    return m[a.length][b.length];
  };
  const best = Object.keys(COMMANDS).map(c => [d(name, c), c]).sort((x, y) => x[0] - y[0])[0];
  return best && best[0] <= 2 ? best[1] : null;
}

/** Arguments déjà développés → texte réinjectable dans une ligne de commande. */
const quote = args => args.map(a => `'${a.replaceAll("'", "'\\''")}'`).join(" ");
const expanding = new Set();   // alias/fonctions en cours : pas de récursion (comme bash)

export const runStage = (words, ui, stdin, tty) => execArgs(argv(words), ui, stdin, tty, words);

/**
 * Exécute une commande déjà découpée en arguments (utilisé aussi par sudo).
 * `words` : mots bruts, pour que sudo redéveloppe les jokers avec les droits root.
 */
export async function execArgs(args, ui, stdin, tty, words = null, builtin = false) {
  if (!args.length) return { status: 0, out: "" };
  const user = !builtin && !expanding.has(args[0]) &&
    (Object.hasOwn(FUNCS, args[0]) ? FUNCS[args[0]].replace(/"\$@"|\$@/g, quote(args.slice(1)))
      : Object.hasOwn(USER_ALIASES, args[0]) ? `${USER_ALIASES[args[0]]} ${quote(args.slice(1))}` : null);
  if (user) {
    expanding.add(args[0]);
    try { return await evalLine(user, ui, stdin, tty); } finally { expanding.delete(args[0]); }
  }
  if (Object.hasOwn(ALIASES, args[0])) args = [...ALIASES[args[0]], ...args.slice(1)];
  const [name, ...rest] = args;
  const cmd = Object.hasOwn(COMMANDS, name) ? COMMANDS[name] : null;
  const io = makeIO(ui, name, stdin, tty);
  io.words = words;
  if (!cmd) {
    io.err(`bash: ${name} : commande introuvable`);
    const s = suggest(name);
    if (s) io.out(`Vouliez-vous dire : ${s} ?`, "dim");
    return { status: 127, out: "" };
  }
  let status;
  try {
    status = (await cmd.run(rest, io)) ?? 0;
  } catch (e) {
    io.err(`${name}: ${e.message ?? e}`);
    status = 1;
  }
  return { status, out: io.captured() };
}

/** Exécute une ligne complète tapée au clavier. */
export async function run(line, ui) {
  await evalLine(line, ui);
  save();
}

/** Évalue une ligne (aussi le corps d'un alias ou d'une fonction) ; sortie capturée hors terminal. */
async function evalLine(line, ui, stdin = null, tty = true) {
  let toks;
  try { toks = tokenize(line); } catch (e) {
    ui.print(`bash: erreur de syntaxe : ${e.message}`, "err");
    state.status = 2;
    return { status: 2, out: "" };
  }
  // Découpage en listes séparées par ; && || puis en étages séparés par |.
  const syntax = msg => { ui.print(`bash: erreur de syntaxe ${msg}`, "err"); state.status = 2; return { status: 2, out: "" }; };
  const lists = [{ sep: ";", stages: [[]] }];
  let empty = true, lastOp = null;   // étage courant vide ? dernier opérateur rencontré
  for (const t of toks) {
    const l = lists[lists.length - 1];
    if (t.op === ";" || t.op === "&&" || t.op === "||" || t.op === "|") {
      if (empty) return syntax(`près du symbole inattendu « ${t.op} »`);
      if (t.op === "|") l.stages.push([]);
      else lists.push({ sep: t.op, stages: [[]] });
      empty = true; lastOp = t.op;
    } else if (t.op) {
      ui.print(t.op === "&" ? "bash: & : pas de tâches de fond ici"
        : `bash: redirection « ${t.op} » : ${ERR.EROFS}`, "err");
      state.status = 1;
      return { status: 1, out: "" };
    } else { l.stages[l.stages.length - 1].push(t); empty = false; }
  }
  if (empty && lastOp && lastOp !== ";") return syntax(`: fin de ligne inattendue après « ${lastOp} »`);
  let out = "";
  for (const l of lists) {
    if (!l.stages[0].length) continue;   // ligne vide, ou « ; » final
    if ((l.sep === "&&" && state.status !== 0) || (l.sep === "||" && state.status === 0)) continue;
    let input = stdin, res = { status: 0 };
    for (let i = 0; i < l.stages.length; i++) {
      res = await runStage(l.stages[i], ui, input, tty && i === l.stages.length - 1);
      input = res.out;
    }
    if (!tty) out += res.out;
    state.status = res.status;
  }
  return { status: state.status, out };
}
