# Backlog — vertagte Arbeit (nach MVP-Paket)

_Stand: 2026-06-11 · git HEAD `65306a8`_

> Bewusst aufgeschobene Arbeit, gruppiert nach MVP-Paket. Jeder Eintrag:
> Beschreibung · warum vertagt · Code-Marker (Datei:Zeile, Grep-verifiziert) · Abhängigkeit.
> Code-Marker sind die `TODO(...)`-Strings im Code; Zeilennummern Stand HEAD `4c00caa`.

---

## MVP-3 — Volumen „Modell A" fertigstellen (Status: Kern fertig, Deckel offen)

- **Level-Korridor-Deckel fehlt.** War `_WOCHEN_VOLUMEN`, in dieser Session entfernt
  (Commit `19f8d5f`, kein Konsument mehr). Obergrenze je Level/Ziel neu bauen
  (Sätze/Muskel/Woche deckeln). · _Vertagt:_ braucht echte Muskel-Aggregation (MVP-4-Splits
  + saubere Tags MVP-2). · _Marker:_ — (Tabelle entfernt). · _Hängt ab von:_ MVP-2, MVP-4.
- **Deload-Faktor:** Code `0.50`, Spec Thema 1 will `0.60`. Unter Modell A nutzt Deload die
  Cap-Unterkante (kein Prozent-Faktor) → Eintrag ist tot. · _Marker:_ `logic/volume_calculator.py:31`
  `TODO(deload-faktor-tot)`. · _Hängt ab von:_ MVP-3-Tidy.
- **Test-Altlast tage=2 + tote Refs:** 3 run_tests-Fälle füttern 2-Tage-Werte
  (`TODO(testdata-tage-min3)`, run_tests:122/132/167) **und** 4 generate_test_plans-Payloads
  scheitern am Parse (05 tage=2 · 09 `ausdauer` · 10 `gesundheit` · 14 `gesundheit`+tage=2 —
  vorbestehend, bei MVP-4-Naht-5 verifiziert). Ein Hygiene-Commit für beide. · _Hängt ab von:_ —.

## MVP-4 — Split-Logik Neubau ✅ umgesetzt (2026-06-11, `4ab789c`…`65306a8`)

- longevity-Crash, Fettabbau-Struktur, Mobility-Entfernung, 20-Min-Sonderfall: **alle erledigt**
  (5 Nähte, Details STATUS Abschnitt 6). Schwachstellen-Fokus-Tag gestrichen → V1.5-Sektion unten.
- **Offen geblieben (→ MVP-7/8): Pattern-Priorität bei kurzer Session** (welches Pflicht-Pattern
  zuerst fällt; V1: Kürzung implizit über die Slot-Templates fixiert, „Dauer gewinnt"). · _Marker:_
  `logic/plan_assembler.py:366` `TODO(short-session-pattern-drop)`.
- **Offen geblieben (→ MVP-7):** Longevity-Athletik-Rotation (`TODO(mvp7-athletik)`,
  split_selector:295) + Conditioning-Block-Rotation/Format-Ausbau (`TODO(mvp7-formate)`,
  split_selector:378) — V1-Stand in COACHING_SPEC Thema 4/6 vermerkt.

## MVP-5 — Verletzungs- & Equipment-Filter (aus Szenario-Analyse)

- **Stufe-1-vs-Stufe-3-Spannung (Befund aus dem Tagging, 2026-06-11):** Die pattern_tags-Blocker
  (Stufe 3, `_VERLETZUNG_BLOCKED` z.B. Knie→lunge) können Übungen blocken, die nach
  Ausschluss-Semantik bewusst NICHT joint_stress-getaggt sind — z.B. blockt Knie→`lunge`
  das eigene Knie-Ersatzziel `bw_reverse_lunge`. Beim MVP-5-Bau entscheiden: Stufe-3-Mapping
  ausdünnen, Reha-Keeper davon ausnehmen, oder Stufe 3 ganz in joint_stress aufgehen lassen. ·
  _Hängt ab von:_ MVP-2-Tagging fertig.
- **Mehrere Verletzungen gleichzeitig:** Filter muss eine Liste verarbeiten, nicht einen
  Einzelwert. · _Hängt ab von:_ MVP-2 (joint_stress/impact_level getaggt).
- **Leerer `substitution_pool` nach Mehrfach-Filter** (z.B. Knie + nur Bodyweight + L1):
  definierter Fallback nötig, kein Crash / kein leerer Plan. · _Hängt ab von:_ MVP-2.
- **Systemische Kontraindikationen** (~10% Klientel, Herz/Schwangerschaft): Anamnese-Gate →
  kein Auto-Plan, manuelle Coach-Betreuung. Bewusste Scope-Grenze, **KEIN** viertes
  Sicherheits-Tag. · _Hängt ab von:_ Anamnese (MVP-1-Erweiterung).
- **`substitutions_b` raus**, sobald der 3-Stufen-Filter den dynamischen Ersatz übernimmt
  (lebender Leser `equipment_filter:104` — letzter Konsument zuerst). · _Marker:_
  `TODO(mvp5-substitutions-b-removal)`. · _Hängt ab von:_ MVP-5.

## MVP-7 — Conditioning-Formate

- **Metcon-Selektor nutzt Kraft-Pattern** (`_METCON_PATTERNS = ["squat","hinge","push_horizontal","core"]`,
  `plan_assembler:365`) statt echter Conditioning-Bewegungen (Spec Thema 6: Burpees, Mountain
  Climbers, …). · _Hängt ab von:_ MVP-2 (conditioning/athletik-Übungen).
- **Hier entscheidet sich, WIE conditioning-Übungen abgefragt werden** → bestimmt Schreibweise
  + Tagging der neuen `conditioning`/`athletik`-Pattern (in SCHEMA.md noch offen).

**Kernproblem, das MVP-7 lösen muss:** Die aktuelle Logik (`_METCON_PATTERNS`,
`plan_assembler:365`) kann „hat Kraft-Pattern" **nicht** von „ist conditioning-tauglich"
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
  SCHEMA.md Abschn. 2, `validate_exercises.py` grün). **Offen nur noch: Ausbau auf 250–300**
  (Coach-Daueraufgabe; neue Übungen direkt nach Semantik taggen, Validator als Gate).
- **`update_exercises.py` schema-stale** (NEW_EXERCISES-Literale noch Alt-Schema) — nicht erneut
  laufen lassen ohne Anpassung. · _Marker:_ `TODO(mvp2-schema-stale)` (Kopf-Kommentar).
- **Bestandsaufnahme offen:** wie viele der 125 sind schon conditioning-tauglich, nur in
  Kraft-Pattern getaggt? Echte Anlage neuer conditioning/athletik-Übungen erst nach MVP-7.
- **`TODO(longevity-volume)`:** Platzhalter-Werte in `realism_validator.py:17` / `:33` / `:53`
  und `logic/plan_assembler.py:45` (`_WDH_MAP`), final mit Thema 4–6.
- **`equipment_requires`** seit der Migration in allen 125 als `[]` materialisiert (dormant,
  0 echte Daten; lebender Leser `equipment_filter:94`).
