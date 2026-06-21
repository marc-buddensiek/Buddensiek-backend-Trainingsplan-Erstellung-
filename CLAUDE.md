# Buddensiek Performance — Backend

## Tech-Stack

| Schicht | Technologie |
|---|---|
| API | FastAPI + Pydantic v2 |
| Hosting | Railway (render.yaml) |
| KI | Anthropic Claude API (claude/) |
| Datenbank | Supabase (PostgreSQL) |
| Frontend | Vercel (separates Repo) |
| PDF | fpdf2 |

## Ordnerstruktur

```
buddensiek-backend/
├── main.py                    # FastAPI App — POST /api/new-plan, GET /health
├── models.py                  # Alle Pydantic-Modelle (KlientenInput, Plan, ...)
├── parsers.py                 # Typeform-Webhook → KlientenInput
├── pdf_generator.py           # Plan-Dict → PDF (fpdf2)
├── realism_validator.py       # Prüft Wochenzeit vs. Ziel-Schwellen
├── db.py                      # Supabase-Writes
│
├── logic/
│   ├── level_calculator.py    # PST-Punkte + Trainingsjahre → Level 1–4
│   ├── volume_calculator.py   # Level + Wochentyp → Sätze/RPE/Stufe
│   ├── split_selector.py      # Ziel + Tage + Dauer → Split-Template
│   ├── equipment_filter.py    # exercises.json × Equipment/Level/Verletzungen
│   └── plan_assembler.py      # Alle Parameter + ClaudeOutput → Plan
│
├── claude/
│   ├── claude_client.py       # API-Call: gefilterte Übungen → ClaudeOutput
│   └── prompt_template.py     # System- + User-Prompt-Builder
│
├── data/
│   ├── exercises.json         # Übungs-Stammdaten (ID, Pattern, Equipment, Cues)
│   ├── fake_typeform.json     # Test-Payload (Standard-Klient)
│   ├── fake_recomp.json       # Test-Payload (Recomp)
│   └── plan_schema_example.json
│
└── scripts/
    ├── run_tests.py           # Logik-Tests ohne API (33 Tests)
    ├── generate_test_plans.py # 16 Test-PDFs ohne API
    ├── generate_plan.py       # Einzel-Plan mit echter Claude API
    ├── test_pipeline.py       # End-to-End-Test mit Claude API
    └── update_exercises.py    # exercises.json Hilfsskript
```

## Befehle

```bash
# Logik-Tests (kein API-Key nötig) — 26 + 7 Tests
python3 scripts/run_tests.py

# 16 Test-PDFs für alle Pipeline-Pfade generieren (kein API-Key nötig)
python3 scripts/generate_test_plans.py
# Output: output/test_plans/*.pdf

# Dev-Server starten
uvicorn main:app --reload

# Einzel-Plan mit Claude API generieren
python3 scripts/generate_plan.py
```

## Pipeline (7 Schritte)

```
Typeform-Webhook
  → parsers.py          (field.ref → KlientenInput)
  → level_calculator    (PST + Trainingsjahre → Level 1–4)
  → split_selector      (Ziel × Tage × Dauer → Sessions + Slots)
  → equipment_filter    (exercises.json → gefilterte Übungen je Pattern)
  → claude_client       (gefilterte Übungen → exercise_ids + Notizen)
  → plan_assembler      (alle Parameter → vollständiger Plan)
  → db.py + PDF         (Supabase + PDF-Generierung)
```

## Coaching-Konventionen

**Level 1–4** — bestimmt durch PST-Punkte (kniebeugen/pushups/situps/burpees/plank) + Trainingsjahre-Cap.

**Session-Slots nach Dauer:**
- 20 min → 3 Slots, 30 min → 4, 45 min → 5, 60 min → 6

**Slot-Tiers:** compound > accessory > isolation > core
- Pausenzeit: compound 180s, accessory 90s, isolation 60s, core 45s

**Periodisierung (3:1-Welle, intensitätsgeführt):** Volumen folgt Modell A v2 (Sätze ~flach + Mike-Rampe);
die Progression läuft über die **RPE**. Die RPE-Welle ist **ziel-abhängig** (`_ZIEL_RPE_WELLE[ziel][woche]`)
und **level-gedeckelt** (`_LEVEL_CAP`):

| Ziel | W1 | W2 | W3 | W4 Deload |
|---|---|---|---|---|
| muskelaufbau | 7 | 8 | 9 | 6 |
| recomp | 7 | 8 | 8 | 6 |
| fettabbau | 7 | 7 | 8 | 6 |
| longevity | 6 | 7 | 7 | 5 |

`_LEVEL_CAP` (Obergrenze je Level): L1 7 · L2 8 · L3 9 · L4 9; Floor 4. Tier-Offset: compound 0 ·
accessory −1 · isolation −2 · core 0. Deload (W4) = W4-Spalte der Welle. Kundenseitig wird
**RIR = 10 − RPE** ausgegeben (intern RPE); Zeit-Holds tragen kein RIR. Konvention: COACHING_SPEC Thema 3.

**Ziel → Session-Format:**
- `muskelaufbau` / `ausdauer` / `gesundheit` — klassisch Sätze × Wdh
- `recomp` — Kraft-Block (Sätze × Wdh) + MetconBlock-Finisher (AMRAP/EMOM)
- `fettabbau` — nur Conditioning: intervalle / amrap / zirkel / emom (rotierend)

**Recovery (Stress/Schlaf):** wirkt NICHT auf Trainingsparameter — `stress_level`/`schlaf_stunden` sind rein informativ (`recovery_modifier` im Snapshot), steuern weder RPE noch Volumen (entkoppelt 2026-06-21; Autoregulation → BACKLOG).

**Verletzungen:** exercises.json `avoid_if_injury` und `substitutions_b` steuern Ausschluss und Ersatz.

**PST Re-Test:** Immer in der letzten Kraft-Session der Deload-Woche (Woche 4).

## Enums (exakt wie Typeform-Labels)

```python
Hauptziel:     muskelaufbau | fettabbau | recomp | ausdauer | gesundheit
Equipment:     gym | home_gym | kettlebell | bodyweight | travel | hybrid
Trainingsjahre: keine | unter_1 | ein_bis_zwei | drei_bis_fuenf | fuenf_plus
```
