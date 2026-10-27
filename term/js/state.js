// État du shell, sauvegardé dans localStorage (dossier courant, historique, thème, sudo).
import { HISTORY_MAX, PROF_KEY, PROF_TIMEOUT } from "./config.js";

const KEY = "termjs";

export const state = {
  cwd: [],          // chemin courant, en segments : ["Sixieme", "S04-Angles"]
  oldpwd: null,     // pour « cd - »
  history: [],
  hIndex: 0,
  status: 0,        // code de retour de la dernière commande ($?)
  root: false,      // shell root (sudo -s) jusqu'à « exit »
  sudoUntil: 0,     // horodatage de fin du cache du mot de passe sudo
  theme: "vert",
};

export function load() {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) || "{}");
    if (Array.isArray(s.cwd)) state.cwd = s.cwd;
    if (Array.isArray(s.history)) state.history = s.history.slice(-HISTORY_MAX);
    if (typeof s.theme === "string") state.theme = s.theme;
    if (s.sudoUntil > Date.now()) { state.sudoUntil = s.sudoUntil; state.root = !!s.root; }
  } catch { /* stockage indisponible (navigation privée...) : on repart de zéro */ }
  state.hIndex = state.history.length;
}

export function save() {
  try {
    localStorage.setItem(KEY, JSON.stringify({
      cwd: state.cwd, history: state.history.slice(-HISTORY_MAX), theme: state.theme,
      root: state.root, sudoUntil: state.sudoUntil,
    }));
  } catch { /* idem */ }
}

/** Mode prof du site, partagé avec les pages (fin en ms, 0 si inactif). */
export function profUntil() {
  try { return +localStorage.getItem(PROF_KEY) || 0; } catch { return 0; }
}
export function setProf(on) {
  try { on ? localStorage.setItem(PROF_KEY, String(Date.now() + PROF_TIMEOUT)) : localStorage.removeItem(PROF_KEY); }
  catch { /* stockage indisponible */ }
}

/** Droits root effectifs : shell root, ou commande lancée via sudo. */
export const isRoot = () => state.root || state.elevated === true;
