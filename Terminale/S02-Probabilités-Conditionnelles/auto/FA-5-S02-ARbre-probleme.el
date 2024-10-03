;; -*- lexical-binding: t; -*-

(TeX-add-style-hook
 "FA-5-S02-ARbre-probleme"
 (lambda ()
   (TeX-add-to-alist 'LaTeX-provided-class-options
                     '(("article" "11pt")))
   (TeX-add-to-alist 'LaTeX-provided-package-options
                     '(("Mathdoc" "")))
   (TeX-run-style-hooks
    "latex2e"
    "article"
    "art11"
    "Mathdoc"))
 :latex)

