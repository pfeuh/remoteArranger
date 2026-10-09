#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import tkinter as tk
from tkinter import ttk

# Chemin vers ton fichier de styles dans le projet
JSON_PATH = os.path.join("styles", "dgx670.json")


class StyleSelectorWindow:

  def __init__(self, parent, callback_on_select):
    self.parent = parent
    self.callback = callback_on_select  # Fonction appelée quand on valide un style

    self.window = tk.Toplevel(parent)
    self.window.title("Sélection du Style DGX-670")
    self.window.geometry("400x450")
    self.window.grab_set()  # Modal (bloque la fenêtre principale tant qu'elle est ouverte)

    # Chargement des styles
    self.styles_data = self.load_styles()
    self.filtered_data = list(self.styles_data)

    # --- ÉLÉMENTS DE L'INTERFACE ---

    # 1. Barre de recherche textuelle
    lbl_search = tk.Label(
        self.window, text="Filtrer par nom ou catégorie :", font=("Helvetica", 10)
    )
    lbl_search.pack(anchor="w", padx=10, pady=(10, 0))

    self.search_var = tk.StringVar()
    self.search_var.trace("w", self.filter_styles)
    self.entry_search = tk.Entry(
        self.window, textvariable=self.search_var, font=("Helvetica", 12)
    )
    self.entry_search.pack(fill="x", padx=10, pady=5)
    self.entry_search.focus()

    # 2. Liste visuelle des styles (Listbox avec barre de défilement)
    frame_list = tk.Frame(self.window)
    frame_list.pack(fill="both", expand=True, padx=10, pady=5)

    self.listbox = tk.Listbox(
        frame_list, font=("Helvetica", 11), selectmode=tk.SINGLE
    )
    scrollbar = tk.Scrollbar(
        frame_list, orient="vertical", command=self.listbox.yview
    )
    self.listbox.config(yscrollcommand=scrollbar.set)

    self.listbox.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Double clic pour valider directement
    self.listbox.bind("<Double-1>", lambda event: self.valider_selection())

    # 3. Bouton de validation
    btn_valider = tk.Button(
        self.window,
        text="Sélectionner ce Style",
        font=("Helvetica", 11, "bold"),
        bg="#28a745",
        fg="white",
        command=self.valider_selection,
    )
    btn_valider.pack(fill="x", padx=10, pady=10)

    # Remplissage initial de la liste
    self.update_listbox()

  def load_styles(self):
    if not os.path.isfile(JSON_PATH):
      print(f"Attention : Fichier introuvable à l'emplacement {JSON_PATH}")
      return []
    try:
      with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception as e:
      print(f"Erreur lors de la lecture du JSON : {e}")
      return []

  def filter_styles(self, *args):
    query = self.search_var.get().lower()
    if not query:
      self.filtered_data = list(self.styles_data)
    else:
      self.filtered_data = [
          s
          for s in self.styles_data
          if query in s["name"].lower() or query in s["category"].lower()
      ]
    self.update_listbox()

  def update_listbox(self):
    self.listbox.delete(0, tk.END)
    for style in self.filtered_data:
      # Affichage formaté : "Nom du style  [Catégorie] (Tempo BPM)"
      line = f"{style['name']}  —  [{style['category']}]  ({style['tempo']} BPM)"
      self.listbox.insert(tk.END, line)

    # Sélectionner le premier élément par défaut s'il y en a
    if self.filtered_data:
      self.listbox.selection_set(0)

  def valider_selection(self):
    selection = self.listbox.curselection()
    if not selection:
      return

    index = selection[0]
    selected_style = self.filtered_data[index]

    # On transmet le dictionnaire complet (name, category, tempo) au script principal
    if self.callback:
      self.callback(selected_style)

    self.window.destroy()