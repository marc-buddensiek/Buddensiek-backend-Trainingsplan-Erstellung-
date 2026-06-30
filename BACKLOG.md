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

## Output-Review — erster echter Lauf

### Output-Review Lauf 1 (Cases 13-15, echter Claude, 2026-06-25)
_Erster echter Claude-Output gegen Checker-Brücke geprüft (--run-dir). 0/3 "regelkonform"
laut Checker — aber die Funde zerfallen in echte Befunde vs. zu strenge Regeln:_

_**BEFUND 1 (strukturell, wichtigste Wurzel): 6-Tage-Split [:2]-Template-Verdopplung.**_
_split_selector.py:368: `ul6 = _upper_lower_sessions(...) + _upper_lower_sessions(...)[:2]`
dupliziert wortwörtlich [UA,LA,UB,LB] + [UA,LA] → Upper A + Lower A je 2×, Upper B + Lower B je 1×.
Folgen:_
_- Push 2×/Pull 1×, Squat 2×/Hinge 1× — Vorderseite verdoppelt. COACH-URTEIL (Alen): suboptimal,
  Pull/Hinge sind bei den meisten Klienten die Schwachstelle → gehört gefixt (Verdopplung sollte
  NICHT pauschal Push/Squat bevorzugen)._
_- s2==s6 sind identische "Lower A"-Templates (beide hinge-Slot) → Picker (Stub UND echter Claude)
  hat keinen Anlass zu variieren → derselbe hinge-Lift 2×/Woche. DAS ist die strukturelle Wurzel
  von ~160 der 224 6-Tage-Regel-3-Funde — NICHT (nur) Round-Robin/Stub-Artefakt._
_- KORREKTUR früherer Lesart: hinge-Repeat bei 6T ist strukturell (Template-Dublette), nicht
  Bibliotheks-Knappheit und nicht bloß Stub-Picker. Pool-Erweiterung allein löst es NICHT._
_- Gegenbeweis dass es Artefakt ist: 5-Tage-Pfad (:365) hängt eine DISTINKTE Akzent-Session an
  statt zu duplizieren. Fix-Richtung: analoge distinkte 6. (und 5.) Session für 6 Tage._
_STATUS: Fix zurückgestellt bis nach vollem Output-Review-Lauf (alle 12 Profile)._

_**KORREKTUR (nach A/B/C-Test, Commit b6aa83a):** Die frühere Einordnung "Template-Verdopplung
ist die strukturelle Wurzel der 6-Tage-Regel-3-Repeats" war ZU ENG. Der A/B/C-Fix (distinkte
Sessions statt [:2]) hat die Repeats NICHT reduziert (Sweep 224→224, bodyweight L1 sogar 2×→3×).
Wahre Wurzel: pattern-basierter Picker × mehrere hinge-Sessions × dünner L1-Pool — der Stub füllt
alle hinge-Slots mit derselben Übung, egal ob die Sessions distinkt sind. → bestätigt Lesart 2
(Picker-Artefakt), nicht Template. A/B/C bleibt wertvoll als REBALANCING-Fix (Push/Pull/Hinge-
Schieflage behoben, spec-konform), löst aber Regel 3 nicht. Regel-3-Repeat am echten Claude zu
prüfen (Stub ≠ Produktivpfad). Zusatz-Spannung: mehr Hinge-Frequenz (Coach-Wunsch) erhöht bei
dünnem Pool die Repeats — Coach-Ziel und Regel-3-Ziel im Konflikt._

_**BEFUND 2 (Regel zu streng): Regel 3 ist level-blind.**_
_Grundübungs-Wiederholung bei L1/Anfänger ist didaktisch RICHTIG (Technik/Frequenz). Regel 3
flaggt sie trotzdem als Mangel. COACH-URTEIL (Alen): bei L1 ist Wiederholung der Grundübung ok.
Kandidat: Regel 3 level-abhängig machen (L1 darf Grundübung wiederholen, L3/L4 nicht)._

_**BEFUND 3 (Knappheit zeigt sich als Pattern-Bruch): Regel 2.**_
_case14: T-Supermans (pull_horizontal) in hinge-Slot — echter Claude wich aus, weil L1-bodyweight-hinge
nur Glute-Bridge-Varianten hat (Pool erschöpft). Echte Knappheit, zeigt sich als Slot-Pattern-Bruch.
Außerdem Tag-Grenzfall: Single Leg Glute Bridge (hinge-getaggt) in single_leg-Slot — die Übung
gehört fachlich in BEIDE Welten; Ein-Pattern-Zuordnung ist hier zu eng._

_**Gesamteinordnung:** Bibliothek solide, Regeln greifen — aber der 6-Tage-Split hat eine
strukturelle Schwäche ([:2]), und Regel 3 ist für L1 zu streng. Substanz-Bewertung der Pläne
(großes Bild, alle Profile) steht noch aus — Lauf 1 deckte nur die 3 Extrem-6T-Profile ab._

### Output-Review Lauf 2 — voller Lauf (run3, alle 15 Profile) + Coach-Review
_15/15 generiert, 0 FAILED. Checker (--run-dir): 7/15 regelkonform. Coach-Review (Alen):
Gerüst überdurchschnittlich solide — Periodisierung, Tier-Logik, Pausen, Tempo, Pattern-
Abdeckung, Knie-Verletzungslogik exzellent (übertrifft kommerzielle Apps). Substanz trägt.
Arbeit liegt im Feintuning, NICHT im Fundament._

_**GERÜST — BEHALTEN (nicht anfassen):**_
_- 3:1-Welle (Akkumulation→Progression→Intensivierung→Deload) intensitätsgeführt, korrekt._
_- RIR zielabhängig sinkend (MA 3→2→2, L4→1, Longevity 4→3→3), Volumen flach + Mike-Rampe W3._
_- L1-Deckelung greift (RIR 3 durchgängig, Anfänger nicht ins Versagen). Deload ~50%+RIR4-5._
_- Pattern-Abdeckung vollständig (alle 7 Muster/Woche), Push/Pull ausbalanciert (Pull≥Push),_
  _Carry eingebaut, Equipment-Logik + Tempo/Cues lehrbuchkonform._

_**PRIO 1 — Muskelvolumen-Balance (größte Baustelle, NEU):**_
_- Glutes/Posterior-Chain 27-39 Sätze/Woche >> produktiver Bereich (MAV ~12-18). Ursache:_
  _hinge + single_leg + glute_bridge + hip_thrust laufen ALLE auf dieselbe Gruppe — Generator_
  _ist muskelblind (wählt nach pattern, zählt nicht pro Muskel) → Posterior-Chain-Stacking._
_- Gegenstück: Arme (Bizeps/Trizeps 0-3), Seitschulter (2-4), Waden (0-4) unterversorgt._
  _Für MA-Ziel zu wenig direkte Armarbeit; Seitschulter bei BW/KB equipmentbedingt limitiert._
_- VERBINDUNG zur zurückgestellten Muskel-Achse: NICHT die Iso-Frage (gezielt Bizeps), sondern_
  _Volumen-BILANZIERUNG pro Muskel. Machbar OHNE volle Muskel-Achse: vorhandene (deskriptive)_
  _muscle_groups-Tags in eine Zähl-/Deckel-Logik einspeisen (begrenzen, wie oft eine Gruppe Primär)._
_- FIX-RICHTUNG (Montag zu entscheiden): Glute-Volumen deckeln, Sätze auf Arme/Seitschulter/Waden_
  _umverteilen, v.a. Muskelaufbau-Pläne._

_**PRIO 1b — Zähl-Verdacht (möglicher echter BUG, ZUERST prüfen):**_
_- Verdacht: unilaterale Übungen (Bulgarian, Lunge, SL-RDL) werden als "3 Sätze" gezählt statt_
  _"3 pro Bein". Falls die interne Volumen-Bilanz uni=bilateral zählt, unterschätzt sie die reale_
  _Beinarbeit → Glute-Dominanz noch größer als Reports zeigen. ÜBERPRÜFBAR im Code (berechne_volumen/_
  _Volumen-Bilanz). Klären VOR der Balance-Arbeit, da es die Grundlage der Volumensteuerung betrifft._

### PRIO 1/1b — Muskel-Volumen-Messung durchgeführt (Reframe + Befund)
_REFRAME bestätigt: Es gibt im Code KEINE Muskel-Volumen-Bilanz und KEIN uni/bilateral-Konzept
(berechne_volumen rechnet rein pro Tier, nie pro Muskel). "Zähl-Bug" war kein Bug, sondern
fehlende Fähigkeit. PRIO 1b fällt mit PRIO 1 zusammen._

_MESSUNG (grob: primär-only, Schulter gruppiert, uni noch nicht ×2) über alle 15 run3-Pläne:_

_**Glute-Dominanz ist KEIN flächendeckendes Problem — konzentriert auf 6-Tage:**_
_- 3-5-Tage-Pläne (7 Stück): Glutes 8-15 Sätze/Wo = im produktiven Bereich (MAV ~12-18). OK._
_- 6-Tage-Pläne (case09/13/14/15): Glutes 30-39 = klar zu viel. case06 (L4, 5T): 29 grenzwertig._
_- WURZEL überlappt mit [:2]-Split (PRIO 4): s2==s6 dupliziert die glute-lastige Lower-A-Session
  → Glute-Volumen mechanisch verdoppelt. Der [:2]-Fix löst den GROSSTEIL der Glute-Dominanz mit._
_→ KEINE komplexe Muskel-Steuer-Logik nötig. Hebel ist der [:2]-Fix (ohnehin geplant)._

_**Arme/Waden-Unterversorgung — separat, NICHT vom Split-Fix lösbar:**_
_- Biceps: 0 Sätze in 11/15 Plänen. Calves: 0 in 12/15. NICHT umfangabhängig (fehlt auch in
  großen Plänen). Ursache: Pool-Imbalance (glutes 73 Primär-Vorkommen vs. biceps 2, calves 3)
  + Generator muskelblind. Diese Muskeln haben kein Pattern-Zuhause._
_→ Das ist die zurückgestellte ISO-SLOT-Frage (Arme/Waden brauchen Iso-Slot zum Selektiertwerden).
  Messung bestätigt rückwirkend: Iso-Slot-Idee ist der richtige Weg für DIESES Teilproblem.
  Bleibt zurückgestellt._

_**Offene Bausteine, falls später echte Muskel-Bilanz gewünscht (NICHT jetzt):**_
_- secondary-Gewichtung (abs 104× sekundär → bei Vollzählung Verzerrung; primär-only oder sek ⅓)._
_- Schulter-Token-Gruppierung (4 Tokens: shoulders/front/lateral/rear) für ehrliche Schulter-Summe._
_- unilateral-Marker (hand-getaggt, ~25-35 Kraft-Übungen) für korrektes ×2-Zählen der Beinarbeit._
_  Name-Heuristik unsauber (37 Treffer mit False Positives einarmig≠einbeinig), pattern=single_leg
  auch kein sauberer Proxy. Expliziter Marker nötig, falls Bilanz Steuerungs-Grundlage werden soll._

_STATUS: PRIO 1 weitgehend auf [:2]-Fix reduziert. Arme/Waden → Iso-Slot (zurückgestellt).
Volle Muskel-Bilanz als Werkzeug bleibt optional/später._

_**PRIO 2 — case07 Wirbelsäule (einziger SAFETY-Befund):**_
_- Plan enthält schwerste axiale Last des Sets: Trap Bar DL + RDL + Barbell Hip Thrust, progressiv_
  _bis RIR 2 bei Rücken-Klient/L2. Positiv: Trap Bar (wirbelsäulenfreundlichste Variante) + McGill-_
  _Big-3 (Bird Dog/Curl-Up/Pallof) korrekt eingebaut. ABER: progressive DL-Last bis RIR 2 zu forsch._
_- FIX-RICHTUNG: Hinge-Intensität bei Wirbelsäulen-Verletzung deckeln (RIR ≥3), Block 1 eher_
  _Hip Thrust/45°-Back-Extension statt freiem Kreuzheben._

_**PRIO 3 — Fettabbau-Conditioning zu plyo-lastig:**_
_- case02 (+teils 05/06): Broad/Split/Tuck Jumps, Plyo-Pushups, Burpees in hoher Dichte —_
  _gelenkbelastend, fürs Ziel nicht nötig, Adhärenz/Regeneration leiden. Mehr Low-Impact_
  _(Carries, Skipping, Step-back-Burpee, Ruder/Bike-Intervalle). case03 (Knie) vermied Plyo_
  _korrekt → konsequent auf alle Fettabbau/Schonungs-Fälle übertragen._

_**PRIO 4 — 6-Tage [:2]-Template-Verdopplung (bekannt, bestätigt):**_
_- split_selector.py:368 [:2] dupliziert [UA,LA,UB,LB]+[UA,LA] → Push 2×/Pull 1×, Squat 2×/Hinge 1×._
  _Coach-Urteil: suboptimal (Vorderseite verdoppelt, Pull/Hinge meist Schwachstelle)._
_- Bestätigt in run3: tritt auch bei voller Gym-Ausstattung auf (case09) → strukturell, nicht_
  _Knappheit. Ist die Wurzel der 6T-Regel-3-Repeats (s2==s6 identische Templates)._
_- FIX-RICHTUNG: distinkte 5./6. Session (analog 5-Tage-Pfad :365, der eine distinkte Akzent-_
  _Session anhängt statt zu duplizieren)._

_**PRIO 5 — Tag-Fehler + Bibliothekslücke (klein, klar):**_
_- gym_face_pull als pattern "push_vertical" getaggt — FALSCH (Face Pull ist Zugmuster). Landet_
  _in pull_horizontal-Slots → Regel-2-Funde case07/09. Tag korrigieren (pull_horizontal o.ä.)._
_- bw_tibialis_raise als "core" getaggt, landet in single_leg-Slots (case05/06/14). Isolations-/_
  _Prehab-Move, eigentlich kein Haupt-Slot-Füller. Einordnung klären._
_- bw_single_leg_glute_bridge (hinge) in single_leg-Slot (case14) — Tag-Grenzfall, Übung gehört_
  _fachlich in BEIDE Welten. Mehr-Pattern-Zuordnung erwägen._
_- BIBLIOTHEKSLÜCKE: bw_pallof_press fehlt — echter Claude griff 3× danach (case07, Wirbel-Klient),_
  _Validator wies ab, Retry. Bedarfssignal vom Modell selbst. Anti-Rotations-Core für Wirbelsäule._

_**PRIO 6 — Regel 3 level-blind (Checker-Feinschliff):**_
_- Regel 3 flaggt Grundübungs-Wiederholung auch bei L1, wo sie didaktisch RICHTIG ist (Coach-Urteil)._
  _Kandidat: Regel 3 level-abhängig (L1 darf Grundübung wiederholen, L3/L4 nicht)._

_**case-spezifisch klein:** case12 (20min L1): Core 8 Sätze > Brust 5 — Core auf 2-3 kürzen,_
_Platz in Compound. case04: RDL 2×/Woche L2 = normale Frequenz, unkritisch._

_STATUS: Alle Fixes offen, Reihenfolge Montag zu entscheiden. Empfehlung: PRIO 1b (Zähl-Bug)_
_zuerst prüfen, da Grundlage; dann PRIO 2 (Safety); dann PRIO 1/3/4. Gerüst bleibt unangetastet._

### Output-Review Lauf 3 — echter 6-Tage-Lauf (case09 gym + case14 bodyweight, nach A/B/C)
_Zweck: klärt am echten Claude, ob die 6-Tage-Regel-3-Repeats Picker-Artefakt (Lesart 2) oder
echte Knappheit (Lesart 1) sind. ANTWORT: hängt von der Pool-Tiefe ab — beide Lesarten stimmen,
je nach Ecke. Das verfeinert die vorige Korrektur ("alles Picker-Artefakt" war zu pauschal)._

_**KERNERGEBNIS — Pool-Tiefe entscheidet:**_
_| | reicher Pool (gym L2) | dünner Pool (bw L1) |_
_| Stub | repeated | repeated |_
_| echter Claude | VARIIERT (0 Regel-3-Funde) | repeated (glute_bridge 3×, inverted_row 2×) |_
_| Diagnose | Picker-Artefakt (Stub) | echte β-Knappheit |_
_| Fix | keiner nötig | Pool-Erweiterung (nicht Picker) |_

_- case09 (gym): 0 Regel-3-Funde über 6 distinkte Sessions. Der echte Claude variiert sauber bei
  reichem Pool. Nur 4 Regel-2-Funde, ALLE = gym_face_pull-Tag-Bug (push_vertical statt pull). Der
  A/B/C-Fix bewährt sich am echten Output: Sessions distinkt, kein Compound wiederholt._
_- case14 (bw L1): echter Claude repeated wie der Stub (glute_bridge 3× über alle 3 Lower-Sessions)
  — bei erschöpftem L1-bodyweight-hinge-Pool KANN er nicht variieren. + t_supermans-Substitution
  in hinge-Slot (Ausweichen mangels Pool). Das ist reale β-Knappheit, Regel 3 flaggt KORREKT._

_**FOLGERUNGEN:**_
_- Regel 3 (PRIO 6): in reicher Ecke ZU STRENG (über-flaggt), in dünner Ecke KORREKT. → Regel 3
  sollte pool-/level-abhängig sein, nicht pauschal flaggen. Bestätigt durch echten Output._
_- gym_face_pull-Tag-Fix (PRIO 5): größter klarer Hebel — verursacht ALLE 4 case09-Funde. Am
  echten Output dreifach bestätigt (auch tibialis_raise, single_leg_glute_bridge)._
_- bw-L1-hinge bleibt reale Lücke: "mehr Glute-Bridge-Varianten" hilft NICHT (Regel 3 zählt
  distinkte ids) — bräuchte eine NICHT-Brücken-L1-hinge (z.B. Good-Morning ohne Last)._
_- Checker-Bewertung: Brücke fing exakt die erwartbaren Dinge, keine Fehlalarme, keine Claude-
  Überraschungen. Checker funktioniert am echten Output wie vorgesehen._

### Mehr-Pattern-Modell — Doppelnatur-Übungen (aus Lauf 3 + Name/Tag-Analyse)
_Erkenntnis: Der echte Claude folgt der BEWEGUNGS-SEMANTIK einer Übung, nicht stur dem pattern-Tag.
Belegt: bei 9 Pike/HSPU-Übungen (Name "push-up", Tag push_vertical) wählt er KORREKT vertikal —
er ist kein naiver Namens-Matcher. Konflikt entsteht nur, wo Name UND Tag beide vertretbar sind._

_**Cluster A — Single-Leg-Hip-Hinges (5 Übungen, echte Doppelnatur):**_
_bw_single_leg_rdl, gym_single_leg_rdl_db, kb_single_leg_rdl, bw_single_leg_glute_bridge,
gym_single_leg_hip_thrust_db — alle jetzt konsistent hinge (Commit c4f4eb9, war inkonsistent).
ABER: sie sind gleichzeitig Hüft-Hinge (Bewegung) UND einbeinig (Stand). Claude setzt sie
weiter manchmal in single_leg-Slots → erzeugt formale Regel-2-Funde, die fachlich okay sind
(die Übung IST einbeinig). Kein Einzel-Retag löst das: hinge ist biomechanisch richtig,
single_leg würde Progressions-Ketten brechen._

_**Gemeinsame Wurzel mit der Iso-/Rolle-Achse:** Das Datenmodell erlaubt nur EIN pattern pro
Übung, aber manche Übungen gehören in ZWEI Kategorien (Single-Leg-Hinge = hinge+single_leg;
Tibialis-Raise = Waden-Iso, weder sauber core noch single_leg). Symptome derselben Grenze._

_**Optionen (zurückgestellt, Modell-Erweiterung):**_
_(a) pattern als Liste (patterns: [hinge, single_leg]) — berührt filtere_uebungen + Regel 2 + Picker._
_(b) Regel 2 whitelistet bekannte Doppelnatur-Übungen als erlaubte Ausnahmen._
_(c) Status quo akzeptieren: hinge-Tag korrekt, Claudes single_leg-Platzierung ist fachlich ok,
    Regel-2-Fund als bekannter False-Positive führen._
_STATUS: zurückgestellt. Bündeln mit Iso-Slot-/Rolle-Achse (alle = "eine Übung, mehrere Rollen")._

## Output-Review MVP-9 — offene Befunde

_Aus dem echten 12-Case-Output-Review (test_runs/2026-06-19_run3/REVIEW.md). Kraft-Auswahl
(Claude) durchweg gut; offene Punkte fast alle in der deterministischen Python-Logik._

**ERLEDIGT:** Befund 1 Knie — Conditioning joint_stress-Tagging (`08923b2`) · Cardio-Spec-Alignment,
LISS-15/HIIT-12 raus (`ae0fe0b`) · Befund 2 Dauer/Display — proportionales Warm-up + kosmetische Anzeige (`fd7d3e5`) ·
Befund 3 Volumen-Korridore + Mike-Rampe (Modell A v2, `04e43ca`).

**MITTEL:**
- **Befund 4 — RPE 9 ab Woche 1**, keine Aufbau-Welle (nur Deload-Abfall). Cases 6/5/3/11.
  _Braucht Coaching-Entscheid:_ RPE-Wellen-Schema pro Block.

**NIEDRIG:**
- ~~**Befund 5 — statische Notiz** „Woche 1…" in W2–4~~ **ERLEDIGT**: week-agnostische Notiz-Regel +
  entschärfte few-shot-Vorbilder im prompt_template. _Optional später:_ echte **Per-Woche-Notizen**
  (Claude pro Woche statt einmal) — größerer Eingriff (4× Calls / week-aware Prompt), nur falls
  wochenspezifische Hinweise gewünscht.
- **Befund 6 — Label vs. Inhalt:** Pull-Tag mit Push-Slots; „+Carry"-Tag ohne Carry-Slot. Cases 1/10 + alle Splits.
- **Befund 7 — `rpe_hinweis` (RIR-Wortlaut) auf Zeit-Holds**, nur L1 (Claude-Output).
- **Befund 1 WS-Teil — Conditioning `spine`-Tagging dünn** (nur `cond_row_erg` trägt `spine`); kein
  akuter Sicherheitsfall, da echte WS-Lader bereits getaggt.
- **Warm-up tagesspezifisch** — System-Hochfahren + gezielte Aktivierung pro Tages-Pattern; eigene Logik.

## Datenschutz / DSGVO

### Datenschutz Prompt-Pfad — verifiziert + offene Go-Live-Punkte
_Prompt-Pfad pseudonymisiert verifiziert (vor erstem echten Call): SYSTEM_PROMPT PII-frei,
USER-Prompt trägt nur fachliche Felder (Alter, Level, Ziel, Equipment, Verletzungen, berechnete
Trainingsparameter, gefilterte Übungen). Sauber DRAUSSEN: vorname, motivation, stress_level,
schlaf_stunden, client_id, trainingsjahre, email. Call ohne Zusatz-Metadaten; Prompt-Inhalt
wird nie geloggt (nur vorgang_id + Modell). Kein Leak, kein Bug._

_OFFEN VOR GO-LIVE (kein Code-Fix, sondern Recht/Doku — NICHT von Claude.ai abschließend beurteilbar,
gehört zu Datenschutz-Expertise):_
_1. Exaktes Alter geht an die API (personenbezogen). Datensparsamkeits-Option: Altersband statt
   exaktem Wert — zu prüfen, ob die Auswahl-Logik ein Band verträgt (alter numerisch gebraucht?)._
_2. Verletzungen = Gesundheitsdaten (DSGVO Art. 9, besondere Kategorie), gehen an Anthropic
   (US-Auftragsverarbeiter). Erfordert: AVV/DPA mit Anthropic, Rechtsgrundlage/Einwilligung für
   Art.-9-Daten im Fillout-Intake, Doku der US-Übermittlung. VOR Go-Live von Datenschutz-Expertise
   prüfen lassen._
_Für Output-Review mit TESTDATEN unkritisch (keine echten Klientendaten). Relevant erst bei
echten Klienten (MVP-12/Go-Live)._

## Verletzungs-Tagging — Audit & Tier (nach elbow-Nachtrag 2026-06-22)

- **Last-/intensitätsabgestufter Verletzungs-Tier (Modell-Grenze):** `joint_stress` ist heute
  **binär** (belastet ja/nein) — keine Last-/Intensitätsabstufung. Folge: bei Ellbogen bleiben nur
  leichte BW-Rows (selbst Ellbogen-Zug) als „tolerierbarer" Rücken-Reiz übrig, während schwere KB-Pulls
  korrekt rausfallen — die Unterscheidung „leicht tolerierbar vs. schwer meiden" ist aber **nicht
  modelliert**. Idee: ein „light/tolerable"-Tier, das leichte Varianten überleben lässt, wenn der
  echte Lader gefiltert ist. Verknüpft mit der fehlenden ellbogen-schonenden Zug-Alternative (KB/BW).
- **Systematischer Verletzungs-Tag-Audit über alle 8 Typen** (`knie · schulter · wirbelsäule · hüfte ·
  ellenbogen · handgelenk · hals · knöchel`): elbow + ankle + knee sind nachgezogen; offen sind v. a.
  `hals/neck` (heute nur 1 Tag) und eine Vollprüfung, dass je Gelenk die echten Lader getaggt sind.
  - **Audit-Leitregel:** pro Gelenk **nur die wirklich belastenden** Übungen taggen (kein Über-Filtern).
    **Teilerledigt (2026-06-22):** Stufe 2 ist jetzt **joint-gegated** (`_HIGH_IMPACT_GATED =
    {knee, ankle, hip, spine, neck}`), `bw_burpee` voll getaggt (shoulder/wrist/elbow/knee/ankle/hip).
    **Endstufe:** Stufe 2 **ganz entfernen**, sobald ALLE Impact-Übungen lückenlos joint-getaggt sind
    (Fuß-Sprünge tragen teils noch kein `hip`/`spine` — Stufe 2 bleibt bis dahin Backstop).
## Verletzungs-Tag-Audit (Phase 4, nach MVP-11, checker-validiert) — „nur echte Lader pro Gelenk"

Fachlich prüfen, nur echte Lader taggen, leichte Varianten NICHT — alles checker-validiert in EINEM Zug.
- **elbow-Drücke:** `bw_one_arm_pushup`, `bw_one_arm_pushup_negatives`, `bw_archer_pushup`,
  `bw_pike_pushup_elevated` (aus vetteter Vorschau, in den Audit gefaltet — Drücken lädt den Ellbogen wie Ziehen).
- **spine/hip an geladenen Hinges:** `gym_rdl_db`, `kb_deadlift` ohne Tag; `gym_rdl_barbell` hat `spine`, **nicht** `hip` (Inkonsistenz).
- **knee:** `gym_box_squat` (nur `spine`), `gym_leg_press_machine`.
- **neck:** HSPU-/Handstand-Inversionen (HWS-Last; repo-weit nur 1× `neck`).
- **wrist:** `bw_incline_pushup` (borderline).
- **NICHT taggen (Reha-Keeper):** Reverse Lunge, Step-up.
- **Leitregel:** pro Gelenk ALLE echten Lader über ALLE Muster; leichte Varianten nicht taggen.

## unit-Reklassifikation (Phase 4)

17 rep-basierte Core-Übungen tragen aktuell **interim `unit=zeit`** (Status quo aus Naht 1, Variante A),
gehören aber auf **`unit=reps` + Core-Rep-Range** (Hold-vs-Rep deliberat im Audit entscheiden; Checker
fängt unit/Wert-Inkohärenz). Kandidaten: `gym_hanging_leg_raise`, `gym_hanging_knee_raise`, `bw_v_up`,
`gym_cable_crunch`, `gym_ab_wheel`, `gym_ab_rollout_standing`, `bw_dragon_flag`, `bw_mcgill_curl_up`,
`kb_turkish_getup`, `kb_windmill`, `bw_mountain_climber`, `bw_bear_crawl`, `bw_crab_walk`, `bw_inchworm`,
`bw_tibialis_raise`, `gym_reverse_hyper`, `ath_med_ball_slam`, `ath_med_ball_rotational_throw`.

## Bibliotheks-Bedarfskarte (β-Pool-Lücken, aus PRIO-6-Sweep)

_Maschinell quantifiziert (Commit 0835c2a): wo pool_size < compound-demand, MUSS wiederholt werden —
das sind keine Plan-Defekte, sondern Bibliothekslücken. Quelle für gezielte Erweiterung._

_**48 β-Vorkommen = nur 2 distinkte Tripel = faktisch EINE Wurzel:**_
_- bodyweight L1 hinge → 24× (pool 2 < demand 3)_
_- travel L1 hinge → 24× (pool 2 < demand 3)_
_travel⊇bodyweight (via _EQUIPMENT_INCLUDES) → identischer hinge-Pool (2: nur Glute-Bridge-Varianten)._
_Die 24× = je 6 Kombis (muskelaufbau/recomp × 6T × {30,45,60}min) × 4 Wochen. NUR bei 6 Tagen
(hinge-compound-demand 3 > pool 2); 3-5 Tage (demand ≤2 = pool) nicht betroffen._

_**Fix (EINE Übung löst alle 48):** eine NICHT-Brücken-L1-Hinge für bodyweight (z.B. Good-Morning ohne
Last / bodyweight Hip Hinge) — erreicht via Inklusion zugleich travel. Mehr Glute-Bridge-Varianten
helfen NICHT (Regel 3 zählt distinkte ids; 2 Brücken-Spielarten bleiben 2). bodyweight L1 hinge 2→3
schließt die einzige raumweite β-Lücke._
_STATUS: Erweiterungs-Backlog, nicht dringlich. Abarbeiten wenn Bibliotheks-Pass ansteht._

## Bibliotheks-Erweiterung (Phase 4, Survival-Matrix-gesteuert)

- **KB-Oberkörper dünn:** 1 ladbarer KB-Horizontaldruck (`kb_floor_press`), **0 KB-Vertikalzug** →
  gesunder KB-Klient bekommt den Oberkörper ~92 % als Bodyweight. Teils physikalisch (KB kein
  Vertikalzug), teils echte Lücke (ladbarer Horizontaldruck oberhalb Floor-Press fehlt). Tag-Erweiterung hilft begrenzt.
- **Ellbogen-schonende Band-Züge (Straight-Arm)** fehlen für KB/BW.

### Coverage-Audit-Befund (vollständige Bedarfsliste, Artefakt-Vorbehalt aufgelöst)

_Read-only-Audit über Pattern×Equipment×Skill-Leiter + Muskel-Erreichbarkeit (via
_EQUIPMENT_INCLUDES). Vier echte Übungs-Lücken + ein Vokabular-Hygiene-Thema:_

_**Echte Übungs-Lücken (Programm bricht / Muskel nicht primär erreichbar):**_
_1. carry LEER bei bodyweight + travel → zugleich forearms-Lücke (alle forearms-Primärtreiber
   sind Carries). EINE bodyweight-taugliche Carry-Übung schließt beide (erreicht via Inklusion
   auch kettlebell/hybrid)._
_2. shoulders_rear primär fehlt bei bodyweight + kettlebell (die 3 Treiber Face Pull/Cuban Press/
   Band Pull-Apart sind alle gym oder band-/gym-getaggt) → Rear-Delt-Übung (Band/Bodyweight, kb)._
_3. push_vertical + pull_vertical L1 Pool=1 bei allen Nicht-gym-Welten → L1-vertikale Compounds
   (bekannt; pull_vertical der härteste, Band-Assisted/Scapular als L1-Einstieg)._
_4. Leiter-Löcher: home_gym hinge L3 fehlt · kettlebell + hybrid pull_horizontal L2 fehlt
   (Progression bricht mittendrin) → je 1 Füll-Übung._

_**Daten-Hygiene (separat, KEIN Übungs-Mangel — vor der Erweiterung zu erledigen):**_
_5. Schulter-Vokabular doppelt codiert: generisch `shoulders` (13 prim/27 sek, für KB/Carry/Core/
   Conditioning) vs. spezifisch `shoulders_front/lateral/rear` (fürs Isotraining). Disjunkt, keine
   Mischformen → sauber normalisierbar. Blockiert belastbare Per-Welt-Schulter-Coverage.
   Normalisierung VOR der Erweiterung, damit neue Übungen gleich sauber getaggt werden._

_Methodik-Anker (was "vollständig" heißt): pro Pattern×Equipment durchgehende Skill-Leiter L1→L4
+ jeder große Muskel pro Welt primär (isoliert) erreichbar + genug distinkte Optionen je Slot
für Wochen-Variation. Quellen für Kandidaten: Vadnal (Bodyweight/Band), Israetel (Gym),
Pavel (Kettlebell)._

### Wirkungsmessung Phase-4-Erweiterung (nach Commit 0fe2053)
_Kreuzprodukt-Sweep erneut: **456 → 224 Regel-3-Funde (−51 %)**, betroffene Kombis 90 → 56.
push/pull_vertical in den Restfunden NICHT mehr vorhanden — vertikaler β-Engpass strukturell
gelöst (Pool 1→≥2). Regel 2/4/5/6 weiter 0 Funde, 0 Level-Mismatches, Verletzungs-Sweep 216/216._

_**Diagnose-Verschiebung — die 224 Restfunde sind NICHT mehr Library-Knappheit:**_
_- 100% hinge, konzentriert auf bw_glute_bridge (192) + kb_deadlift (32), L1 × travel/bodyweight/kb/hybrid × 5-6 Tage._
_- ABER: L1-hinge-Pool ist jetzt 2-4 distinkt (travel/bw: 2 = glute_bridge + single_leg_glute_bridge;
  kb/hybrid: 4; home_gym: 3). Bei Pool≥2 ist Wiederholung NICHT mehr arithmetisch erzwungen._
_→ Lesart 1 (echte Knappheit) für den Rest WIDERLEGT. Die 224 sind Lesart 2 = Stub-Picker-Artefakt:
  _auto_claude_output (Round-Robin) wiederholt bw_glute_bridge statt auf die 2. Übung zu wechseln.
  Der echte Claude würde voraussichtlich variieren → Regel 3 erfüllt. Klärung am Output-Review
  (echter Claude-Lauf), NICHT durch weitere hinge-Übungen (Pool reicht bereits)._

_**Hebel verschoben: von Daten zu Picker.** Bibliotheksarbeit für Regel 3 ist abgeschlossen —
weitere hinge-Übungen würden Regel 3 nicht verbessern. Restfunde sind ein bekanntes Stub-Verhalten._

_**Zwei kleine offene Punkte (niedrige Priorität, kein Regel-Verstoß):**_
_- bodyweight-L1-hinge-Variety: die 2 Optionen sind beide Glute-Bridge-Spielarten — unter Regel-3-Radar,
  aber dünne Bewegungsvielfalt. Optional: eine nicht-Brücken-L1-hinge (z.B. Good-Morning ohne Last)._
_- home_gym hinge L3-Loch: L2 hat 3 Optionen, L4 nur Nordic Curl — fehlende L3-Progressionsstufe,
  KEIN Auswahl-Bruch (skill-Filter liefert L1+L2 weiter). Kosmetisch._

_**carry bodyweight/travel: bewusst NICHT gefüllt** — echter beladener Carry braucht Last;
reines Körpergewicht hat keine sinnvolle Carry-Übung. Scope-Entscheid, kein offener Punkt._

## Befund 6 KORRIGIERT (kein Template-Bug)

- Upper A/B = **Schwerpunkt-Tage** (Betonung im Compound-Tier, nicht im Slot-Count); 5-Slot-Upper =
  2 Push : 2 Pull : 1 Core ist Vorlage.
- Fix = nur **ehrliche Labels** („Oberkörper – Push-Schwerpunkt") → Phase 1, kleiner Punkt.

## Auswahl-Qualität — URSACHEN-Karte (MVP-11.5, checker-validiert)

Root-Cause-Inspektion 2026-06-22: **4 unabhängige Wurzeln, kein gemeinsamer Root.** Symptom-Fix
verlagert nur das Problem — Mechanismus fixen.

**α SKILL-PROXY + fehlende Ziel-Eignung** (Overhead Squat als Hypertrophie-Squat).
Ursache: Primär-Wahl=Claude, gesteuert von prompt_template Prinzip 6 („L3-4 anspruchsvolle Compounds");
`skill_level` misst Komplexität, nicht Eignung (overhead=4 > back=2). Kein Ziel-Eignungs-Signal im Prompt.
FIX: (i) Bewegungs-Rolle-Feld in exercises.json `{massereiz_primär|skill|mobilität|accessory}`;
(ii) Prinzip 6 reframen: „ziel-geeigneter Massereiz als Primär", Komplexität NICHT als Kriterium;
Ziel→Rolle-Mapping im Prompt. **DESIGN-ENTSCHEID offen:** Rolle-Enum+Mapping (Lean) vs Ziel×Übung-Matrix.

**β POOL-KNAPPHEIT** (Cossack als travel-Squat). travel/home-squat-Pool: 0 ladbare bilaterale Squats.
FIX: Bibliotheks-Erweiterung (Survival-Matrix-gesteuert) — Metadaten/Prompt lösen das NICHT.

_β raumweit quantifiziert (Kreuzprodukt-Sweep `23dd5a3`): 456 Regel-3-Verstöße über
90 von 1536 Kombis. Muster: L1 (74 Kombis) × dünnes Equipment (travel 30 · kettlebell 18 ·
bodyweight 18 · home_gym/hybrid je 10 · gym 4) × viele Tage (6T:52 · 5T:24 · 4T:14 · 3T:0).
Mechanismus: zu wenige distinkte ladbare Compounds, um alle Wochen-Compound-Slots ohne
Wiederholung zu füllen. ZWEI LESARTEN, noch nicht entschieden:_
_(1) Echte Pool-Knappheit → Bibliothek erweitern (Phase 4); der Sweep liefert die Bedarfs-Landkarte._
_(2) Stub-Picker-Artefakt → der echte Claude würde im dünnen Pool cleverer variieren/Fallback ziehen,
wo der deterministische Round-Robin-Stub stur wiederholt._
_VERIFIKATION: nur an echten Claude-Läufen für genau diese Kombis (L1×travel/kb/bw×5-6T)
klärbar → an den Output-Review koppeln, NICHT am Checker/Stub "wegmachen" (Regel 3 ist korrekt)._

_β Ursache lokalisiert (Filter-Pfad-Inspektion, roh vs. nach Fallback):_
_- roh == nach Fallback überall → _apply_pattern_fallback feuert in der β-Ecke NICHT
  (greift nur bei leerem Pool; keine 0-Pools). Knappheit = reine Stammdaten-Lücke, kein Fallback-Effekt._
_- KRITISCH: push_vertical UND pull_vertical haben Pool=1 bei L1 für travel/kettlebell/home_gym/hybrid
  (bodyweight ebenso). Bei Pool=1 ist Wiederholung arithmetisch unvermeidbar, sobald die Woche
  das Pattern in ≥2 Compound-Slots braucht — unabhängig vom Picker._
_→ Lesart (2) "Stub-Artefakt" für die Pool=1-Fälle WIDERLEGT (echter Claude kann keine nicht-existente
  zweite Übung wählen). Lesart (1) "echte Bibliothekslücke" BESTÄTIGT. Kein API-Test dafür nötig._
_- Grauzone Pool=2-3 (squat/hinge/pull_horizontal): klügerer Picker könnte variieren, solange Slots ≤ Pool;
  bei 5-6-Tage-Splits oft trotzdem zu wenig. Hier bliebe ein echter Claude-Lauf aussagekräftig (sekundär)._
_- gym durchweg sauber (keine compound-Pattern ≤3) — deckt sich mit Sweep (gym 4 Kombis vs travel 30)._

_BEDARFSLISTE (L1, vor Erweiterung): L1-taugliche (skill_level=1) vertikale Compounds für
NICHT-gym-Equipment — push_vertical + pull_vertical sind der Hauptengpass (Pool 1→≥2 löst den
Großteil der 456 Funde strukturell). Konkrete Übungsauswahl = Coach-Entscheidung (offen)._

**γ-latent SLOT-PATTERN NICHT ERZWUNGEN.** Assembler prüft eingesetztes pattern nie gegen Slot-pattern
(`valid_auswahl` zieht aus allen 161, nicht Slot-Pool); `_pruefe_vollstaendigkeit` zählt nur Slots.
Heute hält nur Claudes Disziplin die Pattern. FIX: striktes Slot-Pattern-Enforcement (verwerfen/
ersetzen bei Mismatch) — kleine Assembler-Naht.

**δ CROSS-SESSION-WIEDERHOLUNG** (Conventional Deadlift 2×/Woche, gleicher Lift). Keine Dedup über
Sessions. FIX: Varianten-/Dedup-Regel (gleicher Primär nicht 2× ohne Variation) — eigene Naht.

**GEMEINSAMER ERMÖGLICHER:** keine Bewegungs-Rolle-Dimension; `skill_level` = Komplexität ≠ Eignung.
**KOMBI-NAHT** deckt α+γ-latent (Rolle+Ziel-Eignung+Prinzip-6+Enforcement); β=Bibliothek; δ=Dedup.
**Checker (MVP-11) validiert:** Primär-Rolle passt zum Ziel; eingesetztes pattern==Slot-pattern; kein
Primär-Lift 2×/Woche ohne Variation.

## JSON-als-Vertrag (MVP-12, API-Contract mit Manu) — Kunde sieht JSON, nicht PDF

Grundsatz: Das JSON muss kundenseitig vollständig/korrekt sein; das Frontend darf NICHTS re-derivieren.
PDF = nur Dev-/Coach-Vorschau. Verifikation ab jetzt gegen JSON, nicht PDF.
- **fokus_anzeige FEHLT:** JSON trägt nur Routing-Key `fokus` („Upper A — Push"); das kundenseitige Label
  („Oberkörper – Push-Schwerpunkt") lebt nur im pdf_generator → muss als eigenes Feld ins JSON.
- **Conditioning-Semantik IMPLIZIT:** `wdh` ist fusionierter String („30 Sek"/„15 m"/„12 Wdh"); `saetze`=Runden
  vs Sätze nur aus `session_typ` ableitbar. Frontend müsste raten → strukturiert: **wert + einheit getrennt**,
  Runden-vs-Sätze + Format explizit pro Block. (Spiegelt das PDF-only „N Runden · Arbeit/Pause".)
- **KONSEQUENZ:** kundenseitige Befund-6-Labels + format-bewusstes Conditioning sind PDF-only erledigt,
  JSON-seitig OFFEN → hier im API-Contract schließen. Kandidat für „free pre-lock change" wie rpe→rir.
- **TODO:** vollständige kundenseitige JSON-Shape mit Manu definieren (welche Felder rendert das Frontend,
  welche Display-Strings liefert das Backend) BEVOR der Contract lockt.

## Reihenfolge (2026-06-22)

Phase 1 Output-Closeout → MVP-10 Persistenz → MVP-11 Checker → Phase 4 Bibliothek + Tag-Audit
(checker-validiert) → MVP-12.

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

## Isometrie-/Zeit-basierte Übungen (Fundament-Naht, geparkt, nach Output-Review)

- **Problem:** Zeit-/Hold-Vorgaben funktionieren heute **NUR über `pattern=="core"`** (`_CORE_WDH`
  liefert feste `"20sec"`..`"60sec"`, `_tempo` gibt `"halten"`). Es gibt **kein** per-Übung-
  Isometrie-Signal. Eine Hold-Übung mit anderem Pattern (z.B. push_vertical „Pike Hold") bekäme im
  Kraft-Slot Wdh-/Tempo-/RPE-Vorgaben (`"3×8-12 @ RPE 7, Tempo 2-0-1-0"`) = **Unsinn**.
- **Betrifft NICHT nur push_vertical:** ganze Hold-Familie über alle Patterns — Pike/Downward-Dog/
  Wall-Handstand Holds (push_vertical), Superman, Hollow Hold, Plank-Varianten, Wall Sit, L-Sit,
  isometrische Squat-/Hinge-Holds etc.
- **Lösung (Fundament, eine Naht):** (1) **Schema-Signal** am Eintrag — Marker „ist_isometrisch"
  (eigenes bool-Feld ODER `pattern_tags`-Wert), Entscheidung offen. (2) **Assembler `_wdh`/`_tempo`:**
  Isometrie-Zweig, der **Zeit statt Wdh** und `"halten"` statt Tempo ausgibt — gesteuert durch das
  **Übungs-Signal**, NICHT durch `pattern=="core"`. (3) **Periodisierung/RPE-Welle (MVP-6):** Zeit
  über die 4 Wochen progressieren (z.B. 30→40→50s) statt Wdh — heute ist auch core-Zeit statisch,
  nicht progressiv.
- **Überschneidet:** MVP-6 (Welle), Assembler-Vorschreibung, Schema.
- **Konsequenz für die Bibliothek:** alle geplanten **HOLD-Übungen sind bis dahin geparkt.** Konkret
  zurückgestellt (push_vertical, Coach-Liste): Downward Dog Hold, Pike Hold, Elevated Pike Hold,
  Wall Handstand Hold. Diese erst anlegen, wenn die Naht steht.
- **Blockiert NICHTS Aktuelles:** rep-basierte Einträge schließen die Lücken; Output-Review (9-4)
  läuft ohne Holds. Reichert die Bibliothek an, kein Plan scheitert ohne.
- **Timing:** eigener Brocken, NICHT jetzt. Nach Output-Review einplanen (Bezug zur geparkten
  „Progression V2", da beide die Zeitachse/Vorschreibung betreffen).

## Klimmzugstangen-Annahme + Alternativ-Übungs-Anzeige (Produkt-Entscheidung, geparkt)

- **INTERIM-ANNAHME (aktiv):** bodyweight/travel-Klienten haben eine **Klimmzugstange/Ringe**. Die
  4 BW/travel-tauglichen pull_vertical-Übungen (`bw_ring_row`, `bw_negative_pullup`, `gym_chinup`,
  `gym_pullup`) tragen `equipment_requires=[]` und werden **ungated** zugewiesen. Ein wirklich
  ausrüstungsloser Klient könnte sie nicht ausführen — heute **bewusst in Kauf genommen** (kein
  Loch, kein Fehlschlag; Pool ≥ 1).
- **Hintergrund:** `KlientenInput.equipment` ist EIN Wert; es gibt **kein „hat Stange"-Signal** im
  Intake. Daher kann das System „bodyweight mit Stange" nicht von „ohne" trennen.
- **Gewünschte Lösung (später, Coach-Idee):** Der Plan zeigt zu stangen-abhängigen Übungen eine
  **Alternative** an („Pull-up — falls keine Stange: Inverted Row"), Kunde wählt selbst → **kein
  Intake-Signal nötig**. `substitution_pool` (100 % befüllt) liefert die Rohdaten; offen ist, ob das
  Feld bis ins **Klienten-PDF** durchgereicht wird (separate CC-Inspektion noch offen). Mögliche
  Schichten: Plan-Modell, Assembler, PDF, Prompt.
- **Alternative Lösung:** „Klimmzugstange vorhanden?" als Frage in den **Fillout-Intake** (beim
  Typeform→Fillout-Wechsel ohnehin Neubau) → dann `equipment_requires`-Gating + der bestehende
  `_FALLBACK_PATTERN["pull_vertical"]="pull_horizontal"` greift sauber.
- **Timing:** Produkt-Entscheidung, NICHT jetzt. An Fillout-Intake-Neubau und/oder Output-Review
  koppeln. Blockiert nichts Aktuelles.

### Entscheidungsmatrix / Intake-Design (→ MVP-11/12)
Intake aus Backend-Anforderungen ableiten (kein Alt-Fillout — Backend ist die Schranke).
Schritt 1 (read-only): Input-Inventar — jedes vom Backend konsumierte Intake-Feld aus
parser + models + ALLEN Logik-Konsumenten, mit Typ/Enum/Wertebereich + Downstream-Wirkung.
Daraus: (a) Fillout-Fragen-Spec (eine Frage je Feld, Optionen = akzeptierte Enums/Bereiche),
(b) Backbone für den Stimmigkeits-Audit der Kette Level→Split→Equipment→Volumen/RPE→Claude-Auswahl.
Schließt die offene Home-Equipment-Granularität ein (= eine Zelle der Matrix; Alt-TODO Home-Equip
hierin aufgegangen). Nicht-Blocker für Beispielpläne.

- **Stress/Schlaf komplett entfernen (Intake + Code) — Entscheidung getroffen:** `stress_level` (1-10) und `schlaf_stunden` (4.0-10.0) werden heute geparst (`parsers.py`), im Plan-Snapshot gespeichert (`plan_assembler.py`, `KlientenSnapshot`) und zu `recovery_modifier` ausgewertet (`volume_calculator.py` `_recovery_lage`) — wirken aber auf NICHTS (kein Pfad in RPE/Volumen/Deckel/Split/Übungswahl; einziger Leser ist ein Dev-`print` in `test_pipeline.py`). Seit Recovery-Entkopplung (Naht A) + Datenschutz (Naht 9-1, raus aus Claude-Prompt) totes Steuer-Signal. **Entscheidung:** vollständig entfernen — auch als Intake-Frage (kein totes Pflichtfeld, keine ungenutzte Gesundheitsdaten-Erhebung = datenschutzfreundlicher). _Scope:_ Intake-Frage (Fillout) + `models.py` (`KlientenInput` + `KlientenSnapshot`) + `parsers.py` + `volume_calculator.py` (`_recovery_lage`/`recovery_modifier`) + `plan_assembler.py`-Snapshot + Dev-Leser in `test_pipeline.py`. _Timing:_ an den Fillout-Intake-Neubau koppeln (Querschnitts-Naht, Inspektion-vor-Build). _Nicht MVP-11._ _Falls Autoregulation später zurückkommt: über wiederkehrendes Check-in-Feedback (V1.5), nicht über einmaligen Intake-Wert._

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

### Korrektheits-Regelliste (geschärft, code-verifiziert 2026-06-23)

Jede Regel gegen den realen Code geprüft (nicht gegen Spec/Memory). Checker = `scripts/plan_checker.py`, eine Regel pro Naht im `REGELN`-Register.

**Gebaut:**
- **Regel 6 — Verletzungs-Sicherheit** (`d01da9f`): exakte Negation des 2-Stufen-Filters (`joint_stress` + high-impact-gated). Konsistenz-/Regressions-Wächter Filter↔Output, NICHT Tag-Vollständigkeit (= Phase-4-Audit). `_VERLETZUNG_MAP`/`_HIGH_IMPACT_GATED` aus `equipment_filter` importiert.
- **Regel 2 — Slot-Pattern-Treue (γ)** (`aab1dd2`): eingesetztes `pattern` == Slot-`pattern`. Heute NICHT erzwungen (`valid_auswahl` zieht aus allen 161) → Checker deckt es auf.
- **Regel 5 — Einheit-Konsistenz** (`f79e3ec`): zwei verschieden-skopierte Teil-Checks. Teil A rir-Gate (GLOBAL, haupt_uebungen + metcon_block + conditioning_block_2): `rir is not None ⟹ unit=="reps"`. Teil B wdh-Format (NUR Kraft-haupt_uebungen): distanz⇒…m, zeit⇒…sec, reps⇒kein sec/m. Conditioning/Blöcke vom wdh-Check ausgenommen — Format-Override (Naht 2a) ist legitim. _Präzisierung ggü. ursprünglich "unit passt zu wdh/rir": global nicht umsetzbar (Conditioning überschreibt Anzeige-Einheit), daher zweigeteilt._
- **Regel 4 — RIR-Welle** (`6341a7c`): End-to-End-Wächter — trägt der fertige Plan die RIR-Welle, die `berechne_volumen` erzeugt? Soll = ORAKEL (`berechne_volumen` aufgerufen, NICHT dupliziert) → longevity-Level-Blindheit + recomp/fettabbau-Cap fallen automatisch korrekt heraus. Pro Kraft-Übung: tier (aus Split) × block_typ → erwartetes RIR; + Session-Sanity (`ziel_rir` == compound-Soll). Komplementär zu `run_tests` (das die Funktion isoliert prüft, Regel 4 den Output).
- **Regel 3 — Primär-Dedup (δ)** (`88d2a21`): derselbe Primär-Lift (compound-Tier via `soll["tiers"]`) nicht 2×/Woche. Pro Woche isoliert gezählt (Block-Konstanz W1=W2 zulässig). Enge Form: nur identische `exercise_id` (Variation Deadlift+RDL erlaubt). Wächter gegen echte-Claude-Dups (δ-Befund Phase-1-Verify Plan 01).

_Signatur aller Regeln: `(plan, EXMAP, soll)` mit `soll = {patterns, tiers, rir}` — erweiterbare Werkzeugkiste, neue Soll-Arten ohne Signatur-Wuchs ergänzbar._

**Spezifiziert, baubar (je eigene Naht):**
_Regel-Satz komplett (5 Regeln). Nächste Naht: Kreuzprodukt-Sprung (kein neuer Regel-Code)._

**Bewusst NICHT im Checker:**
- **Regel 1 — Dauer ≤ Budget — gestrichen:** Dauer-Toleranz bewusst eincodiert (Trim bei >Budget+5), keine harte Invariante — gestrichen. (Emittierte `dauer_min_geschaetzt` ist ohnehin kosmetisch = Budget, s. Befund 2.)
- **RPE-senkt-nie-Volumen — gestrichen:** Stress/Schlaf sind totes Steuer-Signal (Recovery-Entkopplung Naht A), keine Kopplung mehr zu prüfen. (Felder werden ohnehin entfernt, s. Intake-Karte.)
- **Regel α — Primär-Rolle-zum-Ziel:** braucht Bewegungs-Rolle-Feld (existiert nicht) → **Phase 4** (Bibliotheks-Erweiterung).
- **Volumen-Plausibilität pro Muskel/Woche:** Checker kann zählen, aber „fachlich genug?" ist **Coach-Urteil** (unverifizierte Modell-A-Annahme), keine Maschine.

_Kreuzprodukt-Sprung gebaut (`23dd5a3`): Struktur-Sweep 1536 (alle 5 Regeln, ohne Verletzung)
+ Verletzungs-Sweep 216 (nur Regel 6), --kreuzprodukt-Flag, deterministisch ~10s, Exit 0/1.
Level-Ableitung raumweit konsistent (0 Mismatches). Offen: CI-Gate (Exit-Code-Trennung
bekannte vs. neue Funde) — eigenes Thema._

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

## MVP-10 — offene Punkte aus der Status-Persistenz-Naht

- **`speichere_*` async/await-Bug:** `speichere_plan` und `speichere_klient` in `db.py` sind als `async` deklariert, rufen aber das synchrone supabase-py `.execute()` ohne `await`. Vorbestehend, nicht durch `8505eca` entstanden. Bewusst separat geparkt, um die Status-Naht auf ein Thema zu halten. Die drei `vorgang_*`-Funktionen sind bereits korrekt synchron. _Fix:_ entweder die beiden auf synchron umstellen (konsistent mit `vorgang_*`) oder echtes async-DB-Pattern. _Eigener Commit._

- **Submit-Pfad-Robustheit bei DB-Ausfall:** `db.vorgang_starten` läuft synchron im Webhook-Handler (`main.py` Submit-Pfad), bevor `202` zurückgeht. Fehlt die Supabase-Erreichbarkeit (Env nicht gesetzt oder DB down), wirft `POST /api/new-plan` statt sauber `202` zu antworten. In Production mit gesetzter Env unkritisch; lokal/ohne Env relevant. Bewusst nicht in der Status-Naht umhüllt (nicht spezifiziert, eigenes Thema = Endpunkt-Fehlertoleranz). _Fix:_ `vorgang_starten` gegen DB-Ausfall absichern, sodass der Submit-Pfad robust `202` liefert. _Eigener Commit._

- **`pending_review` als Default — bewusste Policy, kein Versäumnis:** Jeder erfolgreiche Plan erhält weiterhin `status="pending_review"` (`db.py`, unangetastet seit `8505eca`), d. h. jeder Plan wird manuell geprüft, bevor er zum Kunden geht. _Trigger zum Umbau:_ Erst wenn eine Qualitätsquote belegt, dass Pläne ohne Korrektur solide rauskommen, auf automatische Freigabe umstellen (Default `freigegeben`, `pending_review` nur noch im Fehlerfall). Hängt am technischen Vorgangs-Status aus MVP-10, der die Fehlererkennung erst ermöglicht. _Nicht anfassen ohne diesen Kontext._

- **Fehlerkontext in `vorgaenge` anreichern (Live-Betrieb-Diagnose):** Heute hält `fehler_text` nur die Exception-Message selbst (z. B. `Parser-Fehler: TypeError: int() argument…`). Für echte Fehlersuche bei Live-Klienten fehlt der Kontext: welcher Pipeline-Schritt (Parser / Claude-Call / Validierung), ein Payload-Ausschnitt, optional der volle Traceback. Konsequenz heute: grobe Ursache steht in `vorgaenge`, das genaue Warum nur in den Render-Logs (Sprung zwischen zwei Orten, Logs nicht dauerhaft). _Fix:_ mehr strukturierten Fehlerkontext direkt in die `vorgaenge`-Zeile schreiben (z. B. Feld `fehler_schritt` + längerer `fehler_text`/Traceback), sodass Diagnose an einem Ort möglich ist. _Konsument: Live-Betrieb (Phase 4+)._ _Eigener Commit._

- **Aktive Benachrichtigung bei Fehlschlag:** Heute wird ein fehlgeschlagener Vorgang nur in `vorgaenge` (status=`fehlgeschlagen`) vermerkt — niemand wird aktiv informiert. Im Live-Betrieb würde ein Fehlschlag erst über Kundenbeschwerde auffallen. _Fix:_ Push-Signal (Mail / Slack / o. ä.) auslösen, wenn `vorgang_fehlgeschlagen` schreibt. Hängt zusammen mit der `pending_review`-Policy: Kunde sieht „Plan in Bearbeitung", Coach bekommt das Prüf-/Fehler-Signal. _Konsument: Live-Betrieb (Phase 4+)._ _Eigener Commit._
