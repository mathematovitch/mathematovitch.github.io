// Mode prof : déverrouillage par le mot de passe et déchiffrement des documents prof (X.enc).
// Schéma (voir tools/profkey.py) : assets/prof.json contient la clé maître K chiffrée en AES-GCM
// par PBKDF2-SHA256(mot de passe) ; chaque X.enc = "MVCH1" + IV (12 octets) + AES-GCM(K, X).
// Module commun au site (wire(), appelé par chaque page) et au terminal (term/js/commands/).
// Session : localStorage[KEY] = { until, k } (k = K en base64), 2 h ; lock() l'efface.

export const KEY = "mathematovitch-prof";
const HOURS = 2;
const MAGIC = "MVCH1";
const BLOB_TTL = 60 * 1000;
const ASSETS = new URL("./", import.meta.url);

const fromB64 = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
const toB64 = u => btoa(String.fromCharCode(...u));

/** Session prof valide, ou null (expirée : effacée au passage). */
export function session() {
  try {
    const s = JSON.parse(localStorage.getItem(KEY) || "null");
    if (s && s.k && s.until > Date.now()) return s;
    if (s !== null) localStorage.removeItem(KEY);
  } catch { /* stockage indisponible ou ancien format */ }
  return null;
}
export const active = () => session() !== null;
export const until = () => session()?.until || 0;

export function lock() {
  try { localStorage.removeItem(KEY); } catch { /* idem */ }
}

/** Vérifie le mot de passe en déchiffrant K ; ouvre la session si c'est le bon. ~1 s (PBKDF2). */
export async function unlock(password) {
  if (!crypto?.subtle) throw new Error("le navigateur refuse le chiffrement ici (page non HTTPS)");
  const r = await fetch(new URL("prof.json", ASSETS), { cache: "no-cache" });
  if (!r.ok) throw new Error(`prof.json : erreur HTTP ${r.status}`);
  const p = await r.json();
  const material = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveKey"]);
  const kek = await crypto.subtle.deriveKey(
    { name: "PBKDF2", hash: "SHA-256", salt: fromB64(p.salt), iterations: p.iter },
    material, { name: "AES-GCM", length: 256 }, false, ["decrypt"]);
  let k;
  try {
    k = new Uint8Array(await crypto.subtle.decrypt({ name: "AES-GCM", iv: fromB64(p.iv) }, kek, fromB64(p.wrapped)));
  } catch { return false; }   // mot de passe faux : GCM refuse
  localStorage.setItem(KEY, JSON.stringify({ until: Date.now() + HOURS * 3600e3, k: toB64(k) }));
  return true;
}

/** Contenu déchiffré de `url` (un .enc), en octets. */
export async function decrypt(url) {
  const s = session();
  if (!s) throw new Error("mode prof inactif");
  const r = await fetch(url);
  if (!r.ok) throw new Error(`erreur HTTP ${r.status}`);
  const buf = new Uint8Array(await r.arrayBuffer());
  if (new TextDecoder().decode(buf.subarray(0, MAGIC.length)) !== MAGIC) throw new Error("fichier chiffré inconnu");
  const key = await crypto.subtle.importKey("raw", fromB64(s.k), "AES-GCM", false, ["decrypt"]);
  const n = MAGIC.length;
  return new Uint8Array(await crypto.subtle.decrypt({ name: "AES-GCM", iv: buf.subarray(n, n + 12) }, key, buf.subarray(n + 12)));
}
export const decryptText = async url => new TextDecoder().decode(await decrypt(url));

const VIEW = { pdf: "application/pdf", html: "text/html", htm: "text/html", png: "image/png", jpg: "image/jpeg",
  jpeg: "image/jpeg", gif: "image/gif", svg: "image/svg+xml", txt: "text/plain", tex: "text/plain" };

/**
 * Ouvre le document chiffré `url` (nom d'origine `name`) : dans un nouvel onglet s'il est
 * affichable (PDF, image...), sinon en téléchargement. À appeler pendant le clic : l'onglet
 * s'ouvre tout de suite, avant le déchiffrement, sinon le bloqueur de pop-ups le refuse.
 */
export function openEnc(url, name) {
  const type = VIEW[name.split(".").pop().toLowerCase()];
  const w = type ? window.open("", "_blank") : null;
  if (w) { w.document.title = name; w.document.body.textContent = `Déchiffrement de ${name}…`; }
  return decrypt(url).then(data => {
    const blob = URL.createObjectURL(new Blob([data], { type: type || "application/octet-stream" }));
    // Adresse blob: valable 1 min seulement (le document déjà affiché reste lisible) :
    // retrouvée plus tard dans l'historique d'un PC partagé, elle ne mène plus à rien.
    setTimeout(() => URL.revokeObjectURL(blob), BLOB_TTL);
    if (w) { w.location.href = blob; return; }
    const a = Object.assign(document.createElement("a"), { href: blob, download: name });
    document.body.append(a); a.click(); a.remove();
  }).catch(e => {
    if (w) w.document.body.textContent = `Impossible d'ouvrir ${name} : ${e.message}`;
    throw e;
  });
}

/** Quitte le mode prof partout : site (classe html.prof) et terminal (shell root). */
export function quit() {
  lock();
  document.documentElement.classList.remove("prof");
}

/** Pages du site : liens chiffrés, bouton « Quitter », connexion (calculatrice de l'accueil, C-x C-x). */
export function wire() {
  const h = document.documentElement;
  document.addEventListener("click", ev => {
    const a = ev.target.closest("a[data-enc]");
    if (!a || ev.button !== 0 || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    ev.preventDefault();
    if (!active()) { h.classList.remove("prof"); return; }
    openEnc(a.href, a.dataset.enc).catch(() => {});
  });
  document.getElementById("profquit")?.addEventListener("click", quit);

  const dlg = document.getElementById("login");
  if (!dlg) return;
  const pw = dlg.querySelector("input"), err = dlg.querySelector(".err"), ok = dlg.querySelector("[type=submit]");
  const toggle = () => {
    if (h.classList.contains("prof")) { quit(); return; }
    pw.value = ""; err.textContent = ""; dlg.showModal();
  };
  document.querySelector(".brand .calc")?.addEventListener("click", toggle);
  // C-x C-x comme sous Emacs, depuis n'importe quelle page. Le premier C-x n'est pas bloqué
  // (couper dans un champ de saisie reste possible), seul le second, dans la seconde qui suit.
  let cx = 0;
  addEventListener("keydown", ev => {
    if (!ev.ctrlKey || ev.altKey || ev.metaKey || ev.key.toLowerCase() !== "x" || dlg.open) { cx = 0; return; }
    if (Date.now() - cx > 1000) { cx = Date.now(); return; }
    ev.preventDefault(); cx = 0; toggle();
  });
  dlg.querySelector(".no").addEventListener("click", () => dlg.close());
  dlg.querySelector("form").addEventListener("submit", async ev => {
    ev.preventDefault();
    err.textContent = "Vérification…"; ok.disabled = true;
    try {
      if (await unlock(pw.value)) { h.classList.add("prof"); dlg.close(); }
      else { err.textContent = "Mot de passe incorrect."; pw.select(); }
    } catch (e) { err.textContent = e.message; }
    finally { ok.disabled = false; }
  });
}
