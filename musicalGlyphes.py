#!/usr/bin/python
# -*- coding: utf-8 -*-

# Définition des constantes de glyphes
MG_IDEM = "MG_IDEM"
MG_TO_CODA = "MG_TO_CODA"      
MG_CODA = "MG_CODA"
MG_SEGNO = "MG_SEGNO"
MG_GOTO_SIGNO = "MG_GOTO_SIGNO"
MG_FINE = "MG_FINE"
MG_REPEAT1 = "MG_REPEAT1"
MG_REPEAT2 = "MG_REPEAT2"
MG_LINE_BREAK = "MG_LINE_BREAK"
MG_SECTION_A = "MG_SECTION_A"        
MG_SECTION_B = "MG_SECTION_B"
MG_SECTION_C = "MG_SECTION_C"
MG_SECTION_D = "MG_SECTION_D"
MG_SECTION_E = "MG_SECTION_E"
MG_SECTION_F = "MG_SECTION_F"

# Configuration centralisée : Contenu, Police, Taille et Positionnement (Grid)
GLYPH_CONFIGS = {
    MG_SECTION_A: {
        "content": "\u0391",
        "font": "GjmRealbook",
        "size": 11,
        "row": "above",
        "align": "left"
    },
    MG_SECTION_B: {
        "content": "\u0392",
        "font": "GjmRealbook",
        "size": 11,
        "row": "above",
        "align": "left"
    },
    MG_SECTION_C: {
        "content": "\u0393",
        "font": "GjmRealbook",
        "size": 11,
        "row": "above",
        "align": "left"
    },
    MG_SECTION_D: {
        "content": "\u0394",
        "font": "GjmRealbook",
        "size": 11,
        "row": "above",
        "align": "left"
    },
    MG_SECTION_E: {
        "content": "\u0395",
        "font": "GjmRealbook",
        "size": 11,
        "row": "above",
        "align": "left"
    },
    MG_SECTION_F: {
        "content": "\u0396",
        "font": "GjmRealbook",
        "size": 11,
        "row": "above",
        "align": "left"
    },
    MG_CODA: {
        "content": "\u00A4",
        "font": "GjmRealbook",
        "size": 11,
        "row": "above",
        "align": "left"
    },
    MG_TO_CODA: {
        "content": "to\u00A4",
        "font": "GjmRealbook",
        "size": 11,
        "row": "above",
        "align": "right"
    },
    MG_IDEM: {
        "content": "\u0025",
        "font": "GjmRealbook",
        "size": 14,
        "row": "inside",
        "align": "center"
    },
    MG_SEGNO: {
        "content": "\ue047",
        "font": "Bravura",
        "size": 15,
        "row": "above",
        "align": "left"
    },
    MG_REPEAT1: {
        "content": "\ue04c",
        "font": "Bravura",
        "size": 15,
        "row": "inside",
        "align": "left"
    },
    MG_REPEAT2: {
        "content": "\ue04d",
        "font": "Bravura",
        "size": 15,
        "row": "inside",
        "align": "right"
    },
    MG_GOTO_SIGNO: {
        "content": "DS",
        "font": "Helvetica",
        "size": 8,
        "row": "above",
        "align": "right"
    },
    MG_FINE: {
        "content": "Fine",
        "font": "Helvetica",
        "size": 8,
        "row": "above",
        "align": "right"
    },
}

# Table de correspondance pour le parseur (texte brut MuseScore -> constante)
ITEMS = {
    "coda": MG_TO_CODA,      
    "coda2": MG_CODA,     
    "ds1": MG_SEGNO,
    "ds2": MG_GOTO_SIGNO,
    "fine": MG_FINE,
    "repeat1": MG_REPEAT1,
    "repeat2": MG_REPEAT2,
    "A": MG_SECTION_A,         
    "B": MG_SECTION_B,
    "C": MG_SECTION_C,
    "D": MG_SECTION_D,
    "E": MG_SECTION_E,
    "F": MG_SECTION_F,
}