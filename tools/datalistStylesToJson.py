# Nécessite : pip install pdfplumber
import json
import os
import pdfplumber


def extract_styles_from_pdf(pdf_path, output_json_path):
  if not os.path.isfile(pdf_path):
    print(
        f"Erreur : Le fichier PDF '{pdf_path}' est introuvable dans le dossier."
    )
    return

  styles_catalog = []

  print(
      f"Ouverture et analyse du PDF '{pdf_path}' (cela peut prendre quelques"
      " secondes)..."
  )

  with pdfplumber.open(pdf_path) as pdf:
    # Les pages de la Style List dans la Data List du DGX-670 se situent
    # généralement entre la page 22 et la page 35 (à adapter si besoin).
    for page_num in range(22, 36):
      if page_num >= len(pdf.pages):
        break
      page = pdf.pages[page_num]
      tables = page.extract_tables()

      for table in tables:
        for row in table:
          for cell in row:
            if not cell:
              continue
            # Nettoyage des lignes pour isoler les noms potentiels de styles
            lines = cell.split("\n")
            for line in lines:
              clean_line = line.strip()
              # On filtre les en-têtes et les mots-clés parasites de l'interface Yamaha
              if not clean_line or clean_line in [
                  "-",
                  "Unison",
                  "Adaptive",
                  "Style List",
                  "Category",
                  "Style Name",
                  "DGX-670 Data List",
              ]:
                continue
              # Éviter d'ajouter des noms de catégories stricts s'ils se glissent là
              if clean_line in [
                  "Pop & Rock",
                  "Ballad",
                  "Dance & R&B",
                  "Country & Blues",
                  "Standards & Jazz",
                  "Entertainment",
              ]:
                continue

              # On ajoute le style au catalogue sous forme de dictionnaire épuré
              styles_catalog.append(
                  {
                      "name": clean_line,
                      "category": "",
                      "tempo": 120,  # À compléter avec le vrai tempo relevé sur le DGX
                  }
              )

  # Sauvegarde au format compact (1 dictionnaire par ligne)
  with open(output_json_path, "w", encoding="utf-8") as f:
    f.write("[\n")
    for i, entry in enumerate(styles_catalog):
      comma = "," if i < len(styles_catalog) - 1 else ""
      f.write(f"{json.dumps(entry, ensure_ascii=False)}{comma}\n")
    f.write("]\n")

  print(
      f"Extraction réussie ! {len(styles_catalog)} styles enregistrés dans"
      f" '{output_json_path}'."
  )


if __name__ == "__main__":
  # Mets ici le nom exact de ton fichier PDF de la Data List du DGX-670
  pdf_filename = "/mnt/Data1/Documents/pdf/yamaha/dgx670/dgx670_datalist.pdf"
  output_filename = "dgx_styles_catalog.json"
  extract_styles_from_pdf(pdf_filename, output_filename)