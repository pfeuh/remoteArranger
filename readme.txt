# Remoted Arranger

**Remoted Arranger** est une application Python dotée d'une interface graphique (Tkinter) permettant d'éditer, d'importer, de visualiser et de jouer des grilles d'accords. Elle sert de pont intelligent entre la notation musicale (fichiers MuseScore), l'édition visuelle/textuelle de grilles, la génération de PDF professionnels et le pilotage d'un arrangeur MIDI en temps réel.

---

## 🏗 Architecture Modulaire

Le projet repose sur une architecture propre et découplée où chaque module a une responsabilité unique :

* **`gridEditor.py`** (Le contrôleur principal) : Gère l'interface graphique (onglets texte et grille), les boîtes de dialogue, la configuration globale et la mémorisation des chemins (`.grid_editor_config.json`).
* **`ms2Grid.py`** (Module d'import) : Pur module sans interface graphique dédié à l'extraction de fichiers MuseScore (`.mscz`). Il gère le dézippage, le parsing XML, la gestion des durées d'accords et retourne une structure de grille standardisée.
* **`pdfGenerator.py`** (Module de rendu) : Encapsule toute la logique de mise en page via ReportLab pour transformer une grille au format JSON en partition PDF soignée.
* **`remotedArranger.py`** : Assure la lecture et le rendu des morceaux en direct via MIDI sur un arrangeur externe.

---

## ✨ Fonctionnalités Principales

* **Import MuseScore (`.mscz`)** : Extraction automatique des métadonnées (titre, compositeur), des signatures rythmiques et des accords mesure par mesure, avec propagation intelligente des durées sur les mesures vides.
* **Édition Hybride** : 
  * Un **Mode Texte** pour un copier-coller rapide des accords.
  * Une **Grille Visuelle** interactive (par blocs de 4 mesures par ligne).
* **Personnalisation & Styles** : Sélection dynamique des styles et des catalogues d'arrangeurs (ex: Yamaha DGX-670).
* **Contrôle MIDI en Direct** : Lancement, arrêt et pilotage de la lecture de la grille connectée à un port MIDI de l'ordinateur.
* **Génération de PDF** : Exportation directe de grilles claires, lisibles et conformes aux standards musicaux.
* **Mémorisation Intelligente** : Sauvegarde automatique des derniers chemins d'accès (fichiers JSON, fichiers MuseScore, PDFs) pour un confort d'utilisation maximal.

## ⏱️ Principe de synchronisation et d'horloge MIDI

La lecture rythmique et le pilotage de l'arrangeur ne reposent pas sur un flux continu de tops d'horloge logiciels complexes, mais sur un principe simple et redoutablement stable :

1. **L'envoi déclencheur (Trigger) :** Le script `remotedArranger.py` envoie le premier accord de la grille au port MIDI de l'arrangeur. C'est cet événement initial qui "réveille" ou déclenche l'accompagnement automatique de l'instrument.
2. **L'indépendance des horloges (Quartz) :** Une fois le style et le tempo initial lancés, le script transmet les mesures au fil de l'eau selon un minutage calculé, mais le maintien strict du tempo repose sur la **précision des quartz matériels** de l'arrangeur d'une part, et de la machine hôte d'autre part. Leurs horloges internes respectives tournent à la même fréquence naturelle, garantissant un défilement parfaitement régulier sans dérive temporelle (pas de décrochage de tempo).
3. **Autonomie du rendu :** L'ordinateur fait office de chef d'orchestre séquentiel (il dicte *quand* changer d'accord), tandis que l'arrangeur gère en totale autonomie le groove, la métrique et l'exécution matérielle des notes en temps réel.