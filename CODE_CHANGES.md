# Code-Änderungs-Übersicht — Buddensiek Performance

> Was sich pro Datei ändert, um die `COACHING_SPEC.md` umzusetzen. Lese-Begleiter beim Coden.
> Phasen-Tags verweisen auf die `ROADMAP.md` (MVP / V1.5 / V2).

_Erstellt: 2026-06-06_

**Legende:** 🟢 bleibt · 🔧 Umbau · ➕ neu · 🔴 entfällt · Phase: `[MVP]` `[V1.5]` `[V2]`

> ⚠️ **Reihenfolge beim Coden:** Erst `models.py` + `data/exercises.json` (das Fundament), dann
> `volume_calculator` → `split_selector` → `equipment_filter` → `plan_assembler` → `pdf_generator`,
> dann Claude + `db.py` + Harness. Genau die Abhängigkeitskette aus der Roadmap.

---

## `models.py` `[MVP]`

- 🔧 **`Hauptziel`-Enum:** `ausdauer` + `gesundheit` raus, `longevity` rein → `muskelaufbau · fettabbau ·
  recomp · longevity`.
- 🔧 **`KlientenInput.tage_pro_woche`:** `ge=2` → `ge=3`.
- 🔴 **`KlientenInput.nebenziel`** entfernen (+ den `nebenziel_nicht_gleich_hauptziel`-Validator).
  _Korrektur (MVP-1 umgesetzt):_ betrifft zusätzlich `claude/prompt_template.py` und
  `scripts/test_pipeline.py` (Anzeige-Zeilen `klient.nebenziel`, sonst Laufzeit-`AttributeError`) —
  also nicht nur `models.py` + `parsers.py`.
- 🔴 **`KlientenInput.schmerzen_akut`** entfernen (+ `parse_bool_from_typeform`-Validator) → wird zur
  Dashboard-Schmerz-Meldung `[V2]`.
- ➕ **`KlientenInput.schwachstelle`** (optional): `Literal["arme","brust","ruecken","schultern","beine"]`
  — Fokus für den Schwachstellen-Tag (5-Tage-Muskelaufbau/Recomp).
- 🔧 **`Session.session_typ`-Literal:** Conditioning-Typen erweitern um
  `tabata, density, for_time, komplexe, ladders`; `zone2`, `athletik` ergänzen (Longevity).
  _Korrektur (MVP-1 umgesetzt):_ `mobility` **NICHT** im Daten-Fundament entfernen — es hat einen live
  Produzenten (`split_selector._mobility_session` → `plan_assembler` → `Session`), das Entfernen aus dem
  Literal bräche den Plan-Bau (5/6-Tage Muskelaufbau/Recomp). Bleibt mit `# TODO(mobility-removal)`;
  Entfernung gebündelt mit dem **Split-/Assembler-Rewrite (MVP-4/8)**, wo der Produzent stirbt.
  In MVP-1 nur additiv erweitert.
- 🔧 **`MetconBlock.typ`-Literal:** analog erweitern (Tabata/Density/For Time/Komplexe/Ladders).
- ➕ **`HauptUebung.rpe_hinweis`** (optional `str`): RIR-Klartext für Level 1 (Thema 3).
- ➕ **`Plan.plan_metadata`** (oder eigenes Sub-Modell): `volume_below_optimal: bool`,
  `recommended_extra_days: int`, `recommended_extra_minutes: int` — internes Coach-Flag (Thema 3).
- 🟢 **`Woche`, `KlientenSnapshot`, Warm-/Cool-Down-Modelle** im Kern unverändert (Snapshot ggf. ohne
  Nebenziel/`schmerzen_akut`).
- 🟢 **`ClaudeOutput`/`UebungAuswahl`** bleiben; ID-Validierung gegen `exercises.json` bleibt.

## `data/exercises.json` `[MVP]` — Coach-Datenarbeit

- 🔧 **Schema-Migration je Übung** _(✅ umgesetzt 2026-06-11, `scripts/migrate_schema_mvp2.py`)_:
  `level_min` → `skill_level`; neue Felder `joint_stress` (Liste), `impact_level` (low/medium/high),
  `substitution_pool` (Liste); `muscle_groups` bleibt **verschachtelt** (`{primary: [], secondary: []}`,
  entschieden — siehe SCHEMA.md).
- ➕ **Ausbau auf 250–300 Übungen** mit Mindestabdeckung je Pattern × Skill-Level (siehe ROADMAP).
- 🟢 Bestehende Felder `id, name, pattern, equipment, coaching_cues, progressions_up/down` bleiben.
- _Hinweis:_ überwiegend Coach-Zeit; ab `[V1.5]` über das „Neue Übung anlegen"-Backoffice pflegbar.

---

## `logic/level_calculator.py` `[MVP]` / `[V1.5]`

- 🟢 **Kern bleibt 1:1** (PST-Punkte, Summen-Schwellen, Trainingsjahre-Deckel = Spec Thema 2).
- 🔧 Nur Feld-Rename mitziehen: liest künftig `skill_level` statt `level_min` (falls hier referenziert).
- ➕ `[V1.5]` Funktion für **Re-Test-Level mit ±1-Klammer pro Block** (Detraining möglich), Deckel gilt
  weiter — gehört zum Block-Übergangs-Generator.

## `logic/volume_calculator.py` `[MVP]` — **größter Umbau**

- 🔧 **Komplett neu: „Modell A".** Von „Wochenvolumen ÷ Frequenz" → „Session-Kapazität (Dauer + Satz-Caps)
  × Tage, gedeckelt durch Level-Korridor".
- 🔴 **`_TRAININGSJAHRE_MODIFIER`** entfernen (Thema 3 gestrichen).
- 🔴 **`_SLOT_TIER_MULTIPLIKATOR`** entfernen → ersetzt durch **Satz-Caps je Tier** (compound 3–4,
  accessory/iso/core 2–3, hart max 4).
- 🔧 **`_WOCHEN_VOLUMEN`** → wird zur **Obergrenze/Korridor** (neue Zahlen je Spec, Fettabbau angepasst),
  nicht mehr Fixwert.
- 🔧 **`_PERIODISIERUNG_FAKTOR["deload"]`** `0.50` → `0.60`.
- 🔧 **`_recovery_modifier`** komplett neu: **nur RPE** (Volumen unberührt!), zweistufig
  (Stress ≥ 8 / Schlaf ≤ 5 → unteres Spannen-Ende; Stress ≥ 9 / Schlaf ≤ 4 → −1; gute Recovery → oberes
  Ende), RPE-Floor 4. Zusammenspiel mit der Welle: Welle = Basis, Recovery = Deckel/Freigabe.
- 🟢 `_RPE_RANGES` je Level bleiben; ➕ **L1-RIR-Hinweis** erzeugen.

## `logic/split_selector.py` `[MVP]` — **zweitgrößter Umbau**

- 🔧 **4-Ziel-Mapping neu** (Thema 4). `ausdauer`/`gesundheit`-Zweige raus → **Longevity**.
- 🔧 **Fettabbau** = Kraft + Conditioning (3T FB+Akzente · 4T 3+1 · 5T 4+1 · 6T 4+2) — **nicht** mehr
  100 % Conditioning. `_FETTABBAU_TYPEN`/`_conditioning_session` umbauen.
- ➕ **Longevity-Pfad** (Kraft + Cardio/Athletik-Tage, alternierend).
- ➕ **Ganzkörper-Akzent-Tag** (5-Tage-Muskel/Recomp). _Schwachstellen-Fokus gestrichen
  (2026-06-11) → V1.5-Idee (BACKLOG), `schwachstelle`-Feld dormant._
- 🔧 **6 Tage = Upper/Lower 3×** (jeder Muskel 3×); PPL-Logik raus.
- 🔴 **Mobility-Sessions** raus (`_mobility_session`, `mit_mobility`) — eigenes Modul später.
- 🔴 **20-Min-Sonderfall / 2-Tage** raus (min. 3 Tage).
- ➕ **Pflicht-Patterns je Session-Typ** durchsetzen (Upper/Lower/Full Body) + **Pattern-Priorität**, wenn
  die Dauer nicht für alle reicht (Dauer gewinnt). Push:Pull-Balance ≥ 1:1, ideal 1:1,2.

## `logic/equipment_filter.py` `[MVP]`

- 🔧 **Verletzungs-Filter → 3-Stufen** (Thema 8): `joint_stress` (== Verletzung) **+** `impact_level:high`
  **+** pattern-spezifische Blocker. `_VERLETZUNG_BLOCKED` bleibt als Stufe 3.
- 🔧 **Level-Check** liest `skill_level` statt `level_min`.
- 🔧 `substitutions_b` → durch `substitution_pool` ersetzen/ergänzen.
- 🟢 `_EQUIPMENT_INCLUDES` (Equipment-Pfade) + `_VERLETZUNG_MAP` (de→en) bleiben.

## `logic/plan_assembler.py` `[MVP]`

- 🔧 **`_METABOLIC_CONFIG`** um neue Formate erweitern (Tabata, Density, For Time, Komplexe, Ladders).
- 🔧 **Recomp-Finisher neu** (`_build_metcon_block`): **globales Bodyweight**-Conditioning (5–10 Min,
  RPE 6–7, equipment-unabhängig, globale Bewegungen statt Haupt-Pattern der Session), Format rotiert.
- ➕ **Longevity-Sessions** (Zone-2 / Athletik) bauen.
- 🔴 **Mobility-Builder** raus (`_mobility_haupt_uebungen`, `_mobility_warm_up`, `_mobility_cool_down`).
- 🔧 **Satz-/Dauer-Logik** an Modell A koppeln (Sätze kommen aus volume_calculator; Session passt per
  Konstruktion in die Dauer — der alte Überlauf entfällt).
- 🔧 **`_WDH_MAP`**: `ausdauer`/`gesundheit` raus, `longevity` rein.
- ➕ **`plan_metadata`** füllen (Kapazitäts-Flag, mit `realism_validator`).
- ➕ **L1-RPE-Hinweis** in die Übung schreiben.
- 🟢 PST-Re-Test-Platzierung (Woche 4, letzte Kraft-Session) bleibt — passt jetzt auch für Fettabbau.

## `parsers.py` `[MVP]`

- 🔴 `nebenziel`- und `schmerzen_akut`-Parsing raus.
- ➕ `schwachstelle`-Parsing rein.
- 🔧 `hauptziel`-Mapping auf neues Enum (Longevity-Label); `tage_pro_woche` min. 3.
- 🟢 Übrige Feld-Logik (choice.ref/label, verletzungen) bleibt.

## `pdf_generator.py` `[MVP]`

- ➕ Rendering für **neue Conditioning-Formate** + **Longevity Zone-2/Athletik**-Sessions.
- 🟢 **CONDITIONING-FINISHER**-Block existiert schon — an neuen Recomp-Finisher anpassen.
- 🔴 **Mobility-Rendering** raus.
- 🔴 **Realism-Warntext im Klient-PDF** raus (wird internes Coach-Flag, nicht sichtbar für Klient).
- ➕ **L1-RPE-Hinweis** anzeigen.

## `realism_validator.py` `[MVP]` — Zweckwechsel

- 🔧 **Wird internes Coach-Flag** statt Klient-Text: liefert `plan_metadata`
  (`volume_below_optimal`, `recommended_extra_days/minutes`), kein PDF-Text mehr.
- 🔧 Schwellen-Logik an **Modell-A-Korridor** koppeln (erreicht der Plan den Korridor?).
- 🔴 `_WARNUNGEN` / `_HINWEISE` (Klient-Texte) raus.
- _Optional umbenennen_ → `capacity_flag.py`.

## `claude/claude_client.py` + `prompt_template.py` `[MVP]`

- 🟢 Struktur bleibt (gefilterte Liste rein → exercise_ids + Cues raus).
- 🔧 **Prompt aktualisieren:** 4 Ziele, neue Bibliotheks-Felder, Pflicht-Patterns je Session, Hinweis auf
  bereits gefilterte (verletzungs-/equipment-sichere) Liste.

## `db.py` `[MVP]` → wächst in `[V1.5]`/`[V2]`

- 🔧 `[MVP]` `klienten` + `plaene` schreiben, inkl. `plan_metadata`.
- ➕ `[V1.5]` Writes/Reads für `exercise_feedback`, `session_feedback`.
- ➕ `[V2]` `exercise_swaps`, `pain_reports`.

## `main.py` `[MVP]` → wächst später

- 🟢 `POST /api/new-plan`, `GET /health` bleiben (Payload ans neue Modell anpassen).
- ➕ `[V1.5]` Endpoints: Logging, Session-Review, Check-in/Mini-Anamnese, Block-Übergang.
- ➕ `[V2]` Endpoints: Übungstausch, Schmerz-Meldung.

## `scripts/` `[MVP]`

- 🔧 `run_tests.py` + `generate_test_plans.py`: an neue Enums/Struktur/`make_payload` anpassen.
- ➕ **Test-Harness** (Plan-Validator) gegen die finale Spec neu — der ursprünglich gestoppte Plan.
- 🟢 `update_exercises.py`: als Basis fürs Bibliotheks-Tagging/„Neue Übung"-Tooling nutzbar.

---

## Neue Supabase-Tabellen

| Tabelle | Phase | Felder |
|---|---|---|
| `klienten` | MVP | (bestehend) Stammdaten aus Anamnese |
| `plaene` | MVP | (bestehend) Plan-JSON **+ `plan_metadata`** (`volume_below_optimal`, `recommended_extra_days`, `recommended_extra_minutes`) |
| `exercise_feedback` | V1.5 | `client_id, session_id, exercise_name, difficulty_rating (leicht/passend/schwer)` |
| `session_feedback` | V1.5 | `client_id, session_id, difficulty_score (1–10), notes, completed_at` |
| `exercise_swaps` | V2 | `client_id, block_number, session_id, exercise_swapped_out, exercise_swapped_in, reason, scope (single_session/entire_block), swapped_at, active (bool)` |
| `pain_reports` | V2 | `client_id, report_date, body_part, description, status (open/coach_acknowledged/resolved)` |

_(Plus später Tabellen/Spalten für Block-Nummern, Re-Test-Ergebnisse und aktualisierte Trainingsjahre,
sobald der Block-Übergangs-Generator `[V1.5]` steht.)_

---

## Was komplett unverändert bleibt

`logic/level_calculator.py` (Kern), `data/fake_typeform.json`-Prinzip, Warm-/Cool-Down-Bausteine im
Assembler, das Grund-Gerüst von `main.py`. Der Rest ist Umbau oder Erweiterung wie oben.
