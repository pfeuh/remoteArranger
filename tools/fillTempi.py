#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os

JSON_FILE = "dgx_styles_catalog.json"


def main():
  if not os.path.isfile(JSON_FILE):
    print(f"Erreur : Le fichier '{JSON_FILE}' est introuvable.")
    return

  with open(JSON_FILE, "r", encoding="utf-8") as f:
    catalog = json.load(f)

  print(f"--- ASSISTANT DE SAISIE DES TEMPI ({len(catalog)} styles) ---")
  print(
      "Instructions : Tape le tempo et appuie sur Entrée."
      "\n- Appuie juste sur Entrée pour garder le tempo actuel (120 par défaut)."
      "\n- Tape 'q' pour quitter et sauvegarder.\n"
  )

  for i, entry in enumerate(catalog):
    # Si le tempo a déjà été modifié (autre que 120 ou déjà saisi), on peut l'afficher pour info
    current_tempo = entry.get("tempo", 120)
    category = entry.get("category", "")
    name = entry.get("name", "")

    # Affichage clair et visible sur le terminal du PC
    print(
        f"\n[{i + 1}/{len(catalog)}] Catégorie : ** {category} **"
        f" \n----------------------------------------"
    )
    print(
        f"👉 STYLE SUR LE DGX : \033[1m{name}\033[0m (Tempo actuel :"
        f" {current_tempo})"
    )

    user_input = input("Entrer le tempo (ou Entrée / q) : ").strip()

    if user_input.lower() == "q":
      print("\nSauvegarde de la progression en cours...")
      break
    elif user_input == "":
      # On garde la valeur actuelle
      continue
    else:
      try:
        new_tempo = float(user_input)
        entry["tempo"] = new_tempo
      except ValueError:
        print(
            "⚠️ Entrée invalide, le tempo n'a pas été modifié pour ce style."
        )

    # Sauvegarde automatique à chaque étape pour ne rien perdre en cas de coupure
    with open(JSON_FILE, "w", encoding="utf-8") as f:
      f.write("[\n")
      for idx, item in enumerate(catalog):
        comma = "," if idx < len(catalog) - 1 else ""
        f.write(f"{json.dumps(item, ensure_ascii=False)}{comma}\n")
      f.write("]\n")

  print(
      "\n✅ Session terminée ! Le fichier JSON a été mis à jour proprement avec"
      " le format compact."
  )


if __name__ == "__main__":
  main()