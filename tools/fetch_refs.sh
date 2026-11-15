#!/usr/bin/env sh
# Télécharge les sources publiques dans refs/pdf et extrait leur texte dans refs/txt.
# Usage : sh tools/fetch_refs.sh   (nécessite curl et pdftotext / poppler-utils)
set -e
cd "$(dirname "$0")/.."
mkdir -p refs/pdf refs/txt refs/photos
get() { [ -f "refs/pdf/$1" ] || curl -L --fail -o "refs/pdf/$1" "$2" || echo "ÉCHEC : $1 ($2)"; }
get onde-electrique-1960-davous-bataille-harrand.pdf http://www.feb-patrimoine.com/projet/gamma60/gamma60_bataille2.pdf
get tumlin-smotherman-evaluation-design-gamma60.pdf  https://db.aconit.org/dbmedia_0/pdf_10/10174.pdf
# Nakala (B61, BPD) et ACM : téléchargement manuel conseillé depuis les liens de docs/SOURCES.md
for f in refs/pdf/*.pdf; do
  t="refs/txt/$(basename "${f%.pdf}").txt"
  [ -f "$t" ] || pdftotext -layout "$f" "$t"
done
echo "Terminé. Voir docs/SOURCES.md pour les documents à récupérer à la main."
