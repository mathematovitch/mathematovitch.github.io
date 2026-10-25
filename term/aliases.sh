# Alias du terminal /term : lus au démarrage, relus par « s » (source ~/.bashrc).
# Syntaxe bash restreinte : alias nom="commande", ou fonction nom() { ... "$@" ... }.

alias c="clear"
alias s="source ~/.bashrc"
alias pdf="open"

cd() {
    builtin cd "$@" && ll
}
