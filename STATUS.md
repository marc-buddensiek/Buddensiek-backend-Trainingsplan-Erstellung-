# Projektstatus — Buddensiek Performance KI-Trainingsplan

_Zuletzt aktualisiert: 2026-06-15 · git HEAD `5171a67` (MVP-7 Naht 1 + 2 fertig) · Branch `mvp-1-data-foundation`_

---

## 1. Aktueller Stand (kurz)

Backend importiert sauber (`import main` ✅). Tests: **Logik 26/26 · Realism 7/7 · RPE-Wellen 5/5 · RIR 3/3 · Conditioning-RPE 2/2 · Format-Baukasten 7/7 · generate_test_plans 17/17** — komplett grün. Achtung Aussagekraft: grün = „läuft/crasht nicht", nicht fachliche Korrektheit (Spec-Validator-Harness = MVP-11).

Spec ist komplett (alle 8 Themen entschieden). Umsetzung läuft entlang der ROADMAP (MVP-1…12).
**Fertig:** MVP-1 + MVP-3-Kern + MVP-2-Kern (Migration `4960c26` + Tagging 125/125 `8980bd7`) + **MVP-4 Split-Logik** (`4ab789c`…`65306a8`) + **MVP-5 Verletzungsfilter** (4 Nähte, `d11ae4a`…`db80429`) + **MVP-6 Recovery-RPE + Periodisierung** (3 Nähte, `82b3c1d`…`798928d`) + **MVP-7 Naht 1 (Schema-Enabler) + Naht 2 (Conditioning-Format-Baukasten, 2a/2b/2c)** (`9536905`…`5171a67`, inkl. Spec-Reconcile Thema 6).
**Offen / nächste große Brocken:** **MVP-7-Rest** — Naht 3 (echte Format-Rotation, ersetzt Trivial-Pick), Naht 4 (Selektor-Umbau auf Conditioning-Pool — braucht getaggte Übungen), Naht 5 (Athletik); dann MVP-8 Coach-Flag + MVP-3-Korridor-Deckel, dann **MVP-9 Claude-Integration finalisieren**; MVP-2-Ausbau auf 250–300 (inkl. ~25 Conditioning + ~10 Athletik) als Coach-Daueraufgabe.
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
| 5 | Equipment/Verletzungs-Filter | ✅ fertig (`db80429`) | 2-Stufen-Filter (joint_stress + impact:high), Mehrfach-Verletzungen (Vereinigung), Leerer-Pool-Fallback (verwandtes Pattern, markiert), substitutions_b entfernt, _VERLETZUNG_BLOCKED/Stufe-3 raus (pattern_tags dormant). Systemische Kontraindikationen bewusst out-of-scope (→ Anamnese/V1.5) | 2 ✓ |
| 6 | Recovery-RPE + Periodisierung | ✅ fertig (`798928d`) | RPE-Welle ankert `rpe_low`→`rpe_high` (0.5-Raster, float; L1/L2 0.5er, L3/L4 1.0er), Deload `rpe_low−1` (Floor 4); toter 0.50-Faktor raus + Spec/CLAUDE.md-Reconcile (Cap-Floor ~67–75 %); L1-RIR `rpe_hinweis` befüllt (nur L1-Kraftsätze, additiv). Volumen bewusst flach (intensitätsgeführt) | 3 ✓ |
| 7 | Conditioning-Formate + Recomp-Finisher | 🟡 Naht 1+2 fertig (`5171a67`), Naht 3/4/5 offen | **Schema-Enabler** (`pattern:"conditioning"` + `conditioning_friendly`, 125 migriert) + **Format-Baukasten** (`logic/conditioning_formats.py`: 7 Formate, emom/for_time raus, Conditioning ohne RPE, Block-Stapelung Tabata/Density, Dauer=session_dauer_min ohne Level-Cap, Fettabbau-Staffelung gemischt+2C, C3-Finisher-Estimate). **Offen:** Naht 3 echte Rotation (Trivial-Pick `TODO(mvp7-formate)`), Naht 4 Selektor-Umbau + Ladders/Komplexe-Dauern, Naht 5 Athletik; Conditioning/Athletik-Übungen net-new (Coach) | 4 ✓ |
| 8 | Assembler/PDF + Coach-Flag | 🟡 Dauer-Kopplung ja, Flag/PDF nein | Modell-A-Satz/Dauer-Kopplung ✓; **Coach-Flag gebaut+verworfen** (plan_metadata=None); PDF rendert **noch** Klient-Realism-Warnung | 4, 6, 7 |
| 9 | Claude-Integration | 🟡 läuft generisch, nicht finalisiert | prompt nutzt hauptziel.value generisch + Ersatz-Pattern-Marker (MVP-5); **nicht** auf neue Bibliotheks-Felder/Pflicht-Patterns aktualisiert. Vorarbeit: Level-Gate als `<=` verifiziert (equipment_filter:73, vor Verletzungsfilter) | 5 ✓ |
| 10 | Supabase | 🟡 Code da, nicht live | db.py: create_client + speichere_klient/_plan; nicht live | 1 |
| 11 | Test-Harness | ❌ offen | run_tests Alt-Stil; neuer Spec-Validator-Harness nicht gebaut | 3–8 |
| 12 | Deployment | ❌ offen | Railway/Typeform-live nicht erfolgt | alle |

**Abhängigkeit (Grep-verifiziert):** 4→1,3 **einseitig** (kein Rückkanal — MVP-1/3-Code zieht nichts aus split_selector; MVP-1/3 bleiben korrekt ohne MVP-4). Korridor-Deckel (MVP-3-Rest) + Coach-Flag (MVP-8) sind **downstream** von MVP-2 **und** MVP-4.

## 4. Offene TODO-Marker (gruppiert nach MVP)

| Marker | Stellen | → MVP |
|---|---|---|
| `TODO(short-session-pattern-drop)` | plan_assembler:371 | MVP-7/8 |
| `TODO(longevity-volume)` | realism_validator:17/33/53, plan_assembler:49 | MVP-3/6 |
| `TODO(mvp7-athletik)` | split_selector:297 | MVP-7 (Naht 5) |
| `TODO(mvp7-formate)` | split_selector:380/390, conditioning_formats:68 | MVP-7 (Naht 3 Rotation, ersetzt Trivial-Pick) |
| `TODO(mvp7-cleanup)` | plan_assembler:149/518, conditioning_formats:95/106 | MVP-7 geparkt (C1/C2/C4 — toter Code/Tests, kein Klienten-Plan) |
| `TODO(v15-schwachstelle)` | models:95, split_selector:313 | V1.5 |
| `TODO(mvp2-schema-stale)` | update_exercises:2 | MVP-2-Tooling |

_Erledigt mit MVP-4: `TODO(ausdauer-rename)`, `TODO(mobility-removal)`. Erledigt 2026-06-12: `TODO(testdata-tage-min3)`. Erledigt mit MVP-5: `TODO(mvp5-substitutions-b-removal)`. Erledigt mit MVP-6: `TODO(deload-faktor-tot)`._

## 5. Test-Stand (verifiziert)

`python3 scripts/run_tests.py` → **Logik 26/26 · Realism 7/7 · RPE-Wellen 5/5 · RIR-Hilfe 3/3 · Conditioning-RPE 2/2 · Format-Baukasten 7/7**, `generate_test_plans.py` → **17/17 PDFs** (Fixture 17 = L4-Fettabbau, zeigt Tabata-Block-Stapelung). Grün heißt weiterhin nur „läuft" — fachliche Korrektheit prüft erst der MVP-11-Harness.

## 6. Session-Historie (neueste zuerst)

**2026-06-14/15 — MVP-7 Naht 1 + 2 (Schema-Enabler + Conditioning-Format-Baukasten, `9536905`…`5171a67`)**
- **Coach-Entscheid Conditioning-Mechanismus (Hybrid):** Gruppe A reine Conditioning-Geräte →
  `pattern:"conditioning"` (leere muscle_groups); Gruppe B Kraft-Pattern + `conditioning_friendly`.
  Dosierung aus dem Slot, kein Dosierungs-Feld. **Naht 1:** Validator + `conditioning_friendly` auf
  alle 125 migriert (idempotent), SCHEMA.md (Pattern 9→10).
- **Spec-Reconcile Thema 6** (`ccce414`/`cb3bc92`): Methodik + finale Format-Parameter. **EMOM +
  Mixed Intervals + For Time gestrichen** (Konfliktregel); aktive Formate (7): Intervall · AMRAP ·
  Zirkel · Tabata · Density · Ladders · Komplexe.
- **Naht 2 (a/b/c):** (a) Conditioning ohne RPE (`HauptUebung.rpe` → Optional); (b) Vokabular final
  (emom/for_time aus Code+Modell); (c) `logic/conditioning_formats.py` — Level→Format-Map +
  Block-Stapelung (Tabata 4-Min-Block, Density 5-Min-Block; n Blöcke füllen die Dauer).
- **Mehrere Coach-Stopps + Korrekturen** (grep-verifiziert, kein Raten): Block-Dauer-**Cap raus**
  → Conditioning-Dauer = `session_dauer_min` (Level steuert nur Format/Work:Rest/skill_level, NICHT
  Dauer; L1/L2/L4 @45 → je ~45). amrap-Notiz auf echte Dauer synchronisiert (C5). **Fettabbau-
  Staffelung** neu: 4/5/6-Tage-Kraft von rein auf **gemischt** (Kraft + amrap-Finisher), reine
  Conditioning fix 2 (4→2+2 · 5→3+2 · 6→4+2), keine reinen Kraft-Tage mehr. **C3:** gemischte Tage
  zählen die Finisher-Minuten intern (MetconBlock ohne eigene Tagesdauer).
- **Abgegrenzt für später:** Übungs-Pull/Selektor-Umbau (Naht 4), echte Rotation (Naht 3,
  `TODO(mvp7-formate)`), Athletik (Naht 5), Ladders/Komplexe-Block-Dauern (Naht 4), `TODO(mvp7-cleanup)`
  (C1/C2/C4). Net-new Conditioning/Athletik-Übungen = Coach-Tagging (Validator bereit).
- Tests durchgehend 26/26 · 7/7 · 5/5 · 3/3 · 2/2 · 7/7 · 17/17 PDFs.

**2026-06-13 — MVP-6 Recovery-RPE + Periodisierung komplett (`82b3c1d`…`798928d`, 3 Nähte)**
- Vorbedingungs-Befund (gestoppt, Coach-Entscheid): Volumen-Welle war platt (W1==Floor==W4 je
  Tier, nur Intensiv-Spike +1). Coach: **kein Bug** — Progression ist intensitätsgeführt, Volumen
  bleibt flach, die Welle läuft über die RPE. Keine Cap-Range-Verbreiterung (out-of-scope/MVP-8).
- Nähte aufsteigenden Risikos: (1) **RPE-Welle neu** — ankert `rpe_low`→`rpe_high`, 0.5-Raster,
  Deload `rpe_low−1` (Floor 4). RPE `int→float` (Frontend-Vertrag; `:g`-Format **nur** im PDF,
  JSON trägt rohen float). 5 neue Wellen-Asserts. (2) **toter 0.50-Deload-Faktor raus** +
  COACHING_SPEC Thema 1/CLAUDE.md per Konfliktregel reconcilet (Cap-Floor ~67–75 % + RPE
  `rpe_low−1` ersetzt die 60-%-Vorgabe, begründet). Kein Verhaltens-Change (Golden). (3)
  **L1-RIR-Hilfe** `rpe_hinweis` — RIR-Klartext nur für Level-1-Kraftsätze, additiv (L1-Metcon +
  Level ≥ 2 bleiben None). 3 neue Asserts.
- Tests durchgehend 26/26 · 7/7 · 5/5 · 3/3 · 16/16. Doku-Nachzug: BACKLOG (MVP-6 fertig +
  MVP-9-Vorarbeit inkl. verifizierter Level-Gate-`<=`-Diagnose), STATUS, ROADMAP-MVP-6-Zeile.

**2026-06-13 — MVP-5 Verletzungsfilter komplett (`d11ae4a`…`db80429`, 4 Nähte)**
- Nähte aufsteigenden Risikos: (1) 2-Stufen-Filter additiv (joint_stress-Vereinigung →
  Mehrfach-Verletzungen automatisch + impact:high), (2) Stufe 3 (`_VERLETZUNG_BLOCKED`)
  gestrichen → Reha-Keeper zurück, (3) substitutions_b abgelöst (verletzungs_flag raus,
  Feld via `migrate_remove_substitutions_b.py` migriert, Werte im substitution_pool
  konserviert), (4) Leerer-Pool-Fallback (`_FALLBACK_PATTERN`, 8 Paare, verwandtes Pattern
  markiert, Sicherheit nie gelockert).
- Coach-reviewt: Fallback-Map (`hinge→single_leg`, kein `core`-Fallback). Sim-verifiziert:
  push_vertical/carry-Leerfälle gefüllt, Safety-Check keine Leaks. `pattern_tags` dormant.
- Tests durchgehend 26/26 · 7/7 · 16/16. Offen aus MVP-5 nur die bewusste Scope-Grenze
  „systemische Kontraindikationen" (→ Anamnese/V1.5, BACKLOG).

**2026-06-12 — Test-Hygiene + MVP-5-Designentscheidung (`3e2f69f`, `cc7310c`, Doku-Commit)**
- Hygiene: alle Testdaten-Altlasten bereinigt → **erstmals komplett grün** (26/26 · 7/7 · 16/16);
  Gym-2T-Duplikat zu Gym/6T/Fettabbau umgewidmet (4K+2C-Pfad abgedeckt).
- **Coach-Entscheidung: Stufe 3 gestrichen** — Kollisions-Analyse zeigte 31 Konflikte mit
  Reha-Keepern, Rest redundant/tot (5 tote Blocker-Tags). Filter wird 2-stufig; ankle-Lücke
  (tiefe Dorsalflexion) per Tagging-Nachtrag geschlossen (12 Übungen, `cc7310c`).
- Validator-Gate als verbindlich für jeden Bibliotheks-Commit in SCHEMA.md verankert;
  Spec Thema 8 per Konfliktregel auf 2-Stufen umformuliert.

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

MVP-7 läuft (Naht 1 + 2 fertig). Reihenfolge innerhalb MVP-7 und danach:
- **MVP-7 Naht 3 — echte Format-Rotation + Equipment-Bevorzugung** (`TODO(mvp7-formate)`): ersetzt
  den trivialen Platzhalter-Pick (erstes Block-Format der Level-Map) durch Rotation (nie 2×
  hintereinander, KB→Komplexe/Density…, BW→Tabata/AMRAP…, zwei verschiedene Formate bei 2 C-Tagen).
- **MVP-7 Naht 4 — Selektor-Umbau** (`conditioning_friendly`/`pattern==conditioning`): Metcon zieht aus
  dem Conditioning-Pool statt Kraft-Pattern; bringt die Ladders/Komplexe-Block-Dauern mit.
  **Braucht getaggte Conditioning-Übungen** (Coach).
- **MVP-7 Naht 5 — Athletik-Rotation** (Longevity, `TODO(mvp7-athletik)`).
- **`TODO(mvp7-cleanup)`** (geparkt): C1/C2/C4 — toter Code/Tests, kein Klienten-Plan.
- **Danach:** MVP-8 Coach-Flag + MVP-3-Korridor-Deckel (baubar: Tagging ✓, Splits ✓), dann **MVP-9
  Claude-Integration finalisieren** (Vorarbeit: Level-Gate als `<=` verifiziert, BACKLOG MVP-9).
**Coach-Daueraufgabe parallel:** MVP-2-Ausbau auf 250–300 — inkl. ~25 Conditioning + ~10 Athletik
(net-new, Validator als Gate, seit Naht 1 bereit) sowie bodyweight push_vertical + carry (senkt MVP-5-Fallback).
