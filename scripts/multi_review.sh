#!/usr/bin/env bash
# Multi-Modell-Review: holt Zweitmeinungen von Codex (GPT) und Antigravity (Gemini)
# zu einem generierten Lebenslauf ein. Die Reviews sind BERATEND — bindend sind die
# HARTEN REGELN in CLAUDE.md und die Master-Daten.
#
# Nutzung: bash scripts/multi_review.sh <resume.json> [stellenanzeige.md|.txt|.pdf]
# Ergebnis: output/reviews/<name>_codex.md und output/reviews/<name>_antigravity.md

set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RESUME="${1:?Nutzung: multi_review.sh <resume.json> [stellenanzeige]}"
ANZEIGE="${2:-}"

[ -f "$RESUME" ] || { echo "FEHLER: $RESUME nicht gefunden" >&2; exit 1; }

NAME="$(basename "$RESUME" .json)"
REVIEWDIR="$ROOT/output/reviews"
mkdir -p "$REVIEWDIR"
PACKET="$REVIEWDIR/${NAME}_paket.md"

# --- Review-Paket zusammenstellen (Prompt + Fakten + Anzeige + CV) ---
{
  cat "$ROOT/daten/kritiker-prompt.md"
  echo; echo "---"; echo
  echo "# MASTER-DATEN (einzige erlaubte Faktenquelle)"
  cat "$ROOT/daten/master-daten.md"
  echo; echo "---"; echo
  if [ -n "$ANZEIGE" ] && [ -f "$ANZEIGE" ]; then
    echo "# STELLENANZEIGE"
    case "$ANZEIGE" in
      *.pdf) pdftotext "$ANZEIGE" - ;;
      *)     cat "$ANZEIGE" ;;
    esac
  else
    echo "# STELLENANZEIGE: keine übergeben — allgemeines Review des Basis-CV"
  fi
  echo; echo "---"; echo
  echo "# ZU PRÜFENDER LEBENSLAUF (JSON-Resume)"
  echo '```json'
  cat "$RESUME"
  echo '```'
} > "$PACKET"

echo "Review-Paket: $PACKET ($(wc -w < "$PACKET") Wörter)"

# --- Beide Reviewer parallel ---
echo "Starte Codex (GPT) ..."
codex exec --skip-git-repo-check -s read-only \
  -o "$REVIEWDIR/${NAME}_codex.md" \
  "$(cat "$PACKET")" >/dev/null 2>"$REVIEWDIR/${NAME}_codex.log" &
PID_CODEX=$!

echo "Starte Antigravity (Gemini) ..."
agy -p "$(cat "$PACKET")" \
  > "$REVIEWDIR/${NAME}_antigravity.md" 2>"$REVIEWDIR/${NAME}_antigravity.log" &
PID_AGY=$!

FAIL=0
wait "$PID_CODEX" || { echo "WARNUNG: Codex-Review fehlgeschlagen (siehe ${NAME}_codex.log)"; FAIL=1; }
wait "$PID_AGY"   || { echo "WARNUNG: Antigravity-Review fehlgeschlagen (siehe ${NAME}_antigravity.log)"; FAIL=1; }

# Reviews an die geprüfte CV-Version binden + Plausibilität prüfen
CV_HASH="$(sha256sum "$RESUME" | cut -c1-12)"
echo
for f in "$REVIEWDIR/${NAME}_codex.md" "$REVIEWDIR/${NAME}_antigravity.md"; do
  if [ -s "$f" ]; then
    TMP="$(mktemp)"
    { echo "> Review vom $(date +%F) für \`$(basename "$RESUME")\` (sha256: ${CV_HASH}…) — gilt NUR für diese Version."
      echo
      cat "$f"; } > "$TMP" && mv "$TMP" "$f"
    if grep -q "GESAMTURTEIL" "$f"; then
      echo "OK:   $f ($(wc -w < "$f") Wörter)"
    else
      echo "UNPLAUSIBEL: $f — erwarteter Abschnitt GESAMTURTEIL fehlt (Format kaputt oder Fehlertext?)"
      FAIL=1
    fi
  else
    echo "LEER: $f"
    FAIL=1
  fi
done
exit $FAIL
