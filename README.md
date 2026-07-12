# KI-Bewerbungsumgebung

Ein lokales Multi-Modell-System, das aus einer zentralen Faktendatei und beliebig vielen
Stellenanzeigen regelkonforme, einseitige Lebensläufe erzeugt. Kernprinzip:

> **KI darf formulieren — aber nie erfinden.**

Entstanden aus einem realen Problem: Wer als Student auf mehreren Plattformen sucht, sitzt
schnell auf Dutzenden Stellenanzeigen und bräuchte für jede einen zugeschnittenen Lebenslauf.
Generische KI-Lebensläufe sind dafür keine Lösung — sie sind aufgebläht und oft schlicht
gelogen. Dieses System dreht den Spieß um: Die KI wird durch bindende Regeln, deterministische
Prüfskripte und unabhängige Kritiker-Modelle gezwungen, ehrlich zu bleiben.

## Architektur

```
Stellenanzeigen sammeln
  Browser-Erweiterung lädt jede Anzeige als .md — Duplikate werden über
  Firmenname/Titel erkannt (~4 Klicks pro Anzeige, plattformübergreifend)
        │
        ▼
Triage — kostenlos (scripts/triage.py)
  Stufe 0: deterministischer Regex-Score (daten/matching-patterns.json)
  Stufe 1: Free-Tier-LLM (z.B. Gemini Flash) → Kategorien A–D mit Begründung
        │  nur A/B bekommen den teuren Volldurchlauf
        ▼
CV-Generierung — High-End-LLM (z.B. Claude)
  wählt NUR aus daten/master-daten.md aus; Regeln in daten/lebenslauf-generator.md
        │
        ▼
Deterministische Checks (scripts/check_cv.sh)
  genau 1 Seite · ATS-Textextraktion · Umlaute · Verbotsbegriffe aus einer Ein-Quellen-Liste
        │
        ▼
Multi-Modell-Review (scripts/multi_review.sh)
  GPT (Codex CLI) + Gemini (Antigravity CLI) begutachten jeden CV unabhängig
  nach demselben Prüf-Prompt — Reviews sind beratend, die Regeln sind bindend
        │
        ▼
Merge + ehrliche Gap-Analyse + Ergebnisprotokoll (HTML-Dashboard)
```

Eine gekürzte, anonymisierte Ansicht des Ergebnisprotokolls liegt in
[`demo/ergebnisprotokoll-demo.html`](demo/ergebnisprotokoll-demo.html) (lokal im Browser öffnen).

## Prinzipien

1. **Single Source of Truth.** Alle Fakten über die Person stehen in genau einer Datei,
   die nur von einem Menschen befüllt wird. Jede CV-Aussage muss sich darauf zurückführen
   lassen — sonst fliegt sie raus.
2. **Regeln schlagen Reviews.** Die Kritiker-Modelle dürfen alles vorschlagen; übernommen
   wird nur, was den harten Regeln standhält. (Praxisbeispiel: Ein Reviewer schlug vor, eine
   geforderte Programmiersprache zu ergänzen, die die Person nicht beherrscht — verworfen.)
3. **Teuer nur, wo nötig.** Massenarbeit (Triage) läuft über Free-Tier-Modelle, Zweitmeinungen
   über vorhandene Abos, nur der eigentliche CV-Zuschnitt über das teuerste Modell.
4. **Mensch entscheidet.** Jeder CV, jede Kategorisierung und jede Bewerbung geht über den
   Tisch der Person — das System bereitet auf, es versendet nichts.
5. **Ehrliche Gap-Analyse.** Passt eine Kernanforderung nicht zum Profil, sagt das System
   „passt nicht" — statt zu kaschieren. Mechanische Checks stellen sicher, dass ausgeschlossene
   Begriffe nie im PDF landen.

## Kostenmodell

| Schritt | Modell | Kosten |
|---|---|---|
| Triage aller Anzeigen | Gemini Flash (Free-Tier-API) | kostenlos |
| Mechanische Checks | Bash/Python-Skripte | kostenlos |
| CV-Zuschnitt + Merge | Claude (Claude Code) | Abo-Kontingent, nur für Kategorie A/B |
| Zweitmeinungen | Codex CLI + Antigravity CLI | über vorhandene Abos |

## Setup

```bash
# Systempakete (WSL/Ubuntu): WeasyPrint-Abhängigkeiten + pdftotext
sudo apt install -y libpango-1.0-0 libpangoft2-1.0-0 poppler-utils

# Python-Umgebung
uv venv .venv
uv pip install -r scripts/requirements.txt --python .venv/bin/python

# Vorlagen ausfüllen (die echten Dateien sind gitignored und bleiben lokal)
cp daten/master-daten.beispiel.md      daten/master-daten.md
cp daten/matching-profil.beispiel.md   daten/matching-profil.md
cp daten/verbotene-begriffe.beispiel.txt daten/verbotene-begriffe.txt
cp .env.beispiel .env                  # Free-Tier-API-Schlüssel eintragen
mkdir -p output triage
```

Nutzung: Anzeigen (.md/.txt/.pdf) nach `stellenanzeigen/`, dann

```bash
python3 scripts/triage.py                                  # Triage A–D → triage/UEBERSICHT.md
.venv/bin/python scripts/build_cv.py <resume.json> <cv.pdf>  # Rendern (bricht bei >1 Seite ab)
bash scripts/check_cv.sh <cv.pdf>                          # Pflicht-Checks
bash scripts/multi_review.sh <resume.json> <anzeige>       # Zweitmeinungen einholen
```

Die CV-Generierung selbst orchestriert ein LLM-Agent (hier: Claude Code) entlang von
`CLAUDE.md` — die Datei ist zugleich Betriebsanleitung und Regelwerk.

## Entstehung

Dieses System wurde KI-gestützt mit Claude Code entwickelt; Konzept, Regeln,
Multi-Modell-Verteilung und Betrieb stammen vom Autor. Es ist damit selbst ein Beispiel
für das Arbeitsprinzip, das es durchsetzt: KI als Kollege — mit klaren Verträgen.

## Lizenz

MIT — siehe [LICENSE](LICENSE).
