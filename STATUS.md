# Projektstatus — Buddensiek Performance KI-Trainingsplan

_Zuletzt aktualisiert: 2026-06-10 · git HEAD `19f8d5f` · Branch `mvp-1-data-foundation`_

---

## 1. Aktueller Stand (kurz)

Backend importiert sauber (`import main` ✅). Tests: **Logik 19/26 · Realism 7/7** — die 7 roten sind ausschließlich veraltete Testdaten + ein nicht-gebautes Feature (MVP-4), **keine Regression** (Belege: Abschnitt 5).

Spec ist komplett (alle 8 Themen entschieden). Umsetzung läuft entlang der ROADMAP (MVP-1…12).
**Fertig:** MVP-1 (Daten-Fundament) + MVP-3-Kern (Volumen „Modell A").
**Offen / nächste große Brocken:** MVP-2 (Bibliothek) und MVP-4 (Split-Logik).
Pipeline (Typeform → … → PDF/Supabase) steht strukturell; Claude/Supabase nicht live.

## 2. Spec-Themen (COACHING_SPEC.md)

Alle **8 Themen ✅ entschieden** — Regelseite vollständig, Rückstand rein in der Umsetzung:
1 Periodisierung · 2 Level/PST · 3 Volumen & Intensität · 4 Split-Logik · 5 Recovery · 6 Conditioning/Cardio · 7 Progression (V1) · 8 Sonderfälle.

## 3. MVP-Pakete 1–12 (verifizierter Stand)

| # | Paket | Status | Beleg | Hängt ab von |
|---|---|---|---|---|
| 1 | Daten-Fundament | ✅ fertig | Hauptziel 4 Ziele, tage ge=3, nebenziel/schmerzen_akut raus, schwachstelle, PlanMetadata, rpe_hinweis (models.py) | — |
| 2 | Bibliothek/Tagging | ❌ offen | 125 Übungen (Ziel 250–300), altes Schema: `level_min`, **kein** skill_level/joint_stress/impact_level/substitution_pool | — |
| 3 | Volumen „Modell A" | 🟡 Kern fertig, Korridor-Deckel offen | _TIER_CAP/_tier_saetze ✓, TJ-Faktor + Tier-Multiplikator raus ✓, Recovery-RPE ✓; **Level-Korridor-Deckel nicht gebaut** (war Naht 3, zurückgerollt) | 1 |
| 4 | Split-Logik | ❌ offen / nicht begonnen | split_selector:399 ausdauer-Crash, :411 else#gesundheit, :391 Fettabbau 100% Conditioning, **kein longevity-Zweig**, _mobility_session noch da | 1, 3 |
| 5 | Equipment/Verletzungs-Filter | ❌ offen | nutzt `level_min`, **kein** joint_stress/impact_level → 3-Stufen nicht gebaut | 2 |
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

**2026-06-09/10 — Modell A (MVP-3-Kern) + Coach-Flag-Rückbau (MVP-8 out-of-order)**
- Modell A gebaut: Naht 1 Tier-Satz-Caps statt Wochenvolumen÷Frequenz (`277e396`), Naht 2a flaches Zeit-Modell (`493d2eb`), Naht 2b Dauer-Trim „Dauer gewinnt" inkl. Cardio (`06b7aeb`). Davor: Recovery→RPE-Tiers (`2b54d98`), Trainingsjahre-Faktor raus (`8150666`), Spec-Thema-3-Zeitparameter (`e2ab9b8`), Korridor-Werte + Test-Renames (`d8cd1f3`/`1730d3b`/`a854ee3`).
- Coach-Flag (MVP-8) gebaut → **Doppelzähl-Bug** (Sub-Label-Mehrfachzählung) + **Tagging-/Skalen-Problem** (glutes/quads zu breit primary getaggt; echte Wochen-Sätze ≫ alter frequenz-geteilter Korridor) gefunden. Recherche: Korridor (12–16) **und** Zählmethode (primary 1,0 / secondary 0,5) sind fachlich korrekt — **Wurzel ist das Tagging**.
- Entscheidung: Flag **komplett verworfen** statt Tagging jetzt zu fixen → 2 Cleanup-Commits (`408c079` budget_saetze raus, `19f8d5f` _WOCHEN_VOLUMEN raus). **Erkenntnis: MVP-8 war out-of-order** (hängt an ungebautem MVP-2 + MVP-3-Deckel + MVP-4). `PlanMetadata` bleibt leerer `Optional=None`-Platzhalter. Reihenfolge auf Roadmap-Kernpfad zurückgesetzt.

**2026-06-07 — MVP-1 Daten-Fundament**
- Hauptziel auf 4 Ziele (longevity statt ausdauer+gesundheit), tage_pro_woche ge=3, nebenziel + schmerzen_akut entfernt, schwachstelle-Feld ergänzt, session_typ/MetconBlock-Literale additiv erweitert, HauptUebung.rpe_hinweis + PlanMetadata-Submodell. Spec/Roadmap/CODE_CHANGES angelegt.

**2026-06-02 — Pre-Spec-Fixes**
- `ist_mobility`/`metcon_blk`-Initialisierung in plan_assembler (NameError-Risiko), MetconBlock-Rendering im PDF (CONDITIONING-FINISHER-Block), CLAUDE.md erstellt.

## 7. Nächster Schritt

**MVP-2 — Übungs-Bibliothek** (Schema-Migration `level_min`→`skill_level` + neue Felder, Ausbau auf 250–300 getaggte Übungen). Begründung: längster Posten (Coach-Zeit), blockt MVP-5, und ist Voraussetzung, um Korridor-Deckel (MVP-3-Rest) + Coach-Flag (MVP-8) später sauber zu kalibrieren.
**Parallel dev-seitig möglich:** MVP-4 (Split-Logik-Neubau — behebt longevity-Crash + Fettabbau-Struktur), hängt nur an MVP-1+3 (beide bereit).
