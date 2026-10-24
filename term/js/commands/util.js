// Outils communs aux commandes.
import { isDir, shortPath, typeClass, lookup, ERR } from "../fs.js";

/** Met un chemin entre guillemets s'il le faut pour être retapé tel quel. */
export const quote = s => (/^[\w./~+,@%-]+$/.test(s) ? s : `'${s.replace(/'/g, "'\\''")}'`);

/** Nom cliquable : un dossier fait « cd », un fichier fait « open ». */
export function entryPart(name, node, segs, label = name + (isDir(node) ? "/" : "")) {
  const p = quote(shortPath(segs));
  return { t: label, cls: `${typeClass(name, node)} click`, cmd: isDir(node) ? `cd ${p}` : `open ${p}` };
}

/**
 * Sépare options courtes (-la, -n 5...) et opérandes. `withValue` : options qui prennent une valeur.
 * Renvoie { opts, rest } ou lève une erreur « option invalide ».
 */
export function getopt(args, allowed, withValue = "") {
  const opts = {}, rest = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    if (a === "--") { rest.push(...args.slice(i + 1)); break; }
    if (!/^-[^-]/.test(a) || /^-\d+$/.test(a) && !allowed.includes("#")) { rest.push(a); continue; }
    if (/^-\d+$/.test(a)) { opts.n = a.slice(1); continue; }   // head -5
    for (let j = 1; j < a.length; j++) {
      const c = a[j];
      if (!allowed.includes(c)) throw new Error(`option invalide -- '${c}'`);
      if (withValue.includes(c)) {
        const v = a.slice(j + 1) || args[++i];
        if (v === undefined) throw new Error(`l'option requiert un argument -- '${c}'`);
        opts[c] = v;
        break;
      }
      opts[c] = true;
    }
  }
  return { opts, rest };
}

/** lookup() + message d'erreur POSIX au format « cmd: chemin: message ». */
export function resolveOr(io, path, prefix = `${io.name}: ${path}`) {
  const r = lookup(path);
  if (r.err) io.err(`${prefix}: ${ERR[r.err]}`);
  return r.err ? null : r;
}

/** Lignes d'un texte (sans la ligne vide finale). */
export const lines = text => { const l = text.split("\n"); if (l[l.length - 1] === "") l.pop(); return l; };
