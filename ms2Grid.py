#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET
import zipfile

# Import des modèles partagés et des constantes pour garantir l'unicité des clés JSON
from models import Header, Bar
from constants import KEY_HEADER, KEY_BARS

# Assurez-vous que musicalGlyphes est accessible
from musicalGlyphes import ITEMS, MG_LINE_BREAK, MG_REPEAT1, MG_REPEAT2

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "lastFile.json"
TEMP_DIR = BASE_DIR / "temp"
SCORES_DIR = BASE_DIR / "scores"
JSON_FNAME = TEMP_DIR / "score.json"
PDF_DIR = BASE_DIR / "../pdf"

# le score parsé est toujours score.json dans TEMP_DIR
# le pdf est toujours sauvé dans PDF_DIR

CR = '\n'

TPC_NOTES = {
    -1: "Fbb",  0: "Cbb",  1: "Gbb",  2: "Dbb",  3: "Abb",  4: "Ebb",  5: "Bbb",
     6: "Fb",   7: "Cb",   8: "Gb",   9: "Db",   10: "Ab",  11: "Eb",  12: "Bb",
     13: "F",   14: "C",   15: "G",   16: "D",   17: "A",   18: "E",   19: "B",
     20: "F#",  21: "C#",  22: "G#",  23: "D#",  24: "A#",  25: "E#",  26: "B#",
     27: "F##", 28: "C##", 29: "G##", 30: "D##", 31: "A##", 32: "E##", 33: "B##"
}

def get_initial_dir():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_path = Path(data.get("last_file", ""))
                if last_path.parent.exists(): return str(last_path.parent)
        except: pass
    return str(SCORES_DIR) if SCORES_DIR.exists() else str(BASE_DIR)

def save_last_file(file_path):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_file": str(file_path)}, f, indent=4)

def extract_mscz(mscz_path, extract_to):
    if extract_to.exists(): shutil.rmtree(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(mscz_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

def parse_mscx(score_name):
    # Recherche dynamique du fichier .mscx extrait dans TEMP_DIR
    mscx_files = list(TEMP_DIR.glob("*.mscx"))
    if not mscx_files:
        raise FileNotFoundError(f"Aucun fichier .mscx trouvé dans {TEMP_DIR}")
    mscx_path = mscx_files[0]

    tree = ET.parse(mscx_path)
    root_elem = tree.getroot()
    
    # Header
    title = next((t.findtext("text") for t in root_elem.iter("Text") if t.findtext("style") == "title"), score_name)
    header = Header(
        title=title, 
        subtitle=root_elem.findtext(".//Text[style='subtitle']/text", ""),
        composer=root_elem.findtext(".//Text[style='composer']/text", ""),
        lyricist=root_elem.findtext(".//Text[style='poet']/text", ""),
        arranger=root_elem.findtext(".//Text[style='arranger']/text", "")
    )
    
    bars = []
    # Correction : On parcourt directement les mesures à la racine du score
    for i, measure in enumerate(root_elem.iter("Measure"), 1):
        chords, system_texts, barlines, markers, sections, jumps = [], [], [], [], [], []
        
        # Helper pour extraire et ajouter un accord
        def process_harmony(h_elem):
            hi = h_elem.find("harmonyInfo")
            if hi is not None:
                r = hi.findtext("root")
                n = hi.findtext("name")
                b = hi.findtext("bass")
                
                root_note = TPC_NOTES.get(int(r), r) if r and (r.isdigit() or (r.startswith('-') and r[1:].isdigit())) else r
                suffix = n if n and n != "None" else ""
                bass_note = f"/{TPC_NOTES.get(int(b), b)}" if b and (b.isdigit() or (b.startswith('-') and b[1:].isdigit())) else ""
                
                chords.append(f"{root_note}{suffix}{bass_note}")

        # Accords
        for h in measure.iter("Harmony"):
            process_harmony(h)

        # Textes (Portée et système)
        for t in measure.iter("StaffText"):
            system_texts.append(t.findtext("text") or "".join(t.itertext()))

        # Markers (ex: Coda, Segno, Rehearsal marks)
        for m in measure.iter("Marker"):
            subtype = m.findtext("subtype")
            mapped = None
            if subtype:
                subtype_clean = subtype.strip()
                mapped = ITEMS.get(subtype_clean, ITEMS.get(subtype_clean.lower()))
            if not mapped:
                text_elem = m.find("text") or m.find("label")
                if text_elem is not None:
                    txt = text_elem.text or "".join(text_elem.itertext())
                    if txt:
                        txt_clean = txt.strip()
                        mapped = ITEMS.get(txt_clean, ITEMS.get(txt_clean.lower(), txt_clean))
            if mapped:
                markers.append(mapped)
            elif subtype:
                markers.append(subtype.strip())

        for rm in measure.iter("RehearsalMark"):
            text_elem = rm.find("text")
            if text_elem is not None:
                txt = text_elem.text or "".join(text_elem.itertext())
                if txt:
                    txt_clean = txt.strip()
                    mapped = ITEMS.get(txt_clean, ITEMS.get(txt_clean.lower(), txt_clean))
                    markers.append(mapped)
            else:
                txt = rm.text or "".join(rm.itertext())
                if txt.strip():
                    txt_clean = txt.strip()
                    mapped = ITEMS.get(txt_clean, ITEMS.get(txt_clean.lower(), txt_clean))
                    markers.append(mapped)

        # Jumps (ex: Da Capo, Dal Segno)
        for j in measure.iter("Jump"):
            mapped = None
            subtype = j.findtext("subtype")
            if subtype:
                subtype_clean = subtype.strip()
                mapped = ITEMS.get(subtype_clean, ITEMS.get(subtype_clean.lower()))
            
            if not mapped:
                text_elem = j.find("text") or j.find("label")
                if text_elem is not None:
                    txt = text_elem.text or "".join(text_elem.itertext())
                    if txt:
                        txt_clean = txt.strip()
                        mapped = ITEMS.get(txt_clean, ITEMS.get(txt_clean.lower(), txt_clean))
            
            if not mapped:
                jump_to = j.findtext("jumpTo")
                if jump_to:
                    jt_clean = jump_to.strip().lower()
                    if jt_clean == "start":
                        mapped = ITEMS.get("D.C.", ITEMS.get("d.c.", "D.C."))
                    elif jt_clean == "segno":
                        mapped = ITEMS.get("D.S.", ITEMS.get("d.s.", "D.S."))
                    else:
                        mapped = jump_to.strip()
            
            if mapped:
                jumps.append(mapped)
            elif subtype:
                jumps.append(subtype.strip())
            else:
                jump_to = j.findtext("jumpTo")
                if jump_to:
                    jt_clean = jump_to.strip().lower()
                    if jt_clean == "start":
                        jumps.append("D.C.")
                    elif jt_clean == "segno":
                        jumps.append("D.S.")
                    else:
                        jumps.append(jump_to.strip())

        # Barlines
        for bl in measure.iter("BarLine"):
            subtype = bl.findtext("subtype")
            if subtype:
                barlines.append(subtype)

        # Time Signature (Chiffrage de mesure)
        timesig = ""
        ts_elem = measure.find(".//TimeSig")
        if ts_elem is not None:
            z = ts_elem.findtext("sigN")
            n = ts_elem.findtext("sigD")
            if z and n:
                timesig = f"{z}/{n}"

        # Volta
        volta = measure.findtext(".//volta", "")

        # Layout / Reprises / Saut de ligne
        has_lb = measure.find(".//LayoutBreak/subtype") is not None or measure.get("repeatStart") == "1"
        
        bars.append(Bar(
            number=i, 
            chords=chords, 
            markers=markers, 
            sections=sections, 
            jumps=jumps, 
            barlines=barlines, 
            system_texts=system_texts, 
            volta=volta, 
            line_break=has_lb, 
            timesig=timesig
        ))

    # Sauvegarde JSON propre via les clés standardisées
    with open(JSON_FNAME, "w", encoding="utf-8") as f:
        json.dump({
            KEY_HEADER: header.to_dict(), 
            KEY_BARS: [b.to_dict() for b in bars]
        }, f, ensure_ascii=False, indent=4)

def selectMsczFname():
    root = tk.Tk(); root.withdraw()
    path = filedialog.askopenfilename(initialdir=get_initial_dir(), filetypes=[("MuseScore Files", "*.mscz"), ("All Files", "*.*")])
    if path:
        mscz_path = Path(path)
        save_last_file(mscz_path)
        extract_mscz(mscz_path, TEMP_DIR)
        parse_mscx(mscz_path.stem)
        return True
    else:
        return False
        
def getOutputPdfFname():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                fullname = data.get("last_file", "")
                filename_ext = os.path.basename(fullname)
                filename = os.path.splitext(filename_ext)[0]
                pdf_fname = os.path.join(PDF_DIR, filename + ".pdf")
                return pdf_fname
        except:
            pass
    return ""

def getJsonFname():
    return JSON_FNAME

if __name__ == "__main__":
    if selectMsczFname():
        print("json généré:%s"%getJsonFname())
        print("pdf de sortie:%s"%getOutputPdfFname())
    else:
        print("abort")