#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import json
import re

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from toCamelCase import to_camel_case
from musicalGlyphes import *
from constants import KEY_HEADER, KEY_BARS

MAX_COLS = 10
MARGIN = 15.0

# Constantes typographiques et musicales
CHAR_SHARP = "\ue10c"
CHAR_FLAT = "\ue10d"
CHORD_FONT_SIZE = 14

GLYPH_DIM = "\ue18e"
GLYPH_M7B5_MODIFIER = "\ue18f"
GLYPH_MAJ7 = "\ue18a"

# Tables de correspondance de couleurs (respect strict de la casse)
COLOR_GLYPH_MAP = {
    "dim": GLYPH_DIM,
    "m7b5": GLYPH_M7B5_MODIFIER,
    "maj7": GLYPH_MAJ7,
    "M7": GLYPH_MAJ7,
    "7M": GLYPH_MAJ7,
    "7maj": GLYPH_MAJ7
}

# Hauteurs par défaut en pourcentage de la page / de la zone disponible
DEFAULT_HEADER_HIGHT_PERCENT = 10 
DEFAULT_ROW_HIGHT_PERCENT = 6 

# Chemins relatifs basés sur l'emplacement de ce script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_FNT   = os.path.join(SCRIPT_DIR, "font/Bravura.ttf")
SECTION_FNT = os.path.join(SCRIPT_DIR, "font/gjm_realbook-webfont.ttf")
TEXT_FNT    = os.path.join(SCRIPT_DIR, "font/MuseJazzText.ttf")

# Nom des polices dans reportlab
default_fnt = "Helvetica" 
music_fnt   = os.path.splitext(os.path.basename(MUSIC_FNT))[0]
section_fnt = os.path.splitext(os.path.basename(SECTION_FNT))[0]
text_fnt    = os.path.splitext(os.path.basename(TEXT_FNT))[0]

# Mapping direct des noms de polices textuels vers les variables réelles
FONT_MAP = {
    "default_fnt": default_fnt,
    "music_fnt": music_fnt,
    "section_fnt": section_fnt,
    "text_fnt": text_fnt,
    "GjmRealbook": section_fnt,
    "Bravura": music_fnt,
    "MuseJazzText": text_fnt
}

class Measure:
    def __init__(self, data):
        self.number = data.get("number", 0)
        self.chords = data.get("chords", [])
        self.markers = data.get("markers", [])
        self.sections = data.get("sections", [])
        self.jumps = data.get("jumps", [])
        self.barlines = data.get("barlines", [])
        self.system_texts = data.get("system_texts", [])
        self.volta = data.get("volta", "")
        self.line_break = data.get("line_break", False)
        self.timesig = data.get("timesig", "")

class Score:
    def __init__(self, json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.header = data.get(KEY_HEADER, {})
        self.measures = [Measure(m) for m in data.get(KEY_BARS, [])]
        self.title = self.header.get("title", "Score")

class Bar:
    def __init__(self, x, y, w, h, sheet=None, no_rect=False):
        self.__x = x
        self.__y = y
        self.__w = w
        self.__h = h
        self.__sheet = sheet
        
        self.__cursors = {
            'nw': 0, 'n': 0, 'ne': 0,
            'w': 0,  'center': 0, 'c': 0, 'e': 0,
            'sw': 0, 's': 0, 'se': 0
        }
        
        if self.__sheet is not None and not no_rect:
            self.__sheet.rect(x, y, w, h)    

    def write(self, text, font, size, anchor="center"):
        if self.__sheet is None:
            return

        resolved_font = FONT_MAP.get(font, font)
        self.__sheet.setFont(resolved_font, size)
        
        text_width = pdfmetrics.stringWidth(text, resolved_font, size)
        text_height = size * 0.7  

        anchor = anchor.lower()
        if anchor == 'c':
            anchor = 'center'

        offset = self.__cursors[anchor]

        if anchor == 'center':
            tx = self.__x + (self.__w - text_width) / 2.0 + offset
        elif 'e' in anchor and 'w' not in anchor: 
            tx = self.__x + self.__w - text_width - offset - 4
        else: 
            tx = self.__x + offset + 4

        if anchor == 'center':
            ty = self.__y + (self.__h - text_height) / 2.0
        elif 'n' in anchor and 's' not in anchor: 
            ty = self.__y + self.__h - text_height - 4
        elif 's' in anchor and 'n' not in anchor: 
            ty = self.__y + 4
        else:
            ty = self.__y + (self.__h - text_height) / 2.0

        self.__sheet.drawString(tx, ty, text)
        self.__cursors[anchor] += text_width + 4

    def draw_diagonal(self):
        """Tire un trait de 'sw' vers 'ne' pour diviser la mesure correctement."""
        if self.__sheet is None:
            return
        x1 = self.__x
        y1 = self.__y
        x2 = self.__x + self.__w
        y2 = self.__y + self.__h
        self.__sheet.line(x1, y1, x2, y2)

    def draw_string_centered(self, text, font, size, center_x, center_y):
        """Garantit que le texte est rigoureusement centré sur le point (center_x, center_y)."""
        if self.__sheet is None or not text:
            return
        
        resolved_font = FONT_MAP.get(font, font)
        self.__sheet.setFont(resolved_font, size)
        text_width = pdfmetrics.stringWidth(text, resolved_font, size)
        text_height = size * 0.7 
        
        tx = center_x - (text_width / 2.0)
        ty = center_y - (text_height / 2.0)
        
        self.__sheet.drawString(tx, ty, text)

    def parse_chord(self, chord_str):
        """Découpe un accord en (fondamentale, couleur, basse) via une regex."""
        if not chord_str:
            return None, None, None

        pattern = r"^([A-G][#b]?)(.*?)(?:/([A-G][#b]?))?$"
        match = re.match(pattern, chord_str.strip())
        if match:
            return match.group(1), match.group(2), match.group(3)
        
        return chord_str, "", None

    def _format_part(self, part_str):
        """Remplace les dièses et bémols par leurs glyphes correspondants."""
        if not part_str:
            return ""
        return part_str.replace("#", CHAR_SHARP).replace("b", CHAR_FLAT)

    def _format_color(self, color_str):
        """Remplace les notations de couleur en respectant strictement la casse."""
        if not color_str:
            return ""
        
        if color_str in COLOR_GLYPH_MAP:
            return COLOR_GLYPH_MAP[color_str]
            
        return self._format_part(color_str)

    def render_glyph_tag(self, tag):
        """Remplace un tag de glyphe par sa configuration et l'écrit au bon endroit."""
        if not tag:
            return
        
        config = GLYPH_CONFIGS.get(tag)
        if not config:
            self.write(tag, text_fnt, 10, "se")
            return
        
        content = config["content"]
        font = config["font"]
        size = config["size"]
        row = config["row"]
        align = config["align"]

        if row == "above":
            anchor = "nw" if align == "left" else ("ne" if align == "right" else "n")
        elif row == "inside":
            anchor = "w" if align == "left" else ("e" if align == "right" else "center")
        else:
            anchor = "center"

        self.write(content, font, size, anchor)

    def write_chord(self, chord_str, position="center"):
        """Rendu d'un accord."""
        if not chord_str:
            return

        root, color, bass = self.parse_chord(chord_str)
        
        formatted_root = self._format_part(root)
        formatted_color = self._format_color(color)
        formatted_bass = self._format_part(bass)
        
        display_str = formatted_root + formatted_color
        if formatted_bass:
            display_str += "/" + formatted_bass

        if position == "center":
            center_x = self.__x + (self.__w / 2.0)
            center_y = self.__y + (self.__h / 2.0)
            self.draw_string_centered(display_str, text_fnt, CHORD_FONT_SIZE, center_x, center_y)
        elif position == "top_left":
            center_x = self.__x + (self.__w * 0.25)
            center_y = self.__y + (self.__h * 0.75)
            self.draw_string_centered(display_str, text_fnt, CHORD_FONT_SIZE, center_x, center_y)
        elif position == "bottom_right":
            center_x = self.__x + (self.__w * 0.75)
            center_y = self.__y + (self.__h * 0.25)
            self.draw_string_centered(display_str, text_fnt, CHORD_FONT_SIZE, center_x, center_y)

class Renderer:
    def __init__(self, score, output_path):
        self.score = score
        self.output_path = output_path
        self.sheet = canvas.Canvas(output_path, pagesize=A4)
        self._register_fonts()

    def _register_fonts(self):
        for item in (music_fnt, MUSIC_FNT), (section_fnt, SECTION_FNT), (text_fnt, TEXT_FNT):
            if os.path.exists(item[1]):
                pdfmetrics.registerFont(TTFont(item[0], item[1]))

    def _calculate_grid(self, max_cols=MAX_COLS):
        bars = self.score.measures
        if not bars:
            return 0, 0, []

        current_row_count = 0
        max_cols_found = 0
        nb_rows = 0
        rows_data = []
        current_row_measures = []

        for bar in bars:
            if current_row_count == 0:
                nb_rows += 1
                current_row_measures = []

            current_row_count += 1
            current_row_measures.append(bar)
            
            if current_row_count > max_cols_found:
                max_cols_found = current_row_count

            if bar.line_break or current_row_count == max_cols:
                rows_data.append(current_row_measures)
                current_row_count = 0

        if current_row_count > 0:
            rows_data.append(current_row_measures)

        if max_cols_found == 0:
            max_cols_found = min(len(bars), max_cols)

        return max_cols_found, nb_rows, rows_data

    def get_sheet_layout(self, nb_rows, cols=4, header_percent=DEFAULT_HEADER_HIGHT_PERCENT, draw_header=True, header_rect=False):
        page_w, page_h = A4
        
        printable_w = page_w - (2 * MARGIN)
        printable_h = page_h - (2 * MARGIN)
        
        header_h = printable_h * (header_percent / 100.0)
        remaining_h = printable_h - header_h
        
        W = printable_w / float(cols)
        
        ideal_h_from_percent = remaining_h * (DEFAULT_ROW_HIGHT_PERCENT / 100.0)
        max_possible_h = remaining_h / float(nb_rows) if nb_rows > 0 else ideal_h_from_percent
        
        H = min(ideal_h_from_percent, max_possible_h)
        
        w = W - 4
        h = H - 4

        header_bar = None
        if draw_header:
            header_y = page_h - MARGIN - header_h
            header_bar = Bar(MARGIN, header_y, printable_w, header_h, self.sheet, no_rect=not header_rect)

        return {
            "page_w": page_w,
            "page_h": page_h,
            "printable_w": printable_w,
            "rows": nb_rows,
            "cols": cols,
            "W": W,
            "H": H,
            "w": w,
            "h": h,
            "header_bar": header_bar,
            "header_h": header_h
        }

    def render(self):
        max_cols_found, nb_rows, rows_data = self._calculate_grid(MAX_COLS)
        layout_info = self.get_sheet_layout(nb_rows=nb_rows, cols=max_cols_found, header_percent=DEFAULT_HEADER_HIGHT_PERCENT)
        
        if self.score.header and layout_info["header_bar"]:
            h_bar = layout_info["header_bar"]
            header = self.score.header

            if (title := header.get("title")):
                h_bar.write(title, text_fnt, 32, "center")
            if (composer := header.get("composer")):
                h_bar.write(composer, text_fnt, 16, "se")
            if (lyricist := header.get("lyricist")):
                h_bar.write(lyricist, text_fnt, 16, "ne")
            if (arranger := header.get("arranger")):
                h_bar.write(arranger, text_fnt, 16, "nw")

        page_h = layout_info["page_h"]
        header_h = layout_info["header_h"]
        default_W, H = layout_info["W"], layout_info["H"]
        printable_w = layout_info["printable_w"]
        
        start_y = page_h - MARGIN - header_h - H
        y = start_y

        threshold_cols = max_cols_found * 0.5

        for row_measures in rows_data:
            nb_measures_in_row = len(row_measures)
            
            if nb_measures_in_row <= threshold_cols:
                W = default_W
            else:
                W = printable_w / float(nb_measures_in_row)

            w = W - 4
            h = H - 4

            x = MARGIN
            for measure in row_measures:
                bar = Bar(x, y, w, h, self.sheet)
                
                num_chords = len(measure.chords)
                if num_chords == 1:
                    bar.write_chord(measure.chords[0], "center")
                elif num_chords == 2:
                    bar.draw_diagonal()
                    bar.write_chord(measure.chords[0], "top_left")
                    bar.write_chord(measure.chords[1], "bottom_right")
                elif num_chords > 2:
                    bar.write_chord(measure.chords[0], "center")

                if measure.volta:
                    bar.write(f"[{measure.volta}]", text_fnt, 8, "nw")
                if measure.markers:
                    for marker in measure.markers:
                        bar.render_glyph_tag(marker)
                if measure.sections:
                    for section in measure.sections:
                        section_tag = section if section.startswith("MG_") else f"MG_SECTION_{section}"
                        bar.render_glyph_tag(section_tag)
                if measure.jumps:
                    for jump in measure.jumps:
                        bar.render_glyph_tag(jump)
                if measure.system_texts:
                    bar.write(" ".join(measure.system_texts), text_fnt, 9, "n")
                if measure.timesig:
                    bar.write(measure.timesig, text_fnt, 10, "w")

                x += W

            y -= H

        self.sheet.save()

def jsonToPdf(json_fname, pdf_path):
    """Fonction modulaire unique : prend un fichier JSON de score et génère le PDF correspondant."""
    os.makedirs(os.path.dirname(os.path.abspath(pdf_path)), exist_ok=True)
    score = Score(json_fname)
    renderer = Renderer(score, pdf_path)
    renderer.render()