// Shell : help, history, clear, source, builtin, alias, echo, whoami, date, theme, sudo, exit, et commandes d'écriture refusées.
import { USER } from "../config.js";
import { state, save, isRoot } from "../state.js";
import { active, unlock, quit } from "../../../assets/prof.js";
import { ERR } from "../fs.js";
import { argv, execArgs } from "../shell.js";
import { COMMANDS, ALIASES } from "./index.js";
import { USER_ALIASES, FUNCS, loadAliases } from "../aliases.js";
import { getopt } from "./util.js";

export const help = {
  help: "liste les commandes, ou explique l'une d'elles",
  usage: "help [commande]",
  run(args, io) {
    if (args.length) {
      let status = 0;
      for (const a of args) {
        const name = Object.hasOwn(ALIASES, a) ? ALIASES[a][0] : a;
        const c = Object.hasOwn(COMMANDS, name) ? COMMANDS[name] : null;
        if (!c) { io.err(`help: aucune aide pour « ${a} »`); status = 1; continue; }
        io.out([{ t: name, cls: "t-dir" }, ` — ${c.help}`]);
        io.out(`  usage : ${c.usage}`);
        (c.more ?? []).forEach(m => io.out(`  ${m}`));
      }
      return status;
    }
    io.out("Commandes disponibles (help commande pour le détail) :");
    const w = Math.max(...Object.keys(COMMANDS).map(k => k.length)) + 2;
    for (const [name, c] of Object.entries(COMMANDS)) {
      if (c.hidden) continue;
      io.out([{ t: name.padEnd(w), cls: "t-dir click", cmd: `help ${name}` }, c.help]);
    }
    io.out("");
    io.out("Tab complète les noms, ↑ ↓ rappellent les commandes, cliquer sur un nom l'ouvre.", "dim");
    io.out("Enchaîner : ls | grep Cours, cd S04-Angles && ls, find / -iname '*angle*'", "dim");
  },
};

export const history = {
  help: "liste les commandes déjà tapées",
  usage: "history [-c] [n]",
  more: ["-c  efface l'historique", "!!  relance la dernière commande, !12 la n° 12, !cd la dernière commençant par cd"],
  run(args, io) {
    const { opts, rest } = getopt(args, "c");
    if (opts.c) { state.history = []; state.hIndex = 0; save(); return; }
    const n = rest[0] ? parseInt(rest[0], 10) : state.history.length;
    const start = Math.max(0, state.history.length - n);
    state.history.slice(start).forEach((h, i) =>
      io.out([String(start + i + 1).padStart(5) + "  ", { t: h, cls: "click", cmd: h }]));
  },
};

export const clear = {
  help: "efface l'écran (aussi : Ctrl+L)",
  usage: "clear",
  run(args, io) { if (io.tty) io.ui.clear(); },
};

export const source = {
  help: "relit les alias (term/aliases.sh) et réaffiche l'accueil, sans changer de dossier",
  usage: "source ~/.bashrc   (alias : s)",
  async run(args, io) {
    await loadAliases();
    if (io.tty) { io.ui.clear(); io.ui.banner(); }
  },
};

export const builtin = {
  hidden: true,
  help: "lance la commande du shell, sans passer par les alias et fonctions",
  usage: "builtin commande [arguments...]",
  async run(args, io) {
    const res = await execArgs(args, io.ui, io.stdin, io.tty, null, true);
    if (res.out) io.out(res.out.replace(/\n$/, ""));
    return res.status;
  },
};

export const alias = {
  help: "liste les alias et fonctions (définis dans term/aliases.sh)",
  usage: "alias",
  run(args, io) {
    for (const [k, v] of Object.entries(USER_ALIASES)) io.out(`alias ${k}='${v}'`);
    for (const [k, v] of Object.entries(FUNCS)) io.out(`${k}() { ${v}; }`);
  },
};

export const echo = {
  help: "affiche un texte",
  usage: "echo [texte...]",
  more: ["echo $PWD  dossier courant   echo $?  code de retour de la commande précédente (0 = succès)"],
  run(args, io) { io.out(args.join(" ")); },
};

export const whoami = {
  help: "affiche le nom de l'utilisateur",
  usage: "whoami",
  run(args, io) { io.out(isRoot() ? "root" : USER); },
};

export const date = {
  help: "affiche la date et l'heure",
  usage: "date",
  run(args, io) {
    io.out(new Date().toLocaleString("fr-FR", { dateStyle: "full", timeStyle: "medium" }));
  },
};

const THEMES = ["vert", "ambre", "gris", "clair"];
export const theme = {
  help: "change les couleurs du terminal",
  usage: `theme [${THEMES.join("|")}]`,
  run(args, io) {
    if (!args.length) { io.out(`Thème actuel : ${state.theme}. Disponibles : ${THEMES.join(", ")}`); return; }
    if (!THEMES.includes(args[0])) { io.err(`theme: thème inconnu « ${args[0]} » (${THEMES.join(", ")})`); return 1; }
    state.theme = args[0];
    document.documentElement.dataset.theme = state.theme;
    save();
  },
};

// --- sudo -----------------------------------------------------------------

/** Demande le mot de passe (3 essais, comme sudo) sauf si le mode prof du site est actif.
 *  C'est celui du mode prof : le bon mot de passe déchiffre la clé des documents prof
 *  (assets/prof.js) et active le mode prof, donc le shell root, pour 2 h. */
async function authenticate(io) {
  if (active()) return true;
  for (let k = 0; k < 3; k++) {
    const pw = await io.ui.readPassword(`[sudo] Mot de passe de ${USER} : `);
    if (pw === null) return false;   // Ctrl+C
    let ok;
    try { ok = await unlock(pw); } catch (e) { io.err(`sudo: ${e.message}`); return false; }
    if (ok) {
      io.out("Shell root : corrigés, évaluations et sources visibles, sans mot de passe pendant 2 h. "
        + "« exit » pour redevenir élève.", "dim");
      return true;
    }
    if (k < 2) io.err("Désolé, essayez de nouveau.");
  }
  io.err("sudo: 3 saisies de mot de passe incorrectes");
  return false;
}

export const sudo = {
  help: "mode professeur : devient root (corrigés, évaluations et sources visibles)",
  usage: "sudo -s | su | sudo commande | sudo -k",
  more: ["su, sudo -s  devient root@mathematovitch jusqu'à « exit » (2 h au plus)",
    "sudo ls      pareil, puis lance la commande",
    "sudo -k      quitte le mode root et le mode prof du site",
    "Le mot de passe est celui du mode prof du site (clic sur la calculatrice de l'accueil) ;",
    "si le mode prof est déjà actif sur le site, le terminal est root d'emblée.",
    "Le site est statique : root ne fait qu'afficher les fichiers masqués, rien n'est modifiable."],
  async run(args, io) {
    if (!args.length) { io.err(`usage: ${sudo.usage}`); return 1; }
    if (args[0] === "-k") { quit(); return 0; }
    if (!(await authenticate(io))) return 1;
    if (["-s", "-i", "su", "bash", "sh"].includes(args[0])) return 0;
    const prev = state.elevated;
    state.elevated = true;
    try {
      // Jokers redéveloppés en root : « sudo ls *.tex » voit les sources.
      if (io.words && argv(io.words.slice(0, 1))[0] === "sudo") args = argv(io.words.slice(1));
      const res = await execArgs(args, io.ui, io.stdin, io.tty);
      if (res.out) io.out(res.out.replace(/\n$/, ""));
      return res.status;
    } finally { state.elevated = prev; }
  },
};

export const exit = {
  help: "quitte le mode root (et le mode prof du site), ou revient au site",
  usage: "exit",
  run(args, io) {
    if (isRoot()) { quit(); io.out("exit"); return 0; }
    io.out("déconnexion");
    setTimeout(() => { location.href = "../index.html"; }, 400);
  },
};

// --- Système de fichiers en lecture seule ------------------------------------

const READONLY = {
  rm: "impossible de supprimer", rmdir: "impossible de supprimer", mkdir: "impossible de créer le répertoire",
  touch: "impossible de faire un touch", cp: "impossible de créer le fichier", mv: "impossible de déplacer",
  ln: "impossible de créer le lien", chmod: "impossible de modifier les droits de",
};
/** Commandes d'écriture : elles existent, mais échouent comme sur un disque en lecture seule. */
export function readonly() {
  const cmds = {};
  for (const [name, msg] of Object.entries(READONLY)) cmds[name] = {
    hidden: true, help: "désactivé : site en lecture seule", usage: `${name} ...`,
    run(args, io) {
      const target = args.filter(a => !a.startsWith("-")).pop();
      io.err(target ? `${name}: ${msg} '${target}': ${ERR.EROFS}` : `${name}: opérande manquant`);
      return 1;
    },
  };
  for (const name of ["nano", "vim", "vi", "emacs"]) cmds[name] = {
    hidden: true, help: "désactivé : site en lecture seule", usage: `${name} fichier`,
    run(args, io) {
      io.err(`${name}: ${ERR.EROFS} — pour lire un fichier : cat${args[0] ? " " + args[0] : " fichier"}`);
      return 1;
    },
  };
  return cmds;
}
