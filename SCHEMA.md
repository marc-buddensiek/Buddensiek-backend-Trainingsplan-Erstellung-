# Übungs-Bibliothek — Schema-Spezifikation (`data/exercises.json`)

_Stand: 2026-06-10 · abgenickt · verbindliche Referenz für MVP-2 (Migration + Tagging)_

> Quelle: COACHING_SPEC.md Thema 8 + Code-verifizierte Konsumenten-Analyse. Bei
> Spec-vs-Code-Konflikt **gewinnt das Code-Vokabular** (lebende Konsumenten matchen dagegen).

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
| `joint_stress` | list[str] | die 8 unten (englisch) | Verletzungsfilter Stufe 1 (MVP-5, **geplant**) | **NEU** (auf allen taggen) |
| `impact_level` | str | low · medium · high | Verletzungsfilter Stufe 2 (MVP-5, **geplant**) | **NEU** (auf allen taggen) |
| `pattern_tags` | list[str] | offen (deep_squat, lunge, jump, overhead_press, bench_heavy, …) | Verletzungsfilter Stufe 3 (equipment_filter:98, **jetzt**) | behalten |
| `substitution_pool` | list[str] | exercise-IDs | Tausch (V2) + Verletzungs-Alternativen | **NEU** (= dedup(subs_a ∪ subs_b.values())) |
| `substitutions_b` | obj | Verl-Region → ID | equipment_filter:102 (**jetzt**) | behalten bis MVP-5, dann raus |
| `substitutions_a` | list[str] | exercise-IDs | 0 Leser | entfällt (geht in `substitution_pool` auf) |
| `coaching_cues` | list[str] | — | Claude, PDF | behalten |
| `progressions_up` / `progressions_down` | list[str] | exercise-IDs | V1.5-Block-Übergang (noch kein aktiver Leser) | behalten |
| `equipment_requires` | list[str] | Equipment-Items | equipment_filter:94 (**jetzt**, dormant — 0 Daten) | behalten (optional, default `[]`) |

---

## 2. Verbindliche Tagging-Vokabel ⚠️ (hier passieren beim Taggen die Fehler)

**`joint_stress` — ENGLISCH, exakt diese 8:**
```
knee · shoulder · spine · hip · elbow · wrist · neck · ankle
```
NICHT „lower_back", NICHT deutsch. Begründung: Klient-Input kommt **deutsch mit Umlaut**
vom Typeform (`VerletzungsBereich`: knie/schulter/wirbelsäule/hüfte/ellenbogen/handgelenk/
hals/knöchel) und wird via `_VERLETZUNG_MAP` (equipment_filter.py) **ins Englische
normalisiert, BEVOR** der Filter matcht. `substitutions_b` nutzt bereits exakt diese
englischen Keys → englisch taggen, dann matcht Stufe 1 ohne weitere Übersetzung.
Besonders: **`spine`** (nicht „lower_back", nicht „wirbelsäule").

**`pattern` — Code-Schreibweise, exakt diese 9:**
```
squat · hinge · single_leg · push_horizontal · push_vertical · pull_horizontal · pull_vertical · core · carry
```
NICHT „horizontal_push" — die Spec-Tabelle (COACHING_SPEC Z.538) ist falsch herum;
equipment_filter / split_selector / plan_assembler matchen auf die obigen Code-Strings.

**`impact_level` — 3 Strings:**
```
low · medium · high
```
`low` deckt „kein/minimaler Impact" mit ab — kein eigener `none`-Wert.

**`conditioning` + `athletik` Pattern:** Schreibweise **noch NICHT festgelegt** (kommt mit
MVP-7/4). Die bestehenden 125 Übungen brauchen sie **nicht** — alle liegen in den 9
Kraft-Pattern oben.

---

## 3. Naming-Regel: Code gewinnt

Bei Spec-vs-Code-Konflikt ist das **Code-Vokabular bindend** (lebende Konsumenten matchen
dagegen). Die Spec-Prosa ist an zwei Stellen ungenau:
- `push_horizontal` (Code) vs. „horizontal_push" (Spec Z.538)
- `spine` (Code/Enum) vs. „lower_back" (Spec Z.539)

---

## 4. `tier` — KEIN Feld in `exercises.json` (Klarstellung)

Der Tier (compound/accessory/isolation/core) kommt aus dem **Slot**, nicht aus der Übung:
`split_selector._slot` setzt ihn positionsbasiert, `plan_assembler:516` liest
`slot_templates[idx]["tier"]`. Der Satz-Cap (Modell A) ist je **Slot-Tier**, nicht je Übung.
→ **Nicht ins Schema aufnehmen.**
