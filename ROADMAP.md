# Umsetzungs-Roadmap — Buddensiek Performance

> Reihenfolge & Aufwand für die Umsetzung der `COACHING_SPEC.md`. Aufgeteilt in **MVP (V1) →
> V1.5 → V2**, mit Abhängigkeiten und Zeitschätzung.

_Erstellt: 2026-06-06_

## Schätzbasis (wichtig)

- **PT = fokussierter Entwicklungstag.** Basis-Annahme: **1 erfahrener Entwickler + KI-Unterstützung**
  (z.B. Claude Code). **Anpassung für deinen Stand:** siehe Abschnitt **Erfahrungs-Faktor** unten.
- Zahlen sind **Ranges** — bewusst grob. Sie werden **kurz vor jeder Phase** verfeinert (zusammen mit dem
  Zahlen-Feinschliff der Spec-Details).
- **Kalenderzeit ≠ PT.** Bei ~2–3 produktiven Tagen/Woche entspricht ein 40-PT-Block grob 3–5 Monaten.
- Frontend-Pakete (Vercel) sind aufwändiger und unsicherer geschätzt als Backend-Logik.

---

## Erfahrungs-Faktor — wichtig

Die PT in diesem Dokument gelten für einen **erfahrenen Entwickler** + KI. Für **deinen Stand
(~6 Monate Python, Fitness-Coach) + Claude Code** sind sie unrealistisch niedrig. Ehrliche Faustregeln:

- **Backend-Logik** (Generator, Modelle, Supabase): **×2–3** — die Zeit geht in Debugging, Integration
  und Architektur-Entscheidungen, genau wo Erfahrung zählt.
- **Frontend** (Next.js/React/Vercel, vermutlich Neuland): **×3–4**, das unsicherste Stück.
- **Ramp-up:** die ersten Pakete dauern länger (FastAPI/Pydantic/Supabase lernen), spätere werden
  schneller. KI drückt Richtung unteres Ende, ersetzt aber nicht das Verständnis beim Debuggen.
- Der Faktor gilt **nur für Entwicklung** — das Bibliotheks-Tagging ist Coach-Fachwissen, davon unberührt.

| Phase | Erfahren (Dev) | **Dein Stand (6 Mo. + KI)** |
|---|---|---|
| MVP / V1 | ~30–44 PT | **~75–130 PT** |
| V1.5 | ~29–44 PT | **~85–160 PT** (frontend-lastig) |
| V2 | ~22–34 PT | **~55–100 PT** |

**Empfehlung:** Die zwei härtesten Brocken — **Generator-Rewrite (MVP-3/4)** und **Frontend (V1.5)** —
sind die Stellen, an denen sich ein erfahrener Entwickler an deiner Seite (oder punktuell beauftragt) am
stärksten auszahlt. Der Rest ist gut allein + KI machbar und zugleich eine wertvolle Lern-Investition.

---

## Phasen-Überblick (Basis: erfahrener Dev)

| Phase | Ziel | Aufwand |
|---|---|---|
| **MVP / V1** | Klient füllt Anamnese aus → bekommt einen methodisch korrekten 4-Wochen-Plan (PDF). Einzelblock, keine Interaktivität. | ~30–44 PT Dev + 8–12 Coach (Tagging) |
| **V1.5** | Feedback-Schleife: Logging, Check-in, Block-zu-Block-Progression. Aus dem Generator wird ein Coaching-System. | ~29–44 PT |
| **V2** | Self-Service, Sicherheit, Lernen: Übungstausch, Schmerz-Meldung, Coach-Backoffice, Daten-Kalibrierung. | ~22–34 PT |

→ Für deinen Erfahrungsstand: Spalte **„Dein Stand"** im Abschnitt Erfahrungs-Faktor oben.

---

## MVP / V1 — „Korrekter Einzelplan end-to-end"

**Ziel:** Ein Klient bekommt über das Formular einen vollständig spec-konformen 4-Wochen-Block als PDF,
gespeichert in Supabase. Noch kein Logging, keine Progression, keine App-Interaktivität.

| # | Arbeitspaket | PT | Hängt ab von |
|---|---|---|---|
| 1 | **Daten-Fundament:** Enum/Modelle anpassen (4 Ziele, Longevity statt Ausdauer/Gesundheit; min. 3 Tage; Nebenziel & `schmerzen_akut` raus); Typeform-Felder anpassen + neues Schwachstellen-Fokus-Feld | 2–3 | — |
| 2 | **Übungs-Bibliothek aufbauen & taggen:** bestehende ~150–200 taggen **+ ~75–125 neue Übungen anlegen**, bis **250–300 vollständig getaggte** Übungen mit Mindestabdeckung je Pattern × Skill-Level 1–4 (Felder: `joint_stress`, `impact_level`, `skill_level`, `substitution_pool`, muscle_groups). KI-Entwürfe + Coach-Review. **→ überwiegend Coach-Zeit, nicht Dev-Zeit** | 8–12 (Coach) | — |
| 3 | **Volumen „Modell A"** (`volume_calculator.py` Neubau: Session-Kapazität × Tage, Satz-Caps, Level-Korridor; TJ-Faktor + Tier-Multiplikator raus) | 3–4 | 1 |
| 4 | **Split-Logik je Ziel** (`split_selector.py` Neubau: FB/UL/UL-3×, Fettabbau Kraft+Conditioning, Longevity Kraft+Cardio/Athletik, Pflicht-Patterns, Pattern-Priorität bei Dauer-Konflikt, Push:Pull, Schwachstellen-Tag) | 5–7 | 1, 3 |
| 5 | **Verletzungs- & Equipment-Filter** (2-Stufen: joint_stress + impact_level; Stufe 3 pattern-Blocker am 2026-06-12 gestrichen, siehe STATUS) | 2 | 2 |
| 6 | **Recovery-RPE + Periodisierung** ✅ (3:1-Welle intensitätsgeführt: RPE ankert `rpe_low`→`rpe_high`; Deload = Cap-Unterkante + RPE `rpe_low−1`; RPE-Deckel nach Stress/Schlaf; L1-RIR-Hilfe) | 1–2 | 3 |
| 7 | **Conditioning-Formate** (erweiterter Baukasten: Tabata/Density/For Time/Komplexe/Ladders + Athletik) + **Recomp-Finisher** | 3–4 | 4 |
| 8 | **Plan-Assembler + PDF** an neue Formate/Ziele anpassen; **internes Coach-Kapazitäts-Flag** (`plan_metadata`) | 3–4 | 4, 6, 7 |
| 9 | **Claude-Integration** finalisieren (Übungsauswahl + Cues, Prompt) | 2–3 | 5 |
| 10 | **Supabase** Basis (Tabellen `klienten`, `plaene`) + `db.py` | 2–3 | 1 |
| 11 | **Test-Harness** gegen die finale Spec neu aufbauen (der ursprünglich gestoppte Plan — jetzt sinnvoll, weil die Regeln feststehen) | 3–4 | 3–8 |
| 12 | **Deployment** (Railway, Typeform-Webhook live, PDF-Auslieferung an Klient) + Integration/Puffer | 4–6 | alle |

**Summe MVP: ~30–44 PT Entwicklung** (erfahren; dein Stand ~75–130 PT) **+ ~8–12 PT Coach-Zeit** fürs
Bibliotheks-Tagging (läuft parallel zur Entwicklung).
**Ergebnis:** Funktionierender, methodisch korrekter Plan-Generator. Genug, um mit echten Klienten zu starten
(Coach betreut Progression vorerst manuell).

> **📚 Bibliothek = Daueraufgabe, kein einmaliges Paket.** Die 250–300 getaggten Übungen sind nur der
> MVP-Start — die Bibliothek wächst danach kontinuierlich weiter. **Mindestabdeckung für MVP-Start je
> Pattern:** Horizontal/Vertical Push je 6–8 · Horizontal/Vertical Pull je 6–8 · Squat 10 · Hinge 8 ·
> Single Leg 8 · Core/Carry 10 · Conditioning Bodyweight 15 · Kettlebell-spezifisch 15 · Athletik/Sprünge 10
> — alle Skill-Level 1–4 je Pattern abgedeckt. Für das kontinuierliche Wachstum bekommt das Coach-Backoffice
> ab **V1.5** ein **„Neue Übung anlegen"-Feature** (siehe V1.5).

---

## V1.5 — „Feedback-Schleife & Progression"

**Ziel:** Logging im Block, Check-in am Blockende, automatischer Block-zu-Block-Übergang. Das System
übernimmt die Progression statt des Coaches.

| # | Arbeitspaket | PT | Hängt ab von |
|---|---|---|---|
| 13 | **DB-Tabellen** `exercise_feedback`, `session_feedback` | 1 | MVP-10 |
| 14 | **Trainings-Logging** (Gewicht/Wdh pro Satz erfassen) — Backend + UI | 4–6 | 13 |
| 15 | **Session-Review** (Leicht/Passend/Schwer, Gesamt-Score 1–10, Notiz, Abbruch-Handling) | 2–3 | 14 |
| 16 | **Mini-Anamnese / Check-in-Flow** (Ziel/Equipment/Trainingsjahre-Update, generische Schmerzfrage, Stress/Schlaf) | 3–4 | MVP-1 |
| 17 | **PST-Re-Test-Integration** → Level-Update (±1/Block, Deckel gilt) | 1–2 | MVP-3 |
| 18 | **Block-Übergangs-Generator** (Logs + Re-Test + Check-in → nächster Block; Sätze→Schwierigkeit; Übungs-Rotation Kern/Rest) | 4–6 | 14–17 |
| 19 | **Klient-Dashboard (Vercel):** Plan-Ansicht, Logging-UI, Session-Review | 6–10 | 14, 15 |
| 20 | **Coach-Backoffice Basis** (Kapazitäts-Flags, Plan-/Klient-Übersicht) + Puffer | 3–5 | MVP-8 |
| 20a | **„Neue Übung anlegen"-Feature** im Coach-Backoffice (alle Tag-Felder) — damit die Bibliothek kontinuierlich wachsen kann | 2–3 | 13, MVP-2 |

**Summe V1.5: ~26–40 PT** (+ Puffer ≈ 29–44).
**Ergebnis:** Selbstständige Langzeit-Progression mit Daten-Feedback; Bibliothek wächst über das Backoffice weiter.

---

## V2 — „Self-Service, Sicherheit, Lernen"

**Ziel:** Klient wird autonomer, Sicherheits-Kanäle stehen, das System lernt aus echten Daten.

| # | Arbeitspaket | PT | Hängt ab von |
|---|---|---|---|
| 21 | **Self-Service-Übungstausch** (UI + `exercise_swaps`; Grund-Logik, Scope single/block, 3-Stufen-Filter bei Schmerz, Block-Übergang) | 5–8 | MVP-2/5, V1.5-19 |
| 22 | **Schmerz-Meldung** (`pain_reports` + „Schmerz melden"-Button + Coach-Notification) | 3–4 | V1.5-19/20 |
| 23 | **Coach-Backoffice erweitert** (Tag-Korrektur, Swap-/Schmerz-Notifications, Verlauf) | 3–5 | V1.5-20 |
| 24 | **Daten-Kalibrierung & Lernen** (Log-Schwellen mit echten Daten feinjustieren; Lernen aus Tausch-Mustern) | 3–5 | echte Nutzerdaten |
| 25 | **Puffer / Stabilisierung** | 3–4 | — |

**Summe V2: ~17–26 PT** (+ Puffer ≈ 22–34).

**Separate optionale Module** (eigene Mini-Projekte, nicht in V2-Summe):
- **Mobility-Modul** (dedizierte tägliche Routine): ~5–8 PT
- **Endurance-Modul** (Event-/Lauf-Periodisierung): ~5–8 PT

---

## Abhängigkeits-Kernpfad

```
Daten-Fundament (MVP-1) + Bibliotheks-Tagging (MVP-2)
        ↓
Generator-Logik (MVP-3,4,5,6,7) → Assembler/PDF (MVP-8) → Claude (MVP-9)
        ↓
Supabase (MVP-10) + Test-Harness (MVP-11) → Deploy (MVP-12)   ⟹  MVP fertig
        ↓
Logging + Review (V1.5-14,15) → Block-Übergang (V1.5-18) + Dashboard (V1.5-19)
        ↓
Swap (V2-21) + Schmerz-Meldung (V2-22) + Backoffice (V2-23) + Kalibrierung (V2-24)
```

**Kritisch zuerst:** Bibliotheks-Tagging (MVP-2) blockiert Verletzungs-Logik & Tausch. Generator-Logik
(MVP-3/4) ist der größte und risikoreichste Brocken — hier zuerst Klarheit, dann der Rest.

## Hinweis zum Zahlen-Feinschliff

Die in der Spec geparkten Detailzahlen (Conditioning-Format-Parameter, Pattern-Prioritäts-Reihenfolge,
Log-Schwellen) werden **jeweils zu Beginn des zugehörigen Arbeitspakets** festgelegt — nicht jetzt.

---

## Ideen / später

> Lose Notizen, noch nicht eingeplant. Werden bei Bedarf in ein Arbeitspaket überführt.

- **Körper-Fokus OK/UK-Gewichtung:** Klient wählt einen Schwerpunkt (Oberkörper vs. Unterkörper), der
  die Volumen-/Split-Verteilung gewichtet. Logik gehört in den Generator-Rewrite (MVP-3/4); Spec dafür ist
  **noch offen**. Eigenes Feld, getrennt vom bestehenden `schwachstelle` (Region-Fokus für den
  Schwachstellen-Tag).
- **Output-Pfad-Klärung:** Das **Plan-JSON** ist der eigentliche Output für die Web-App. Das **PDF** ist
  ein Test-/Coach-Tool (Sichtprüfung, Coaching), nicht der primäre Auslieferungsweg. Welche Plan-Teile der
  **Klient** vs. der **Coach** sieht (z.B. internes `plan_metadata` nur für den Coach), regelt das
  Web-App-Backend — nicht der Generator/das PDF.
