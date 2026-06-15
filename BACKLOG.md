# Backlog — vertagte Arbeit (nach MVP-Paket)

_Stand: 2026-06-15 · git HEAD `5171a67` (MVP-7 Naht 1 + 2 fertig)_

> Bewusst aufgeschobene Arbeit, gruppiert nach MVP-Paket. Jeder Eintrag:
> Beschreibung · warum vertagt · Code-Marker (Datei:Zeile, Grep-verifiziert) · Abhängigkeit.
> Code-Marker sind die `TODO(...)`-Strings im Code; Zeilennummern Stand HEAD `4c00caa`.

---

## MVP-3 — Volumen „Modell A" fertigstellen (Status: Kern fertig, Deckel offen)

- **Level-Korridor-Deckel fehlt.** War `_WOCHEN_VOLUMEN`, in dieser Session entfernt
  (Commit `19f8d5f`, kein Konsument mehr). Obergrenze je Level/Ziel neu bauen
  (Sätze/Muskel/Woche deckeln). · _Vertagt:_ braucht echte Muskel-Aggregation (MVP-4-Splits
  + saubere Tags MVP-2). · _Marker:_ — (Tabelle entfernt). · _Hängt ab von:_ MVP-2, MVP-4.
- ~~**Deload-Faktor** `0.50` vs Spec `0.60`~~ **erledigt (MVP-6 Naht 2, `7031b42`):** toter
  Faktor + `TODO(deload-faktor-tot)` aus `_PERIODISIERUNG_FAKTOR` entfernt; Spec Thema 1 +
  CLAUDE.md per Konfliktregel auf den Modell-A-Deload reconcilet (Cap-Unterkante ~67–75 % des
  Peaks + RPE `rpe_low−1`, Floor 4). Kein Verhaltens-Change (Golden bestätigt).
- ~~Test-Altlast tage=2 + tote Refs~~ **erledigt (2026-06-12, Hygiene-Commit):** run_tests +
  generate_test_plans komplett grün (26/26 · 7/7 · 16/16); Gym-2T-Duplikat zu Gym/6T/Fettabbau
  umgewidmet (deckt 4K+2C-Pfad).

## MVP-4 — Split-Logik Neubau ✅ umgesetzt (2026-06-11, `4ab789c`…`65306a8`)

- longevity-Crash, Fettabbau-Struktur, Mobility-Entfernung, 20-Min-Sonderfall: **alle erledigt**
  (5 Nähte, Details STATUS Abschnitt 6). Schwachstellen-Fokus-Tag gestrichen → V1.5-Sektion unten.
- **Offen geblieben (→ MVP-7/8): Pattern-Priorität bei kurzer Session** (welches Pflicht-Pattern
  zuerst fällt; V1: Kürzung implizit über die Slot-Templates fixiert, „Dauer gewinnt"). · _Marker:_
  `logic/plan_assembler.py:366` `TODO(short-session-pattern-drop)`.
- **Offen geblieben (→ MVP-7):** Longevity-Athletik-Rotation (`TODO(mvp7-athletik)`,
  split_selector:295) + Conditioning-Block-Rotation/Format-Ausbau (`TODO(mvp7-formate)`,
  split_selector:378) — V1-Stand in COACHING_SPEC Thema 4/6 vermerkt.

## MVP-5 — Verletzungs- & Equipment-Filter ✅ umgesetzt (2026-06-13, `d11ae4a`…`db80429`)

- 2-Stufen-Filter (joint_stress + impact:high), Stufe 3 gestrichen, Mehrfach-Verletzungen
  (Vereinigung), `substitutions_b` abgelöst, Leerer-Pool-Fallback (verwandtes Pattern):
  **alle erledigt** (4 Nähte, Details STATUS Abschnitt 6).
- **Offen geblieben (bewusste Scope-Grenze): Systemische Kontraindikationen**
  (~10% Klientel, Herz/Schwangerschaft): Anamnese-Gate → kein Auto-Plan, manuelle
  Coach-Betreuung. **KEIN** viertes Sicherheits-Tag. · _Hängt ab von:_ Anamnese-Erweiterung
  (V1.5-Check-in). · Nicht MVP-5-Filter-Logik.

## MVP-7 — Conditioning-Formate

**Stand 2026-06-15 — Naht 1 + 2 fertig (`9536905`…`5171a67`):**
- **Mechanismus (Hybrid, entschieden):** Gruppe A `pattern:"conditioning"`, Gruppe B
  `conditioning_friendly:true` (bool). Die „Option A/B"-Designfrage unten ist damit **erledigt**.
- **Gebaut:** Schema-Enabler (Validator + 125 migriert) · Format-Baukasten (`logic/conditioning_formats.py`):
  7 Formate, Conditioning ohne RPE, Block-Stapelung Tabata/Density, Dauer = `session_dauer_min` (kein
  Level-Cap), Fettabbau-Staffelung gemischt + 2 reine Conditioning-Tage, C3-Finisher-Estimate.
- **Offen (Naht 3/4/5):** echte Format-Rotation (`TODO(mvp7-formate)`, ersetzt Trivial-Pick) · **Selektor-
  Umbau** auf den Conditioning-Pool (Naht 4, s. Bullet unten — braucht getaggte Übungen, bringt
  Ladders/Komplexe-Block-Dauern mit) · Athletik (Naht 5) · `TODO(mvp7-cleanup)` C1/C2/C4 (geparkt).

**For Time gestrichen (Spec Thema 6):** offene Dauer („so schnell wie möglich") kollidiert mit der festen
Session-Länge / Modell A. Falls je reaktiviert: `max_time_cap` als **Pflichtparameter** (Session-Dauer-Deckel)
nötig — nicht V1.

**Format-Parameter final (2026-06-14, `TODO(mvp7-format-params)` aufgelöst):** EMOM + Mixed Intervals
**gestrichen** (EMOM = Intervall sobald Arbeitszeit fix vorgegeben; Mixed Intervals nie definiert). Density =
5-Min-Block (feste Zeit, max. Wdh bei festem Gewicht), Ladders = aufsteigend (1-2-3-…-Cap), Komplexe =
Block-Format (nur Last). Aktive Formate: **Intervall · AMRAP · Zirkel · Tabata · Density · Ladders ·
Komplexe** (7). Finale Spec in COACHING_SPEC Thema 6.

- **Naht 4 — Metcon-Selektor nutzt noch Kraft-Pattern** (`_METCON_PATTERNS = ["squat","hinge","push_horizontal","core"]`,
  `plan_assembler:294`) statt echter Conditioning-Bewegungen (Spec Thema 6: Burpees, Mountain
  Climbers, …). Umbau auf `pattern=="conditioning" OR conditioning_friendly`. · _Hängt ab von:_
  getaggte Conditioning-Übungen (Coach). Der **Schema-Mechanismus dafür steht** (Naht 1).

**Kernproblem, das Naht 4 löst:** Die aktuelle Logik (`_METCON_PATTERNS`,
`plan_assembler:294`) kann „hat Kraft-Pattern" **nicht** von „ist conditioning-tauglich"
unterscheiden — das differenzierende Merkmal fehlt. Folge: der Metcon zieht potenziell reine
Kraftübungen (z.B. schwerer Back Squat, Kreuzheben) in eine Conditioning-Session, nur weil das
Pattern passt — obwohl sie keinen Puls oben halten.

**Designfrage (NICHT jetzt entscheiden, nur festhalten): conditioning-tauglich vs. reine
Kraftübung im selben Pattern differenzieren —**
- _Option A:_ eigenes `conditioning`-Pattern. Problem: eine Übung hat nur **1** Pattern; ein
  Thruster ist Conditioning **UND** push_vertical → geht nicht sauber.
- _Option B:_ zusätzliches Feld `conditioning_geeignet` (bool) bzw. `conditioning_role`,
  unabhängig vom Pattern. Metcon filtert dann **pattern UND conditioning-tauglich**.
- → **Tendenz Option B**, aber erst entscheiden, wenn der Metcon-Selektor-Neubau (MVP-7) steht.
  **Tag-Definition hängt am Konsumenten** — nicht den MVP-8-Fehler wiederholen (Tag ohne fertige
  Logik bauen).

**Bestandsaufnahme (2026-06-10, signal-basiert — kein conditioning-Tag vorhanden):** dediziert
conditioning/athletik-tauglich, aber in Kraft-Pattern getaggt: **6** (KB Swing ×2, KB Snatch,
KB Clean → `hinge`; Jump Squat → `squat`; Skater Squat → `single_leg`). Wiederverwendbarer Pool:
**44 bodyweight-fähig / 65 kettlebell-fähig**. Klassische Staples (Burpee, Mountain Climber, Box
Jump, Bear Crawl, Throw …): **0 vorhanden → net-new** (~25, ROADMAP-Mindestabdeckung).

**Bei MVP-7 konkret zu prüfen:** für **jede** der 6 mis-filed + den 44/65-Reuse-Pool **einzeln**
entscheiden, ob conditioning-tauglich ja/nein. Coach-Fachwissen pro Übung, **kein**
Pattern-Automatismus.

## MVP-8 — Assembler + Coach-Flag (zurückgerollt, kommt zurück wenn MVP-2/3/4 stehen)

- **Coach-Flag komplett entfernt** (volume_below_optimal, recommended_extras, Muskel-Aggregation).
  War out-of-order (hängt an ungebautem MVP-2/3-Deckel/4). Cleanup-Commits `408c079` + `19f8d5f`.
  `PlanMetadata` bleibt als `Optional=None`-Platzhalter im Modell (`models.py`). · _Hängt ab von:_
  MVP-2, MVP-3-Deckel, MVP-4.
- ~~Tag-Bug Single Leg RDL~~ **widerlegt (2026-06-11, Git-verifiziert):** `gym_single_leg_rdl_db`
  hat seit Initial-Commit `hamstrings,glutes` primary — identisch mit allen 5 RDL-Varianten.
  Der Befund aus der Coach-Flag-Session war eine Fehlbeobachtung; kein Datenfix nötig.

## MVP-6 — Recovery-RPE + Periodisierung ✅ umgesetzt (2026-06-13, `82b3c1d`…`798928d`)

- 3 Nähte aufsteigenden Risikos: (1) **RPE-Welle neu** — ankert `rpe_low`→`rpe_high`, 0.5-Raster,
  Deload `rpe_low−1` (Floor 4); RPE int→float (Frontend-Vertrag, `:g` nur im PDF). (2) **toter
  Deload-Faktor raus** + Spec/Doc-Reconcile (Konfliktregel). (3) **L1-RIR-Hilfe** (`rpe_hinweis`,
  rein additiv, nur Level-1-Kraftsätze). Details STATUS Abschnitt 6.
- **Coach-Befund verriegelt:** Volumen bleibt bewusst flach (intensitätsgeführt) — die Welle läuft
  über die RPE, nicht über die Sätze. Keine Cap-Range-Verbreiterung (als out-of-scope/MVP-8 eingestuft).
- Tests: Logik 26/26 · Realism 7/7 · **Wellen 5/5** · **RIR 3/3** · generate_test_plans 16/16.

## MVP-9 — Claude-Integration (Vorarbeit / Review)

- **Output-Review (NACH MVP-9, an echten PDFs):** Sind die Pläne in der Gesamt-Schwierigkeit zu
  leicht / Klient unterfordert? Stellschrauben falls ja: RPE-Spannen-Höhe (Thema 3),
  Volumen-Korridor/Caps (MVP-3), oder Skill-Level-Übungsauswahl (MVP-9). **Erst an der Matrix
  Ziel × Level × 20–50 Min × 2–5 Tage beurteilen — kein Vorab-Raten.** · Nicht MVP-6-Scope.
- **Level-Gate-Semantik (MVP-9-Vorarbeit) — Diagnose erledigt (2026-06-13, read-only):** Frage war
  „Exakt-Match `==` oder Obergrenze `<=`?". **Befund:** Der Gate ist bereits `<=` —
  `equipment_filter.py:73` `if ex["skill_level"] > level: continue` behält alle Übungen mit
  `skill_level ≤ level`. (Die im Prompt genannte `:91` ist der Fallback-Aufruf, nicht der Gate.)
  **Reihenfolge:** Level-Check (`:73`) läuft VOR dem Verletzungsfilter (Stufe 1 `:81`, Stufe 2 `:84`).
  **Kein Fix nötig.** · _Offene Teilfrage für MVP-9:_ Soll es eine Unterkante geben (kein
  L1-Trivialkram für L4-Athlet)? Aktuell **kein Floor** — L4 sieht L1–L4. Bei MVP-9 entscheiden.

## V1.5 — Ideen (aus MVP-4 vertagt)

- **Schwachstellen-Fokus-Tag** (5T Muskelaufbau/Recomp): Klient wählt Region
  (arme/brust/ruecken/schultern/beine), 5. Tag wird Fokus-Template statt Ganzkörper-Akzent.
  Gestrichen am 2026-06-11 (V1 = Ganzkörper-Akzent); braucht Anamnese-/Typeform-Feld +
  Fokus-Slot-Templates (lagen als `_SCHWACHSTELLEN_PATTERNS` vor, siehe Commit a88943c). ·
  _Marker:_ `TODO(v15-schwachstelle)` (models.py). · _Hängt ab von:_ V1.5-Check-in/Anamnese.

## MVP-11 — Test-Harness

- **Aktuelle Tests prüfen nur „läuft / crasht nicht", NICHT fachliche Korrektheit** der Pläne.
  Spec-Validator-Harness muss diese Lücke schließen (grün = läuft, nicht = richtig). · _Hängt
  ab von:_ MVP-3…8.

## MVP-2 — laufend

- **Schema-Spec abgenickt** → `SCHEMA.md` ist die verbindliche Referenz.
- **Schema-Migration umgesetzt** (`4960c26`, `scripts/migrate_schema_mvp2.py`): alle 125 auf
  neuem Schema.
- **Tagging der 125 fertig** (`8980bd7`, 9 Coach-reviewte Pattern-Batches, Ausschluss-Semantik
  SCHEMA.md Abschn. 2, `validate_exercises.py` grün). **+33 Conditioning/Athletik** (`bc14040`) →
  **158 getaggt**. **Offen nur noch: Ausbau auf 250–300** (Coach-Daueraufgabe; neue Übungen direkt
  nach Semantik taggen, Validator als Gate).
- **Conditioning-Pool-Ausbau (Coach):** Der Conditioning-Pool (41) deckt KB + Athletik, hat aber
  Lücken — **Bodyweight-Conditioning L3/L4 = 0**, **keine Pull-Pattern-Conditioning**
  (pull_horizontal/pull_vertical), **KB-Conditioning L4 = 0**, **single_leg dünn**. Kein MVP-7-Blocker
  (Naht 4 funktioniert mit dem aktuellen Pool), aber für Format-/Pattern-Vielfalt im Metcon nachziehen.
- **Ausbau-Priorität aus MVP-5-Sim:** Beim Ausbau zuerst die Pattern abdecken, die den
  Verletzungs-Fallback (MVP-5 Naht 4) am häufigsten auslösen — **Bodyweight-`push_vertical`**
  (schulter-/handgelenk-schonende Vertikaldrück-Varianten, z.B. Landmine-artig/Band) und
  **`carry`-Varianten** (griffschonend bei Handgelenk). Sim: 14 bzw. 17 Equipment×Level×
  Verletzungs-Kombos greifen sonst auf das Ersatz-Pattern zurück. Senkt die Fallback-Häufigkeit.
- **`update_exercises.py` schema-stale** (NEW_EXERCISES-Literale noch Alt-Schema) — nicht erneut
  laufen lassen ohne Anpassung. · _Marker:_ `TODO(mvp2-schema-stale)` (Kopf-Kommentar).
- **Bestandsaufnahme offen:** wie viele der 125 sind schon conditioning-tauglich, nur in
  Kraft-Pattern getaggt? Echte Anlage neuer conditioning/athletik-Übungen erst nach MVP-7.
- **`TODO(longevity-volume)`:** Platzhalter-Werte in `realism_validator.py:17` / `:33` / `:53`
  und `logic/plan_assembler.py:45` (`_WDH_MAP`), final mit Thema 4–6.
- **`equipment_requires`** seit der Migration in allen 125 als `[]` materialisiert (dormant,
  0 echte Daten; lebender Leser `equipment_filter:94`).
