#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os
import signal
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import rtmidi
import ms2Grid
import pdfGenerator
from toCamelCase import to_camel_case

# Chemin de configuration par défaut
CONFIG_FILE_PATH = ".grid_editor_config.json"
DEFAULT_CATALOG_PATH = os.path.join("styles", "dgx670.json")


class StyleSelectorModal:
    """Petite fenêtre modale pour chercher et choisir un style depuis le catalogue de l'arrangeur."""

    def __init__(self, parent, catalog_path, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("Sélection du Style")
        self.window.geometry("400x450")
        self.window.grab_set()

        self.catalog_path = catalog_path
        self.callback = callback
        self.catalog = self.load_styles()
        self.filtered_data = list(self.catalog)

        # Recherche
        lbl = tk.Label(
            self.window,
            text="Rechercher un style ou une catégorie :",
            font=("Helvetica", 10),
        )
        lbl.pack(anchor="w", padx=10, pady=(10, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_styles)
        self.entry = tk.Entry(
            self.window, textvariable=self.search_var, font=("Helvetica", 12)
        )
        self.entry.pack(fill="x", padx=10, pady=5)
        self.entry.focus()

        # Liste
        frame = tk.Frame(self.window)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.listbox = tk.Listbox(frame, font=("Helvetica", 11), selectmode=tk.SINGLE)
        scrollbar = tk.Scrollbar(
            frame, orient="vertical", command=self.listbox.yview
        )
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.listbox.bind("<Double-1>", lambda event: self.valider())

        # Bouton valider
        btn = tk.Button(
            self.window,
            text="Sélectionner ce Style",
            font=("Helvetica", 11, "bold"),
            bg="#28a745",
            fg="white",
            command=self.valider,
        )
        btn.pack(fill="x", padx=10, pady=10)

        self.update_listbox()

    def load_styles(self):
        if os.path.isfile(self.catalog_path):
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erreur de lecture du catalogue : {e}")
        return []

    def filter_styles(self, *args):
        q = self.search_var.get().lower()
        if not q:
            self.filtered_data = list(self.catalog)
        else:
            self.filtered_data = [
                s
                for s in self.catalog
                if q in s.get("name", "").lower() or q in s.get("category", "").lower()
            ]
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for s in self.filtered_data:
            sig_str = s.get("sig", "4/4")
            tempo_val = s.get("tempo", 120)
            name_val = s.get("name", "Inconnu")
            cat_val = s.get("category", "Général")
            self.listbox.insert(
                tk.END,
                f"{name_val}  —  [{cat_val}]  ({tempo_val} BPM, {sig_str})",
            )
        if self.filtered_data:
            self.listbox.selection_set(0)

    def valider(self):
        sel = self.listbox.curselection()
        if sel:
            style_info = self.filtered_data[sel[0]]
            if self.callback:
                self.callback(style_info)
        self.window.destroy()


class HybridGridEditorApp:

    def __init__(self, root):
        self.root = root
        self.root.geometry("850x730")

        self.current_filepath = None
        self.last_musescore_filepath = None
        self.last_pdf_filepath = None
        self.style_catalog_path = DEFAULT_CATALOG_PATH
        self.midi_port_idx = 0
        self.arranger_process = None
        self.is_modified = False

        self.load_config()

        # Interception de la fermeture de la fenêtre (croix rouge)
        self.root.protocol("WM_DELETE_WINDOW", self.file_close)

        # Création de la barre de menu
        menubar = tk.Menu(root)
        
        # Menu File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", command=self.file_new)
        file_menu.add_command(label="Load...", command=self.load_json)
        file_menu.add_command(label="Load from MuseScore...", command=self.load_musescore)
        file_menu.add_command(label="Save", command=self.file_save)
        file_menu.add_command(label="Save As...", command=self.file_save_as)
        file_menu.add_command(label="Save a Copy...", command=self.file_save_copy)
        file_menu.add_separator()
        file_menu.add_command(label="Generate PDF...", command=self.generate_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.file_close)
        menubar.add_cascade(label="File", menu=file_menu)

        # Menu Style
        style_menu = tk.Menu(menubar, tearoff=0)
        style_menu.add_command(label="Select Arranger...", command=self.select_arranger)
        style_menu.add_command(label="Choose Style...", command=self.open_style_selector)
        menubar.add_cascade(label="Style", menu=style_menu)

        self.root.config(menu=menubar)

        # Cadre En-tête global (Informations + Paramètres Style / Tempo / Signature)
        header_frame = ttk.LabelFrame(root, text="Informations de la Grille & Style")
        header_frame.pack(fill="x", padx=10, pady=5)

        # Ligne 1 : Titre et Compositeur
        ttk.Label(header_frame, text="Titre :").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        self.title_entry = ttk.Entry(header_frame, width=22)
        self.title_entry.insert(0, "Ma Grille")
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)
        self.title_entry.bind("<KeyRelease>", lambda e: self.mark_as_modified())

        ttk.Label(header_frame, text="Compositeur :").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        self.composer_entry = ttk.Entry(header_frame, width=18)
        self.composer_entry.insert(0, "Pierre Faller")
        self.composer_entry.grid(row=0, column=3, padx=5, pady=5)
        self.composer_entry.bind("<KeyRelease>", lambda e: self.mark_as_modified())

        # Ligne 2 : Style, Catégorie, Arrangeur et Paramètres (Tempo / Signature)
        ttk.Label(header_frame, text="Style :").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        
        style_display_frame = ttk.Frame(header_frame)
        style_display_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        self.style_name_var = tk.StringVar(value="StandardRock")
        self.lbl_style_display = ttk.Label(
            style_display_frame,
            textvariable=self.style_name_var,
            font=("Arial", 9, "bold"),
            foreground="#0056b3",
        )
        self.lbl_style_display.pack(side="left", padx=(0, 4))

        self.style_category_var = tk.StringVar(value="")
        self.lbl_category_display = ttk.Label(
            style_display_frame,
            textvariable=self.style_category_var,
            font=("Arial", 9, "italic"),
            foreground="#666",
        )
        self.lbl_category_display.pack(side="left")

        arranger_frame = ttk.Frame(header_frame)
        arranger_frame.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        ttk.Label(arranger_frame, text="Arr. :", font=("Arial", 9)).pack(side="left", padx=2)
        self.arranger_name_var = tk.StringVar(value=os.path.basename(self.style_catalog_path))
        self.lbl_arranger_display = ttk.Label(
            arranger_frame,
            textvariable=self.arranger_name_var,
            font=("Arial", 9, "bold"),
            foreground="#444",
        )
        self.lbl_arranger_display.pack(side="left", padx=2)

        param_frame = ttk.Frame(header_frame)
        param_frame.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        ttk.Label(param_frame, text="Tempo :").pack(side="left", padx=2)
        self.bpm_entry = ttk.Entry(param_frame, width=6)
        self.bpm_entry.insert(0, "110.0")
        self.bpm_entry.pack(side="left", padx=2)
        self.bpm_entry.bind("<KeyRelease>", lambda e: self.mark_as_modified())

        ttk.Label(param_frame, text="Sig :").pack(side="left", padx=(10, 2))
        self.timesig_combo = ttk.Combobox(
            param_frame,
            values=["4/4", "3/4", "6/8", "9/8", "12/8", "2/4", "5/4"],
            width=5,
        )
        self.timesig_combo.set("4/4")
        self.timesig_combo.pack(side="left", padx=2)
        self.timesig_combo.bind("<<ComboboxSelected>>", lambda e: self.mark_as_modified())

        # Ligne 3 : Contrôles MIDI et Bouton unique Play / Stop intelligent
        control_frame = ttk.LabelFrame(root, text="Contrôle MIDI & Lecture (remotedArranger)")
        control_frame.pack(fill="x", padx=10, pady=5)

        midi_sub_frame = ttk.Frame(control_frame)
        midi_sub_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        ttk.Label(midi_sub_frame, text="Port MIDI :").pack(side="left", padx=2)
        
        self.midi_ports_list = self.get_available_midi_ports()
        self.midi_port_combo = ttk.Combobox(
            midi_sub_frame,
            values=self.midi_ports_list,
            width=28,
            state="readonly"
        )
        self.midi_port_combo.pack(side="left", padx=5)
        if self.midi_ports_list:
            if 0 <= self.midi_port_idx < len(self.midi_ports_list):
                self.midi_port_combo.current(self.midi_port_idx)
            else:
                self.midi_port_combo.current(0)
        self.midi_port_combo.bind("<<ComboboxSelected>>", self.on_midi_port_changed)

        btn_refresh_midi = ttk.Button(midi_sub_frame, text="🔄", width=3, command=self.refresh_midi_ports)
        btn_refresh_midi.pack(side="left", padx=2)

        # Bouton unique Play / Stop
        self.btn_toggle_play = tk.Button(
            control_frame,
            text="▶ Play",
            font=("Helvetica", 10, "bold"),
            padx=15,
            command=self.toggle_playback
        )
        self.btn_toggle_play.pack(side="right", padx=5, pady=5)
        
        self.default_btn_bg = self.btn_toggle_play.cget("bg")

        # Création des onglets
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # --- ONGLET 1 : TEXTE BRUT ---
        self.tab_text = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_text, text=" 📝 Mode Texte (Copier/Coller) ")

        text_container = ttk.Frame(self.tab_text)
        text_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.text_editor = tk.Text(text_container, wrap="word", font=("Courier", 11))
        text_scroll = ttk.Scrollbar(
            text_container, orient="vertical", command=self.text_editor.yview
        )
        self.text_editor.configure(yscrollcommand=text_scroll.set)

        self.text_editor.pack(side="left", fill="both", expand=True)
        text_scroll.pack(side="right", fill="y")

        self.text_editor.bind("<<Modified>>", self.on_text_modified_event)

        default_text = (
            "C C C G7\n"
            "Am F C G\n"
        )
        self.text_editor.insert("1.0", default_text)
        self.text_editor.edit_modified(False)

        # --- ONGLET 2 : GRILLE VISUELLE ---
        self.tab_grid = ttk.Frame(self.notebook)
        self.notebook.add(
            self.tab_grid, text=" 🎹 Grille Visuelle (4 mesures/ligne) "
        )

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        container = ttk.Frame(self.tab_grid)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        self.canvas = tk.Canvas(container, borderwidth=0, background="#f0f0f0")
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )

        self.canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-4>", self._on_mouse_wheel)
        self.canvas.bind_all("<Button-5>", self._on_mouse_wheel)

        self.bar_entries = []

        default_cat = self.find_category_for_style(self.style_name_var.get())
        if default_cat:
            self.style_category_var.set(f"[{default_cat}]")
        else:
            self.style_category_var.set("[Pop & Rock]")

        if self.current_filepath and os.path.isfile(self.current_filepath):
            self._load_from_path(self.current_filepath, show_popup=False)
        else:
            self.update_title()
            self.update_grid_from_text()
            self.set_modified(False)

        self.check_arranger_status()

    def find_category_for_style(self, style_name):
        if os.path.isfile(self.style_catalog_path):
            try:
                with open(self.style_catalog_path, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
                    for s in catalog:
                        if s.get("name", "").lower() == style_name.lower():
                            return s.get("category", "")
            except Exception:
                pass
        return ""

    def get_available_midi_ports(self):
        try:
            midi_out = rtmidi.MidiOut()
            ports = midi_out.get_ports()
            del midi_out
            if ports:
                return [f"[{i}] {p}" for i, p in enumerate(ports)]
        except Exception:
            pass
        return ["Aucun port MIDI disponible"]

    def refresh_midi_ports(self):
        self.midi_ports_list = self.get_available_midi_ports()
        self.midi_port_combo['values'] = self.midi_ports_list
        if self.midi_ports_list and "Aucun" not in self.midi_ports_list[0]:
            self.midi_port_combo.current(0)
            self.midi_port_idx = 0

    def on_midi_port_changed(self, event):
        sel = self.midi_port_combo.current()
        if sel >= 0:
            self.midi_port_idx = sel
            self.save_config()

    def toggle_playback(self):
        if self.arranger_process and self.arranger_process.poll() is None:
            self.stop_arranger_process()
        else:
            self.start_arranger_process()

    def start_arranger_process(self):
        self.stop_arranger_process()

        if self.current_filepath:
            if self.is_modified:
                self.file_save()
        else:
            saved = self.file_save_as()
            if not saved:
                return

        port_idx = self.midi_port_combo.current()
        if port_idx < 0:
            messagebox.showwarning("Avertissement", "Veuillez sélectionner un port MIDI valide.")
            return

        script_path = "remotedArranger.py"
        if not os.path.isfile(script_path):
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "remotedArranger.py")

        if not os.path.isfile(script_path):
            messagebox.showerror("Erreur", "Le fichier 'remotedArranger.py' est introuvable.")
            return

        try:
            cmd = [sys.executable, script_path, str(port_idx), self.current_filepath]
            self.arranger_process = subprocess.Popen(cmd)
            self.btn_toggle_play.config(text="⏹ En cours...", bg="#28a745", fg="white")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lancer l'arrangeur :\n{e}")

    def stop_arranger_process(self):
        if self.arranger_process:
            try:
                if self.arranger_process.poll() is None:
                    self.arranger_process.send_signal(signal.SIGINT)
                    self.arranger_process.wait(timeout=1.5)
            except Exception:
                try:
                    self.arranger_process.terminate()
                except Exception:
                    pass
            self.arranger_process = None

        self.btn_toggle_play.config(text="▶ Play", bg=self.default_btn_bg, fg="black")

    def check_arranger_status(self):
        if self.arranger_process is not None:
            if self.arranger_process.poll() is not None:
                self.arranger_process = None
                self.btn_toggle_play.config(text="▶ Play", bg=self.default_btn_bg, fg="black")
        
        self.root.after(500, self.check_arranger_status)

    def mark_as_modified(self):
        if not self.is_modified:
            self.set_modified(True)

    def set_modified(self, status):
        self.is_modified = status
        self.update_title()

    def on_text_modified_event(self, event=None):
        if self.text_editor.edit_modified():
            self.mark_as_modified()
            self.text_editor.edit_modified(False)

    def _on_mouse_wheel(self, event):
        try:
            if self.notebook.select() == str(self.tab_grid):
                if event.num == 4:
                    self.canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    self.canvas.yview_scroll(1, "units")
                else:
                    self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def update_title(self):
        if self.current_filepath:
            filename = os.path.basename(self.current_filepath)
            base_title = f"Remoted Arranger - {filename}"
        else:
            base_title = "Remoted Arranger - Sans titre"

        if self.is_modified:
            self.root.title(base_title + " *")
        else:
            self.root.title(base_title)

    def get_default_filename(self):
        title_val = self.title_entry.get().strip()
        if not title_val:
            return "grille.json"
        safe_title = "".join(c if c.isalnum() or c in (' ', '_', '-') else "_" for c in title_val)
        safe_title = safe_title.strip().replace(" ", "_").lower()
        return f"{safe_title}.json" if safe_title else "grille.json"

    def get_default_pdf_filename(self):
        title_val = self.title_entry.get().strip()
        if self.current_filepath:
            base_name = os.path.splitext(os.path.basename(self.current_filepath))[0]
            return to_camel_case(base_name) + ".pdf"
        elif title_val:
            return to_camel_case(title_val) + ".pdf"
        return "score.pdf"

    def check_save_before_action(self):
        if not self.is_modified:
            return True

        filename = os.path.basename(self.current_filepath) if self.current_filepath else "Sans titre"
        response = messagebox.askyesnocancel(
            "Modifications non enregistrées",
            f"Le fichier '{filename}' a été modifié.\nVoulez-vous enregistrer les modifications ?"
        )
        
        if response is True:
            return self.file_save()
        elif response is False:
            return True
        else:
            return False

    def load_config(self):
        if os.path.isfile(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    path = config.get("last_filepath")
                    if path and os.path.isfile(path):
                        self.current_filepath = path
                    
                    ms_path = config.get("last_musescore_filepath")
                    if ms_path:
                        self.last_musescore_filepath = ms_path

                    pdf_path = config.get("last_pdf_filepath")
                    if pdf_path:
                        self.last_pdf_filepath = pdf_path

                    catalog = config.get("style_catalog_path")
                    if catalog and os.path.isfile(catalog):
                        self.style_catalog_path = catalog
                        if hasattr(self, 'arranger_name_var'):
                            self.arranger_name_var.set(os.path.basename(catalog))

                    p_idx = config.get("midi_port_idx")
                    if p_idx is not None:
                        self.midi_port_idx = int(p_idx)
            except Exception:
                pass

    def save_config(self):
        try:
            config = {
                "last_filepath": self.current_filepath,
                "last_musescore_filepath": self.last_musescore_filepath,
                "last_pdf_filepath": self.last_pdf_filepath,
                "style_catalog_path": self.style_catalog_path,
                "midi_port_idx": self.midi_port_idx
            }
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def select_arranger(self):
        initial_dir = os.path.dirname(self.style_catalog_path) if os.path.exists(self.style_catalog_path) else "styles"
        if not os.path.exists(initial_dir):
            initial_dir = "."

        filepath = filedialog.askopenfilename(
            title="Sélectionner le catalogue de l'arrangeur",
            initialdir=initial_dir,
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self.style_catalog_path = filepath
            self.arranger_name_var.set(os.path.basename(filepath))
            self.save_config()
            cat = self.find_category_for_style(self.style_name_var.get())
            self.style_category_var.set(f"[{cat}]" if cat else "")

    def file_new(self):
        if not self.check_save_before_action():
            return

        self.stop_arranger_process()
        self.current_filepath = None
        self.save_config()
        
        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, "Ma Grille")
        self.composer_entry.delete(0, tk.END)
        self.composer_entry.insert(0, "Pierre Faller")
        self.style_name_var.set("StandardRock")
        
        cat = self.find_category_for_style("StandardRock")
        self.style_category_var.set(f"[{cat}]" if cat else "[Pop & Rock]")

        self.bpm_entry.delete(0, tk.END)
        self.bpm_entry.insert(0, "110.0")
        self.timesig_combo.set("4/4")
        
        self.text_editor.unbind("<<Modified>>")
        self.text_editor.delete("1.0", tk.END)
        default_text = "C C C G7\nAm F C G\n"
        self.text_editor.insert("1.0", default_text)
        self.text_editor.edit_modified(False)
        self.text_editor.bind("<<Modified>>", self.on_text_modified_event)

        self.update_grid_from_text()
        self.set_modified(False)

    def file_save(self):
        if self.current_filepath:
            return self._save_to_path(self.current_filepath)
        else:
            return self.file_save_as()

    def file_save_as(self):
        if self.current_filepath:
            initial_dir = os.path.dirname(self.current_filepath)
            initial_file = os.path.basename(self.current_filepath)
        else:
            initial_dir = os.getcwd()
            initial_file = self.get_default_filename()

        filepath = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if filepath:
            self.current_filepath = filepath
            self.save_config()
            return self._save_to_path(filepath)
        return False

    def file_save_copy(self):
        if self.current_filepath:
            initial_dir = os.path.dirname(self.current_filepath)
            initial_file = os.path.basename(self.current_filepath)
        else:
            initial_dir = os.getcwd()
            initial_file = self.get_default_filename()

        filepath = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if filepath:
            self._save_to_path(filepath)

    def file_close(self):
        if self.check_save_before_action():
            self.stop_arranger_process()
            self.root.destroy()

    def _save_to_path(self, filepath):
        try:
            bpm_val = float(self.bpm_entry.get().strip())
        except ValueError:
            bpm_val = 120.0

        cat_raw = self.style_category_var.get().strip()
        cat_clean = cat_raw.strip("[]")

        data = {
            "header": {
                "title": self.title_entry.get().strip(),
                "composer": self.composer_entry.get().strip(),
                "style": self.style_name_var.get().strip(),
                "category": cat_clean,
                "bpm": bpm_val,
                "timesig": self.timesig_combo.get().strip(),
            },
            "bars": self.get_bars_data(),
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.current_filepath = filepath
            self.save_config()
            self.set_modified(False)
            return True
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement :\n{e}")
            return False

    def load_musescore(self):
        """Ouvre un fichier MuseScore (.mscz) en déléguant tout le parsing au module ms2Grid."""
        if not self.check_save_before_action():
            return

        initial_dir = "scores" if os.path.exists("scores") else "."
        if self.last_musescore_filepath:
            parent_dir = os.path.dirname(self.last_musescore_filepath)
            if os.path.exists(parent_dir):
                initial_dir = parent_dir

        filepath = filedialog.askopenfilename(
            title="Sélectionner un fichier MuseScore",
            initialdir=initial_dir,
            filetypes=[("Fichiers MuseScore", "*.mscz"), ("Tous les fichiers", "*.*")]
        )
        if not filepath:
            return

        self.last_musescore_filepath = filepath
        self.save_config()

        try:
            grid_data = ms2Grid.getGrid(filepath)

            header = grid_data.get("header", {})
            title = header.get("title", Path(filepath).stem)
            composer = header.get("composer", "Inconnu")
            style = header.get("style", "StandardRock")
            category = header.get("category", "Pop & Rock")
            bpm = header.get("bpm", 110.0)
            timesig = header.get("timesig", "4/4")

            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, title)
            self.composer_entry.delete(0, tk.END)
            self.composer_entry.insert(0, composer)
            
            self.style_name_var.set(style)
            self.style_category_var.set(f"[{category}]" if category else "[Pop & Rock]")
            
            self.bpm_entry.delete(0, tk.END)
            self.bpm_entry.insert(0, str(bpm))
            self.timesig_combo.set(timesig)

            bars = grid_data.get("bars", [])
            lines_chords = []
            current_line_bars = []

            for bar in bars:
                chords_list = bar.get("chords", [])
                current_line_bars.append(" ".join(chords_list))
                if len(current_line_bars) == 4:
                    lines_chords.append("    ".join(current_line_bars))
                    current_line_bars = []

            if current_line_bars:
                lines_chords.append("    ".join(current_line_bars))

            self.text_editor.unbind("<<Modified>>")
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", "\n".join(lines_chords) + "\n")
            self.text_editor.edit_modified(False)
            self.text_editor.bind("<<Modified>>", self.on_text_modified_event)

            self.update_grid_from_text()
            self.set_modified(True)

            messagebox.showinfo("Succès", f"Partition '{title}' importée avec succès depuis MuseScore !")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'importation MuseScore :\n{e}")

    def generate_pdf(self):
        """Génère le PDF de la grille en cours via le module pdfGenerator."""
        if not self.current_filepath or self.is_modified:
            if not self.file_save():
                return

        initial_dir = "pdf" if os.path.exists("pdf") else "."
        if self.last_pdf_filepath:
            parent_dir = os.path.dirname(self.last_pdf_filepath)
            if os.path.exists(parent_dir):
                initial_dir = parent_dir

        initial_file = self.get_default_pdf_filename()
        if self.last_pdf_filepath:
            initial_file = os.path.basename(self.last_pdf_filepath)

        pdf_path = filedialog.asksaveasfilename(
            title="Générer le PDF de la grille",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".pdf",
            filetypes=[("Fichiers PDF", "*.pdf"), ("Tous les fichiers", "*.*")]
        )

        if not pdf_path:
            return

        self.last_pdf_filepath = pdf_path
        self.save_config()

        try:
            pdfGenerator.jsonToPdf(self.current_filepath, pdf_path)
            messagebox.showinfo("Succès", f"PDF généré avec succès :\n{pdf_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la génération du PDF :\n{e}")

    def open_style_selector(self):
        StyleSelectorModal(self.root, self.style_catalog_path, self.on_style_selected)

    def on_style_selected(self, style_info):
        self.style_name_var.set(style_info.get("name", "StandardRock"))
        
        cat = style_info.get("category", "Pop & Rock")
        self.style_category_var.set(f"[{cat}]")

        if "tempo" in style_info:
            self.bpm_entry.delete(0, tk.END)
            self.bpm_entry.insert(0, str(style_info["tempo"]))

        style_sig = style_info.get("sig", "4/4")
        self.timesig_combo.set(style_sig)
        
        self.mark_as_modified()

    def add_grid_row(self):
        current_bars_count = len(self.bar_entries)
        row_frame = ttk.Frame(self.scrollable_frame)
        row_frame.pack(fill="x", pady=4, anchor="w")

        for col in range(4):
            bar_num = current_bars_count + col + 1
            cell_frame = ttk.Frame(row_frame, borderwidth=1, relief="solid")
            cell_frame.pack(side="left", padx=4, pady=2)

            lbl = ttk.Label(
                cell_frame,
                text=f"{bar_num}.",
                width=4,
                anchor="center",
                font=("Arial", 9, "bold"),
            )
            lbl.pack(side="left")

            entry = ttk.Entry(cell_frame, width=14, font=("Courier", 10))
            entry.pack(side="left", padx=2, pady=2)
            entry.bind("<KeyRelease>", lambda e: self.mark_as_modified())
            self.bar_entries.append(entry)

    def clear_grid_widgets(self):
        for entry in self.bar_entries:
            cell_frame = entry.master
            row_frame = cell_frame.master
            cell_frame.destroy()
            if row_frame.winfo_children() == []:
                row_frame.destroy()
        self.bar_entries.clear()

    def update_grid_from_text(self):
        text_content = self.text_editor.get("1.0", tk.END).strip()
        lines = text_content.split("\n") if text_content else []

        all_bars_chords = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split("    ") if p.strip()]
            if len(parts) == 1 and " " in parts[0]:
                parts = [p.strip() for p in parts[0].split() if p.strip()]
            for p in parts:
                all_bars_chords.append(p)

        self.clear_grid_widgets()
        total_bars = max(len(all_bars_chords), 4)
        while len(self.bar_entries) < total_bars:
            self.add_grid_row()

        for idx, chords_str in enumerate(all_bars_chords):
            if idx < len(self.bar_entries):
                self.bar_entries[idx].delete(0, tk.END)
                self.bar_entries[idx].insert(0, chords_str)

    def on_tab_changed(self, event):
        selected_tab = self.notebook.select()
        if selected_tab == str(self.tab_grid):
            self.update_grid_from_text()

    def get_bars_data(self):
        bars = []
        for idx, entry in enumerate(self.bar_entries, 1):
            val = entry.get().strip()
            chords = [c.strip() for c in val.split() if c.strip()]
            bars.append({
                "number": idx,
                "chords": chords
            })
        return bars

    def _load_from_path(self, filepath, show_popup=True):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            header = data.get("header", {})
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, header.get("title", "Ma Grille"))
            
            self.composer_entry.delete(0, tk.END)
            self.composer_entry.insert(0, header.get("composer", "Pierre Faller"))
            
            style = header.get("style", "StandardRock")
            self.style_name_var.set(style)
            
            cat = header.get("category", "")
            if not cat:
                cat = self.find_category_for_style(style)
            self.style_category_var.set(f"[{cat}]" if cat else "[Pop & Rock]")
            
            self.bpm_entry.delete(0, tk.END)
            self.bpm_entry.insert(0, str(header.get("bpm", 110.0)))
            
            timesig = header.get("timesig", "4/4")
            self.timesig_combo.set(timesig)

            bars = data.get("bars", [])
            lines = []
            current_line = []

            for bar in bars:
                chords = bar.get("chords", [])
                chord_str = " ".join(chords)
                current_line.append(chord_str)
                if len(current_line) == 4:
                    lines.append("    ".join(current_line))
                    current_line = []
            
            if current_line:
                lines.append("    ".join(current_line))

            self.text_editor.unbind("<<Modified>>")
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", "\n".join(lines) + "\n")
            self.text_editor.edit_modified(False)
            self.text_editor.bind("<<Modified>>", self.on_text_modified_event)

            self.update_grid_from_text()
            self.current_filepath = filepath
            self.save_config()
            self.set_modified(False)

            if show_popup:
                messagebox.showinfo("Succès", f"Fichier chargé avec succès :\n{filepath}")
        except Exception as e:
            if show_popup:
                messagebox.showerror("Erreur", f"Erreur lors du chargement du fichier :\n{e}")

    def load_json(self):
        if not self.check_save_before_action():
            return
        initial_dir = os.path.dirname(self.current_filepath) if self.current_filepath else "."
        filepath = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("Fichiers JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        if filepath:
            self._load_from_path(filepath, show_popup=True)


if __name__ == "__main__":
    root = tk.Tk()
    app = HybridGridEditorApp(root)
    root.mainloop()