#!/bin/bash

# Fonction pour copier la commande cd dans le presse-papier sans guillemets
go_to_wherever() {
    local dir=$1
    local cd_command="cd $dir"
    echo "$cd_command" | xclip -selection clipboard
    echo "La commande suivante a été copiée dans votre presse-papier :"
    echo "$cd_command"
}

#!/bin/bash

# Fonction qui liste les dossiers dans un répertoire donné, numérote, et permet de choisir
go_to_directory_and_select() {
    local chemin=$1
    # Vérifier si le répertoire existe
    if [ ! -d "$chemin" ]; then
        echo "Le répertoire spécifié n'existe pas."
        return 1
    fi

    # Liste des dossiers dans le répertoire, triée par ordre alphabétique
    echo "Liste des dossiers dans $chemin :"
    # Utilisation de `find` pour lister uniquement les dossiers et triage par ordre alphabétique
    dirs=$(find "$chemin" -maxdepth 1 -type d | sed 's|^'"$chemin"'/||' | tail -n +2 | sort)
    
    # Affichage des dossiers numérotés
    i=1
    for dir in $dirs; do
        echo "$i) $dir"
        i=$((i+1))
    done

    # Demander à l'utilisateur de choisir un numéro de dossier ou de valider avec "Enter" pour choisir le dernier
    read -p "Choisissez un dossier (appuyez sur Enter pour le dernier) : " choice

    # Si aucune sélection, on prend le dernier dossier
    if [ -z "$choice" ]; then
        choice=$((i-1))
    fi

    # Obtenir le nom du dossier choisi
    selected_dir=$(echo "$dirs" | sed -n "${choice}p")

    # Vérifier que le dossier existe
    if [ -z "$selected_dir" ]; then
        echo "Choix invalide."
        return 1
    fi

    # Afficher la commande cd correspondante
    full_path="$chemin/$selected_dir"

    # Copier la commande dans le presse-papier
    cd_command="cd $full_path"
    echo -n "$cd_command" | xclip -selection clipboard
    echo "La commande a été copiée dans votre presse-papier."
    echo "$cd_command"
}

# Demande à l'utilisateur de choisir un niveau
echo "Choisissez un niveau :"
echo "1) Terminale STMG"
echo "2) Première Spé"
echo "5) Cinquième"
echo "6) Sixième"
read -p "Votre choix : " niveau

# Définir le chemin en fonction du niveau
case "$niveau" in
    1)
        chemin="$HOME/Cours/Terminale"
        ;;
    2)
        chemin="$HOME/Cours/Premiere"
        ;;
    5)
        chemin="$HOME/Cours/Cinquieme"
        ;;
    6)
        chemin="$HOME/Cours/Sixieme"
        ;;
    *)
        echo "Choix invalide."
        exit 1
        ;;
esac

# Copier la commande cd dans le presse-papier sans guillemets
go_to_directory_and_select "$chemin"
