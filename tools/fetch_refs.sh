#!/usr/bin/env sh
# Extrait le texte des PDF d'archive (archives/docs/) dans refs/txt/, sous le même nom.
# Aucun téléchargement : les PDF sont versionnés dans archives/docs/.
# Un .txt déjà présent n'est jamais écrasé (certains ont un meilleur OCR que pdftotext).
# Usage : sh tools/fetch_refs.sh   (nécessite pdftotext / poppler-utils)
set -e
cd "$(dirname "$0")/.."
mkdir -p refs/txt refs/photos
for f in archives/docs/*.pdf; do
  t="refs/txt/$(basename "${f%.pdf}").txt"
  [ -f "$t" ] || pdftotext -q -layout "$f" "$t" || echo "ÉCHEC : $f"
done
echo "Terminé. Liste des sources : docs/SOURCES.md."
