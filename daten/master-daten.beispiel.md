# Master-Daten — [NAME] (Single Source of Truth)

**Zweck:** Hier steht ALLES über die Person, vollständig und ehrlich. Aus dieser Datei +
einer Stellenanzeige erzeugt der Generator (`lebenslauf-generator.md`) einen zugeschnittenen
Lebenslauf. Diese Datei wird nie 1:1 zum CV — sie ist der Vorrat, aus dem pro Stelle
ausgewählt wird. **Nur ein Mensch befüllt diese Datei — nie eine KI eigenständig.**
`[…]` = noch zu ergänzen/bestätigen.

---

## 1. Kontakt & Persönliches
- Name: Max Mustermann
- Adresse: Musterstraße 1, 12345 Musterstadt
- Telefon: +49 123 4567890
- E-Mail: max@example.org
- GitHub: https://github.com/beispiel

## 2. Kurzprofil (Bausteine, kein fixer Text)
Kernaussagen, aus denen pro Stelle ein 2–3-Zeilen-Profil gebaut wird:
- [Studiengang/Beruf, Institution]
- [belegbare Kernstärke 1 — z.B. „baut & betreibt eigene Projekte im Dauerbetrieb"]
- [belegbare Kernstärke 2]
- [was gesucht wird — z.B. Werkstudentenstelle]

## 3. Ausbildung
- **[Hochschule — Abschluss — seit MM/JJJJ]**
- **[Schule — Abschluss (Note) — MM/JJJJ – MM/JJJJ]**

## 4. Projekte
### [Projektname — Einzeiler]
- Was: [Was tut das Projekt, für wen, in einem Satz]
- Tech-Stack: [ehrlich: was wurde benutzt]
- Umgesetzt (verifiziert): [nur belegbare Punkte]
- Status: [läuft produktiv? Prototyp? eingestellt?]
- WICHTIG bei KI-generiertem Code: die EIGENE Leistung beschreiben (Konzept, Betrieb,
  Integration) — nicht die Programmiersprache als eigene Kenntnis ausweisen.

## 5. Berufserfahrung
- **[Firma — Position — Ort — MM/JJJJ – MM/JJJJ]**
  - [1–2 sachliche Aufgaben-Bullets]

## 6. Technische Kenntnisse (EHRLICH)
- **[Cluster 1]:** […]
- **[Cluster 2]:** […]
- **NICHT auf den CV** (nicht beherrscht): […] — maschinell geprüfte Fassung in
  `daten/verbotene-begriffe.txt`, Änderungen immer DORT nachziehen.

## 7. Sprachen
- [Sprache — Niveau]

## 8. Interessen
- […]

## 9. Ehrlichkeits-Regeln (gelten für jeden generierten CV)
- Nur, was die Person im Interview 60 Sekunden erklären kann.
- Persönliche Ausschluss-Regeln, z.B.: „[Sprache/Tool X] NICHT als eigene Kenntnis
  ausweisen, weil KI-generiert / nicht selbst beherrscht — auch wenn die Anzeige es verlangt."
- Keine erfundenen Metriken oder Prozentzahlen.
- Keine Tools, die nie selbst benutzt wurden.
