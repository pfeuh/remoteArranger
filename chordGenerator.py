#!/usr/bin/python
# -*- coding: utf-8 -*-

# Dictionnaire des décalages de demi-tons par rapport à Do (C)
NOTE_OFFSETS = {
    "C": 0,
    "B#": 0,
    "C#": 1,
    "Db": 1,
    "D": 2,
    "D#": 3,
    "Eb": 3,
    "E": 4,
    "Fb": 4,
    "F": 5,
    "E#": 5,
    "F#": 6,
    "Gb": 6,
    "G": 7,
    "G#": 8,
    "Ab": 8,
    "A": 9,
    "A#": 10,
    "Bb": 10,
    "B": 11,
    "Cb": 11,
}

# Intervalles (en demi-tons par rapport à la fondamentale) et extensions enrichies
QUALITY_INTERVALS = {
    "": [0, 4, 7],  # Majeur
    "maj": [0, 4, 7],  # Majeur
    "m": [0, 3, 7],  # Mineur
    "min": [0, 3, 7],  # Mineur
    "7": [0, 4, 7, 10],  # 7e dominante
    "maj7": [0, 4, 7, 11],  # Majeur 7
    "7M": [0, 4, 7, 11],  # Alias Majeur 7
    "m7": [0, 3, 7, 10],  # Mineur 7
    "9": [0, 4, 7, 10, 14],  # 9e
    "m9": [0, 3, 7, 10, 14],  # Mineur 9
    "maj9": [0, 4, 7, 11, 14],  # Majeur 9
    "9M": [0, 4, 7, 11, 14],  # Majeur 9
    "dim": [0, 3, 6],  # Diminué
    "dim7": [0, 3, 6, 9],  # Diminué 7
    "m7b5": [0, 3, 6, 10],  # Semi-diminué
    "aug": [0, 4, 8],  # Augmenté
    "+": [0, 4, 8],  # Augmenté (alias)
    "5+": [0, 4, 8],  # Augmenté (alias)
    "6": [0, 4, 7, 9],  # Sixte
    "m6": [0, 3, 7, 9],  # Mineur 6
    "sus4": [0, 5, 7],  # Sus4
    "sus2": [0, 2, 7],  # Sus2
    "7sus4": [0, 5, 7, 10],  # 7Sus4
    "7sus2": [0, 2, 7, 10],  # 7Sus2
}


def chord_to_midi(chord_str, base_octave=1):
  """Convertit dynamiquement n'importe quel accord (avec slash chords type C/D)

  en notes MIDI dans la zone basse/main gauche. La première lettre de la
  fondamentale (et de la basse) est tolérée en minuscule ou majuscule.
  """
  clean_chord = chord_str.strip()
  bass_note_midi = None

  # Gestion des accords inversés (Slash chords ex: c/d)
  if "/" in clean_chord:
    chord_part, bass_part = clean_chord.split("/", 1)
    chord_part = chord_part.strip()
    bass_part = bass_part.strip()

    b_root_letter = bass_part[0].upper()
    if len(bass_part) > 1 and bass_part[1] in ["#", "b"]:
      b_root = b_root_letter + bass_part[1]
    else:
      b_root = b_root_letter

    if b_root in NOTE_OFFSETS:
      base_midi = base_octave * 12 + 12
      bass_note_midi = base_midi + NOTE_OFFSETS[b_root]
  else:
    chord_part = clean_chord

  # Extraction de la racine : première lettre en majuscule, altération et qualité strictes
  root_letter = chord_part[0].upper()
  if len(chord_part) > 1 and chord_part[1] in ["#", "b"]:
    root = root_letter + chord_part[1]
    quality = chord_part[2:]
  else:
    root = root_letter
    quality = chord_part[1:]

  if root not in NOTE_OFFSETS:
    root = "C"
    quality = ""

  if quality not in QUALITY_INTERVALS:
    quality = ""

  base_midi = base_octave * 12 + 12
  semitone_base = NOTE_OFFSETS[root]
  intervals = QUALITY_INTERVALS[quality]

  notes = [base_midi + semitone_base + interval for interval in intervals]

  # Intégration de la note de basse si présente
  if bass_note_midi is not None:
    if bass_note_midi not in notes:
      notes.append(bass_note_midi)
    notes.sort()

  # Sécurité anti-dépassement de split (Sol2 = 43)
  while any(n > 43 for n in notes):
    notes = [n - 12 for n in notes]

  return notes