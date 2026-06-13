# Übungs-Bibliothek — Schema-Spezifikation (`data/exercises.json`)

_Stand: 2026-06-10 · abgenickt · verbindliche Referenz für MVP-2 (Migration + Tagging)_

> Quelle: COACHING_SPEC.md Thema 8 + Code-verifizierte Konsumenten-Analyse.
> Konfliktregel: siehe Abschnitt 3 → COACHING_SPEC.md „Arbeitsregel: Spec-vs-Code-Konflikte".

---

## 1. Feld-Tabelle

| Feld | Typ | Erlaubte Werte | Konsument (wo) | Aktion |
|---|---|---|---|---|
| `id` | str | unique | ex_by_id-Key, Claude-Matching | behalten |
| `name` | str | — | PDF/Plan | behalten |
| `pattern` | str | die 9 unten (+2 neu, MVP-2-Ausbau) | equipment_filter:108, plan_assembler:513, Split | behalten |
| `equipment` | list[str] | gym · home_gym · kettlebell · bodyweight · travel · hybrid | equipment_filter:88 | behalten |
| `skill_level` | int | 1–4 | Level-Gate (equipment_filter:91) | **migrieren** (`level_min`→`skill_level`) |
| `muscle_groups` | obj `{primary:[], secondary:[]}` | bestehendes Muskel-Vokabular (nested belassen) | Volumen-Korridor (MVP-3, **geplant**) | behalten |
| `joint_stress` | list[str] | die 8 unten (englisch) | Verletzungsfilter Stufe 1 (MVP-5) | ✅ getaggt (125/125 + ankle-Nachtrag) |
| `impact_level` | str | low · medium · high | Verletzungsfilter Stufe 2 (MVP-5) | ✅ getaggt (125/125) |
| `pattern_tags` | list[str] | offen (deep_squat, lunge, jump, overhead_press, bench_heavy, …) | **0 Leser** — ehem. Stufe 3, Blocker entfernt (MVP-5 Naht 2) | **dormant behalten** (Coach-Wissen, entschieden 2026-06-12) |
| `substitution_pool` | list[str] | exercise-IDs | Tausch (V2) + Verletzungs-Alternativen | **NEU** (= dedup(subs_a ∪ subs_b.values())) |
| ~~`substitutions_b`~~ | — | — | 0 Leser — verletzungs_flag durch 2-Stufen-Filter abgelöst | **entfernt (MVP-5 Naht 3)**, Werte im `substitution_pool` konserviert |
| `substitutions_a` | list[str] | exercise-IDs | 0 Leser | entfällt (geht in `substitution_pool` auf) |
| `coaching_cues` | list[str] | — | Claude, PDF | behalten |
| `progressions_up` / `progressions_down` | list[str] | exercise-IDs | V1.5-Block-Übergang (noch kein aktiver Leser) | behalten |
| `equipment_requires` | list[str] | Equipment-Items | equipment_filter:94 (**jetzt**, dormant — 0 Daten) | behalten (optional, default `[]`) |

---

## 2. Verbindliche Tagging-Vokabel ⚠️ (hier passieren beim Taggen die Fehler)

**Tagging-Semantik (entschieden 2026-06-11 · Konsument = MVP-5-3-Stufen-Filter):**
- `joint_stress` ist ein **Ausschluss-Tag**, keine Beteiligungs-Liste: nur Gelenke taggen,
  bei deren Verletzung der Coach die Übung dem Klienten **wegnehmen** würde (Stufe 1
  filtert hart). Beteiligung allein (z.B. Schulter hält die Stange beim Squat) ist KEIN
  Tag-Grund. Over-Tagging leert die Substitutions-Pools — im Zweifel schmaler taggen.
- `impact_level` bewertet **Stoßbelastung** (Sprünge/Landungen/Plyo), nicht Lastschwere:
  `high` fliegt bei JEDER Verletzung raus (Stufe 2). Schweres Kreuzheben = `low`.
- **Fertig-Marker:** `impact_level != null` = Übung ist getaggt. `joint_stress: []` ist
  nach dem Tagging ein legitimer Endwert (bewusst kein Ausschluss); `impact_level: null`
  bleibt das einzige Ungetaggt-Signal. Halb getaggt (joint_stress gesetzt, impact null)
  ist ein Validator-Fehler.
- **Validator-Gate (VERBINDLICH, 2026-06-12):** `python3 scripts/validate_exercises.py`
  muss grün sein, bevor Änderungen an `exercises.json` committet werden — gilt für Tagging,
  Korrekturen und den gesamten Bibliotheks-Ausbau auf 250–300 (und später fürs
  Backoffice-„Neue Übung anlegen"). Seit Streichung der pattern_tags-Blocker (Stufe 3)
  sind die Tags die **einzige** Sicherheitsquelle des Verletzungsfilters.

**`joint_stress` — ENGLISCH, exakt diese 8:**
```
knee · shoulder · spine · hip · elbow · wrist · neck · ankle
```
NICHT „lower_back", NICHT deutsch. Begründung: Klient-Input kommt **deutsch mit Umlaut**
vom Typeform (`VerletzungsBereich`: knie/schulter/wirbelsäule/hüfte/ellenbogen/handgelenk/
hals/knöchel) und wird via `_VERLETZUNG_MAP` (equipment_filter.py) **ins Englische
normalisiert, BEVOR** der Filter matcht. (Das historische `substitutions_b` nutzte exakt
diese Keys — Feld 2026-06-12 entfernt, Vokabel-Herkunft bleibt dieselbe.)
Besonders: **`spine`** (nicht „lower_back", nicht „wirbelsäule").

**`pattern` — Code-Schreibweise, exakt diese 9:**
```
squat · hinge · single_leg · push_horizontal · push_vertical · pull_horizontal · pull_vertical · core · carry
```
NICHT „horizontal_push" — die frühere Spec-Tabelle (Thema 8, 2026-06-11 durch Verweis
ersetzt) war falsch herum; equipment_filter / split_selector / plan_assembler matchen
auf die obigen Code-Strings.

**`impact_level` — 3 Strings:**
```
low · medium · high
```
`low` deckt „kein/minimaler Impact" mit ab — kein eigener `none`-Wert.

**`conditioning` + `athletik` Pattern:** Schreibweise **noch NICHT festgelegt** (kommt mit
MVP-7/4). Die bestehenden 125 Übungen brauchen sie **nicht** — alle liegen in den 9
Kraft-Pattern oben.

---

## 3. Konfliktregel → COACHING_SPEC.md

Spec-vs-Code-Konflikte regelt die **„Arbeitsregel: Spec-vs-Code-Konflikte"** in
COACHING_SPEC.md — die einzige ausformulierte Stelle. Kurzform: fachlich gewinnt die
Spec (Code wird gefixt), bei Bezeichnern gewinnt der Code (Spec wird korrigiert);
die Verliererseite wird im selben oder nächsten Commit angeglichen.
Historische Bezeichner-Drifts („horizontal_push", „lower_back" in der früheren
Thema-8-Tabelle) wurden 2026-06-11 in der Spec bereinigt (Tabelle → Verweis hierher).

---

## 4. `tier` — KEIN Feld in `exercises.json` (Klarstellung)

Der Tier (compound/accessory/isolation/core) kommt aus dem **Slot**, nicht aus der Übung:
`split_selector._slot` setzt ihn positionsbasiert, `plan_assembler:516` liest
`slot_templates[idx]["tier"]`. Der Satz-Cap (Modell A) ist je **Slot-Tier**, nicht je Übung.
→ **Nicht ins Schema aufnehmen.**
