# Backlog — vertagte Arbeit (nach MVP-Paket)

_Stand: 2026-06-10 · git HEAD `4c00caa`_

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
- **Test-Altlast tage=2:** 3 Tests füttern 2-Tage-Werte, Spec-Minimum ist 3. · _Marker:_
  `scripts/run_tests.py:123`, `:133`, `:168` `TODO(testdata-tage-min3)`. · _Hängt ab von:_ —.

## MVP-4 — Split-Logik Neubau

- **longevity-Crash:** `logic/split_selector.py:399` `elif ziel == Hauptziel.ausdauer:` —
  `Hauptziel.ausdauer` existiert nach MVP-1-Rename nicht mehr → `AttributeError`. **Bewusst
  NICHT** als Mini-Rename gefixt — das lieferte den fachlich falschen alten ausdauer-Split
  statt Kraft+Cardio+Athletik (Thema 4). · _Marker:_ `scripts/run_tests.py:120`
  `TODO(ausdauer-rename)` (verweist auf split_selector.py:399). · _Hängt ab von:_ MVP-1, MVP-3.
- **Fettabbau noch 100% Conditioning** (`split_selector.py:391`), Spec Thema 4 will
  Kraft+Conditioning (3T FB+Akzente · 4T 3+1 · 5T 4+1 · 6T 4+2). · _Hängt ab von:_ MVP-1, MVP-3.
- **longevity + fettabbau teilen Conditioning/Athletik-Infrastruktur** → zusammen bauen.
- **Mobility-Sessions raus** (`_mobility_session`, `mit_mobility`) — eigenes Modul später. ·
  _Marker:_ `models.py:262` `TODO(mobility-removal)`. · _Hängt ab von:_ Split-/Assembler-Rewrite.
- **Pattern-Priorität bei kurzer Session** (welches Pflicht-Pattern zuerst fällt). · _Marker:_
  `logic/plan_assembler.py:440` `TODO(short-session-pattern-drop)`. · _Hängt ab von:_ MVP-4.

## MVP-5 — Verletzungs- & Equipment-Filter (aus Szenario-Analyse)

- **Mehrere Verletzungen gleichzeitig:** Filter muss eine Liste verarbeiten, nicht einen
  Einzelwert. · _Hängt ab von:_ MVP-2 (joint_stress/impact_level getaggt).
- **Leerer `substitution_pool` nach Mehrfach-Filter** (z.B. Knie + nur Bodyweight + L1):
  definierter Fallback nötig, kein Crash / kein leerer Plan. · _Hängt ab von:_ MVP-2.
- **Systemische Kontraindikationen** (~10% Klientel, Herz/Schwangerschaft): Anamnese-Gate →
  kein Auto-Plan, manuelle Coach-Betreuung. Bewusste Scope-Grenze, **KEIN** viertes
  Sicherheits-Tag. · _Hängt ab von:_ Anamnese (MVP-1-Erweiterung).
- **`substitutions_b` raus**, sobald der 3-Stufen-Filter den dynamischen Ersatz übernimmt
  (lebender Leser `equipment_filter:102` — letzter Konsument zuerst). · _Hängt ab von:_ MVP-5.

## MVP-7 — Conditioning-Formate

- **Metcon-Selektor nutzt Kraft-Pattern** (`_METCON_PATTERNS = ["squat","hinge","push_horizontal","core"]`,
  `plan_assembler:365`) statt echter Conditioning-Bewegungen (Spec Thema 6: Burpees, Mountain
  Climbers, …). · _Hängt ab von:_ MVP-2 (conditioning/athletik-Übungen).
- **Hier entscheidet sich, WIE conditioning-Übungen abgefragt werden** → bestimmt Schreibweise
  + Tagging der neuen `conditioning`/`athletik`-Pattern (in SCHEMA.md noch offen).

## MVP-8 — Assembler + Coach-Flag (zurückgerollt, kommt zurück wenn MVP-2/3/4 stehen)

- **Coach-Flag komplett entfernt** (volume_below_optimal, recommended_extras, Muskel-Aggregation).
  War out-of-order (hängt an ungebautem MVP-2/3-Deckel/4). Cleanup-Commits `408c079` + `19f8d5f`.
  `PlanMetadata` bleibt als `Optional=None`-Platzhalter im Modell (`models.py`). · _Hängt ab von:_
  MVP-2, MVP-3-Deckel, MVP-4.
- **Tag-Bug:** „Single Leg RDL (Kurzhantel)" ist `quads,glutes` primary, sollte
  `hamstrings,glutes` (wie die anderen Single-Leg-RDLs). Nur relevant, wenn die Aggregation
  zurückkommt. · _Hängt ab von:_ MVP-8 (Aggregation).

## MVP-11 — Test-Harness

- **Aktuelle Tests prüfen nur „läuft / crasht nicht", NICHT fachliche Korrektheit** der Pläne.
  Spec-Validator-Harness muss diese Lücke schließen (grün = läuft, nicht = richtig). · _Hängt
  ab von:_ MVP-3…8.

## MVP-2 — laufend

- **Schema-Spec abgenickt** → `SCHEMA.md` ist die verbindliche Referenz.
- **Bestandsaufnahme offen:** wie viele der 125 sind schon conditioning-tauglich, nur in
  Kraft-Pattern getaggt? Echte Anlage neuer conditioning/athletik-Übungen erst nach MVP-7.
- **`TODO(longevity-volume)`:** Platzhalter-Werte in `realism_validator.py:17` / `:33` / `:53`
  und `logic/plan_assembler.py:45` (`_WDH_MAP`), final mit Thema 4–6.
- **`equipment_requires` bleibt** (dormant, 0 Daten, default `[]`) — darf bei der Migration
  nicht rausfallen (lebender Leser `equipment_filter:94`).
