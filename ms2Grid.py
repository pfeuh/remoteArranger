#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

# Import des modèles partagés et des constantes pour garantir l'unicité des clés JSON
from models import Header, Bar
from constants import KEY_HEADER, KEY_BARS
from musicalGlyphes import ITEMS, MG_LINE_BREAK, MG_REPEAT1, MG_REPEAT2

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"

TPC_NOTES = {
    -1: "Fbb",  0: "Cbb",  1: "Gbb",  2: "Dbb",  3: "Abb",  4: "Ebb",  5: "Bbb",
    6: "Fb",   7: "Cb",   8: "Gb",   9: "Db",   10: "Ab",  11: "Eb",  12: "Bb",
    13: "F",   14: "C",   15: "G",   16: "D",   17: "A",   18: "E",   19: "B",
    20: "F#",  21: "C#",  22: "G#",  23: "D#",  24: "A#",  25: "E#",  26: "B#",
    27: "F##", 28: "C##", 29: "G##", 30: "D##", 31: "A##", 32: "E##", 33: "B##"
}

def _extract_mscz(mscz_path, extract_to):
    if extract_to.exists(): 
        shutil.rmtree(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(mscz_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

def getGrid(mscz_path):
    """
    Fonction modulaire unique : prend le chemin d'un fichier .mscz, 
    gère le dézippage, le parsing XML, la propagation des durées d'accords,
    et retourne le dictionnaire complet compatible avec gridEditor.
    """
    mscz_path = Path(mscz_path)
    if not mscz_path.exists():
        raise FileNotFoundError(f"Fichier MuseScore introuvable : {mscz_path}")

    _extract_mscz(mscz_path, TEMP_DIR)

    # Recherche dynamique du fichier .mscx extrait dans TEMP_DIR
    mscx_files = list(TEMP_DIR.glob("*.mscx"))
    if not mscx_files:
        raise FileNotFoundError(f"Aucun fichier .mscx trouvé dans {TEMP_DIR}")
    mscx_path = mscx_files[0]

    tree = ET.parse(mscx_path)
    root_elem = tree.getroot()
    
    # Header
    title = next((t.findtext("text") for t in root_elem.iter("Text") if t.findtext("style") == "title"), mscz_path.stem)
    header = Header(
        title=title, 
        subtitle=root_elem.findtext(".//Text[style='subtitle']/text", ""),
        composer=root_elem.findtext(".//Text[style='composer']/text", "Inconnu"),
        lyricist=root_elem.findtext(".//Text[style='poet']/text", ""),
        arranger=root_elem.findtext(".//Text[style='arranger']/text", "")
    )
    
    # Détection de la signature rythmique globale
    global_timesig = "4/4"
    for ts in root_elem.iter("TimeSig"):
        z = ts.findtext("sigN")
        n = ts.findtext("sigD")
        if z and n:
            global_timesig = f"{z}/{n}"
            break

    bars = []
    last_chord = []  # Mémorisation des accords de la mesure précédente pour assurer la durée

    for i, measure in enumerate(root_elem.iter("Measure"), 1):
        chords, system_texts, barlines, markers, sections, jumps = [], [], [], [], [], []
        
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

        # Extraction des accords de la mesure courante
        for h in measure.iter("Harmony"):
            process_harmony(h)

        # Propagation des accords sur les mesures vides (gestion de la durée)
        if chords:
            last_chord = chords
        elif last_chord:
            chords = list(last_chord)

        # Textes (Portée et système)
        for t in measure.iter("StaffText"):
            system_texts.append(t.findtext("text") or "".join(t.itertext()))

        # Markers
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

        # Jumps
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

        # Barlines
        for bl in measure.iter("BarLine"):
            subtype = bl.findtext("subtype")
            if subtype:
                barlines.append(subtype)

        # Time Signature
        timesig = ""
        ts_elem = measure.find(".//TimeSig")
        if ts_elem is not None:
            z = ts_elem.findtext("sigN")
            n = ts_elem.findtext("sigD")
            if z and n:
                timesig = f"{z}/{n}"

        volta = measure.findtext(".//volta", "")
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

    header_data = header.to_dict()
    header_data["style"] = "StandardRock"
    header_data["category"] = "Pop & Rock"
    header_data["bpm"] = 110.0
    header_data["timesig"] = global_timesig

    return {
        KEY_HEADER: header_data, 
        KEY_BARS: [b.to_dict() for b in bars]
    }