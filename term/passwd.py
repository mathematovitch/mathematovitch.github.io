#!/usr/bin/env python3
"""Change le mot de passe de « sudo » du terminal web.

Usage : python3 term/passwd.py

Le mot de passe n'est jamais stocké : seuls un sel aléatoire et SHA-256(sel + mot de passe)
sont écrits dans term/js/config.js. Rappel : le site est statique et public, sudo ne fait
qu'afficher les fichiers masqués (sources .tex...) ; ce n'est pas une protection.
"""
import getpass
import hashlib
import re
import secrets
import sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parent / "js" / "config.js"

pw = getpass.getpass("Nouveau mot de passe sudo : ")
if not pw or pw != getpass.getpass("Confirmation : "):
    sys.exit("Mots de passe vides ou différents, rien n'est changé.")
salt = secrets.token_hex(12)
digest = hashlib.sha256((salt + pw).encode()).hexdigest()
s = CONFIG.read_text("utf-8")
s = re.sub(r'SUDO_SALT = "[0-9a-f]*"', f'SUDO_SALT = "{salt}"', s)
s = re.sub(r'SUDO_HASH = "[0-9a-f]*"', f'SUDO_HASH = "{digest}"', s)
CONFIG.write_text(s, "utf-8")
print(f"Mot de passe changé dans {CONFIG}")
