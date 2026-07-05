#!/bin/bash

create_sequence_directory() {
    # Liste des niveaux
    echo "Choisissez un niveau :"
    echo "1) Terminale"
    echo "2) Première"
    echo "5) Cinquièmes"
    echo "6) Sixièmes"

    # Lecture du choix utilisateur
    read -p "Entrez le numéro correspondant : " niveau_choix

    # Déterminer le chemin en fonction du choix
    case $niveau_choix in
        6) niveau="Sixieme";;
        5) niveau="Cinquieme";;
        2) niveau="Premiere";;
        1) niveau="Terminale";;
        *) echo "Choix invalide. Abandon."; return 1;;
    esac

    chemin="$HOME/Cours/$niveau"

    # Vérifier si le répertoire existe
    if [ ! -d "$chemin" ]; then
        echo "Le répertoire $chemin n'existe pas. Vérifiez la structure de vos dossiers."
        return 1
    fi

    # Lister les dossiers actuels dans le répertoire et trouver le dernier numéro
    echo "Recherche des séquences existantes dans $chemin ..."
    existing_dirs=$(find "$chemin" -maxdepth 1 -type d -name "S[0-9][0-9]-*" | sort)
    last_number=$(echo "$existing_dirs" | sed 's|.*/S\([0-9][0-9]\)-.*|\1|' | sort -n | tail -n 1)

    # Si aucun dossier n'existe, commencer à 01
    if [ -z "$last_number" ]; then
        next_number="01"
    else
        next_number=$(printf "%02d" $((10#$last_number + 1)))
    fi

    # Demander à l'utilisateur le nom de la nouvelle séquence
    read -p "Entrez le nom de la nouvelle séquence : " sequence_name

    # Valider le nom de la séquence
    if [ -z "$sequence_name" ]; then
        echo "Le nom de la séquence ne peut pas être vide. Abandon."
        return 1
    fi

    # Créer le dossier
    new_dir="S${next_number}-${sequence_name}"
    full_path="$chemin/$new_dir"
    mkdir -p "$full_path"
    echo "Dossier créé : $full_path"

    # Copier la commande `cd` dans le presse-papier
    cd_command="cd $full_path ; copy_template.sh"
    echo -n "$cd_command" | xclip -selection clipboard
    echo "La commande suivante a été copiée dans votre presse-papier :"
    echo "$cd_command"
}

# Appeler la fonction
create_sequence_directory
