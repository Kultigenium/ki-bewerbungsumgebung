# CLAUDE.md — KI-Bewerbungsumgebung (Vorlage)

## Was dieses Repo ist
Lokale Bewerbungsumgebung: Aus `daten/master-daten.md` (Single Source of Truth über die
eigene Person) und einer Stellenanzeige in `stellenanzeigen/` wird ein zugeschnittener
Lebenslauf erzeugt (JSON-Resume-Schema → einseitiges PDF).

## Erste Schritte
Die persönlichen Dateien sind Vorlagen (`*.beispiel.*`) — kopieren, ausfüllen, die echten
Fassungen bleiben lokal (gitignored). Siehe README „Setup".

## Ordnerstruktur
- `daten/master-daten.md` — ALLE Fakten über die Person. Einzige Quelle. Nie erfinden,
  nur auswählen. Wird ausschließlich von einem Menschen befüllt.
- `daten/lebenslauf-generator.md` — Der Generator-Prompt mit allen Regeln. Bei jeder
  CV-Erzeugung vollständig befolgen.
- `daten/kritiker-prompt.md` — Gemeinsamer Prüf-Prompt für alle Reviewer-Modelle.
- `daten/interessen-profil.md` — **Führende Achse der Triage (interessen-first):** Was die Person
  machen WILL. Entscheidet VOR der Qualifikation und liefert das CV-Framing. Vorlage:
  `interessen-profil.beispiel.md`.
- `daten/matching-profil.md` — Präferenzen + Kategorien (A–D) für die Stellen-Triage
  (interessen-first: fehlende Muss-Skills werfen ein Wunsch-Thema nicht raus, sie werden nur als
  Lücke markiert; echte Misfit-Kerne bleiben C/D).
- `daten/matching-patterns.json` — Signal-Wortlisten/Gewichte fürs Pattern-Matching
  (eine Quelle für Skript und Triage-LLM; an das eigene Profil anpassen).
- `daten/verbotene-begriffe.txt` — Bindende Ein-Quellen-Liste der Begriffe, die nie im
  PDF stehen dürfen; wird von `check_cv.sh` maschinell geprüft.
- `stellenanzeigen/` — Stellenanzeigen als .md/.txt/.pdf.
- `output/` — resume.json-Varianten und gerenderte PDFs (lokal).
- `output/reviews/` — Review-Ergebnisse der externen Modelle (beratend, nicht bindend).
- `triage/UEBERSICHT.md` — Menschlich lesbares Triage-Ergebnis; `triage/details/` je Anzeige.
- `scripts/build_cv.py` — Rendert resume.json → PDF; bricht bei mehr als 1 Seite ab.
- `scripts/check_cv.sh` — Mechanische Pflicht-Checks (Extraktion, 1 Seite, Umlaute,
  Verbotsliste).
- `scripts/multi_review.sh` — Zweitmeinungen von Codex (GPT) und Antigravity (Gemini).
- `scripts/triage.py` — Free-Tier-Triage aller Anzeigen (Stufe 0: Regex, Stufe 1: LLM).

## Workflow pro Bewerbung
0. Bei mehreren neuen Anzeigen zuerst Triage (spart High-End-Tokens):
   `python3 scripts/triage.py` → `triage/UEBERSICHT.md` lesen. Triage ist **interessen-first**
   (Feld `interesse` hoch/mittel/gering führt vor der Kategorie). Nur Kategorie A/B bekommen
   den Volldurchlauf; D wird nicht bearbeitet.
1. Stellenanzeige nach `stellenanzeigen/` legen.
2. Anzeige lesen + `daten/master-daten.md` lesen + Regeln aus
   `daten/lebenslauf-generator.md` anwenden.
3. `output/resume_<firma>.json` erzeugen (JSON-Resume-Schema, valide).
4. Rendern: `.venv/bin/python scripts/build_cv.py output/resume_<firma>.json output/<name>.pdf`
5. Mechanische Checks: `bash scripts/check_cv.sh output/<name>.pdf` — muss BESTANDEN sein.
6. Multi-Modell-Review: `bash scripts/multi_review.sh output/resume_<firma>.json stellenanzeigen/<anzeige>`.
   Beide Reviews lesen und mergen: Übernommen wird nur, was den HARTEN REGELN und den
   Master-Daten standhält — Reviews sind beratend, Regeln sind bindend.
7. Kurze, ehrliche Gap-Analyse an die Person (was passt, was fehlt) + Liste, welche
   Reviewer-Vorschläge übernommen und welche (mit Grund) verworfen wurden.

## HARTE REGELN (an die eigene Person anpassen — dann nie brechen)
1. **Nur Master-Daten.** Keine Skills, Tools, Erfahrungen oder Metriken erfinden — auch
   nicht, wenn die Anzeige sie verlangt. Die Verbotsliste ist bindend.
2. **Persönliche Ausschluss-Regeln.** Beispiel: „Sprache/Tool X NIE als Kenntnis, als ‚im
   Aufbau' oder als ‚lerne ich' ausweisen, weil nicht selbst beherrscht." Solche Regeln
   gehören in die Master-Daten UND als Begriffe in `daten/verbotene-begriffe.txt`.
3. **Interview-Test:** Nur Formulierungen, die die Person 60 Sekunden lang erklären kann.
4. **Eine Seite, einspaltig, ATS-lesbar.** Keine Skill-Balken/`level`-Felder, keine Grafiken.
5. **Landes-Standard.** Hier: deutsch, tabellarisch, antichronologisch.
6. **Ehrliche Gap-Analyse statt Schönfärben.** Passt die Kernanforderung nicht zum Profil,
   das offen sagen — nicht kaschieren.

## Setup (einmalig)
`uv venv .venv && uv pip install -r scripts/requirements.txt --python .venv/bin/python`
(Details und Systempakete im README.)
