#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class TextGridEditorApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Éditeur de Grille Texte - Arranger")
    self.root.geometry("650x550")

    # Cadre En-tête
    header_frame = ttk.LabelFrame(root, text="Informations")
    header_frame.pack(fill="x", padx=10, pady=5)

    ttk.Label(header_frame, text="Titre :").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )
    self.title_entry = ttk.Entry(header_frame, width=25)
    self.title_entry.insert(0, "Ma Grille")
    self.title_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(header_frame, text="Compositeur :").grid(
        row=0, column=2, sticky="w", padx=5, pady=5
    )
    self.composer_entry = ttk.Entry(header_frame, width=20)
    self.composer_entry.insert(0, "Pierre Faller")
    self.composer_entry.grid(row=0, column=3, padx=5, pady=5)

    # Instructions / Aide
    info_text = (
        "Instructions :\n"
        "• 1 ligne = 1 mesure\n"
        "• Séparez les accords par des espaces (ex: C C C G7)\n"
        "• Ligne vide = mesure vide (prolongation)"
    )
    ttk.Label(root, text=info_text, foreground="gray").pack(
        anchor="w", padx=12, pady=2
    )

    # Zone de texte principale
    text_frame = ttk.Frame(root)
    text_frame.pack(fill="both", expand=True, padx=10, pady=5)

    self.text_editor = tk.Text(text_frame, wrap="word", font=("Courier", 11))
    text_scroll = ttk.Scrollbar(
        text_frame, orient="vertical", command=self.text_editor.yview
    )
    self.text_editor.configure(yscrollcommand=text_scroll.set)

    self.text_editor.pack(side="left", fill="both", expand=True)
    text_scroll.pack(side="right", fill="y")

    # Exemple par défaut dans l'éditeur
    default_text = (
        "C C C G7\n"
        "Am F C G\n"
        "\n"
        "C5+ C5+ C5+ C5+\n"
        "C6\n"
    )
    self.text_editor.insert("1.0", default_text)

    # Boutons d'actions
    actions_frame = ttk.Frame(root)
    actions_frame.pack(fill="x", padx=10, pady=10)

    ttk.Button(
        actions_frame, text="Enregistrer JSON", command=self.save_json
    ).pack(side="left", padx=5)
    ttk.Button(
        actions_frame, text="Charger JSON", command=self.load_json
    ).pack(side="left", padx=5)
    ttk.Button(
        actions_frame, text="Effacer tout", command=self.clear_text
    ).pack(side="right", padx=5)

  def clear_text(self):
    if messagebox.askyesno(
        "Confirmation", "Voulez-vous effacer tout le texte ?"
    ):
      self.text_editor.delete("1.0", tk.END)

  def save_json(self):
    filepath = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
    )
    if not filepath:
      return

    # Analyse ligne par ligne du texte brut
    raw_content = self.text_editor.get("1.0", tk.END)
    lines = raw_content.splitlines()

    bars_data = []
    for i, line in enumerate(lines):
      line_clean = line.strip()
      # Ignore les commentaires éventuels ou lignes vides pures
      chords_list = line_clean.split() if line_clean else []

      bars_data.append(
          {"number": len(bars_data) + 1, "timesig": "4/4", "chords": chords_list}
      )

    data = {
        "header": {
            "title": self.title_entry.get().strip(),
            "composer": self.composer_entry.get().strip(),
        },
        "bars": bars_data,
    }

    try:
      with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
      messagebox.showinfo("Succès", f"Grille enregistrée avec succès :\n{filepath}")
    except Exception as e:
      messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement :\n{e}")

  def load_json(self):
    filepath = filedialog.askopenfilename(
        filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
    )
    if not filepath:
      return

    try:
      with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

      if "header" in data:
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(
            0, data["header"].get("title", "Partition sans titre")
        )
        self.composer_entry.delete(0, tk.END)
        self.composer_entry.insert(
            0, data["header"].get("composer", "Pierre Faller")
        )

      if "bars" in data:
        self.text_editor.delete("1.0", tk.END)
        lines_to_insert = []
        for bar in data["bars"]:
          chords = bar.get("chords", [])
          lines_to_insert.append(" ".join(chords))

        self.text_editor.insert("1.0", "\n".join(lines_to_insert))
        messagebox.showinfo("Succès", "Grille chargée dans l'éditeur !")
    except Exception as e:
      messagebox.showerror("Erreur", f"Erreur lors du chargement :\n{e}")


if __name__ == "__main__":
  root = tk.Tk()
  app = TextGridEditorApp(root)
  root.mainloop()