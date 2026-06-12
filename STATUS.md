# Projektstatus — Buddensiek Performance KI-Trainingsplan

_Zuletzt aktualisiert: 2026-06-11 · git HEAD `65306a8` (MVP-4 fertig) · Branch `mvp-1-data-foundation`_

---

## 1. Aktueller Stand (kurz)

Backend importiert sauber (`import main` ✅). Tests: **Logik 26/26 · Realism 7/7 · generate_test_plans 16/16** — komplett grün seit dem Testdaten-Hygiene-Commit (2026-06-12). Achtung Aussagekraft: grün = „läuft/crasht nicht", nicht fachliche Korrektheit (Spec-Validator-Harness = MVP-11).

Spec ist komplett (alle 8 Themen entschieden). Umsetzung läuft entlang der ROADMAP (MVP-1…12).
**Fertig:** MVP-1 (Daten-Fundament) + MVP-3-Kern (Volumen „Modell A") + MVP-2-Kern (Migration `4960c26` + Tagging 125/125 `8980bd7`) + **MVP-4 Split-Logik** (5 Nähte + Schwachstellen-Streichung, `4ab789c`…`65306a8`).
**Offen / nächste große Brocken:** **MVP-5 (3-Stufen-Filter — entsperrt)**, MVP-7 (Conditioning-Formate — durch MVP-4 entsperrt); MVP-2-Ausbau auf 250–300 als Coach-Daueraufgabe.
Pipeline (Typeform → … → PDF/Supabase) steht strukturell; Claude/Supabase nicht live.

## 2. Spec-Themen (COACHING_SPEC.md)

Alle **8 Themen ✅ entschieden** — Regelseite vollständig, Rückstand rein in der Umsetzung:
1 Periodisierung · 2 Level/PST · 3 Volumen & Intensität · 4 Split-Logik · 5 Recovery · 6 Conditioning/Cardio · 7 Progression (V1) · 8 Sonderfälle.

## 3. MVP-Pakete 1–12 (verifizierter Stand)

| # | Paket | Status | Beleg | Hängt ab von |
|---|---|---|---|---|
| 1 | Daten-Fundament | ✅ fertig | Hauptziel 4 Ziele, tage ge=3, nebenziel/schmerzen_akut raus, schwachstelle, PlanMetadata, rpe_hinweis (models.py) | — |
| 2 | Bibliothek/Tagging | 🟡 125 fertig getaggt, Ausbau offen | Migration `4960c26` + Tagging 125/125 (`8980bd7`, Ausschluss-Semantik SCHEMA.md Abschn. 2, `validate_exercises.py` grün); impact: 118 low · 6 medium (Ballistics) · 1 high (Jump Squat); 38 Reha-Keeper ohne Ausschluss. **Offen: Ausbau auf 250–300 (Coach-Daueraufgabe)** | — |
| 3 | Volumen „Modell A" | 🟡 Kern fertig, Korridor-Deckel offen | _TIER_CAP/_tier_saetze ✓, TJ-Faktor + Tier-Multiplikator raus ✓, Recovery-RPE ✓; **Level-Korridor-Deckel nicht gebaut** (war Naht 3, zurückgerollt) | 1 |
| 4 | Split-Logik | ✅ fertig (`65306a8`) | Longevity-Pfad (Kraft+Zone-2, V1 ohne Athletik → `TODO(mvp7-athletik)`), Fettabbau Kraft+Conditioning, 5T Ganzkörper-Akzent (Schwachstellen-Fokus gestrichen → V1.5), 6T UL3×, Mobility + 20-Min-Sonderfall raus | 1, 3 |
| 5 | Equipment/Verletzungs-Filter | ❌ offen, **entsperrt** | liest `skill_level`; joint_stress/impact_level jetzt vollständig getaggt → 3-Stufen-Filter baubar (Stufe-1-vs-Stufe-3-Spannung beachten, BACKLOG) | 2 ✓ |
| 6 | Recovery-RPE + Periodisierung | 🟡 teilweise | Recovery-RPE ✓, 3:1-Welle ✓; **Deload 60% nicht** (noch 0.50, tot/TODO); **L1-RIR (rpe_hinweis) nicht befüllt** | 3 |
| 7 | Conditioning-Formate + Recomp-Finisher | 🟡 teilweise | _METABOLIC_CONFIG nur amrap/emom/zirkel/intervalle; **tabata/density/for_time/komplexe/ladders + Athletik fehlen**; Recomp-Finisher ✓ | 4 |
| 8 | Assembler/PDF + Coach-Flag | 🟡 Dauer-Kopplung ja, Flag/PDF nein | Modell-A-Satz/Dauer-Kopplung ✓; **Coach-Flag gebaut+verworfen** (plan_metadata=None); PDF rendert **noch** Klient-Realism-Warnung | 4, 6, 7 |
| 9 | Claude-Integration | 🟡 läuft generisch, nicht finalisiert | prompt nutzt hauptziel.value generisch; **nicht** auf neue Bibliotheks-Felder/Pflicht-Patterns aktualisiert | 5 |
| 10 | Supabase | 🟡 Code da, nicht live | db.py: create_client + speichere_klient/_plan; nicht live | 1 |
| 11 | Test-Harness | ❌ offen | run_tests Alt-Stil; neuer Spec-Validator-Harness nicht gebaut | 3–8 |
| 12 | Deployment | ❌ offen | Railway/Typeform-live nicht erfolgt | alle |

**Abhängigkeit (Grep-verifiziert):** 4→1,3 **einseitig** (kein Rückkanal — MVP-1/3-Code zieht nichts aus split_selector; MVP-1/3 bleiben korrekt ohne MVP-4). Korridor-Deckel (MVP-3-Rest) + Coach-Flag (MVP-8) sind **downstream** von MVP-2 **und** MVP-4.

## 4. Offene TODO-Marker (gruppiert nach MVP)

| Marker | Stellen | → MVP |
|---|---|---|
| `TODO(short-session-pattern-drop)` | plan_assembler:366 | MVP-7/8 |
| `TODO(longevity-volume)` | realism_validator:17/33/53, plan_assembler:44 | MVP-3/6 |
| `TODO(deload-faktor-tot)` | volume_calculator:31 | MVP-3-Tidy |
| `TODO(mvp5-substitutions-b-removal)` | equipment_filter:102 | MVP-5 |
| `TODO(mvp7-athletik)` | split_selector:295 | MVP-7 |
| `TODO(mvp7-formate)` | split_selector:378 | MVP-7 |
| `TODO(v15-schwachstelle)` | models:95, split_selector:313 | V1.5 |
| `TODO(mvp2-schema-stale)` | update_exercises:2 | MVP-2-Tooling |

_Erledigt mit MVP-4: `TODO(ausdauer-rename)`, `TODO(mobility-removal)`. Erledigt 2026-06-12: `TODO(testdata-tage-min3)` (Hygiene-Commit, inkl. generate_test_plans-Payloads)._

## 5. Test-Stand (verifiziert)

`python3 scripts/run_tests.py` → **Logik 26/26 · Realism 7/7**, `generate_test_plans.py` → **16/16 PDFs**. Hygiene-Commit 2026-06-12: 3× tage=2 auf tage=3 (Gym-2T-Duplikat → neuer Fall **Gym/6T/Fettabbau**, deckt den 4K+2C-Pfad), 4 generate_test_plans-Payloads auf longevity/tage=3 umgestellt. Grün heißt weiterhin nur „läuft" — fachliche Korrektheit prüft erst der MVP-11-Harness.

## 6. Session-Historie (neueste zuerst)

**2026-06-11 (Fortsetzung 2) — MVP-4 Split-Logik komplett (`4ab789c`…`65306a8`, 7 Commits)**
- 5 Nähte aufsteigenden Risikos: (1) Testdaten ausdauer→longevity inkl. 6T-Abdeckung, (2) Longevity-Pfad
  ersetzt tote ausdauer/gesundheit-Zweige (3T FB · 4T 3K+1Z2 · 5T 3K+2Z2 · 6T UL4×+2Z2; `session_typ=zone2`),
  (3) Fettabbau Kraft+Conditioning (3T FB+Metcon-Akzente · 4T 3K+1C · 5T UL+1C · 6T UL+2C),
  (4) 5T-Tag + 6T UL3× statt PPL, (5) Toter-Code-Abbau (Mobility komplett, 20-Min-Sonderfall,
  `"mobility"`-Literal; assembler −130 Zeilen Hardcode).
- **Coach-Entscheidung zwischen Naht 4 und 5:** Schwachstellen-Fokus-Tag **gestrichen** (`527e26d`) —
  5T = Ganzkörper-Akzent (FB-C); Fokus-Templates liegen in `a88943c`, V1.5-Idee im BACKLOG,
  `schwachstelle`-Feld dormant.
- V1-Abweichungen per Konfliktregel in der Spec vermerkt: Zone-2-only (`TODO(mvp7-athletik)`),
  Format-Statik (`TODO(mvp7-formate)`). Abnahme-Kriterium erfüllt: 4 Ziel-Tests grün, 3 tage=2 bleiben,
  keine neuen Failures; generate_test_plans 12/16 wie vor MVP-4.

**2026-06-11 (Fortsetzung) — MVP-2 Tagging komplett: 125/125 (`d662852`…`8980bd7`)**
- Tagging-Semantik in SCHEMA.md festgezurrt (joint_stress = Ausschluss-Tag, impact = Stoßbelastung,
  Fertig-Marker impact_level != null) + `scripts/validate_exercises.py` als Dauervalidierung (`d662852`).
- 9 Pattern-Batches je als KI-Entwurf (Seed: substitutions_b-Keys + Ersatzziel-Analyse) mit
  Coach-Review im Chat; 2 Coach-Korrekturen (Close Grip Bench shoulder bleibt, Seitheben shoulder rein).
  Kern-Heuristiken: subs_b-**Ersatzziele** nicht für ihre Region taggen (Reha-Keeper, 38 Übungen leer),
  relative Ersatz-Ketten ≠ sicher (Ballistics trotzdem getaggt), McGill/Reha-Übungen per Design leer.
- Ergebnis: impact 118 low · 6 medium · 1 high; joint_stress shoulder 44 · wrist 34 · spine 31 ·
  hip 24 · elbow 24 · knee 23 · neck 1 · ankle 1. Pool je Verletzung 81–124 von 125.
- Beifang: BACKLOG-Tag-Bug Single-Leg-RDL widerlegt (`2395b10`); MVP-5-Befund Stufe-1-vs-Stufe-3
  notiert (`04421a5`). Tests durchgehend unverändert 19/26 · 7/7.

**2026-06-11 — MVP-2 Schema-Migration (`4960c26`)**
- `scripts/migrate_schema_mvp2.py` (idempotent, Backup `.bak`, Verifikation vor dem Schreiben):
  `level_min`→`skill_level` · `substitution_pool` = dedup(subs_a + subs_b.values()) · `substitutions_a`
  raus (0 Leser) · `substitutions_b` bleibt bis MVP-5 (`TODO(mvp5-substitutions-b-removal)`,
  equipment_filter) · `joint_stress=[]` / `impact_level=null` (= bewusst ungetaggt, NICHT "low") /
  `equipment_requires=[]` neu auf allen 125.
- Konsumenten mitgezogen: `equipment_filter:91` + `prompt_template:256` lesen `skill_level`.
  `update_exercises.py` als schema-stale markiert (`TODO(mvp2-schema-stale)`).
- Tests unverändert: Logik 19/26 · Realism 7/7 (dieselben bekannten 7 Roten — keine Regression).

**2026-06-09/10 — Modell A (MVP-3-Kern) + Coach-Flag-Rückbau (MVP-8 out-of-order)**
- Modell A gebaut: Naht 1 Tier-Satz-Caps statt Wochenvolumen÷Frequenz (`277e396`), Naht 2a flaches Zeit-Modell (`493d2eb`), Naht 2b Dauer-Trim „Dauer gewinnt" inkl. Cardio (`06b7aeb`). Davor: Recovery→RPE-Tiers (`2b54d98`), Trainingsjahre-Faktor raus (`8150666`), Spec-Thema-3-Zeitparameter (`e2ab9b8`), Korridor-Werte + Test-Renames (`d8cd1f3`/`1730d3b`/`a854ee3`).
- Coach-Flag (MVP-8) gebaut → **Doppelzähl-Bug** (Sub-Label-Mehrfachzählung) + **Tagging-/Skalen-Problem** (glutes/quads zu breit primary getaggt; echte Wochen-Sätze ≫ alter frequenz-geteilter Korridor) gefunden. Recherche: Korridor (12–16) **und** Zählmethode (primary 1,0 / secondary 0,5) sind fachlich korrekt — **Wurzel ist das Tagging**.
- Entscheidung: Flag **komplett verworfen** statt Tagging jetzt zu fixen → 2 Cleanup-Commits (`408c079` budget_saetze raus, `19f8d5f` _WOCHEN_VOLUMEN raus). **Erkenntnis: MVP-8 war out-of-order** (hängt an ungebautem MVP-2 + MVP-3-Deckel + MVP-4). `PlanMetadata` bleibt leerer `Optional=None`-Platzhalter. Reihenfolge auf Roadmap-Kernpfad zurückgesetzt.

**2026-06-07 — MVP-1 Daten-Fundament**
- Hauptziel auf 4 Ziele (longevity statt ausdauer+gesundheit), tage_pro_woche ge=3, nebenziel + schmerzen_akut entfernt, schwachstelle-Feld ergänzt, session_typ/MetconBlock-Literale additiv erweitert, HauptUebung.rpe_hinweis + PlanMetadata-Submodell. Spec/Roadmap/CODE_CHANGES angelegt.

**2026-06-02 — Pre-Spec-Fixes**
- `ist_mobility`/`metcon_blk`-Initialisierung in plan_assembler (NameError-Risiko), MetconBlock-Rendering im PDF (CONDITIONING-FINISHER-Block), CLAUDE.md erstellt.

## 7. Nächster Schritt

**MVP-5 (3-Stufen-Verletzungsfilter)** — vollständig entsperrt (Tagging ✓): joint_stress → impact_level:high → pattern-Blocker; **vorher die Stufe-1-vs-Stufe-3-Designfrage entscheiden** (BACKLOG MVP-5) und Mehrfach-Verletzungen + Leerer-Pool-Fallback mitbauen. Quick-Win davor: Hygiene-Commit Testdaten (3× tage-min3 in run_tests + 4 Parse-Altlasten in generate_test_plans).
**Coach-Daueraufgabe parallel:** MVP-2-Ausbau auf 250–300 Übungen (`validate_exercises.py` als Gate); ab MVP-7 zusätzlich ~25 Athletik-/Conditioning-Übungen (entsperrt `TODO(mvp7-athletik/formate)`).
