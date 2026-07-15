#!/usr/bin/env python3
"""Triage aller Stellenanzeigen in stellenanzeigen/ nach daten/matching-profil.md.

Stufe 0: deterministisches Pattern-Matching (daten/matching-patterns.json) — kostenlos.
Stufe 1: Free-Tier-LLM (OpenAI-kompatible API, Standard: Gemini Flash) — Kategorie A–D.

Nutzung:
  python3 scripts/triage.py               # alles triagieren (Cache: nur Neues/Geändertes)
  python3 scripts/triage.py --nur-scan    # nur Stufe 0, kein API-Aufruf
  python3 scripts/triage.py --limit 3     # nur die ersten 3 (Testlauf)
  python3 scripts/triage.py --force       # Cache ignorieren, alles neu

Konfiguration über .env im Repo-Root (gitignored) oder Umgebungsvariablen:
  TRIAGE_API_KEY   (oder GEMINI_API_KEY / GROQ_API_KEY / OPENROUTER_API_KEY)
  TRIAGE_API_BASE  Standard: https://generativelanguage.googleapis.com/v1beta/openai
  TRIAGE_MODEL     Standard: gemini-3.5-flash
Ergebnis: triage/details/<name>.json + triage/UEBERSICHT.md
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANZEIGEN = ROOT / "stellenanzeigen"
TRIAGE = ROOT / "triage"
DETAILS = TRIAGE / "details"
KAT_ORDNUNG = {"A": 0, "B": 1, "C": 2, "D": 3, "?": 4}
INTERESSE_RANG = {"hoch": 0, "mittel": 1, "gering": 2}  # führende Sortier-Achse (interessen-first)


def slug_von(stem):
    """Kollisionssicherer Dateiname für triage/details/ (Basis + Hash-Suffix)."""
    base = re.sub(r"[^a-z0-9äöüß]+", "-", stem.lower()).strip("-")[:60]
    return f"{base}-{hashlib.sha256(stem.encode('utf-8')).hexdigest()[:6]}"


def lade_env():
    env_datei = ROOT / ".env"
    if env_datei.exists():
        for zeile in env_datei.read_text(encoding="utf-8").splitlines():
            zeile = zeile.strip()
            if zeile and not zeile.startswith("#") and "=" in zeile:
                k, _, v = zeile.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def api_konfig():
    key = (os.environ.get("TRIAGE_API_KEY") or os.environ.get("GEMINI_API_KEY")
           or os.environ.get("GROQ_API_KEY") or os.environ.get("OPENROUTER_API_KEY"))
    base = os.environ.get("TRIAGE_API_BASE",
                          "https://generativelanguage.googleapis.com/v1beta/openai").rstrip("/")
    modell = os.environ.get("TRIAGE_MODEL", "gemini-3.5-flash")
    return key, base, modell


def anzeigen_sammeln():
    dateien, gesehen = [], set()
    for p in sorted(x for x in ANZEIGEN.rglob("*") if x.is_file()):
        if p.name.endswith(":Zone.Identifier"):
            p.unlink()  # Windows-Metadaten-Müll (Mark of the Web) — automatisch entsorgen
            continue
        if p.name == "README.md":
            continue
        if p.name in gesehen:
            print(f"übersprungen (gleicher Dateiname bereits erfasst): {p}")
            continue
        gesehen.add(p.name)
        if p.suffix.lower() in (".md", ".txt"):
            text = p.read_text(encoding="utf-8", errors="replace")
            # Portal-Export-Rauschen entfernen: verlinkte Fremd-Anzeigen ("beliebte Jobs")
            # als Überschriften-Links, die sonst Titel/Urteil des LLM verfälschen.
            text = "\n".join(z for z in text.splitlines()
                             if not re.match(r"\s*#+\s*\[", z)
                             and "bei anderen Jobsuchenden beliebt" not in z)
            dateien.append((p, text))
        elif p.suffix.lower() == ".pdf":
            text = subprocess.run(["pdftotext", str(p), "-"], capture_output=True,
                                  text=True).stdout
            dateien.append((p, text))
    return dateien


def stufe0(text, patterns):
    """Deterministisches Pattern-Matching. Liefert Score + gefundene Signale."""
    t = text.lower()
    signale, score = {}, 0
    for gruppe in ("signale_positiv_stark", "signale_positiv", "signale_negativ",
                   "stunden_abwertung"):
        gewicht = patterns[gruppe]["gewicht"]
        treffer = [m for m in patterns[gruppe]["muster"] if re.search(m, t, re.IGNORECASE)]
        if treffer:
            signale[gruppe] = treffer
            score += gewicht * len(treffer)
    werkstudent = any(re.search(m, t, re.IGNORECASE)
                      for m in patterns["stellenart_erforderlich"]["muster"])
    standort = any(re.search(m, t, re.IGNORECASE) for m in patterns["standort_ok"]["muster"])
    verdacht = [m for m in patterns["knockout_verdacht"]["muster"]
                if re.search(m, t, re.IGNORECASE)]
    return {"score": score, "werkstudent_signal": werkstudent, "standort_signal": standort,
            "knockout_verdacht": verdacht, "signale": signale}


def stufe1(profil, patterns, anzeige_text, key, base, modell):
    """Free-Tier-LLM-Aufruf über OpenAI-kompatible API. Liefert dict oder wirft Exception."""
    system = (profil + "\n\n## Signal-Listen (Wortschatz)\n"
              + json.dumps(patterns, ensure_ascii=False))
    body = json.dumps({
        "model": modell,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": "STELLENANZEIGE:\n\n" + anzeige_text[:15000]},
        ],
    }).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions", data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    for versuch, pause in enumerate((15, 30, 60), start=1):
        try:
            with urllib.request.urlopen(req, timeout=120) as antwort:
                daten = json.loads(antwort.read().decode("utf-8"))
            inhalt = daten["choices"][0]["message"]["content"]
            return json.loads(inhalt[inhalt.index("{"):inhalt.rindex("}") + 1])
        except urllib.error.HTTPError as e:
            if e.code == 429 and versuch < 3:
                print(f"    Rate-Limit (429) — warte {pause}s ...")
                time.sleep(pause)
            else:
                raise
    raise RuntimeError("Rate-Limit nach 3 Versuchen nicht überwunden")


def duplikate_markieren(ergebnisse):
    """Plattformübergreifende Duplikate: gleiche Firma + inhaltlich gleicher Titel.
    Boilerplate (werkstudent, (m/w/d), Portal-Floskeln) wird vor dem Vergleich entfernt,
    damit generische Titel-Bausteine keine False Positives erzeugen. Das erste Vorkommen
    (alphabetisch nach Datei) bleibt Original, der Rest wird markiert."""
    from difflib import SequenceMatcher

    def norm_firma(f):
        f = re.sub(r"\b(gmbh|ag|ug|se|kg|co|holding|ggmbh|mbh|haftungsbeschränkt|"
                   r"haftungsbeschraenkt|e\.v)\b\.?", "", str(f).lower())
        return re.sub(r"[^a-z0-9äöüß]", "", f)

    BOILER = {"werkstudent", "werkstudentin", "werkstudentinnen", "studentenjobs", "teilzeit",
              "homeoffice", "home", "office", "xing", "jobs", "job", "berlin", "in", "für",
              "der", "die", "das", "im", "bereich", "all", "genders", "mwd", "wmd", "mwdx", "d"}

    def titel_tokens(t):
        t = re.sub(r"\((?:all genders|[mwdxf/ -]+)\)", " ", str(t).lower())
        toks = re.findall(r"[a-z0-9äöüß]+", t)
        return [w for w in toks if w not in BOILER and len(w) > 1]

    gesehen = []
    for e in sorted(ergebnisse, key=lambda x: x["datei"]):
        e.pop("duplikat_von", None)
        nf = norm_firma(e.get("firma", ""))
        toks = titel_tokens(e.get("titel", ""))
        if not nf or nf in {"unklar", "?"} or not toks or e.get("kategorie", "?") == "?":
            continue
        s1 = set(toks); j1 = " ".join(toks)
        for gf, gs, gj, ge in gesehen:
            if gf != nf:
                continue
            # Token-Teilmenge (gleiche Rolle, ein Titel ausführlicher) ODER hohe Ähnlichkeit
            if s1 <= gs or gs <= s1 or SequenceMatcher(None, j1, gj).ratio() >= 0.82:
                e["duplikat_von"] = ge["datei"]
                break
        else:
            gesehen.append((nf, s1, j1, e))


def uebersicht_schreiben(ergebnisse):
    zeilen = [
        "# Triage-Übersicht Stellenanzeigen",
        "",
        f"Stand: {date.today().isoformat()} — Profil: `daten/matching-profil.md`",
        "",
        "**Kategorien:** A = bewerben (stark) · B = bewerben (mit Lücken) · "
        "C = Grenzfall (nur bei Kapazität) · D = nicht bewerben · ? = nur Stufe 0 (kein LLM)",
        "",
    ]
    uniq = [e for e in ergebnisse if not e.get("duplikat_von")]
    anz = {k: sum(1 for e in uniq if e.get("kategorie", "?") == k) for k in KAT_ORDNUNG}
    kopf = " · ".join(f"**{k}: {n}**" for k, n in anz.items() if n) or "(keine Anzeigen)"
    if len(ergebnisse) - len(uniq):
        kopf += (f" · **Duplikate: {len(ergebnisse) - len(uniq)}** "
                 "(plattformübergreifend erkannt, ans Tabellenende sortiert)")
    zeilen.append(kopf)
    zeilen += ["", "| Interesse | Kat | Stelle | Firma | Ort/Remote | Score | Lücken / Knock-out | Quelle |",
               "|-----------|-----|--------|-------|------------|-------|--------------------|--------|"]
    for e in sorted(ergebnisse, key=lambda e: (1 if e.get("duplikat_von") else 0,
                                               INTERESSE_RANG.get(e.get("interesse", "mittel"), 1),
                                               KAT_ORDNUNG.get(e.get("kategorie", "?"), 4),
                                               -e.get("stufe0", {}).get("score", 0))):
        ort = e.get("ort", "?")
        if e.get("remote") and e.get("remote") != "unklar":
            ort += f" ({e['remote']}{', INT' if e.get('int_flag') else ''})"
        problem = e.get("knockout") or "; ".join(e.get("luecken", [])) or "—"
        if e.get("duplikat_von"):
            problem = f"DUPLIKAT von `{e['duplikat_von']}`"
        zeilen.append(
            f"| {e.get('interesse', '?')} | {e.get('kategorie', '?')} | {e.get('titel', e['datei'])} "
            f"| {e.get('firma', '?')} | {ort} | {e['stufe0']['score']} "
            f"| {problem} | `{e['datei']}` |")
    zeilen += ["", "Details je Anzeige (Begründung, Signale): `triage/details/*.json`", ""]
    (TRIAGE / "UEBERSICHT.md").write_text("\n".join(zeilen), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nur-scan", action="store_true", help="nur Stufe 0, kein API-Aufruf")
    parser.add_argument("--limit", type=int, default=0, help="max. Anzahl Anzeigen (Testlauf)")
    parser.add_argument("--force", action="store_true", help="Cache ignorieren")
    args = parser.parse_args()

    lade_env()
    key, base, modell = api_konfig()
    profil = (ROOT / "daten" / "matching-profil.md").read_text(encoding="utf-8")
    interessen_pfad = ROOT / "daten" / "interessen-profil.md"
    if interessen_pfad.exists():
        profil += ("\n\n# INTERESSEN-PROFIL (führende Achse — Interesse zuerst!)\n"
                   + interessen_pfad.read_text(encoding="utf-8"))
    patterns_text = (ROOT / "daten" / "matching-patterns.json").read_text(encoding="utf-8")
    patterns = json.loads(patterns_text)
    regeln_hash = hashlib.sha256((profil + patterns_text).encode("utf-8")).hexdigest()
    DETAILS.mkdir(parents=True, exist_ok=True)

    dateien = anzeigen_sammeln()
    if args.limit:
        dateien = dateien[:args.limit]
    if not dateien:
        print("Keine Stellenanzeigen in stellenanzeigen/ gefunden.")
        return 1
    llm_aktiv = bool(key) and not args.nur_scan
    if not llm_aktiv:
        print("HINWEIS: kein API-Schlüssel bzw. --nur-scan — es läuft nur Stufe 0 "
              "(Kategorie bleibt '?').")

    ergebnisse, neu, fehler_429_in_folge = [], 0, 0
    for pfad, text in dateien:
        detail_pfad = DETAILS / f"{slug_von(pfad.stem)}.json"
        checksumme = hashlib.sha256(text.encode("utf-8")).hexdigest()

        alt = None
        if detail_pfad.exists() and not args.force:
            alt = json.loads(detail_pfad.read_text(encoding="utf-8"))
            if (alt.get("checksumme") == checksumme
                    and alt.get("regeln_checksumme") == regeln_hash
                    and (alt.get("kategorie", "?") != "?" or not llm_aktiv)):
                ergebnisse.append(alt)
                continue

        eintrag = {"datei": pfad.name, "checksumme": checksumme,
                   "regeln_checksumme": regeln_hash,
                   "stufe0": stufe0(text, patterns)}
        if llm_aktiv and fehler_429_in_folge < 2:
            print(f"Triage ({modell}): {pfad.name}")
            try:
                eintrag.update(stufe1(profil, patterns, text, key, base, modell))
                fehler_429_in_folge = 0
                time.sleep(float(os.environ.get("TRIAGE_DELAY", "5")))
            except Exception as fehler:
                print(f"    FEHLER Stufe 1: {fehler} — Eintrag bleibt bei Stufe 0.")
                eintrag["stufe1_fehler"] = str(fehler)
                if "429" in str(fehler):
                    fehler_429_in_folge += 1
                    if fehler_429_in_folge >= 2:
                        print("ABBRUCH LLM-Stufe: Kontingent offenbar erschöpft — Rest bleibt "
                              "bei Stufe 0. Später erneut ausführen (Cache überspringt Fertiges).")
        eintrag.setdefault("kategorie", "?")
        detail_pfad.write_text(json.dumps(eintrag, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        ergebnisse.append(eintrag)
        neu += 1

    duplikate_markieren(ergebnisse)
    for e in ergebnisse:
        (DETAILS / f"{slug_von(Path(e['datei']).stem)}.json").write_text(
            json.dumps(e, ensure_ascii=False, indent=2), encoding="utf-8")

    uebersicht_schreiben(ergebnisse)
    dups = sum(1 for e in ergebnisse if e.get("duplikat_von"))
    print(f"\nFertig: {len(ergebnisse)} Anzeigen ({neu} neu/aktualisiert, "
          f"{len(ergebnisse) - neu} aus Cache, {dups} Duplikate) → triage/UEBERSICHT.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
