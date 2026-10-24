// Interface du terminal : affichage, prompt, clavier, historique, complétion.
import { HOST, USER } from "./config.js";
import { state, load, save, isRoot } from "./state.js";
import { loadFS, META, lookup, absPath, isDir } from "./fs.js";
import { run } from "./shell.js";
import { complete } from "./complete.js";

const BANNER = [
  " ▗▄▄▖ ▗▄▖ ▗▖ ▗▖▗▄▄▖  ▗▄▄▖    ▗▄▄▄  ▗▄▄▄▖    ▗▖  ▗▖ ▗▄▖▗▄▄▄▖▗▖ ▗▖ ▗▄▄▖",
  "▐▌   ▐▌ ▐▌▐▌ ▐▌▐▌ ▐▌▐▌       ▐▌  █ ▐▌       ▐▛▚▞▜▌▐▌ ▐▌ █  ▐▌ ▐▌▐▌   ",
  "▐▌   ▐▌ ▐▌▐▌ ▐▌▐▛▀▚▖ ▝▀▚▖    ▐▌  █ ▐▛▀▀▘    ▐▌  ▐▌▐▛▀▜▌ █  ▐▛▀▜▌ ▝▀▚▖",
  "▝▚▄▄▖▝▚▄▞▘▝▚▄▞▘▐▌ ▐▌▗▄▄▞▘    ▐▙▄▄▀ ▐▙▄▄▖    ▐▌  ▐▌▐▌ ▐▌ █  ▐▌ ▐▌▗▄▄▞▘",
].join("\n");

const $ = s => document.querySelector(s);
const term = $("#term"), out = $("#out"), line = $("#line"), ps1 = $("#ps1"), input = $("#cmd");
let busy = false;
let password = null;   // résolveur de la saisie de mot de passe en cours
let draft = "";        // ligne en cours de frappe quand on remonte l'historique

const selecting = () => { const s = getSelection(); return !!s && !s.isCollapsed && s.toString() !== ""; };

// --- Affichage ----------------------------------------------------------------

/** Contenu : texte, ou liste de morceaux (texte | { t, cls, cmd, href }). */
function fill(el, content) {
  if (typeof content === "string") { el.textContent = content; return el; }
  for (const p of content) {
    if (typeof p === "string") { el.append(p); continue; }
    let s;
    if (p.href) { s = document.createElement("a"); s.href = p.href; s.target = "_blank"; s.rel = "noopener"; }
    else s = document.createElement("span");
    s.textContent = p.t;
    if (p.cls) s.className = p.cls;
    if (p.cmd) {
      s.tabIndex = 0; s.setAttribute("role", "button"); s.title = p.cmd;
      s.onclick = () => exec(p.cmd);
      s.onkeydown = e => { if (e.key === "Enter") { e.preventDefault(); exec(p.cmd); } };
    }
    el.append(s);
  }
  return el;
}

const scroll = () => { term.scrollTop = term.scrollHeight; };

const ui = {
  print(content, cls) {
    const d = fill(document.createElement("div"), content);
    if (cls) d.className = cls;
    out.append(d);
    scroll();
  },
  /** Plusieurs noms en colonnes, comme ls dans un vrai terminal. */
  cols(items) {
    const d = document.createElement("div");
    d.className = "cols";
    const w = Math.max(...items.map(it => it.reduce((n, p) => n + (typeof p === "string" ? p : p.t).length, 0)));
    d.style.setProperty("--w", `${Math.min(w, 48) + 1}ch`);
    for (const it of items) d.append(fill(document.createElement("span"), it));
    out.append(d);
    scroll();
  },
  node(el) { out.append(el); el.addEventListener?.("load", scroll); scroll(); },
  clear() { out.replaceChildren(); },
  /** Saisie masquée (sudo). Renvoie le texte, ou null si Ctrl+C. */
  readPassword(prompt) {
    return new Promise(resolve => {
      password = resolve;
      ps1.textContent = prompt;
      input.type = "password";
      input.value = "";
      line.hidden = false;
      input.focus();
    });
  },
};

function psParts() {
  const root = isRoot();
  return [{ t: `${root ? "root" : USER}@${HOST}`, cls: root ? "ps-root" : "ps-user" }, ":",
    { t: absPath(state.cwd), cls: "ps-path" }, root ? "# " : "$ "];
}

function showPrompt() {
  ps1.replaceChildren();
  fill(ps1, psParts());
  input.type = "text";
  input.value = "";
  line.hidden = false;
  // Le dossier courant est aussi dans l'URL : /term/#/Sixieme/S04-Angles est partageable.
  const h = "#" + absPath(state.cwd);
  if (location.hash !== encodeURI(h)) history.replaceState(null, "", h === "#/" ? location.pathname : h);
  document.title = `${absPath(state.cwd)} — Terminal`;
  scroll();
  if (!matchMedia("(pointer: coarse)").matches) input.focus({ preventScroll: true });
}

// --- Exécution ----------------------------------------------------------------

/** !!, !n, !préfixe : rappel de l'historique, comme bash. */
function expandHistory(cmd) {
  const h = state.history;
  // Pas d'expansion entre apostrophes : 'Bravo!' reste tel quel (morceaux impairs du split).
  return cmd.split(/('[^']*')/).map((part, k) => (k % 2 ? part : part.replace(/!(!|-?\d+|[A-Za-z][\w-]*)/g, (m, x) => {
    let r;
    if (x === "!") r = h[h.length - 1];
    else if (/^-?\d+$/.test(x)) r = h[+x > 0 ? +x - 1 : h.length + +x];
    else r = [...h].reverse().find(c => c.startsWith(x));
    if (r === undefined) throw new Error(`bash: ${m} : événement introuvable`);
    return r;
  }))).join("");
}

async function exec(cmd) {
  if (busy || password) return;
  busy = true;
  line.hidden = true;
  input.value = "";
  ui.print([...psParts(), cmd]);
  try {
    const expanded = expandHistory(cmd);
    if (expanded !== cmd) { cmd = expanded; ui.print(cmd); }
    if (cmd.trim() && state.history[state.history.length - 1] !== cmd) state.history.push(cmd);
    state.hIndex = state.history.length;
    draft = "";
    await run(cmd, ui);
  } catch (e) {
    ui.print(e.message ?? String(e), "err");
    state.status = 1;
  }
  save();
  busy = false;
  showPrompt();
}

function interrupt() {
  // Commande en cours : seules celles qui écoutent « term-interrupt » (clock) s'arrêtent.
  if (busy && !password) { dispatchEvent(new Event("term-interrupt")); return; }
  if (password) { const r = password; password = null; ui.print(ps1.textContent + "^C"); line.hidden = true; r(null); return; }
  ui.print([...psParts(), input.value + "^C"]);
  state.status = 130;
  state.hIndex = state.history.length;
  showPrompt();
}

function tab() {
  const r = complete(input.value, input.selectionStart ?? input.value.length);
  if (!r) return;
  input.value = r.value;
  input.setSelectionRange(r.caret, r.caret);
  if (r.choices.length) {
    ui.print([...psParts(), input.value]);
    ui.cols(r.choices.map(c => [c]));
  }
}

function recall(dir) {
  const h = state.history;
  if (state.hIndex === h.length) draft = input.value;
  state.hIndex = Math.max(0, Math.min(h.length, state.hIndex + dir));
  input.value = state.hIndex === h.length ? draft : h[state.hIndex];
  const n = input.value.length;
  requestAnimationFrame(() => input.setSelectionRange(n, n));
}

function key(k, e) {
  const caret = input.selectionStart ?? 0;
  switch (k) {
    case "Enter":
      if (password) {
        const r = password, v = input.value;
        password = null; line.hidden = true; input.value = "";
        ui.print(ps1.textContent);   // la ligne du mot de passe reste visible, sans le mot de passe
        r(v);
      }
      else exec(input.value);
      break;
    case "Tab": if (!password && !busy) tab(); break;
    case "ArrowUp": if (!password && !busy) recall(-1); break;
    case "ArrowDown": if (!password && !busy) recall(1); break;
    case "C-c": interrupt(); break;
    case "C-l": ui.clear(); break;
    case "C-u": input.value = input.value.slice(caret); input.setSelectionRange(0, 0); break;
    case "C-k": input.value = input.value.slice(0, caret); break;
    case "C-a": input.setSelectionRange(0, 0); break;
    case "C-e": input.setSelectionRange(input.value.length, input.value.length); break;
    case "C-w": {
      const b = input.value.slice(0, caret).replace(/\S*\s*$/, "");
      input.value = b + input.value.slice(caret);
      input.setSelectionRange(b.length, b.length);
      break;
    }
    default: return false;
  }
  e?.preventDefault();
  return true;
}

input.addEventListener("keydown", e => {
  if (e.isComposing) return;
  if (e.ctrlKey && !e.altKey && !e.metaKey && /^[clukaew]$/i.test(e.key)) {
    // Ctrl+C copie quand du texte est sélectionné dans la sortie, sinon interrompt.
    if (e.key.toLowerCase() === "c" && selecting()) return;
    key(`C-${e.key.toLowerCase()}`, e);
    return;
  }
  if (!e.ctrlKey && !e.altKey && !e.metaKey) key(e.key, e);
});

// Un clic dans le terminal donne le focus à la ligne de commande (sauf sélection de texte).
term.addEventListener("click", e => {
  if (selecting() || e.target.closest("a, [role=button]")) return;
  if (!line.hidden) input.focus({ preventScroll: true });
});

// Touches tactiles : Tab, flèches, ^C, et raccourcis tapés.
for (const b of document.querySelectorAll("#keys button")) {
  b.addEventListener("pointerdown", e => e.preventDefault());  // garde le clavier virtuel ouvert
  b.addEventListener("click", () => {
    if (b.dataset.key) key(b.dataset.key);
    else if (!busy && !password) exec(b.dataset.type);
    input.focus({ preventScroll: true });
  });
}

// Clavier virtuel : garder la ligne visible quand il se déplie.
window.visualViewport?.addEventListener("resize", scroll);

// --- Démarrage ----------------------------------------------------------------

function cwdFromHash() {
  let h;
  try { h = decodeURIComponent(location.hash.slice(1)); } catch { return; }   // %E9, % isolé...
  if (!h.startsWith("/")) return;
  const r = lookup(h, []);
  if (!r.err && isDir(r.node)) state.cwd = r.segs;
}

function banner() {
  const probe = document.createElement("span");
  probe.textContent = "M".repeat(10);
  out.append(probe);
  const cols = term.clientWidth / (probe.getBoundingClientRect().width / 10);
  probe.remove();
  if (cols >= 72) ui.print(BANNER, "banner");
  else ui.print([{ t: META.title ?? "Cours de Maths", cls: "t-dir" }]);
  ui.print(`Cours de ${META.author} · ${META.school} · année ${META.year}`, "dim");
  ui.print("");
  ui.print(["Tapez ", { t: "help", cls: "t-dir click", cmd: "help" }, " pour la liste des commandes, ",
    { t: "ls", cls: "t-dir click", cmd: "ls" }, " pour voir les dossiers. ",
    "Tab complète les noms, ↑ ↓ rappellent les commandes, un clic sur un nom l'ouvre."]);
  ui.print(["Version classique du site : ", { t: "../index.html", href: "../index.html" }], "dim");
  ui.print("");
}

async function main() {
  load();
  document.documentElement.dataset.theme = state.theme;
  try {
    await loadFS();
  } catch (e) {
    ui.print(`Impossible de charger l'arborescence du site (${e.message}).`, "err");
    ui.print(["Le site reste accessible ici : ", { t: "../index.html", href: "../index.html" }]);
    return;
  }
  // Dossier sauvegardé disparu depuis (renommage...) : retour à la racine.
  const saved = lookup(absPath(state.cwd), []);
  if (saved.err || !isDir(saved.node)) state.cwd = [];
  if (state.root || state.sudoUntil) {
    if (state.sudoUntil < Date.now()) { state.root = false; state.sudoUntil = 0; }
  }
  cwdFromHash();
  window.addEventListener("hashchange", () => { if (!busy) { cwdFromHash(); showPrompt(); } });
  banner();
  showPrompt();
  input.focus({ preventScroll: true });
}

main();
