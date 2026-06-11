# Projektstatus — Buddensiek Performance KI-Trainingsplan

_Zuletzt aktualisiert: 2026-06-11 · git HEAD `8980bd7` (MVP-2-Tagging komplett) · Branch `mvp-1-data-foundation`_

---

## 1. Aktueller Stand (kurz)

Backend importiert sauber (`import main` ✅). Tests: **Logik 19/26 · Realism 7/7** — die 7 roten sind ausschließlich veraltete Testdaten + ein nicht-gebautes Feature (MVP-4), **keine Regression** (Belege: Abschnitt 5).

Spec ist komplett (alle 8 Themen entschieden). Umsetzung läuft entlang der ROADMAP (MVP-1…12).
**Fertig:** MVP-1 (Daten-Fundament) + MVP-3-Kern (Volumen „Modell A") + MVP-2-Kern: Schema-Migration (`4960c26`) **und Tagging aller 125** (9 Batches, Coach-reviewt, `8980bd7`).
**Offen / nächste große Brocken:** MVP-4 (Split-Logik) und **MVP-5 (3-Stufen-Filter — jetzt entsperrt)**; MVP-2-Ausbau auf 250–300 als Coach-Daueraufgabe.
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
| 4 | Split-Logik | ❌ offen / nicht begonnen | split_selector:399 ausdauer-Crash, :411 else#gesundheit, :391 Fettabbau 100% Conditioning, **kein longevity-Zweig**, _mobility_session noch da | 1, 3 |
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
| `TODO(ausdauer-rename)` | split_selector:399 (Prod-Crash), run_tests:120 | MVP-4 |
| `TODO(mobility-removal)` | models:262 | MVP-4/8 |
| `TODO(short-session-pattern-drop)` | plan_assembler:440 | MVP-3/4 |
| `TODO(longevity-volume)` | realism_validator:17/33/53, plan_assembler:45 | MVP-3/4/6 |
| `TODO(deload-faktor-tot)` | volume_calculator:31 | MVP-3-Tidy |
| `TODO(testdata-tage-min3)` | run_tests:123/133/168 | MVP-11/Hygiene |

## 5. Test-Stand (verifiziert)

`python3 scripts/run_tests.py` → **Logik 19/26 · Realism 7/7**. Die 7 roten Logik-Tests, eindeutig zugeordnet. **Keine Regression durch den Flag-Rückbau** — Gegentest auf Pre-Rückbau-Stand `06b7aeb` ergab identische 7 (alle scheitern beim Parse oder in split_selector, nicht in volume_calculator):

| Test(s) | Fehler | Ursache |
|---|---|---|
| Kettlebell/3T/Ausdauer · Gym/4T/Ausdauer | ValidationError: hauptziel | totes `ausdauer`-Enum in Testdaten → MVP-4 |
| Bodyweight/5T/Longevity · Gym/4T/Longevity | AttributeError split_selector:399 | longevity-Split nicht gebaut → MVP-4 |
| Travel/2T · Gym/2T · Tim 2×20 | ValidationError: tage_pro_woche | `tage=2 < 3` veraltete Testdaten → tage-min3 |

→ **4× MVP-4, 3× tage-min3.** Keiner „etwas anderes".

## 6. Session-Historie (neueste zuerst)

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

**MVP-4 (Split-Logik-Neubau)** — behebt longevity-Crash + Fettabbau-Struktur, macht 4 der 7 roten Tests grün; hängt nur an MVP-1+3 (beide bereit). **Oder MVP-5 (3-Stufen-Filter)** — durch das fertige Tagging jetzt entsperrt; vorher die Stufe-1-vs-Stufe-3-Spannung entscheiden (BACKLOG MVP-5). Empfehlung: MVP-4 zuerst (größerer Brocken, blockt MVP-7/8-Kette).
**Coach-Daueraufgabe parallel:** MVP-2-Ausbau auf 250–300 Übungen (Mindestabdeckung je Pattern × Level, ROADMAP); neue Übungen direkt nach SCHEMA.md-Semantik taggen, `validate_exercises.py` als Gate.
