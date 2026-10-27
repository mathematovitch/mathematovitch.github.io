#!/usr/bin/env python3
"""Clé du mode prof : les documents prof (DS, corrigés …-Corr, Seq, Prep, archives, .tex à corrigé) ne
sont dans le dépôt que chiffrés (X.enc) ; le site et le terminal les déchiffrent une fois le
mot de passe saisi (assets/prof.js).

Usage : python3 tools/profkey.py init      crée la clé et choisit le mot de passe
        python3 tools/profkey.py passwd    change le mot de passe (les fichiers ne changent pas)
        python3 tools/profkey.py restore   autre machine : retrouve la clé avec le mot de passe

Schéma :
- clé maître K (32 octets aléatoires), gardée en local dans dev/prof.key (jamais commitée) ;
- assets/prof.json (public) : K chiffrée en AES-256-GCM par PBKDF2-SHA256(mot de passe, sel,
  600 000 itérations). Un mot de passe faux fait échouer GCM : c'est la vérification. Le dépôt
  sert donc de sauvegarde de la clé, mais sa sécurité est celle du mot de passe ;
- X.enc = MAGIC + IV (12 octets) + AES-256-GCM(K, contenu de X). IV = HMAC(K, chemin, empreinte
  du contenu) : même fichier => même .enc à l'octet près (pas de faux diff git au build).

Stdlib + le module `cryptography` (AES-GCM), importé seulement quand il sert : build.py peut
importer ce fichier pour is_secret() sans lui.
"""
import base64
import getpass
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
KEY_FILE = ROOT / "dev" / "prof.key"
PUBLIC = ROOT / "assets" / "prof.json"
ITERATIONS = 600_000
MAGIC = b"MVCH1"
ENC = ".enc"

# Ce qui n'est publié que chiffré (le mode prof du site les montre, déchiffrés).
LEVEL_DIRS = {"Sixieme", "Cinquieme", "Quatrieme", "Troisieme"}
PROF_TYPES = ("Seq", "Prep", "DS")
PROF_RE = re.compile(rf"^({'|'.join(PROF_TYPES)})-")
CORR = "-Corr"  # corrigé = nom du sujet + -Corr : Ex-6C04-01-Nom.pdf -> Ex-6C04-01-Nom-Corr.pdf


def is_corr(name):
    return PurePosixPath(name).stem.endswith(CORR)


def is_secret(rel, read_text):
    """`rel` : chemin relatif à la racine du dépôt ; `read_text()` : son contenu (lu seulement
    pour un .tex). Vrai pour un fichier en clair qui ne doit pas être commité."""
    p = PurePosixPath(rel)
    if not p.parts or p.parts[0] not in LEVEL_DIRS or p.name == "index.html" \
            or p.suffix == ENC or p.name.startswith("."):
        return False
    if "_Archive" in p.parts or PROF_RE.match(p.name) or is_corr(p.name):
        return True
    return p.suffix == ".tex" and "\\ifcorrige" in read_text()


def _aesgcm(key):
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        sys.exit("Module Python « cryptography » manquant (paquet python-cryptography).")
    return AESGCM(key)


def load_key():
    """K depuis dev/prof.key, ou None (clé pas encore créée ou restaurée sur cette machine)."""
    try:
        k = bytes.fromhex(KEY_FILE.read_text().strip())
    except (OSError, ValueError):
        return None
    return k if len(k) == 32 else None


def encrypt(key, rel, data):
    iv = hmac.new(key, rel.encode() + b"\0" + hashlib.sha256(data).digest(), "sha256").digest()[:12]
    return MAGIC + iv + _aesgcm(key).encrypt(iv, data, None)


def decrypt(key, blob):
    if not blob.startswith(MAGIC):
        raise ValueError("fichier chiffré inconnu")
    n = len(MAGIC)
    return _aesgcm(key).decrypt(blob[n:n + 12], blob[n + 12:], None)


def _kek(password, salt, iterations):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)


def wrap(key, password):
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    b64 = lambda b: base64.b64encode(b).decode()
    return {"v": 1, "iter": ITERATIONS, "salt": b64(salt), "iv": b64(iv),
            "wrapped": b64(_aesgcm(_kek(password, salt, ITERATIONS)).encrypt(iv, key, None))}


def unwrap(pub, password):
    """K, ou None si le mot de passe est faux."""
    from cryptography.exceptions import InvalidTag
    d = lambda k: base64.b64decode(pub[k])
    try:
        return _aesgcm(_kek(password, d("salt"), pub["iter"])).decrypt(d("iv"), d("wrapped"), None)
    except InvalidTag:
        return None


def _save_key(key):
    KEY_FILE.parent.mkdir(exist_ok=True)
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(key.hex() + "\n")


def _save_public(pub):
    PUBLIC.write_text(json.dumps(pub, indent=1) + "\n", "utf-8")


def _new_password():
    pw = getpass.getpass("Nouveau mot de passe prof : ")
    if not pw or pw != getpass.getpass("Confirmation : "):
        sys.exit("Mots de passe vides ou différents, rien n'est changé.")
    if len(pw) < 12:
        print("Attention : moins de 12 caractères. Tout repose sur ce mot de passe "
              "(le dépôt est public) : 4 mots au hasard, c'est mieux.")
    return pw


def _ask_key():
    """K de la machine, sinon retrouvée avec le mot de passe actuel."""
    key = load_key()
    if key:
        return key
    if not PUBLIC.is_file():
        sys.exit("Pas de clé : lancer d'abord « python3 tools/profkey.py init ».")
    key = unwrap(json.loads(PUBLIC.read_text("utf-8")), getpass.getpass("Mot de passe prof actuel : "))
    if not key:
        sys.exit("Mot de passe incorrect.")
    return key


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "init":
        if PUBLIC.is_file() or KEY_FILE.is_file():
            sys.exit("Une clé existe déjà (assets/prof.json ou dev/prof.key) : "
                     "« passwd » pour changer le mot de passe, « restore » sur une autre machine.")
        key = secrets.token_bytes(32)
        _save_public(wrap(key, _new_password()))
        _save_key(key)
        print(f"Clé créée : {KEY_FILE.relative_to(ROOT)} (locale) et {PUBLIC.relative_to(ROOT)} "
              "(publique). Lancer ./build.sh pour chiffrer les documents prof.")
    elif cmd == "passwd":
        key = _ask_key()
        _save_public(wrap(key, _new_password()))
        _save_key(key)
        print(f"Mot de passe changé ({PUBLIC.relative_to(ROOT)}, à committer).")
    elif cmd == "restore":
        if not PUBLIC.is_file():
            sys.exit(f"{PUBLIC.relative_to(ROOT)} introuvable.")
        key = unwrap(json.loads(PUBLIC.read_text("utf-8")), getpass.getpass("Mot de passe prof : "))
        if not key:
            sys.exit("Mot de passe incorrect.")
        _save_key(key)
        print(f"Clé restaurée dans {KEY_FILE.relative_to(ROOT)}.")
    else:
        sys.exit(__doc__.split("\n\n")[1])


if __name__ == "__main__":
    main()
