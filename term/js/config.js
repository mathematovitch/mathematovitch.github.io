// Réglages du terminal. SUDO_SALT / SUDO_HASH sont réécrits par `python3 term/passwd.py`.
export const HOST = "mathematovitch";
export const USER = "eleve";
export const SITE = "..";            // racine du site, relative à /term/
export const SUDO_SALT = "738a2a63edceada125301cf5";
export const SUDO_HASH = "a7aaa77745777913b93421b2965de66098993aae9bd5ff07d9204ffaebef8c2b";
export const SUDO_TIMEOUT = 15 * 60 * 1000;  // comme sudo : mot de passe redemandé après 15 min
export const HISTORY_MAX = 500;
// Mode prof du site (même mot de passe) : clé localStorage et durée, comme PROF_KEY / PROF_HOURS
// de tools/build.py. Un sudo réussi l'active, et tant qu'il est actif sudo ne redemande rien.
export const PROF_KEY = "mathematovitch-prof";
export const PROF_TIMEOUT = 2 * 60 * 60 * 1000;
