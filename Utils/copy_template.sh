#!/bin/bash

# Définir les modèles disponibles
declare -A MODELES=(
    ["1"]="cours-template.tex"
    ["2"]="exercice-template.tex"
    ["3"]="activite-template.tex"
    ["4"]="devoir-template.tex"
    ["5"]="tikz-template.tex"
)

TEMPLATES_PATH="$HOME/texmf/tex/latex/Mathdoc"
current_dir=$(basename "$PWD")

# Fonction pour vérifier le numéro de séquence
verifier_sequence() {
    if [[ $current_dir =~ ^S([0-9]{2}) ]]; then
        printf "${BASH_REMATCH[1]}"
    else
        printf "0"
    fi
}

# Fonction pour copier un modèle
copier_modele() {
    local sequence_number; sequence_number=$(verifier_sequence)
    local choix=$1
    local template="${MODELES[$choix]}"
    local chemin_modele="$TEMPLATES_PATH/$template"

    if [[ ! -f "$chemin_modele" ]]; then
        printf "Erreur : le modèle '%s' n'existe pas.\n" "$template" >&2
        return 1
    fi

    local nom_fichier
    case $choix in
        1)
            read -p "Entrez le nom du cours (e.g. Addition) : " course_name
            # Si sequence_number est 0, ajuster le nom final
	    if [[ "$sequence_number" == "0" ]]; then
		output_file="Cours-${course_name}.tex"
	    else
		output_file="Cours-S${sequence_number}-${course_name}.tex"
	    fi

            ;;
        2)
            read -p "Entrez le code de l'exercice (e.g. 1a) : " exercise_code
            read -p "Entrez le nom de l'exercice (e.g. Addition) : " exercise_name
	    if [[ "$sequence_number" == "0" ]]; then
		output_file="Ex-${exercise_code}-${exercise_name}.tex"
	    else
		output_file="Ex-${exercise_code}-S${sequence_number}-${exercise_name}.tex"
	    fi
            ;;
        3)
            read -p "Entrez le code de l'activité (e.g. 1a) : " activity_code
            read -p "Entrez le nom de l'activité (e.g. Addition) : " activity_name
	    if [[ "$sequence_number" == "0" ]]; then
		output_file="Act-${activity_code}-${activity_name}.tex"
	    else
		output_file="Act-${activity_code}-S${sequence_number}-${activity_name}.tex"
	    fi
            ;;
        4)
            read -p "Entrez le code du devoir (e.g. 1a) : " exam_code
            read -p "Entrez le nom du devoir (e.g. Addition) : " exam_name
	    if [[ "$sequence_number" == "0" ]]; then
		output_file="DS-${exam_code}-${exam_name}.tex"
	    else
		output_file="DS-${exam_code}-S${sequence_number}-${exam_name}.tex"
	    fi
            ;;
        5)
            read -p "Entrez le nom du fichier (e.g. Triangle) : " file_name
            output_file="${file_name}.tex"
            ;;
        *)
            printf "Option invalide.\n" >&2
            return 1
            ;;
    esac

    cp "$chemin_modele" "$output_file" && printf "Fichier créé : %s\n" "$output_file" || printf "Erreur lors de la création du fichier.\n" >&2
}

# Fonction principale
main() {
    while true; do
        printf "1) Cours\n"
        printf "2) Exercice\n"
        printf "3) Activité\n"
        printf "4) Devoir\n"
        printf "5) Fichier TikZ\n"
        printf "Entrez votre choix (ou 'q' pour quitter) : "
        read -r choix

        if [[ "$choix" == "q" ]]; then
            exit 0
        fi

        if [[ -n "${MODELES[$choix]}" ]]; then
            copier_modele "$choix"
        else
            printf "Choix invalide.\n"
        fi

        printf "\nVoulez-vous créer un autre fichier ? (y/N) : "
        read -r continuer
        if [[ "$continuer" != "y" ]]; then
            break
        fi
    done
}

# Lancer le script
main
