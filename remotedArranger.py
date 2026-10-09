#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import time
from chordGenerator import chord_to_midi
import rtmidi

from constants import (
    KEY_HEADER, KEY_BARS,
    KEY_CHORDS, KEY_TIMESIG
)

# Initialisation de la sortie MIDI
midi_out = rtmidi.MidiOut()
ports = midi_out.get_ports()

# Configuration d'argparse
parser = argparse.ArgumentParser(
    description="Envoie une grille d'accords en MIDI via un port."
)
parser.add_argument(
    "pnum",
    nargs="?",
    type=int,
    help="Numéro du port MIDI (laisse vide pour lister les ports)",
)
parser.add_argument(
    "fname",
    nargs="?",
    type=str,
    default="grille.json",
    help="Chemin vers le fichier de grille JSON (défaut : grille.json)",
)

args = parser.parse_args()

# Si aucun numéro de port n'est fourni, on liste les ports et on quitte
if args.pnum is None:
    print("Ports MIDI disponibles :")
    if ports:
        for i, port_name in enumerate(ports):
            print(f"[{i}] {port_name}")
        print("\nExemples d'utilisation :")
        print("  python remotedArranger.py 1")
        print("  python remotedArranger.py 1 /chemin/vers/grille.json")
    else:
        print("Aucun port MIDI détecté.")
    sys.exit(0)

# Validation du port MIDI
if args.pnum < 0 or args.pnum >= len(ports):
    print(f"Erreur : Le port {args.pnum} n'existe pas.")
    print("Ports disponibles :")
    for i, port_name in enumerate(ports):
        print(f"[{i}] {port_name}")
    sys.exit(1)

port_idx = args.pnum

# Chargement du fichier JSON de la grille
grid_path = args.fname
if not os.path.isfile(grid_path):
    print(f"Erreur : Le fichier de grille '{grid_path}' est introuvable.")
    sys.exit(1)

try:
    with open(grid_path, "r", encoding="utf-8") as f:
        grid_data = json.load(f)
except Exception as e:
    print(f"Erreur lors de la lecture du fichier de grille : {e}")
    sys.exit(1)

# Lecture exclusive du tempo depuis le JSON de la grille (valeur de repli : 120.0)
json_grid_bpm = 120.0
if KEY_HEADER in grid_data and "bpm" in grid_data[KEY_HEADER]:
    try:
        json_grid_bpm = float(grid_data[KEY_HEADER]["bpm"])
    except Exception:
        pass

bpm = json_grid_bpm


def parse_musescore_json(data):
    """Parse les données JSON de la grille et gère la structure des temps."""
    seq = []
    current_timesig = "4/4"

    if KEY_HEADER in data and KEY_TIMESIG in data[KEY_HEADER]:
        current_timesig = data[KEY_HEADER][KEY_TIMESIG]

    for bar in data.get(KEY_BARS, []):
        if KEY_TIMESIG in bar:
            current_timesig = bar[KEY_TIMESIG]

        try:
            num_str, den_str = current_timesig.split("/")
            num = int(num_str)
            den = int(den_str)

            if current_timesig == "6/8":
                beats_per_bar = 2.0
            elif current_timesig == "12/8":
                beats_per_bar = 4.0
            elif current_timesig == "3/4":
                beats_per_bar = 3.0
            else:
                beats_per_bar = float(num)
        except Exception:
            beats_per_bar = 4.0

        chords_raw = bar.get(KEY_CHORDS, [])

        if not chords_raw:
            if seq:
                seq[-1]["beats"] += beats_per_bar
            else:
                notes = chord_to_midi("C")
                seq.append(
                    {
                        "notes": notes,
                        "beats": beats_per_bar,
                        "name": "C",
                    }
                )
            continue

        chord_list = []
        for c in chords_raw:
            if isinstance(c, dict):
                chord_list.append(c.get("chord", c.get("name", c.get("symbol", "C"))))
            else:
                chord_list.append(str(c))

        duration_per_element = beats_per_bar / len(chord_list)

        for chord_name in chord_list:
            if seq and seq[-1]["name"] == chord_name:
                seq[-1]["beats"] += duration_per_element
            else:
                notes = chord_to_midi(chord_name)
                seq.append(
                    {
                        "notes": notes,
                        "beats": duration_per_element,
                        "name": chord_name,
                    }
                )
    return seq


try:
    sequence = parse_musescore_json(grid_data)
    grid_display = f"Fichier: {grid_path}"
except Exception as e:
    print(f"Erreur lors du parsing de la grille : {e}")
    sys.exit(1)

midi_out.open_port(port_idx)
print(f"Connecté au port : {ports[port_idx]}")
print(f"Grille active : {grid_display} | Tempo : {bpm} BPM")

last_notes = []


def play_chord(notes):
    global last_notes
    for n in last_notes:
        midi_out.send_message([0x80, n, 0])
    for n in notes:
        midi_out.send_message([0x90, n, 100])
    last_notes = notes


def stop_arranger():
    global last_notes
    for n in last_notes:
        midi_out.send_message([0x80, n, 0])
    last_notes = []

    for channel in range(16):
        midi_out.send_message([0xB0 + channel, 123, 0])
        midi_out.send_message([0xB0 + channel, 121, 0])

    midi_out.send_message([0xFC])

    sysex_yamaha_stop = [0xF0, 0x43, 0x10, 0x4C, 0x00, 0x00, 0x7E, 0x00, 0xF7]
    try:
        midi_out.send_message(sysex_yamaha_stop)
    except Exception:
        pass


seconds_per_beat = 60.0 / bpm

print("\nDémarrage de l'envoi des accords (Appuie sur Ctrl+C pour quitter)...")
try:
    next_time = time.time()
    
    # Lecture séquentielle unique de la grille du début à la fin
    for step in sequence:
        chord = step["notes"]
        beats = step["beats"]
        chord_name = step["name"]
        duration = seconds_per_beat * beats

        play_chord(chord)
        print(
            f"Accord [{chord_name}] (durée: {beats} temps), notes MIDI: {chord},"
            f" timestamp : {time.strftime('%H:%M:%S')}"
        )

        next_time += duration
        sleep_time = next_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)

    # Fin de la grille atteinte : arrêt propre de l'arrangeur
    stop_arranger()
    print("\nFin de la grille : Transport Stop envoyé à l'arrangeur.")

except KeyboardInterrupt:
    stop_arranger()
    print(
        "\nArrêt du script : Transport Stop et SysEx Yamaha envoyés à l'arrangeur."
    )