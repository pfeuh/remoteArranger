#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import tkinter as tk
from tkinter import messagebox

JSON_FILE = "dgx_styles_catalog.json"


class TempoApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Assistant Tempo DGX-670")
    self.root.geometry("450x280")
    self.root.resizable(False, False)

    if not os.path.isfile(JSON_FILE):
      messagebox.showerror(
          "Erreur", f"Le fichier '{JSON_FILE}' est introuvable."
      )
      self.root.destroy()
      return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
      self.catalog = json.load(f)

    self.index = 0

    # Widgets de l'interface
    self.lbl_progress = tk.Label(
        root, font=("Helvetica", 10), fg="gray", text=""
    )
    self.lbl_progress.pack(pady=5)

    self.lbl_category = tk.Label(
        root, font=("Helvetica", 12, "bold"), fg="#0056b3", text=""
    )
    self.lbl_category.pack(pady=5)

    self.lbl_name_title = tk.Label(root, font=("Helvetica", 10), text="STYLE :")
    self.lbl_name_title.pack()

    self.lbl_name = tk.Label(root, font=("Helvetica", 18, "bold"), text="")
    self.lbl_name.pack(pady=5)

    # Cadre pour la saisie du tempo
    frame_input = tk.Frame(root)
    frame_input.pack(pady=10)

    tk.Label(
        frame_input, font=("Helvetica", 11), text="Tempo :"
    ).pack(side=tk.LEFT, padx=5)

    self.entry_tempo = tk.Entry(
        frame_input, font=("Helvetica", 14), width=8, justify="center"
    )
    self.entry_tempo.pack(side=tk.LEFT, padx=5)
    # Lier la touche Entrée pour valider directement
    self.entry_tempo.bind("<Return>", lambda event: self.valider_et_suivant())

    self.btn_valider = tk.Button(
        root,
        text="Valider & Suivant",
        font=("Helvetica", 11, "bold"),
        bg="#28a745",
        fg="white",
        command=self.valider_et_suivant,
    )
    self.btn_valider.pack(pady=10, ipadx=10, ipady=3)

    # Afficher le premier style
    self.afficher_style()
    self.entry_tempo.focus()

  def afficher_style(self):
    if self.index < len(self.catalog):
      item = self.catalog[self.index]
      self.lbl_progress.config(
          text=f"Style {self.index + 1} sur {len(self.catalog)}"
      )
      self.lbl_category.config(text=f"Catégorie : {item.get('category', '')}")
      self.lbl_name.config(text=item.get("name", ""))

      self.entry_tempo.delete(0, tk.END)
      self.entry_tempo.insert(0, str(item.get("tempo", 120)))
      self.entry_tempo.select_range(0, tk.END)
    else:
      self.sauvegarder_json()
      messagebox.showinfo(
          "Terminé !",
          "Tous les styles ont été parcourus et enregistrés avec succès.",
      )
      self.root.destroy()

  def valider_et_suivant(self):
    val = self.entry_tempo.get().strip()
    try:
      tempo = float(val)
      self.catalog[self.index]["tempo"] = tempo
    except ValueError:
      messagebox.showwarning(
          "Attention", "Veuillez entrer un nombre valide pour le tempo."
      )
      return

    # Sauvegarde automatique à chaque étape
    self.sauvegarder_json()

    self.index += 1
    self.afficher_style()

  def sauvegarder_json(self):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
      f.write("[\n")
      for idx, item in enumerate(self.catalog):
        comma = "," if idx < len(self.catalog) - 1 else ""
        f.write(f"{json.dumps(item, ensure_ascii=False)}{comma}\n")
      f.write("]\n")


if __name__ == "__main__":
  root = tk.Tk()
  app = TempoApp(root)
  root.mainloop()