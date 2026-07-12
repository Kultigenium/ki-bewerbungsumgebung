#!/usr/bin/env bash
# Mechanische Pflicht-Checks für ein gerendertes CV-PDF (HARTE REGELN aus CLAUDE.md).
# Verbotene Begriffe kommen aus daten/verbotene-begriffe.txt (eine Quelle, bindend).
# Nutzung: bash scripts/check_cv.sh output/Lebenslauf_....pdf

set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PDF="${1:?Nutzung: check_cv.sh <datei.pdf>}"
LISTE="$ROOT/daten/verbotene-begriffe.txt"
[ -f "$PDF" ] || { echo "FEHLER: $PDF nicht gefunden" >&2; exit 1; }
[ -f "$LISTE" ] || { echo "FEHLER: $LISTE fehlt (bindende Verbotsliste)" >&2; exit 1; }

FAIL=0
TEXT="$(pdftotext "$PDF" - 2>/dev/null)"

# Leere/fast leere Extraktion = harter FAIL (sonst prüfen alle greps ins Leere)
ZEICHEN=$(printf '%s' "$TEXT" | wc -c)
if [ "$ZEICHEN" -lt 200 ]; then
  echo "FEHLER: pdftotext liefert nur $ZEICHEN Zeichen — PDF nicht ATS-lesbar oder Extraktion kaputt"
  exit 1
fi
echo "OK:     Textextraktion ($ZEICHEN Zeichen)"

PAGES="$(pdfinfo "$PDF" 2>/dev/null | awk '/^Pages:/{print $2}')"
if [ "$PAGES" = "1" ]; then
  echo "OK:     genau 1 Seite"
else
  echo "FEHLER: $PAGES Seiten (erlaubt: genau 1)"; FAIL=1
fi

LEAK=0
while IFS= read -r BEGRIFF; do
  case "$BEGRIFF" in ''|'#'*) continue;; esac
  if printf '%s' "$TEXT" | grep -qi -- "$BEGRIFF"; then
    echo "FEHLER: verbotener Begriff im PDF: '$BEGRIFF' (daten/verbotene-begriffe.txt)"
    printf '%s' "$TEXT" | grep -ni -- "$BEGRIFF" | head -3 | sed 's/^/        /'
    FAIL=1; LEAK=1
  fi
done < "$LISTE"
[ $LEAK -eq 0 ] && echo "OK:     kein verbotener Begriff im PDF ($(grep -cvE '^\s*(#|$)' "$LISTE") geprüft)"

if printf '%s' "$TEXT" | grep -q 'ü\|ö\|ä\|ß'; then
  echo "OK:     Umlaute korrekt extrahierbar (ATS-lesbar)"
else
  echo "FEHLER: keine Umlaute im extrahierten Text — Encoding kaputt"; FAIL=1
fi

if [ $FAIL -eq 0 ]; then
  echo "ALLE CHECKS BESTANDEN"
fi
exit $FAIL
