import pandas as pd
import re

def reorganize_unique_id(file_path):
    # Charger le fichier CSV dans un DataFrame
    df = pd.read_csv(file_path,sep=';', dtype=str, encoding='iso8859_15')
    
    # Fonction pour réorganiser les valeurs de la colonne 'unique ID'
    def modify_id(value):
        # Vérifie la présence de '-1', '-2' ou '-3' après le code principal
        match = re.search(r'(.*?)-([123])\s(.*)', value)
        if match:
            # Extraire les différentes parties de l'identifiant unique
            base, suffix, rest = match.groups()
            # Reformater l'identifiant unique
            return f"{base} {rest}-{suffix}"
        return value  # Retourne la valeur inchangée si aucun changement n'est nécessaire
    
    # Appliquer la fonction de modification à la colonne 'unique ID'
    df['unique ID'] = df['unique ID'].apply(modify_id)
    
    # Sauvegarder le DataFrame modifié dans un nouveau fichier CSV
    output_path = file_path.replace(".csv", "_modified.csv")
    df.to_csv(output_path, sep=';', index=False, encoding='iso8859_15')
    print(f"Fichier modifié enregistré sous : {output_path}")

# Exécuter la fonction avec le chemin de votre fichier .csv
reorganize_unique_id("output/outputTemp.csv")
