// État du shell, sauvegardé dans localStorage (dossier courant, historique, thème).
import { HISTORY_MAX } from "./config.js";
import { active } from "../../assets/prof.js";

const KEY = "termjs";

export const state = {
  cwd: [],          // chemin courant, en segments : ["Sixieme", "S04-Angles"]
  oldpwd: null,     // pour « cd - »
  history: [],
  hIndex: 0,
  status: 0,        // code de retour de la dernière commande ($?)
  theme: "vert",
};

export function load() {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) || "{}");
    if (Array.isArray(s.cwd)) state.cwd = s.cwd;
    if (Array.isArray(s.history)) state.history = s.history.slice(-HISTORY_MAX);
    if (typeof s.theme === "string") state.theme = s.theme;
  } catch { /* stockage indisponible (navigation privée...) : on repart de zéro */ }
  state.hIndex = state.history.length;
}

export function save() {
  try {
    localStorage.setItem(KEY, JSON.stringify({
      cwd: state.cwd, history: state.history.slice(-HISTORY_MAX), theme: state.theme,
    }));
  } catch { /* idem */ }
}

/** Droits root : shell root = mode prof du site actif (2 h, jusqu'à « exit » ou « Quitter »). */
export const isRoot = () => state.elevated === true || active();
