#!/usr/bin/env sh
# Extrait le texte des PDF et pages HTML d'archive (archives/docs/) dans refs/txt/, sous le même nom.
# Aucun téléchargement : les PDF sont versionnés dans archives/docs/.
# Un .txt déjà présent n'est jamais écrasé (certains ont un meilleur OCR que pdftotext).
# Usage : sh tools/fetch_refs.sh   (PDF : pdftotext / poppler-utils ; HTML : python)
set -e
cd "$(dirname "$0")/.."
mkdir -p refs/txt
for f in archives/docs/*.pdf; do
  t="refs/txt/$(basename "${f%.pdf}").txt"
  [ -f "$t" ] || pdftotext -q -layout "$f" "$t" || echo "ÉCHEC : $f"
done
# Pages HTML archivées (MAIT, LEC) : texte brut par tools/html2txt.py (Python seul).
for f in archives/docs/*.htm; do
  t="refs/txt/$(basename "${f%.htm}").txt"
  [ -f "$t" ] || python tools/html2txt.py "$f" "$t" || echo "ÉCHEC : $f"
done
echo "Terminé. Liste des sources : docs/SOURCES.md."
