// Registre des commandes : nom → { help, usage, more?, hidden?, run(args, io) → code de retour }.
import { ls, cd, pwd, tree } from "./nav.js";
import { cat, open, head, tail, wc, sort } from "./files.js";
import { find, grep } from "./search.js";
import { help, history, clear, echo, whoami, date, theme, sudo, exit, readonly } from "./misc.js";

export const COMMANDS = {
  help, ls, cd, pwd, tree, open, cat, find, grep, head, tail, wc, sort,
  history, echo, whoami, date, clear, theme, sudo, exit,
  ...readonly(),
};

export const ALIASES = {
  man: ["help"], ll: ["ls", "-l"], la: ["ls", "-a"], l: ["ls"], dir: ["ls"],
  "xdg-open": ["open"], less: ["cat"], more: ["cat"], cls: ["clear"],
  su: ["sudo", "-s"], logout: ["exit"], quit: ["exit"], "cd..": ["cd", ".."],
};
