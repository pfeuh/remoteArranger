#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys


def convert_file(input_path, output_path):
    if not os.path.isfile(input_path):
        print(f"Erreur : Le fichier d'entrée '{input_path}' est introuvable.")
        sys.exit(1)

    # Espace de noms pour exécuter et extraire TINY_STYLES du fichier source
    namespace = {}
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            code_content = f.read()
        exec(code_content, namespace)
    except Exception as e:
        print(f"Erreur lors de la lecture ou de l'exécution du fichier source : {e}")
        sys.exit(1)

    if "TINY_STYLES" not in namespace:
        print(f"Erreur : La variable 'TINY_STYLES' est introuvable dans le fichier '{input_path}'.")
        sys.exit(1)

    tiny_styles = namespace["TINY_STYLES"]
    catalog = []

    # Structure du tuple attendue : (name, id, category, tempo, num_sig, den_sig)
    for item in tiny_styles:
        if len(item) >= 6:
            name, style_id, category, tempo, num, den = item[:6]
            style_dict = {
                "name": name,
                "id": hex(style_id) if isinstance(style_id, int) else str(style_id),
                "category": category,
                "tempo": tempo,
                "sig": f"{num}/{den}"
            }
            catalog.append(style_dict)

    # Tri alphabétique par nom de style pour la recherche
    catalog.sort(key=lambda x: x["name"].lower())

    # Création du dossier de sortie si nécessaire
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    # Écriture du fichier JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=4)

    print(f"Succès ! Fichier JSON généré : {output_path} ({len(catalog)} styles convertis)")


if __name__ == "__main__":
    #~ parser = argparse.ArgumentParser(description="Convertit un fichier de styles Python contenant TINY_STYLES en JSON.")
    #~ parser.add_argument("input_file", help="Chemin vers le fichier Python source (ex: source_genos.py)")
    #~ parser.add_argument("output_file", nargs="?", default="styles/genos.json", help="Chemin du fichier JSON de sortie (défaut : styles/genos.json)")

    #~ args = parser.parse_args()
    #~ convert_file(args.input_file, args.output_file)
    
    convert_file("/mnt/Data1/Documents/sources/python/remoteGenosArranger/styles/genos.sty", "/mnt/Data1/Documents/sources/python/remotedArranger/styles/genos.json")
    