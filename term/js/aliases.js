// Alias et fonctions de term/aliases.sh (comme un ~/.bash_aliases), développés à l'exécution.
export const USER_ALIASES = {};   // nom → ligne de commande
export const FUNCS = {};          // nom → corps (« "$@" » remplacé par les arguments)

/** Lit la syntaxe bash restreinte : alias nom="…" / '…', et nom() { … } sur plusieurs lignes. */
export function parseAliases(text) {
  for (const o of [USER_ALIASES, FUNCS]) for (const k of Object.keys(o)) delete o[k];
  text = text.replace(/^\s*#.*$/gm, "");
  for (const m of text.matchAll(/^\s*alias\s+([\w.-]+)=(?:"([^"]*)"|'([^']*)'|(\S+))/gm))
    USER_ALIASES[m[1]] = m[2] ?? m[3] ?? m[4];
  for (const m of text.matchAll(/^\s*(?:function\s+)?([\w.-]+)\s*\(\)\s*\{([\s\S]*?)^\s*\}/gm))
    FUNCS[m[1]] = m[2].split("\n").map(l => l.trim()).filter(Boolean).join(" ; ");
}

/** Recharge aliases.sh (absent ou illisible : pas d'alias, le terminal marche quand même). */
export async function loadAliases() {
  try {
    const r = await fetch("aliases.sh", { cache: "no-cache" });
    parseAliases(r.ok ? await r.text() : "");
  } catch { parseAliases(""); }
}
