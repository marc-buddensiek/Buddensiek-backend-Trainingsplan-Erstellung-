# Backlog — vertagte Arbeit (nach MVP-Paket)

_Stand: 2026-06-16 · git HEAD `f8ab9d6` (MVP-7 Naht 1–5 fertig, Komplexe offen)_

> Bewusst aufgeschobene Arbeit, gruppiert nach MVP-Paket. Jeder Eintrag:
> Beschreibung · warum vertagt · Code-Marker (Datei:Zeile, Grep-verifiziert) · Abhängigkeit.
> Code-Marker sind die `TODO(...)`-Strings im Code; Zeilennummern Stand HEAD `4c00caa`.

---

## MVP-3 — Volumen „Modell A" fertigstellen (Status: Kern fertig, Deckel offen)

- ~~**Level-Korridor-Deckel**~~ **VERWORFEN (bewusst, endgültig — 2026-06-17). Nicht aufgeschoben,
  gestrichen.** War `_WOCHEN_VOLUMEN` (entfernt `19f8d5f`). _Begründung:_ Volumen wird bereits durch
  **Modell A** dosiert (Tier-Sätze + Slot-Limit + Dauer-Deckel). Ein Muskel-Korridor-Deckel wäre eine
  **konkurrierende Steuerung auf anderer Achse** (Muskel-Sätze vs. Tier-Sätze) → Steuerungs-Konflikte,
  und bräuchte eine Muskel-Aggregation, die es nicht gibt. Schon einmal aus genau diesem Grund verworfen
  (Tagging-Wurzel: glutes/quads-Übertagging). Coach reviewt Pläne ohnehin manuell (human-in-the-loop) —
  automatische Kapazitäts-Kennzahl bringt keinen Mehrwert. _Offene Annahme dazu s. MVP-11 (Output-Review)._
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
- ~~**Offen geblieben (→ MVP-7):** Longevity-Athletik-Rotation + Conditioning-Block-Rotation/Format-Ausbau~~
  **erledigt mit MVP-7** (Athletik = Naht 5, Format-/Übungs-Rotation = Naht 3/4d/4e; `TODO(mvp7-athletik)`
  entfernt, `TODO(mvp7-formate)`-Marker + stale Rest-Kommentare entfernt; s. MVP-7-Abschnitt).

## MVP-5 — Verletzungs- & Equipment-Filter ✅ umgesetzt (2026-06-13, `d11ae4a`…`db80429`)

- 2-Stufen-Filter (joint_stress + impact:high), Stufe 3 gestrichen, Mehrfach-Verletzungen
  (Vereinigung), `substitutions_b` abgelöst, Leerer-Pool-Fallback (verwandtes Pattern):
  **alle erledigt** (4 Nähte, Details STATUS Abschnitt 6).
- **Offen geblieben (bewusste Scope-Grenze): Systemische Kontraindikationen**
  (~10% Klientel, Herz/Schwangerschaft): Anamnese-Gate → kein Auto-Plan, manuelle
  Coach-Betreuung. **KEIN** viertes Sicherheits-Tag. · _Hängt ab von:_ Anamnese-Erweiterung
  (V1.5-Check-in). · Nicht MVP-5-Filter-Logik.

## MVP-7 — Conditioning-Formate

**Stand 2026-06-16 — Naht 1–5 fertig, nur Komplexe offen (`9536905`…`f8ab9d6`):**
- **Mechanismus (Hybrid, entschieden):** Gruppe A `pattern:"conditioning"`, Gruppe B
  `conditioning_friendly:true` (bool). Die „Option A/B"-Designfrage unten ist damit **erledigt**.
- **Gebaut:** Schema-Enabler (Validator + 125 migriert) · Format-Baukasten (`logic/conditioning_formats.py`):
  7 Formate, Conditioning ohne RPE, Block-Stapelung Tabata/Density, Dauer = `session_dauer_min` (kein
  Level-Cap), Fettabbau-Staffelung gemischt + 2 reine Conditioning-Tage, C3-Finisher-Estimate ·
  **Naht 3** räumliche Format-Rotation (`pick_conditioning_formats`, weiche Equipment-Bevorzugung) ·
  **+33 Conditioning/Athletik-Übungen** (`bc14040`, Pool 41) · **Naht 4** Pool-Selektor **A1
  (deterministisch im Assembler, Claude für C-Sessions umgangen, kein MVP-9-Touch):** 4a Pool-Helfer,
  4b Finisher aus Pool (BW-Mehrheit + Zusatz), 4c reine C-Tage via `pool:"conditioning"`-Marker
  equipment-korrekt aus dem Pool (Naht-4-Bullet unten damit **erledigt**) · **Naht 4d** (`e6ce594`…
  `b5d8190`): **Ladders** block-dosierbar (5-Min-Block), **Format-Maxima** `_FORMAT_MAX_MIN`,
  **Multi-Format-Segmentierung** langer reiner C-Tage (`split_conditioning_segments` mit
  kapazitätsbewusstem Erstformat + Maxima-Check; nicht abdeckbar → ValueError), **`conditioning_block_2`**-
  Feld + PDF („FORMAT 2") · **Naht 4e** (`b674840`/`ada7377`): Übungs-Rotation reiner C-Tage
  (Per-Pattern-Offset, BW-first bleibt; 2 C-Tage/Woche + Wochen verschieden → 4d-Caveat abgefedert) +
  Finisher-Format-/Übungs-Rotation **{amrap, zirkel}** (nie 2× hintereinander; Tabata/Density-Finisher
  vertagt) · **Naht 5** (`8d198f4`/`d346ac3`/`f8ab9d6`, `logic/athletik.py`): Athletik-Tag (pool:"athletik",
  skill-Dosierung, keine RPE, kein Cardio, Deload ×0.67), Longevity 5/6 → 1× Z2 + 1× Athletik, Longevity 4
  → zeitliche Z2/Athletik-Rotation, Leer-Pool→Zone-2-Fallback.
- **Offen:**
  - **Komplexe** (`TODO(mvp7-komplexe)`, `conditioning_formats:29`): brauchen **vordefinierte Coach-
    Ketten** (Flow ohne Ablegen, nur Last) — **nicht aus Einzelübungen generierbar**. Bleibt gültiges
    Enum, aber aus dem Rotations-Pool gefiltert. Eigener Schritt — **letzter offener MVP-7-Punkt**.
  - ~~**`TODO(mvp7-cleanup)`** C1/C2/C4~~ **erledigt:** C1 `block_session_dauer` + C4
    `ZEIT_PRO_SATZ_COND` (toter is_metabolic-Zweig, verhaltensneutral) entfernt; C2
    Intervall-Notiz liest `level_work_rest(level)` statt hardcodiert — Work:Rest jetzt
    level-basiert (L1 40/20 · L2/L3 45/15 · L4 50/10), Wochen-Rampe läuft über die Rundenzahl.
  - ~~Lange-Session-Caveat (4d)~~ **durch Naht 4e abgefedert:** identische C-Tag-Formate werden über
    die rotierte Übungs-Auswahl differenziert (BW-L4-60 → beide density+amrap, aber verschiedene Übungen).
  - **Conditioning-/Athletik-Pool-Ausbau** (Coach, s. MVP-2-Abschnitt): Bodyweight-Conditioning L3/L4,
    Pull-Pattern, **Athletik L1/Bodyweight** (L1-Bodyweight-Athletik-Pool leer → Zone-2-Fallback).

**For Time gestrichen (Spec Thema 6):** offene Dauer („so schnell wie möglich") kollidiert mit der festen
Session-Länge / Modell A. Falls je reaktiviert: `max_time_cap` als **Pflichtparameter** (Session-Dauer-Deckel)
nötig — nicht V1.

**Format-Parameter final (2026-06-14, `TODO(mvp7-format-params)` aufgelöst):** EMOM + Mixed Intervals
**gestrichen** (EMOM = Intervall sobald Arbeitszeit fix vorgegeben; Mixed Intervals nie definiert). Density =
5-Min-Block (feste Zeit, max. Wdh bei festem Gewicht), Ladders = aufsteigend (1-2-3-…-Cap), Komplexe =
Block-Format (nur Last). Aktive Formate: **Intervall · AMRAP · Zirkel · Tabata · Density · Ladders ·
Komplexe** (7). Finale Spec in COACHING_SPEC Thema 6.

- ~~**Naht 4 — Metcon-Selektor nutzt noch Kraft-Pattern**~~ **erledigt (2026-06-15, `fa7598f`/`de39977`):**
  `_METCON_PATTERNS` entfernt; Finisher **und** reine C-Tage ziehen jetzt aus `conditioning_pool`
  (`pattern=="conditioning" OR conditioning_friendly`), equipment-korrekt, A1-deterministisch.
  Verifiziert: kein Back Squat mehr im Conditioning; BW-Kunde reine BW inkl. Burpee/Mountain Climbers.

**Kernproblem, das Naht 4 gelöst hat (historisch):** Die alte Logik (`_METCON_PATTERNS`) konnte
„hat Kraft-Pattern" **nicht** von „ist conditioning-tauglich" unterscheiden — das differenzierende
Merkmal fehlte, sodass der Metcon potenziell reine Kraftübungen (z.B. schwerer Back Squat) in eine
Conditioning-Session zog. Mit `conditioning_friendly` (Naht 1) + Pool-Selektor (Naht 4) behoben.

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

## MVP-8 — Assembler/PDF (Coach-Flag + Kapazitäts-Infos VERWORFEN)

- **Coach-Kapazitäts-Flag + jegliche Kapazitäts-Infos VERWORFEN (bewusst, endgültig — 2026-06-17),
  nicht aufgeschoben.** (`volume_below_optimal`, `recommended_extras`, Muskel-Aggregation; Code schon
  entfernt `408c079`+`19f8d5f`.) _Begründung:_ Modell A dosiert das Volumen bereits (Tier-Sätze +
  Slot-Limit + Dauer-Deckel); ein Kapazitäts-Flag setzt einen Muskel-Korridor voraus, der seinerseits
  verworfen ist (s. MVP-3) — **konkurrierende Steuerung**, keine Aggregation vorhanden. Coach reviewt
  manuell (human-in-the-loop), die Kennzahl bringt keinen Mehrwert.
- **`plan_metadata` bleibt als `Optional=None`-Platzhalter** im Modell (`models.py`) — **bewusst
  ungenutzt**, kein Konsument, schadet nicht; wird nicht befüllt und nicht entfernt.
- **MVP-8 = nur noch Assembler/PDF** (der Assembler baut alle Ziele fertig).
- **Realism-/Kapazitäts-Warnung aus dem Klienten-PDF entfernt (2026-06-17):** `pdf_generator`
  rendert keine „Volumen suboptimal"-Warnung mehr (Methode + Aufruf + Imports raus). Konsistent mit
  der Kapazitäts-Streichung — gehört nicht ins Premium-PDF. `pruefe_realismus` (`realism_validator.py`)
  **bleibt** (Funktion + Unit-Tests), hat aber **keinen Produktions-Konsumenten** mehr (als ungenutzt
  markiert). · _Folge-Thema (Intake/Frontend, Fillout/Manu — MVP-12):_ Die Info „Klient hat zu wenig
  Zeit fürs Ziel gewählt" gehört **beim Ausfüllen** ins Intake-Formular/Frontend, nicht ins fertige
  PDF. Dort `pruefe_realismus` (oder dieselben Schwellen) wiederverwenden.
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
  Tier-Satz-Caps/Slot-Dosierung (Modell A; Muskel-Korridor verworfen, s. MVP-3/11), oder
  Skill-Level-Übungsauswahl (MVP-9). **Erst an der Matrix
  Ziel × Level × 20–50 Min × 2–5 Tage beurteilen — kein Vorab-Raten.** · Nicht MVP-6-Scope.
- **Level-Gate-Semantik (MVP-9-Vorarbeit) — Diagnose erledigt (2026-06-13, read-only):** Frage war
  „Exakt-Match `==` oder Obergrenze `<=`?". **Befund:** Der Gate ist bereits `<=` —
  `equipment_filter.py:73` `if ex["skill_level"] > level: continue` behält alle Übungen mit
  `skill_level ≤ level`. (Die im Prompt genannte `:91` ist der Fallback-Aufruf, nicht der Gate.)
  **Reihenfolge:** Level-Check (`:73`) läuft VOR dem Verletzungsfilter (Stufe 1 `:81`, Stufe 2 `:84`).
  **Kein Fix nötig.** · _Offene Teilfrage für MVP-9:_ Soll es eine Unterkante geben (kein
  L1-Trivialkram für L4-Athlet)? Aktuell **kein Floor** — L4 sieht L1–L4. Bei MVP-9 entscheiden.
- **Modellwahl (Naht 9-4) — OFFEN bei Output-Review:** Modellwahl an echtem Output verifizieren.
  Default **Sonnet 4-6**. Falls Übungs-Auswahl oder Cues/Notizen nicht überzeugen, denselben
  Klienten-Satz mit **Opus** gegentesten (Sonnet vs. Opus direkt vergleichen) und den Aufpreis nur
  nehmen, wenn der Qualitätsunterschied es rechtfertigt. Entscheidung an Daten, nicht vorab.
- **Kraft↔Conditioning-Trennung (Output-Review) — OFFEN:** Die fachliche Begründung (Kraft → Claude
  wegen mehrdimensionaler Urteils-Kriterien; Conditioning/Athletik → deterministisch, weil mechanisch
  regularisierbar; Pool-Größe ist NICHT der Grund) ist **Arbeitshypothese** (COACHING_SPEC, Naht-4/A1).
  Am echten Output prüfen: (1) wirkt die deterministische Conditioning-Auswahl fachlich gut oder
  schematisch? (2) erfüllt Claudes Kraft-Auswahl Balance/Symmetrie/Variation tatsächlich? Erst danach
  endgültig: Trennung so lassen oder anpassen.
- **Dritter-Pool-Drift (claude_client ↔ plan_assembler) — kein Handlungsbedarf jetzt:**
  `_pruefe_vollstaendigkeit` (9-3a) filtert Kraft-Sessions über `slot["pool"]` **truthy** (jeder
  Wert), der Assembler bypassed Claude exakt bei `pool == "conditioning"`/`"athletik"`. Heute
  deckungsgleich. Wird je ein **dritter pool-Typ** eingeführt, müssen **beide** Stellen mitwandern
  (sonst nähme der Filter ihn aus SOLL, während der Assembler ihn nicht bypassed → Inkonsistenz).
  _Auslöser:_ neuer Pool-Typ.

## Logging / Observability

- **Fundament gebaut** (`logging_config.py`, zentral, dictConfig, Plaintext + Modulname,
  `vorgang_id`-Correlation, PII-frei). Konvention im Modul-Docstring.
- **Später auf JSON + gehosteten Log-Dienst umstellbar** (z.B. Better Stack): Das Fundament ist
  zentral vorbereitet — der Wechsel ist ein **Formatter-Tausch an EINER Stelle** (`logging_config`).
  _Auslöser:_ Aggregator/Alerting anschließen, oder Log-Volumen zu groß fürs bloße Auge. Nicht jetzt.

## V1.5 — Ideen (aus MVP-4 vertagt)

- **Schwachstellen-Fokus-Tag** (5T Muskelaufbau/Recomp): Klient wählt Region
  (arme/brust/ruecken/schultern/beine), 5. Tag wird Fokus-Template statt Ganzkörper-Akzent.
  Gestrichen am 2026-06-11 (V1 = Ganzkörper-Akzent); braucht Anamnese-/Typeform-Feld +
  Fokus-Slot-Templates (lagen als `_SCHWACHSTELLEN_PATTERNS` vor, siehe Commit a88943c). ·
  _Marker:_ `TODO(v15-schwachstelle)` (models.py). · _Hängt ab von:_ V1.5-Check-in/Anamnese.

## Progression V2 — Übungs-Progression (geparkt, nach Output-Review)

- **Zeitgesteuerte Übungs-Progression (nicht-belastbare Übungen):** deterministischer Übungswechsel
  entlang der Block-Zeitachse statt nur über die RPE-Welle — sind die Reps bei **nicht-belastbaren**
  Übungen ausgereizt, Wechsel zur nächsten `progressions_up`-Sprosse (z.B. 3×12 Push-up →
  3×8–10 Archer). **NUR nicht-belastbare Übungen.** _Architektur-Implikation:_ der Slot trägt dann
  eine **Sequenz über die Wochen** statt einer einzelnen Übung. _Offene Entscheidungen:_
  Trigger-Zeitpunkt; Claude wählt Einstiegs-Sprosse vs. deterministisches Hochklettern; Verhalten
  bei zu kurzer Kette. **Eigener MVP-Brocken NACH dem Output-Review**; verknüpft mit dem geparkten
  Thema „4-Wochen-Block-Ende".
- **Progression über komplexere Varianten bei belastbaren Übungen:** dort primär über **Last**
  (RPE-Welle) — eine komplexere Variante ggf. über den **nächsten Plan/Block**, separat zu
  durchdenken. Bewusst vorerst raus.

## MVP-11 — Test-Harness

- **Aktuelle Tests prüfen nur „läuft / crasht nicht", NICHT fachliche Korrektheit** der Pläne.
  Spec-Validator-Harness muss diese Lücke schließen (grün = läuft, nicht = richtig). · _Hängt
  ab von:_ MVP-3…8.
- **OFFEN — bei Output-Review prüfen: Dosiert Modell A das Volumen fachlich ausreichend, OHNE
  Muskel-Korridor-Deckel?** Der Korridor wurde bewusst gestrichen (s. MVP-3 / MVP-8) unter der
  Annahme, dass Modell A (Tier-Sätze + Slot-Limit + Dauer-Deckel) genügt. **Diese Annahme ist
  NICHT verifiziert.** Bei der Test-Output-Review über alle Konstellationen (Ziel × Tage × Dauer ×
  Level) muss als Coach geprüft werden, ob das Volumen pro Muskel/Woche fachlich plausibel
  rauskommt. Falls nicht: **neue, gezielte Lösung statt des verworfenen Generaldeckels.** Ziel:
  Pläne sind ohne manuelles Drüberschauen fachlich korrekt.

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
