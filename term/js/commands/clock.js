// clock : l'heure en grand, police figlet « doh », comme l'alias « termdown -z -f doh ».
import { DOH } from "./doh.js";
import { getopt } from "./util.js";

// « : » éteint (même largeur, hardblanks gardés) pour le clignotement.
const COLON_OFF = DOH[":"].map(l => l.replace(/:/g, " "));

/** Assemble le texte en mode « fitting » de figlet : chaque glyphe glisse vers la gauche jusqu'à toucher. */
export function figlet(text) {
  let rows = DOH["0"].map(() => "");
  for (const ch of text) {
    const g = ch === "!" ? COLON_OFF : DOH[ch];
    if (!g) continue;
    const w = Math.max(...rows.map(r => r.length));
    rows = rows.map(r => r.padEnd(w));
    const trail = s => s.length - s.trimEnd().length;
    const lead = s => s.length - s.trimStart().length;
    const k = Math.min(...rows.map((r, i) => trail(r) + lead(g[i])), w);
    const off = w - k;
    rows = rows.map((r, i) => {
      const out = [...r.padEnd(off + g[i].length)];
      [...g[i]].forEach((c, j) => { if (c !== " ") out[off + j] = c; });
      return out.join("");
    });
  }
  return rows.map(r => r.replaceAll("$", " ").trimEnd());
}

const now = secs => {
  const d = new Date(), p = n => String(n).padStart(2, "0");
  return `${p(d.getHours())}:${p(d.getMinutes())}` + (secs ? `:${p(d.getSeconds())}` : "");
};

export const clock = {
  help: "affiche l'heure en grand, plein écran (pour un contrôle)",
  usage: "clock [-s]",
  more: ["-s  avec les secondes (sinon les « : » clignotent chaque seconde)",
    "Échap ou Ctrl+C pour revenir au terminal. L'écran ne se met pas en veille."],
  run(args, io) {
    const { opts } = getopt(args, "s");
    if (!io.tty) { figlet(now(opts.s)).forEach(l => io.out(l)); return 0; }

    const box = document.createElement("div");
    box.className = "clock";
    box.setAttribute("role", "timer");
    const pre = document.createElement("pre");
    box.append(pre);
    document.body.append(box);

    // Taille de police calculée pour que le texte remplisse l'écran sans déborder.
    const fit = () => {
      pre.style.fontSize = "10px";
      const r = pre.getBoundingClientRect();
      if (!r.width || !r.height) return;
      const s = Math.min(box.clientWidth * 0.94 / r.width, box.clientHeight * 0.9 / r.height);
      pre.style.fontSize = `${Math.max(2, 10 * s)}px`;
    };
    let shown = "";
    const tick = () => {
      const t = now(opts.s);
      // Sans secondes, les « : » clignotent : on voit que l'horloge tourne.
      const blink = !opts.s && new Date().getSeconds() % 2 === 1;
      const key = t + blink;
      if (key === shown) return;
      shown = key;
      pre.textContent = figlet(blink ? t.replace(":", "!") : t).join("\n");
      box.setAttribute("aria-label", t);
      fit();
    };
    tick();
    const timer = setInterval(tick, 250);
    addEventListener("resize", fit);

    // Plein écran du navigateur et écran toujours allumé (projecteur), si le navigateur le permet.
    let lock = null;
    navigator.wakeLock?.request("screen").then(l => { lock = l; }).catch(() => {});
    box.requestFullscreen?.().catch(() => {});

    return new Promise(resolve => {
      const quit = () => {
        clearInterval(timer);
        removeEventListener("resize", fit);
        document.removeEventListener("keydown", onKey, true);
        document.removeEventListener("fullscreenchange", onFs);
        removeEventListener("term-interrupt", quit);
        lock?.release().catch(() => {});
        if (document.fullscreenElement) document.exitFullscreen().catch(() => {});
        box.remove();
        resolve(0);
      };
      // Seuls Échap et Ctrl+C quittent : une touche ou un clic au hasard ne ferme rien.
      const onKey = e => {
        e.preventDefault();
        if (e.key === "Escape" || (e.ctrlKey && e.key.toLowerCase() === "c")) quit();
      };
      // En plein écran, Échap est intercepté par le navigateur : la sortie du plein écran quitte aussi.
      const onFs = () => { if (!document.fullscreenElement) quit(); };
      document.addEventListener("keydown", onKey, true);
      document.addEventListener("fullscreenchange", onFs);
      addEventListener("term-interrupt", quit);   // bouton ^C tactile
    });
  },
};
