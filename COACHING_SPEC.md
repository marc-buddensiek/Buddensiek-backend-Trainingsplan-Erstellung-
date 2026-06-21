# Coaching-Spezifikation — Buddensiek Performance

> Die verbindliche Beschreibung von Alens Trainingsmethodik. Quelle der Wahrheit für die
> Generierungs-Logik und (später) für den Test-Harness. Wird Thema für Thema gemeinsam
> erarbeitet. Solange ein Thema "offen" ist, sind die Werte im Code **unbestätigt**.

_Zuletzt aktualisiert: 2026-06-11_

## Arbeitsregel: Spec-vs-Code-Konflikte

Bei Konflikten zwischen Spec und Code wird der Konflikt als **Befund** behandelt, nie
automatisch aufgelöst. **Fachliche Konflikte** (Methodik, Korridore, Zähllogik): Spec
gewinnt, Code wird gefixt. **Bezeichner-Konflikte** (Enum-Strings, Feldnamen,
Schreibweisen): Code gewinnt, Spec wird korrigiert. In beiden Fällen wird die
Verliererseite im selben oder nächsten Commit angeglichen — kein Konflikt bleibt stehen.

## Themen-Roadmap

| # | Thema | Status |
|---|---|---|
| 1 | Periodisierung | ✅ entschieden |
| 2 | Level-System & PST | ✅ entschieden |
| 3 | Volumen & Intensität | ✅ entschieden |
| 4 | Split-Logik je Ziel | ✅ entschieden |
| 5 | Recovery-Anpassung | ✅ entschieden |
| 6 | Conditioning- & Cardio-Formate | ✅ entschieden |
| 7 | Progression über Blöcke hinweg | ✅ entschieden (V1) |
| 8 | Sonderfälle (Verletzungen, akuter Schmerz, Nebenziel) | ✅ entschieden |

---

## 1. Periodisierung — ✅ entschieden (2026-06-02)

**Grundmodell: 3:1-Welle innerhalb jedes 4-Wochen-Blocks.**

Drei Wochen ansteigende Belastung, dann eine Deload-Woche:

| Woche | Typ | Belastung (intensitätsgeführt — Volumen ~flach, RPE trägt die Welle) |
|---|---|---|
| 1 | Akkumulation | niedrig (Einstieg) — RPE am unteren Spannen-Ende (`rpe_low`); Volumen auf Cap-Unterkante |
| 2 | Progression | mittel — RPE in der Spannen-Mitte; Volumen unverändert |
| 3 | Intensivierung | hoch (Peak) — RPE am oberen Spannen-Ende (`rpe_high`); Volumen +1 Satz (Intensiv-Spike) |
| 4 | **Deload** | RPE auf `rpe_low − 1` (Floor 4); Volumen = Cap-Unterkante (~67–75 % des Peak-Volumens) |

**Entscheidungen im Detail:**

- **Modell:** 3:1-Welle (wie bisher im Code). Begründung: einfach, vorhersehbar, gut im PDF
  kommunizierbar, eingebauter Erholungspuffer, funktioniert über alle Ziele.
- **Level-Differenzierung:** **Keine.** Das Periodisierungs-Modell ist für **alle Level (1–4)
  einheitlich**. (Level beeinflusst weiterhin Volumen/Intensität — das ist Thema 3 —, aber NICHT
  die Wellen-Struktur selbst.)
- **Deload:** **Fix in Woche 4** (jeder Block endet mit Deload). Realisierung unter Modell A:
  Volumen = Tier-Cap-Unterkante (compound 3 von 4 = 75 %, accessory/iso/core 2 von 3 = 67 %
  → **~67–75 % des Peak-Volumens**), RPE auf **`rpe_low − 1`** (Floor 4, eine Stufe unter der
  leichtesten Ladewoche).
  → **Konfliktregel-Anpassung (2026-06-13, Coach):** Die frühere Vorgabe „60 % des Volumens"
  (alter Code-Faktor `_PERIODISIERUNG_FAKTOR["deload"] = 0.50`) ist unter Modell A gegenstandslos —
  der Deload nutzt **keinen Prozent-Faktor**, sondern die Cap-Unterkante. Statt eines Volumen-Prozents
  trägt jetzt das **Doppel aus Cap-Floor-Volumen + abgesenktem RPE** den Deload. Begründung: bewusst
  leichter Deload für gemischte, verletzungsbelastete Population; kein %1RM verfügbar (PST ist
  Bodyweight). **Ersetzt** die 0.60/0.50-Festlegung (toter Code-Faktor in MVP-6 Naht 2 entfernt).
- Gleiche Übungen über alle 4 Wochen, nur Sätze (Intensiv-Spike) / RPE verändern sich.

**Begründung:** 3:1-Welle gewählt, weil sie über alle Ziele/Level robust ist, im PDF leicht erklärbar und
einen Erholungspuffer (Deload) fest eingebaut hat. Verworfen: *linear* (kein Deload → höheres
Übertrainings-Risiko bei häufiger Block-Wiederholung), *undulierend/DUP* (für gemischte Population &
Einsteiger zu komplex, schwer im statischen PDF zu kommunizieren), *Block-Periodisierung* (bräuchte
gekettete Blöcke — zu viel Overhead für V1). Einheitlich statt level-abhängig: hält Logik und Tests
einfach; das Level steuert ohnehin Volumen/Intensität, nicht die Wellen-Struktur. Die früher als
„60 % statt 50 %" diskutierte Deload-Tiefe ist unter Modell A in die Cap-Floor-Logik + RPE-Absenkung
(`rpe_low − 1`) übergegangen — siehe Konfliktregel-Anpassung oben.

**Noch offen / abhängig von späteren Themen:**
- Exakte Volumen-/RPE-Faktoren der Wochen 1–3 → gehört zu **Thema 3 (Volumen & Intensität)**.
- Wie Block N+1 an Block N anknüpft (unabhängig vs. gekettet) → **Thema 7 (Progression über Blöcke)**.

---

## 2. Level-System & PST — ✅ entschieden (2026-06-02)

**Struktur-Entscheidungen:**

- **Test-Battery:** Die **5 Bodyweight-Tests bleiben** — Kniebeugen, Push-Ups, Sit-Ups, Burpees,
  Plank (jeweils max. Wiederholungen in 60 Sek. bzw. Plank-Haltezeit in Sek.).
  Begründung: equipment-unabhängig, für jeden Klienten gleich durchführbar, schnell.
- **Scoring-Methode:** **Summe** der Punkte aller 5 Tests. Jeder Test gibt 1–4 Punkte → Gesamtsumme
  5–20. Eine starke Domäne darf eine schwache kompensieren (bewusst so gewollt, kein „schwächstes Glied").
- **Anzahl Level:** 4 (unverändert).
- **Trainingsjahre-Deckel:** **bleibt.** Endlevel = `min(PST-Level, Deckel)`. Schützt fitte
  Neueinsteiger vor zu komplexem/anspruchsvollem Programm. (Ab Block 2 werden die Trainingsjahre in der
  Mini-Anamnese aktualisiert → der Deckel wächst mit, siehe Thema 7.)

- **Differenzierung nach Geschlecht/Alter:** **Keine.** Einheitliche Latte für alle Klienten
  (bewusste Entscheidung). Jeder Test zählt in der Summe gleich viel (keine Gewichtung).

**Schwellenwerte — bestätigt:**

_Punkte je Test (max. Wdh. in 60 Sek. / Plank in Sek.):_

| Test | 1 Pkt | 2 Pkt | 3 Pkt | 4 Pkt |
|---|---|---|---|---|
| Kniebeugen | <30 | 30–50 | 51–70 | 71+ |
| Push-Ups | <15 | 15–30 | 31–50 | 51+ |
| Sit-Ups | <30 | 30–50 | 51–70 | 71+ |
| Burpees | <15 | 15–25 | 26–35 | 36+ |
| Plank (Sek.) | <60 | 60–120 | 121–180 | 181+ |

_Summe → Level:_ ≤8 → L1 · 9–13 → L2 · 14–17 → L3 · ≥18 → L4

_Trainingsjahre-Deckel:_ keine → max L1 · <1 J → max L2 · 1–2 J → max L3 · 3–5 J → max L4 ·
5+ J → kein Deckel

→ Diese Werte entsprechen exakt dem aktuellen Code (`logic/level_calculator.py`) — hier keine
Code-Anpassung nötig.

**Begründung:** Bodyweight-PST behalten, weil equipment-unabhängig (funktioniert für Gym wie für
Reise/Bodyweight-Klienten) und schnell ohne Maximaltests durchführbar. Verworfen: Kraft-/1RM-Proxy
(bräuchte Equipment + Technik, schließt Bodyweight-Klienten aus). Summen-Scoring statt „schwächstem Glied",
weil eine starke Domäne eine schwache kompensieren darf — bewusst, um nicht zu konservativ einzustufen.
Erfahrungs-Deckel behalten, weil ein von Natur aus fitter Neuling sonst zu komplexes Programm bekäme,
dessen Technik er nicht beherrscht. Einheitliche Schwellen (kein Geschlecht/Alter): bewusst simpel für V1.

---

## 3. Volumen & Intensität — ✅ entschieden (2026-06-04)

### Volumen-Modell: „Von der Session aus aufbauen" (Modell A)

Statt ein festes Wochenvolumen runterzubrechen (wie bisher), wird das Volumen aus dem aufgebaut,
was real in die Einheiten passt:

1. **Session-Dauer ist die harte Grenze.** Ein Plan überschreitet nie die gewünschte Dauer
   (Warm-up + Hauptteil + Cardio + Cool-down zusammen ≤ gewünschte Dauer, kleine Toleranz erlaubt).
2. **Satz-Cap pro Übung** (je Tier abgestuft, harte Obergrenze 4) verhindert Unsinn wie 6 Sätze
   auf einer Übung.
3. **Trainingstage bestimmen die Gesamtmenge** — mehr Tage = mehr Wochenvolumen, automatisch.
4. **Ziel × Level = Obergrenze/Korridor**: das pro Level erholbare Maximum. Volumen wird nie
   darüber hinaus gestapelt.

**Kein Auto-Eingriff bei Zeitmangel:** Reicht die Zeit (Tage × Dauer) nicht, um den Ziel-Korridor
zu füllen, wird einfach der **bestmögliche Plan mit den gegebenen Tagen und der Dauer** gebaut.
**Keine** Vorschläge für mehr Tage, **keine** RPE-Anhebung, kein automatischer Ausgleich.
**Bei Konflikt** (Zeit ließe mehr zu, als das Level verträgt): der **Level-Deckel gewinnt** (Sicherheit).

### Intensität & Frequenz

- **RPE-basiert**, RPE-Spannen je Level, steigend über die Welle.
- **Level 1:** zusätzlich Klartext-Hilfe zum RPE (z.B. „2–3 Wiederholungen in Reserve"). _Neu ggü. Code._
- **Frequenz:** ≤3 Tage Ganzkörper; ab 4 Tagen Upper/Lower → jeder Muskel 2×/Woche.

### Zahlen

**Satz-Cap je Tier (harte Obergrenze 4):**

| Tier | Sätze |
|---|---|
| Grundübung (compound) | 3–4 |
| Zusatz (accessory) | 2–3 |
| Isolation | 2–3 |
| Core | 2–3 |

**Ziel-Volumen-Korridor — Sätze/Muskelgruppe/Woche (Obergrenze je Level):**

| Ziel | L1 | L2 | L3 | L4 |
|---|---|---|---|---|
| Muskelaufbau | 8–10 | 12–16 | 16–20 | 18–22 |
| Recomp | 8–10 | 12–16 | 16–20 | 18–22 |
| Fettabbau | 6–8 | 10–14 | 14–18 | 16–20 |

_Logik Fettabbau:_ im Kaloriendefizit braucht ein höher trainierter Klient **mehr** Volumen für den
Muskelerhalt, nicht weniger — daher steigt der Korridor mit dem Level stärker an als zuvor.
_Recomp = wie Muskelaufbau:_ bei Erhaltungskalorien / leichtem Überschuss ist volles Volumen möglich.

**RPE-Spannen je Level (steigen über die Welle):** L1 = 6–7 · L2 = 7–8 · L3 = 7–9 · L4 = 7–9.
Tier-Abstufung: accessory = compound − 1, isolation = compound − 2 (min. 4).

**Session-Kapazität — Zeit-Parameter (Modell-A-Eingaben):**

Arbeitssätze pro Session = (Session-Dauer − Warmup − Finisher) ÷ Zeit pro Arbeitssatz.

| Parameter | Wert |
|---|---|
| Zeit pro Arbeitssatz (inkl. Pause) — Kraft | 2 Min |
| Zeit pro Arbeitssatz (inkl. Pause) — Conditioning | 1,5 Min |
| Warmup-Abzug pro Session | 10 Min |
| Finisher-Abzug — Recomp-Sessions | 8 Min (aus Recomp-Finisher 5–10 Min, Thema 6) |
| Finisher-Abzug — andere Kraft-Sessions | 0 Min |
| Session-Dauer | Klienten-Input (keine feste Liste), harte Obergrenze |

_Warum ein Schnitt pro Session-Typ (nicht pro Tier):_ Der Tier-Mix mittelt sich innerhalb der Session —
die Tier-Satz-Caps begrenzen die einzelne Übung, die Zeit-Formel verteilt das verfügbare Budget.
Per-Tier-Zeitwerte sind V2-Feintuning mit echten Daten.

**Begründung:** Modell A („von der Session aus") gewählt, weil das alte „festes Wochenvolumen ÷ Frequenz"
kurze Einheiten überlud (45 → ~100 Min im Recomp-PDF) und bei vielen Tagen Potenzial verschenkte.
Verworfen: festes Wochenvolumen (Überlauf bleibt), reines Zeitbudget (kein „so viel verträgt das Level"-
Sicherheitsnetz). Satz-Cap je Tier (max 4), weil 5–6 Arbeitssätze auf einer Übung praxisfern sind.
Korridor als Obergrenze statt Fixwert: Volumen folgt der real verfügbaren Zeit (Tage × Dauer), gedeckelt
durch das pro Level Erholbare. Fettabbau-Korridor steigt stärker mit Level, weil im Defizit mehr Volumen
für den Muskelerhalt nötig ist (nicht weniger). RPE statt %1RM, weil kein Maxtest vorliegt (PST ist
Bodyweight); Anfänger-RIR-Hilfe, weil L1 RPE schwer einschätzt. Kein Auto-Eingriff bei Zeitmangel: hält
das Modell ehrlich und vorhersehbar — der Coach steuert via internem Kapazitäts-Flag.

### Umsetzungs-Hinweise & offene Punkte (kein Code jetzt)

- `volume_calculator.py` wird grundlegend umgebaut: von „Wochenvolumen ÷ Frequenz" zu
  „Session-Kapazität (Dauer + Satz-Caps) × Tage, gedeckelt durch Level-Korridor".
- Der **A22-Dauer-Check** (aus dem gestoppten Harness) ist damit automatisch erfüllt — Sessions
  laufen per Konstruktion nicht mehr über.
- **Trainingsjahre-Modifikator (alt: ×0.8 … ×1.2): gestrichen.** Erfahrung wirkt nur noch über den
  Level-Deckel (Thema 2) — ein zusätzlicher Volumen-Faktor wäre doppelt gemoppelt. → Code: Faktor raus aus
  `volume_calculator.py`. (Das Eingabefeld `trainingsjahre` **bleibt** — es steuert weiter den Level-Deckel.)
- **Tier-Anteil-Multiplikator (alt: ×1.0/0.9/0.7/0.8):** entfällt — ersetzt durch die Tier-Satz-Caps.
- **Realism-Hinweis → internes Coach-Flag (entschieden):** Kein Hinweis im Klient-PDF. Bei
  Plan-Generierung prüft das System, ob der Plan den Volumen-Korridor für Level/Ziel erreicht. Falls
  **nein** → Flag in `plan_metadata` (`volume_below_optimal: true`, `recommended_extra_days`,
  `recommended_extra_minutes`). Das Coach-Backoffice zeigt es als Hinweis-Karte pro Klient
  („Suboptimale Trainings-Kapazität"). Der Klient merkt nichts — sein Plan ist einfach der bestmögliche.
  Begründung: Premium-Coaching ohne Kritik-Beigeschmack; Coach kann proaktiv das Gespräch suchen.
- Longevity-Volumen: hängt vom Session-Format ab → final erst mit **Thema 4/6**.
  (Ziel-Set wurde in Thema 4 geändert: Ausdauer & Gesundheit → **Longevity**.)

---

## 4. Split-Logik je Ziel — ✅ entschieden (2026-06-04)

**Grundlegende Rahmen-Änderungen:**

- **Ziel-Set: 4 Pfade statt 5.** Muskelaufbau · Recomp · Fettabbau · **Longevity**
  (Longevity ersetzt die bisherigen *Ausdauer* + *Gesundheit*).
  → ⚠️ betrifft `Hauptziel`-Enum, Typeform-Labels, `models.py`, Parser — **zu bestätigen**.
- **Mobility raus aus dieser Spec** — wird als eigenes Modul später behandelt. Keine Mobility-Sessions
  mehr in der Split-Logik; ersetzt durch Akzent- / Conditioning- / Cardio-Tage je Ziel.
- **5. Trainingstag (Muskelaufbau/Recomp) = Ganzkörper-Akzent-Tag.** Der ursprünglich geplante
  **Schwachstellen-Fokus-Tag ist gestrichen** (Entscheidung 2026-06-11): Fokus-Wahl
  (Arme/Brust/Rücken/Schultern/Beine) ggf. als **V1.5-Feature** (BACKLOG), inkl. Anamnese-Feld.
  Das `schwachstelle`-Feld bleibt dormant in `models.py` (`TODO(v15-schwachstelle)`).

### Wochen-Struktur nach Trainingstagen

**Muskelaufbau / Recomp** (identische Struktur):
| Tage | Struktur |
|---|---|
| 3 | Full Body |
| 4 | Upper / Lower (A/B) |
| 5 | Upper/Lower + 1 Ganzkörper-Akzent-Tag |
| 6 | Upper/Lower 3× wiederholt → jeder Muskel 3×/Woche (PPL entfällt) |

→ **Kein angehängtes Cardio:** Muskelaufbau & Recomp sind reine Kraft (Recomp ggf. + Conditioning-
Finisher, s. Thema 6). Ein LISS-/Cardio-Block wird NICHT angehängt — LISS/Cardio ist ausschließlich
dem **Longevity**-Pfad zugeordnet (Zone-2).

**Fettabbau** (Kraft + Conditioning — KEIN reines Conditioning mehr):
| Tage | Struktur |
|---|---|
| 3 | Full Body mit metabolischen Akzenten |
| 4 | 3 Kraft + 1 Conditioning |
| 5 | 4 Kraft + 1 Conditioning |
| 6 | 4 Kraft + 2 Conditioning |
→ ⚠️ große Änderung ggü. Code (heute: Fettabbau = 100 % Conditioning).
→ **Kein angehängtes Cardio:** Fettabbau ist **Kraft + Conditioning** — ein zusätzlicher LISS-/HIIT-
Cardio-Block wird NICHT angehängt. LISS/Cardio ist ausschließlich dem **Longevity**-Pfad zugeordnet (Zone-2).

**Longevity** (Kraft + Cardio + Athletik):
| Tage | Struktur |
|---|---|
| 3 | Full Body |
| 4 | Upper/Lower + 1–2 Cardio/Athletik |
| 5 | 3 Kraft + 2 Cardio/Athletik |
| 6 | 4 Kraft + 2 Cardio/Athletik |

**Longevity-Definition:** der **Generalist-Pfad** — Kraft + Cardio + Athletik (Sprünge, Koordination,
Bewegungs-Vielseitigkeit) für allgemeine Fitness fürs Leben. Enthält nur **ROM-Arbeit im Aufwärmen**
und allgemeines **Zone-2-Cardio**.

**Abgrenzung zu späteren Extra-Modulen** (ergänzen Longevity bei Bedarf, ersetzen es nicht):
- **Mobility-Modul:** tägliche dedizierte Mobility-Routine, löst spezifische Einschränkungen.
- **Endurance-Modul:** Event-Vorbereitung (Marathon etc.) mit strukturierter Lauf-Periodisierung.

### Pattern-Logik je Session-Typ (verpflichtende Mindest-Patterns)

**Upper-Day** — muss enthalten:
- 1× Horizontal Push · 1× Horizontal Pull · 1× Vertical Push · 1× Vertical Pull
- optional 1–2 Isolation (Bizeps / Trizeps / Schulter-Detail)

**Lower-Day** — muss enthalten:
- 1× Squat (kniedominant) · 1× Hinge (hüftdominant) · 1× Single Leg · 1× Core/Carry
- optional 1 Isolation (Waden / Glutes-Detail)

**Full Body** — muss enthalten:
- 1× Squat ODER Hinge · 1× Push (horiz. o. vert.) · 1× Pull (horiz. o. vert.) · 1× Core/Carry
- optional 1–2 Akzent-Übungen

**Upper/Lower-Schwerpunkte (4 Tage):**
- Upper A: Push-Fokus (Horizontal Push = schwerste Compound)
- Upper B: Pull-Fokus (Vertical/Horizontal Pull = schwerste Compound)
- Lower A: Squat-Fokus · Lower B: Hinge-Fokus

**6 Tage (Upper/Lower 3×):** Rotation A/B/A oder A/B/C, je nach Schwerpunkt-Wunsch.

**Push : Pull-Balance über die Woche:** minimum 1:1, ideal **1 : 1,2** (leicht mehr Pull als Push).

### Entschieden & Umsetzungs-Hinweise

- **Ziel-Set: 4 Pfade bestätigt** (Muskelaufbau · Recomp · Fettabbau · Longevity). Ausdauer & Gesundheit
  entfallen. → Code-Änderung: `Hauptziel`-Enum, Typeform-Labels, `models.py`, `parsers.py`.
- **Mindestens 3 Trainingstage** — 2 Tage werden nicht angeboten. → Code-Änderung:
  `KlientenInput.tage_pro_woche` von `ge=2` auf `ge=3`; Typeform-Option „2" entfernen.
- **Pflicht-Patterns vs. Dauer: Dauer gewinnt.** Reicht die Zeit nicht für alle Pflicht-Patterns, werden
  sie nach Priorität gekürzt (wichtigste/schwerste Compound zuerst, dann Balance) — Session bleibt in der
  gewünschten Dauer. Konsistent mit Thema 3.
  → **Umsetzungs-Detail offen:** die Prioritäts-Reihenfolge je Session-Typ (welches Pattern zuerst fällt)
  definieren wir bei der Implementierung. Vorschlag: Schwerpunkt-Compound des Tages immer behalten.
- **Recomp-Metcon-Finisher:** behält Recomp einen Conditioning-Finisher? → offen, Detail für **Thema 6**.
- Frequenz-Verfeinerung ggü. Thema 3: 4 Tage → 2×/Muskel, **6 Tage → 3×/Muskel**.

**Begründung:** Full Body → Upper/Lower → U/L 3× nach Tagen, weil so die Frequenz pro Muskel mit den
Tagen mitwächst (wenige Tage = hohe FB-Frequenz; 4 Tage = 2×; 6 Tage = 3×). PPL verworfen, weil ein
einmaliger Durchlauf nur 1×/Muskel bringt (für Hypertrophie suboptimal) — U/L 3× ist dichter. Min. 3 Tage,
weil 2 Tage für keines der Ziele sinnvoll programmierbar ist. 4 Ziele statt 5: Ausdauer + Gesundheit
überlappten stark → zu **Longevity** (Generalist) zusammengefasst; spezifische Bedürfnisse (Marathon,
Mobility) kommen als eigene Zusatz-Module statt als verwässerte Hauptziele. Pflicht-Patterns je Session
sichern die Bewegungs-Balance über alle Ebenen; bei Konflikt gewinnt die Dauer (konsistent mit Thema 3 —
Session läuft nie über). Push:Pull 1:1,2 leicht pull-lastig, weil Alltag/Haltung meist push-dominant ist.
Ganzkörper-Akzent-Tag statt Mobility-Tag bei 5 Tagen, weil Mobility ein eigenes Modul wird.

---

## 5. Recovery-Anpassung — ✅ entschieden (2026-06-04)

**Nur die RPE wird angepasst — das Volumen (Sätze) bleibt in allen Fällen unverändert.** Keine
Steigerung über den Level-Korridor hinaus. Eingaben: `stress_level` (1–10), `schlaf_stunden` (4–10).
Die RPE wird relativ zur RPE-Spanne des Klienten-Levels gesetzt:

| Recovery-Lage | Bedingung | RPE-Ziel |
|---|---|---|
| Sehr hohe Belastung | Stress ≥ 9 **oder** Schlaf ≤ 4 h | unteres Ende der Spanne **− 1** |
| Hohe Belastung | Stress ≥ 8 **oder** Schlaf ≤ 5 h | unteres Ende der Spanne |
| Gute Recovery | Stress < 5 **und** Schlaf ≥ 7 h | oberes Ende der Spanne |
| Normal/moderat | sonst (z.B. Stress 6–7, Schlaf 6 h) | normale Spanne, keine Anpassung |

Auswertung in dieser Reihenfolge (schlechtester zutreffender Fall gewinnt): sehr hoch → hoch → gut → normal.

_Beispiel (Level 2, RPE-Spanne 7–8):_ gute Recovery → bis 8 · hohe Belastung → max 7 · sehr hohe → max 6.

**Untergrenze:** RPE fällt nie unter **4** (Plan-Minimum).

**Umsetzungs-Detail (beim Coden klären) — Zusammenspiel mit der 3:1-Welle:** Bisher steigt die RPE über
die Welle (Akkumulation → Intensivierung). Vorschlag zur Auflösung: Die Welle bestimmt die Basis-RPE;
die Recovery-Regel wirkt als **Deckel nach oben** (schlechte Recovery) bzw. **Freigabe bis oberes Ende**
(gute Recovery). In der Deload-Woche greift ohnehin der RPE-Floor (Thema 1).

**Begründung:** Nur RPE anpassen, Volumen unangetastet, weil zwei gleichzeitige Stellschrauben (Volumen
UND RPE) sich überlagern und schwer nachvollziehbar machen — die RPE ist der direktere Hebel für die
Tagesform. Verworfen: Volumen senken (kollidiert mit Modell A und der Block-Progression über Logs),
beides gleichzeitig (zu aggressiv/intransparent). Nur abwärts, keine Steigerung über den Korridor: gute
Recovery nutzt das obere Ende der bestehenden Spanne, geht aber nie über das Level-Erholbare hinaus.
Zweistufige Schwelle, weil Stress 9 / Schlaf ≤ 4 h eine deutlich stärkere Entlastung rechtfertigt als
Stress 8 / Schlaf 5 h. RPE-Floor 4, damit das Training ein Reiz bleibt.

---

## 6. Conditioning- & Cardio-Formate — ✅ entschieden (2026-06-04)

### Format-Baukasten

| Format | Typ | Definition |
|---|---|---|
| AMRAP | Session-füllend | feste Zeit, so viele Runden wie möglich |
| Zirkel (Circuit) | Session-füllend | Übungen nacheinander ohne Pause, X Runden |
| Intervalle | Session-füllend | HIIT, Work:Rest aus dem **Level-Mapping** (s.u.), Ziel 85–90 % HF-Max |
| Tabata | **Block** (4 Min) | 8 × 20 s on / 10 s off für **eine** Übung; Session = mehrere Blöcke (s.u.) |
| Density Block | **Block** (5 Min) | feste Zeit, max. Wiederholungen bei **festem Gewicht**; mehrere Blöcke füllen die Session |
| Ladders | **Block** | **aufsteigendes** Schema (z.B. 1-2-3-4-5 … bis Cap), v.a. Kettlebell |
| Komplexe | **Session-füllend** | vordefinierte Kette mehrerer Übungen mit **einer Last ohne Ablegen**, 6–8 Runden (~10–20 Min) — **ab `skill` 2**, **nur KB/Hantel/LH, nie Bodyweight** (Lasthalten = definierendes Merkmal); die Ketten s. Komplexe-Abschnitt unten |

**Gestrichen (Konfliktregel):**
- **EMOM (2026-06-14):** sobald die Arbeitszeit fix vorgegeben ist (z.B. 45 s/15 s), ist es
  definitionsgemäß ein **Intervall**, kein EMOM (EMOM = feste Wdh-Zahl, variable Pause). Die Intervalle
  übernehmen die Rolle vollständig über die Level-Work:Rest-Werte.
- **Mixed Intervals (2026-06-14):** war nie definiert, für V1 nicht nötig — aus L4 entfernt.
- **For Time (2026-06-13):** offene Dauer („so schnell wie möglich") kollidiert mit der festen
  Session-Länge / Modell A. Falls je reaktiviert: `max_time_cap` als **Pflichtparameter** → Backlog, nicht V1.

→ ⚠️ Neu ggü. Code (heute `amrap/emom/zirkel/intervalle`; **emom entfällt** mit Naht 2): **Tabata, Density
Block, Komplexe, Ladders** + **Athletik** (s.u.). Betrifft `MetconBlock.typ`-Enum + Format-Logik. Alle
Format-Parameter sind jetzt festgelegt (Tabelle + Level→Format-Mapping unten). Conditioning trägt **keine
RPE** (s.u.).

### Format-Dauer vs. Session-Dauer

Die Formate teilen sich in zwei Bauarten — entscheidend, damit der Generator kein „Tabata 20 min" baut:

- **Session-füllend** (ein Block = ganze Session): AMRAP, Intervalle, Zirkel/Circuit, **Komplexe**
  (vordefinierte Kette × 6–8 Runden, s.u.). Dauer = die gewählte **`session_dauer_min`** (level-unabhängig).
- **Block-Formate** (mehrere Blöcke füllen die Session, ~60 s Pause dazwischen): Tabata, Density, Ladders.
  Der Generator **stapelt Blöcke**, bis die gewählte **`session_dauer_min` (− Warmup)** gefüllt ist.

> **Dauer-Regel (2026-06-15):** Die Conditioning-Dauer kommt **ausschließlich** aus der vom Klienten
> gewählten `session_dauer_min`. Das **Level deckelt die Dauer NICHT** — es steuert nur Format-Verfügbarkeit,
> Work:Rest und Übungskomplexität (`skill_level`). Ein L1-, L2- und L4-Klient mit 45 Min bekommt je ~45 Min
> Conditioning, nur in unterschiedlichen Formaten. (Ausnahme: gemischte Tage — Recomp + Fettabbau ≤3 — der
> amrap-Finisher bleibt fix ≤ 10 Min, bewusste Regel, keine Level-Deckelung.)

**Tabata:** Ein **Block** = 8 Runden 20 s on / 10 s off = **4 Min für EINE Übung**. Eine **Session** =
mehrere Blöcke mit **je unterschiedlicher Übung**, dazwischen **60 s Pause**. Die **Blockzahl füllt die
gewählte `session_dauer_min` (− Warmup)** — je länger die gewählte Session, desto mehr Blöcke (z.B. 45-Min-
Session ≈ 7 Blöcke). _Beispiel:_ Block 1 Squats · Block 2 Push-ups · Block 3 Mountain Climbers (je 8 × 20/10,
60 s Pause dazwischen).

**Density:** ein **Block = 5 Min** feste Zeit, max. Wiederholungen bei festem Gewicht; mehrere Blöcke
(~60 s Pause) bis die gewählte **`session_dauer_min`** gefüllt ist. **Ladders:** **aufsteigendes** Schema (z.B. 1-2-3-4-5 … bis Cap),
Block-Format. **Komplexe:** vordefinierte Kette mehrerer Übungen mit **einer Last ohne Ablegen**,
6–8 Runden — **session-füllend** (NICHT block-gestapelt), **ab `skill` 2**, nur KB/Hantel/LH;
die Ketten s. Abschnitt unten.

### Komplexe — vordefinierte Ketten (Coach-Entscheidung, `TODO(mvp7-komplexe)`)

**Rahmen:**
- Komplexe ist ein **session-füllendes Conditioning-Format** (wie Intervall/AMRAP/Zirkel),
  **6–8 Runden, ~10–20 Min**. **Kein Block-Format.**
- **Pfad-Abgrenzung:** Komplexe lebt **ausschließlich im Conditioning-Pfad**. Tritt in den
  session-füllenden Conditioning-Selektor ein (zusammen mit Intervall/AMRAP/Zirkel), wird mit
  diesen rotiert, kann Teil einer Multi-Format-Aufteilung (`conditioning_block_2`) sein. Kommt
  **nie** im Kraft-Übungs-Selektor und **nie** im Finisher-Mechanismus vor.
- **Format-Gate: ab `skill` 2.** skill-1-Klienten bekommen **nie** Komplexe (Bewegungs-Lernphase —
  Verkettung unter Ermüdung fachlich kontraproduktiv), sie fallen auf andere session-füllende
  Formate zurück.
- **Auswahl:** Welche Kette gezogen wird, hängt von **`skill` UND Equipment** ab.
- **Equipment:** Gym → alle Ketten (LH/KH/KB). Kettlebell → nur KB-Ketten. Bodyweight → keine
  Komplexe (Leer-Pool-Fallback auf anderes Format).
- Jede Kette = **eine Last ohne Ablegen**, Flow biomechanisch durchgängig.

**Ketten (`skill` 2–4):**

_Langhantel (LH):_
- **L2 Barbell:** 5 RDL · 5 Bent Row · 5 Hang High Pull · 5 Front Squat · 5 Push Press
- **L3 Barbell Athletic:** 5 RDL · 5 Hang Clean · 5 Front Squat · 5 Push Press · 5 Back Squat · 5 Good Morning
- **L3 Full Body:** 5 Deadlift · 5 Hang Clean · 5 Front Squat · 5 Push Press · 5 Bent Row · 5 RDL
- **L4 Barbell Power:** 5 Bent Row · 5 Hang High Pull · 5 Power Clean · 5 Front Squat · 5 Push Jerk · 5 Overhead Reverse Lunge

_Kurzhantel (KH):_
- **L2 DB Allrounder:** 6 RDL · 6 Row · 6 Front Squat · 6 Push Press · 6 Reverse Lunge
- **L2 DB Metabolisch:** 8 Front Squat · 8 Push Press · 8 Reverse Lunge · 20 March Steps
- **L3 DB Strength:** 6 DB RDL · 6 DB Hang Clean · 6 DB Front Squat · 6 DB Push Press · 6 DB Reverse Lunge · 6 DB Bent Row
- **L4 DB Athletic** (einarmig, eine Hantel durch die ganze Kette, alles pro Seite, **4–6 Runden**):
  5 DB Snatch · 5 DB Overhead Squat · 5 DB Push Press · 5 DB Front Rack Lunge · 5 DB Bent Row

_Kettlebell (Double KB sofern nicht anders genannt):_
- **L2 KB Thruster:** 6 Front Squat · 6 Push Press · 6 Thruster
- **L2 KB Swing-Basis A:** 10 Double KB Swing · 6 Front Squat · 6 Push Press
- **L2 KB Swing-Basis B:** 10 Double KB Swing · 6 Front Squat · 6 Reverse Lunge · 6 Push Press
- **L2 KB Swing-Thruster:** 10 Double KB Swing · 8 Thruster
- **L3 Double KB Flow:** 6 Double KB Swing · 6 Double KB Clean · 6 Front Squat · 6 Push Press · 6 Reverse Lunge · 6 Bent Row
- **L4 Double KB Athletic:** 5 Double KB Deadlift · 5 Double KB High Pull · 5 Double KB Clean · 5 Front Squat · 5 Thruster · 5 Overhead Walk Steps

**Verworfen (nicht implementieren):** alle skill-1-Ketten (L1 ist kein Komplexe-Format);
Double-KB- und Double-DB-Varianten mit (Hang) Clean auf L2 (Clean gehört ab `skill` 3).
Hybrid KB+DB = Zirkel, kein Komplex.

**Offene Coach-Daueraufgabe:** Ketten-Bibliothek bei Bedarf erweitern (mehr Abwechslung pro
`skill`/Equipment für die Rotation).

### Conditioning-Mechanismus (Schema — gebaut MVP-7 Naht 1)

Wie „conditioning-tauglich" markiert ist (Hybrid, Details in SCHEMA.md):
- **Gruppe A** — reine Conditioning-Geräte/Bewegungen ohne Kraft-Pattern (Air Bike, Battle Ropes, Row/Ski
  Erg, Jump Rope, Sled): `pattern: "conditioning"`, **keine** muscle_groups. Laufen ausschließlich in
  Metcon-Formaten; der Kraft-Selektor matcht nur die 9 Kraft-Pattern → ignoriert sie strukturell.
- **Gruppe B** — Übungen mit echtem Kraft-Pattern, die auch metcon-tauglich sind (Burpee, KB Swing,
  Thruster, Mountain Climber …): behalten ihr Kraft-Pattern + `conditioning_friendly: true`.
- **Metcon-Selektor** zieht: „Pattern == `conditioning` **ODER** `conditioning_friendly` == true".
- **Dosierung kommt aus dem Slot** (Modell A), nicht aus der Übung — dieselbe Übung im Kraft-Slot bekommt
  Kraft-Dosierung, im Metcon-Block die Metcon-Parameter. Kein eigenes Dosierungs-Feld.

### Komplexität, Progression & Level→Format-Mapping

- **Komplexität läuft über `skill_level` (1–4)** — Conditioning-Übungen werden beim Anlegen wie alle
  anderen mit `skill_level` getaggt (z.B. Mountain Climber 1 · KB Swing 2 · Burpee 3 · Barbell Thruster 4).
  Gating unverändert: der Klient bekommt Übungen **bis zu seinem Level** (L4 inkl. aller einfacheren).
  `impact_level` (low/med/high) bleibt für den Verletzungsfilter.
- **Progression primär über Trainingsdichte, nicht über Übungstausch:** dieselbe Übung kommt über mehrere
  Level vor; der Unterschied entsteht über **Format und Work:Rest** (NICHT über die Dauer — die kommt aus
  `session_dauer_min`).

**Level → Format / Work:Rest:**

| Level | Formate | Work:Rest | _Dauer-Band (nur Referenz, KEIN Cap)_ |
|---|---|---|---|
| L1 | Intervall, einfacher Circuit | 40:20 | _8–12 min_ |
| L2 | Intervall, AMRAP, Density, Ladders, Komplexe | 45:15 | _12–18 min_ |
| L3 | AMRAP, Circuit, Density, Ladders, Tabata, Komplexe | 45:15 | _15–22 min_ |
| L4 | AMRAP, Tabata, Density, Komplexe | 50:10 | _20–30 min_ |

> Die letzte Spalte ist eine **Referenz-Notiz** (typische Intensitäts-Bänder), **kein Dauer-Cap**: die reale
> Conditioning-Dauer = `session_dauer_min` (s. Dauer-Regel oben). Das Level steuert Format + Work:Rest, nicht die Dauer.

- **Format-eigenes Timing schlägt Level-Work:Rest.** **Tabata** bringt festes Timing mit (**20:10 × 8**,
  fix) und überschreibt die Level-Work:Rest. Nur die Work:Rest-Formate (Intervall, Circuit) nehmen die
  Werte aus dem Mapping. **Der Generator darf kein Tabata mit Level-Work:Rest bauen.**
- **Komplexe ab `skill` 2** (nie skill 1) und **nur mit Last** (KB/Hantel/LH), nie Bodyweight —
  Lasthalten ist das definierende Merkmal; skill-1-Klienten fallen auf andere session-füllende
  Formate zurück. Verfügbarkeit ist **skill-gegated, nicht L4-exklusiv** (Tabelle: L2–L4). Details +
  Ketten s. **Komplexe**-Abschnitt oben.
- **Conditioning trägt KEINE RPE.** Die Intensität ergibt sich aus **Format + Work:Rest + Dauer**. Die
  RPE-Welle und `rpe_hinweis` (Thema 1/3) gelten ausschließlich für **Kraftsätze**, nie für
  Metcon/Conditioning-Blöcke (in MVP-6 bereits so gebaut: `rpe_hinweis` nur nicht-metabolic).

### Recomp-Finisher

Jede Recomp-Kraftsession endet mit einem **globalen Bodyweight-Conditioning-Finisher**:
- **Dauer:** 5–10 Min · **Intensität:** moderat (kein Maximaleinsatz) — über Format/Dauer, **keine RPE**
  (Conditioning trägt keine RPE, Konfliktregel 2026-06-13; früher „RPE 6–7").
- **Equipment:** ausschließlich Bodyweight (unabhängig vom Setup des Klienten)
- **Übungsauswahl:** globale Bewegungen, **keine** isolierten Hauptmuskelgruppen der Session.
  Geeignet: Burpees, Mountain Climbers, Jumping Jacks, Squat Jumps, Push-Ups, High Knees, Bear Crawl,
  Plank Variations.
- **Formate (KI wählt automatisch):** AMRAP, Tabata, Density Block, Zirkel.
- **Abwechslung:** nicht zweimal hintereinander dasselbe Format im 4-Wochen-Block.

### Fettabbau — Conditioning-Tage

- **Rotations-Regel (Konfliktregel, 2026-06-15):** Die **2 Conditioning-Tage einer Woche
  unterscheiden sich** (zwei verschiedene Formate); **kein Format 2× direkt hintereinander**;
  **Wiederholung über die Wochen ist erlaubt.** _(Ersetzt „jeder C-Tag im 4-Wochen-Block ein
  anderes Format" — bei 7 Formaten und bis zu ~24 C-Einheiten/Block mathematisch unerfüllbar.)_
  Verfügbare Formate je **Level** (Level→Format-Map) × **Equipment-Bevorzugung**.
- **Equipment-spezifische Bevorzugung:**
  - Kettlebell → Komplexe, Density, Ladders
  - Bodyweight → AMRAP, Tabata, Zirkel
  - Gym / Home-Gym → alle Formate möglich

> **V1-Stand (MVP-7 Naht 3, 2026-06-15):** Räumliche Rotation gebaut — die 2 reinen
> Conditioning-Tage (Fettabbau 4/5/6) bekommen 2 verschiedene Formate je Level × Equipment
> (`pick_conditioning_formats`, **weiche Bevorzugung**: Equipment-Formate zuerst, dann der
> Level-Rest → 2 C-Tage differenzieren immer). Der Pool umfasst **nur implementierte Formate**
> (amrap/zirkel/intervalle/tabata/density + **Ladders** ab Naht 4d); **Komplexe** bleibt ausgelassen
> (`TODO(mvp7-komplexe)`, s.u.) — bis dahin füllt der Level-Rest die KB-Präferenz auf, soweit nötig.
>
> **V1-Stand (MVP-7 Naht 4, 2026-06-15):** Der **Übungs-Selektor** zieht jetzt aus dem
> Conditioning-Pool (`pattern == "conditioning"` **ODER** `conditioning_friendly`) —
> **deterministisch im Assembler** (Entscheidung A1: Claude für reine C-Sessions umgangen, kein
> MVP-9-Touch): (4a) Pool-Helfer `conditioning_pool`, (4b) **Recomp-/Mischtag-Finisher** zieht aus
> dem Pool (BW-Mehrheit zuerst, Zusatz-Equipment nur ergänzend), (4c) reine C-Tage tragen einen
> `pool:"conditioning"`-Slot-Marker und ziehen ihre Übungen equipment-korrekt aus dem Pool
> (verifiziert: BW-Kunde reine BW inkl. Burpee/Mountain Climbers; KB-Kunde BW-Mehrheit + KB-Zusatz).
> Block-Stapelung über `n_blocks` unverändert.
>
> **Fachliche Begründung der Trennung (nachgetragen 2026-06-17)** — vorher nur pragmatisch/historisch
> dokumentiert („Claude für C-Sessions umgangen, kein MVP-9-Touch"):
> - **Kraft → Claude:** Die Übungswahl trägt mehrdimensionale Urteils-Kriterien, die sich nicht sauber
>   als deterministische Regel fassen lassen — Push:Pull-Balance über die Woche, Symmetrie, energie-
>   intensivster Compound zuerst, Block-Variation, gelenkschonende Wahl bei Verletzung aus mehreren
>   passenden Optionen, plus klient-spezifische Cues/Notizen.
> - **Conditioning/Athletik → deterministisch:** Die analogen Auswahl-Aspekte (Format-Abwechslung,
>   Übungs-Rotation, BW-Mehrheit) sind mechanisch klar regularisierbar und als Code-Regeln kodiert;
>   ein KI-Urteil brächte hier keinen Mehrwert.
> - **Der Auswahlraum (Pool-Größe) ist NICHT der Unterscheidungsgrund** — beide Pools sind ähnlich
>   groß (Kraft ~6–20/Pattern gym, Conditioning roh 15–32). Der Unterschied ist die **Regulierbarkeit
>   der Auswahl-Logik**.
>
> **STATUS: Arbeitshypothese, am echten Output zu verifizieren (Output-Review).** Offen zu prüfen:
> (1) Greift die deterministische Conditioning-Logik fachlich gut, oder wirkt sie schematisch?
> (2) Überzeugt Claudes KI-Auswahl bei Kraft (Balance/Symmetrie/Variation tatsächlich erfüllt)?
> Erst nach Output-Review endgültig: Trennung so lassen (a) oder anpassen.
>
> **V1-Stand (MVP-7 Naht 4d, 2026-06-15) — Ladders + Multi-Format:** **Ladders** ist jetzt
> block-dosierbar (5-Min-Block wie Density, Stapelung identisch) und im Rotations-Pool. **Komplexe**
> bleibt ausgelassen (`TODO(mvp7-komplexe)`: braucht vordefinierte Coach-Ketten — Flow ohne Ablegen,
> nicht aus Einzelübungen stapelbar; gültiges Enum, aber aus dem Pool gefiltert).
> **Format-Maxima** (Maximaldauer am Stück): AMRAP 20 · Density 30 · Tabata 20 · Intervall 25 ·
> Ladders 20 · Zirkel 30 Min. **Multi-Format-Aufteilung reiner C-Tage:** Conditioning-Zeit =
> `session_dauer_min − Warmup`. ≤ Max[Format] → 1 Format füllt die Zeit; größer → 2 Segmente (erstes
> bis zu seinem Max, zweites den Rest; jedes ≥ 10 Min, 5-Min-Raster/Tabata 4er, **nie Rumpf < 10** →
> erstes kürzen, z.B. 35 → 20+15 oder 25+10, nie 30+5). Zweitformat ≠ erstes, **AMRAP bevorzugt**.
> **Kapazitätsbewusstes Erstformat NUR bei langen Sessions:** decken Rotations-Erst- + AMRAP-Zweit-
> format die Zeit nicht innerhalb beider Maxima ab (z.B. 50 Min, nur Max-20-Formate), wird auf ein
> großes Erstformat (Zirkel 30 bevorzugt, sonst Density 30) ausgewichen — sonst bleibt die Naht-3-
> Rotation unangetastet. Nicht abdeckbar → Fehler (melden, nicht still strecken/kürzen). Das 2.
> Segment steht im `conditioning_block_2` (eigenes Feld, nicht der Recomp-Finisher). **Caveat:** bei
> sehr langen Sessions mit erzwungenem großem Erstformat können beide C-Tage identisch werden (die
> räumliche Differenzierung aus Naht 3 verliert Vorrang) → Naht-4e-Gebiet.
>
> **V1-Stand (MVP-7 Naht 4e, 2026-06-16) — Rotationen:** Die **Übungs-Auswahl** rotiert jetzt über
> einen Per-Pattern-Offset (`_pick_finisher_uebungen(..., offset)`): Pattern-Reihenfolge + BW-first
> bleiben, nur welche Übung je Pattern wird je `(woche_idx × C-Tag)` rotiert. → die 2 reinen C-Tage
> einer Woche ziehen **verschiedene Übungen** (nicht nur Format), über die Wochen variiert die Auswahl;
> federt den 4d-Lange-Session-Caveat ab. Der **Mischtag-Finisher** rotiert sein Format über die 4 Wochen
> aus **{AMRAP, Zirkel}** (nie 2× hintereinander; **Tabata/Density-Finisher vertagt** — Block-Count
> sprengt das ~8-Min-Budget) und seine Übungen mit demselben Offset (immer anderer AMRAP/Zirkel);
> mehrere Mischtage/Woche (Fettabbau 5/6) unterscheiden sich untereinander.
>
> **Offen:** nur noch Komplexe (`TODO(mvp7-komplexe)`) — Coach-Ketten + Rahmen (session-füllend) sind
> festgehalten, s. Abschnitt **Komplexe — vordefinierte Ketten** oben.

### Longevity — Cardio/Athletik-Tage

Rotieren zwischen zwei Typen:
- **Zone-2-Cardio:** 30–60 Min lockeres Dauer-Cardio (120–135 bpm) — Laufen, Rad, Rower, schneller Spaziergang.
- **Athletik:** Sprünge (Box Jumps, Broad Jumps), Koordination (Agility-Drills, Sprung-Variationen),
  Bewegungs-Vielseitigkeit (Crawls, Throws).

**Verteilung:**
- 1 Tag/Woche → alternierend (Woche 1 Zone-2, Woche 2 Athletik, …).
- 2 Tage/Woche → 1× Zone-2 + 1× Athletik.

> **V1-Stand (MVP-7 Naht 5, 2026-06-16) — Athletik gebaut:** Longevity-Cardio-Tage rotieren jetzt
> Zone-2 ↔ Athletik (getrennter Pfad `logic/athletik.py`). **2 Cardio-Tage/Woche** (Longevity 5/6) →
> 1× Zone-2 + 1× Athletik (räumlich). **1 Cardio-Tag/Woche** (Longevity 4) → alternierend über die
> Wochen (W1 Zone-2 → W2 Athletik → …, `rotate_cardio`-Flag, Assembler entscheidet je Woche).
> Athletik-Tag: Übungen aus dem **Athletik-Pool** (`"athletik" ∈ pattern_tags`, A1-deterministisch),
> **skill-gestaffelte Dosierung** (Wdh = 20 − skill·4, Sätze 4/4/3/2, Pause ~120 s, „Quality over
> fatigue"), **keine RPE**, **kein Cardio-Block** (ersetzt den Zone-2-Tag), 3:1-Welle mit Deload-Volumen
> ×0.67, Übungs-Rotation wie die C-Tage. **Leer-Pool-Fallback → Zone-2** (greift bei L1-Bodyweight:
> Athletik-Pool leer, weil skill-1-Athletik Equipment braucht → der Tag wird ein Zone-2-Cardio-Tag).
> **Coverage-Lücke** (Coach-Daueraufgabe): Bodyweight = nur Sprünge, **L1-Bodyweight-Athletik-Pool leer**.

**Begründung:** Breiter Format-Baukasten statt weniger Formate, weil Abwechslung den Reiz frisch hält und
verschiedene Energiesysteme trifft. Rotation (Conditioning-Tage einer Woche verschieden, nie 2× direkt
hintereinander dasselbe) gegen Monotonie und Anpassung. Equipment-spezifische Bevorzugung, weil z.B. Komplexe/
Ladders an die Kettlebell gehören, Tabata eher Bodyweight. Recomp-Finisher als globales Bodyweight-
Conditioning (5–10 Min, moderate Intensität ohne RPE), bewusst NICHT die Hauptmuskeln der Session (sonst Ermüdung der Arbeitssätze)
und equipment-unabhängig (immer machbar). Fettabbau jetzt Kraft + Conditioning statt 100 % Conditioning, weil
reines Conditioning im Defizit Muskelmasse kostet — der Kraftreiz erhält Muskel. Longevity Zone-2 + Athletik
alternierend, weil Generalist = Ausdauer UND Athletik (Sprünge/Koordination), nicht nur lockeres Cardio.

---

## 7. Progression über Blöcke hinweg — ✅ entschieden V1 (2026-06-06)

Der Übergang **Block N → N+1** basiert auf drei Datenquellen:

**1) Mini-Anamnese (Check-in am Blockende):**
- Ziel-Änderung? (Muskelaufbau / Fettabbau / Recomp / Longevity)
- Equipment-Änderung?
- **Trainingserfahrung (Trainingsjahre) — neu erfasst**, damit der Level-Deckel (Thema 2) mitwächst (K4).
- **„Hast du aktuell Schmerzen oder Beschwerden?" (Ja/Nein)** → falls ja: **„Welche Körperbereiche?"**
  (Mehrfachauswahl: Knie, Schulter, Rücken, …). Generische Frage — der Klient muss NICHT zwischen
  „neuem" und „altem" Schmerz unterscheiden. Das System gleicht die Antwort intern mit den bisherigen
  Schmerz-/Verletzungsdaten ab und entscheidet, ob ein Filter aktiv bleibt oder neu greift (K2).
- aktuelles Stress-Level (1–10) · aktuelle Schlafstunden
- → Auswertung über bereits definierte Logik (Level, Recovery, Equipment-Filter, Verletzungs-Overrides).

**2) PST Re-Test (Woche 4):**
- Gleiche 5 Übungen wie initial, eigene Session in Woche 4.
- Fließt in die Level-Berechnung für den nächsten Block — **max. ±1 Level pro Block (symmetrisch):**
  deutlich besserer Re-Test → +1, deutlich schlechterer (Detraining) → −1 (K5). Der Trainingsjahre-Deckel
  (aktualisiert via Mini-Anamnese) gilt weiterhin als Obergrenze.

**3) Trainings-Logging während des Blocks:**
- Pro Session: Session-RPE (1–10), Session-Bewertung (zu leicht / passend / zu schwer), optional Notiz.
- Pro Übung: tatsächliche Gewichte und Wiederholungen.

**Logging-basierte Block-Anpassung — zwei Hebel in fester Reihenfolge:**

_Stufe 1 — Sätze (Haupt-Hebel):_ überwiegend „zu leicht" → **+1 Satz** pro Hauptübung (bis Cap 4);
überwiegend „zu schwer" → **−1 Satz** (bis Minimal-Satz).

_Stufe 2 — Übungs-Schwierigkeit (erst wenn Stufe 1 ausgeschöpft):_ „zu leicht" UND Cap 4 erreicht →
schwierigere Variante (`progressions_up`); „zu schwer" UND Minimal-Satz erreicht → leichtere Variante
(`progressions_down`).

- **RPE-Einstieg wird NICHT durch Logging angepasst** — RPE steuert ausschließlich Periodisierung (Welle)
  + Recovery (Stress/Schlaf). Sonst überlagern sich die Hebel.
- **Last-Logs (Gewichte/Wdh):** konkrete **Last-Ziele für den nächsten Block** + **Overload-Tracking**.
- _V1-Hinweis:_ Schwellen für „überwiegend zu leicht/schwer" + Gewichtung über Sessions werden mit
  echten Klienten-Daten feinjustiert.

**Übungs-Rotation — „Kern bleibt, Rest rotiert":**
- **Haupt-Compounds bleiben konstant** über Blöcke (Squat-, Hinge-, Press-, Pull-Slot). Wechsel nur bei
  Equipment-Änderung, Verletzung oder Level-Sprung (→ schwierigere Variante derselben Bewegung).
  Grund: Technik-Aufbau + Progressions-Tracking brauchen Konsistenz.
- **Accessories & Isolation rotieren** — pro Slot möglichst andere Übung als im Vorblock.
- **Bei Ziel-Änderung:** Haupt-Compounds meist gleich (Pattern bleibt), nur Volumen/Format ändert sich.
- **Bei Equipment-Änderung:** alle Übungen neu gewählt (Equipment-Filter greift).

**Volumen/Intensität-Progression:** abgeleitet aus den drei Indikatoren (PST-Re-Test + Mini-Anamnese +
Trainings-Logs), umgesetzt über die Hebel oben (Sätze → Schwierigkeit; RPE nur via Welle + Recovery).

### Session-Feedback — UX-Konzept

- **Während der Session:** Klient trägt nur **Gewicht + Wiederholungen pro Satz** ein. Keine Bewertung
  während des Trainings (kein Flow-Bruch).
- **Session-Review am Ende:** alle Übungen mit den eingegebenen Werten · pro Übung 3-Stufen-Bewertung
  **Leicht / Passend / Schwer** (optional) · **Session-Gesamtbewertung 1–10 (Pflicht zum Abschluss)** ·
  optionale Notiz.
- **Skala-Bedeutung (Frontend-Hinweis):** 1–3 sehr leicht (kein Reiz) · 4–6 passend · 7–8 anstrengend
  aber machbar · 9–10 an der Grenze.
- **Abgebrochene Sessions:** geloggte Sätze bleiben gespeichert; beim nächsten App-Start Hinweis
  „Letzte Session nicht abgeschlossen — bewerten?". Nach 24 h ohne Abschluss → automatisch als
  unvollständig markiert, Daten bleiben.

### Datenbank (neu)

- `exercise_feedback`: client_id, session_id, exercise_name, difficulty_rating (leicht/passend/schwer)
- `session_feedback`: client_id, session_id, difficulty_score (1–10), notes, completed_at

### Self-Service Übungs-Tausch (Feature)

Klient kann Übungen **vor oder während** der Session tauschen, ohne Coach-Anfrage.
- **Trigger:** vor Session „Tauschen"-Button pro Übung (Plan-Ansicht); während Session „Tauschen"-Option.
- **Flow:** Übung wählen → Grund angeben (`Schmerzen/Verletzung` / `Equipment fehlt` / `Variation`) →
  System schlägt **2–3 Alternativen aus gleichem Pattern** vor (aus `substitution_pool`) → Klient wählt →
  Plan wird aktualisiert.
- **Auswahl-Regeln:** Tausch nur innerhalb desselben Patterns (Push→Push, Squat→Squat). Bei
  `Schmerzen/Verletzung` greift **derselbe 3-Stufen-Filter wie im Generator** (Thema 8): `joint_stress`
  + `impact_level: high` + pattern-spezifische Blocker (z.B. Knie → `deep_squat, lunge, jump, plyo`).
  Wochen-Balance bleibt erhalten. (K1)

**Geltungsbereich nach Grund:**
- `Schmerzen/Verletzung`: Übung wird in der aktuellen Session **und automatisch in ALLEN folgenden
  Sessions des aktuellen Blocks** ersetzt. Klient-Hinweis „auch in den folgenden Wochen ersetzt".
  Coach-Notification „Klient X hat Y wegen Schmerzen durch Z ersetzt — für gesamten Block aktiv".
- `Equipment fehlt` / `Variation`: **nur die einzelne Session**, andere Wochen unverändert.

**Block-Übergang:** getauschte Übungen werden im neuen Block **nicht** automatisch wieder aufgenommen.
Mini-Anamnese fragt „Besteht das Schmerz-Problem noch?" → ja: bleibt ersetzt · nein: Original wird
wieder angeboten.

**Neue Tabelle `exercise_swaps`:** client_id, block_number, session_id, exercise_swapped_out,
exercise_swapped_in, reason (schmerzen_verletzung / equipment_fehlt / variation), scope
(single_session / entire_block), swapped_at, active (bool — true bis Block-Übergang oder Aufhebung).

**V2-Potenzial:** System lernt aus Tausch-Patterns (z.B. 3× in Folge getauschte Übung → in der
Standard-Auswahl reduzieren).

### ⚠️ Scope-Hinweis — neue System-Bausteine (weit über die heutige Plan-Generierung hinaus)

- Check-in/Mini-Anamnese-Flow am Blockende (neues Formular).
- Trainings-Logging im Block + Session-Review (UI + Tabellen `exercise_feedback`, `session_feedback`).
- Block-Übergangs-Generator (Logs + Re-Test + Check-in → Block N+1).
- Self-Service Übungs-Tausch (UI + Tabelle `exercise_swaps` + Bibliotheks-Felder).
- Eigene Features/Tabellen, nicht nur Logik-Änderungen — für die Roadmap zentral.

**Begründung:** Drei Datenquellen (Re-Test + Mini-Anamnese + Logs), weil echte Langzeit-Progression
objektive Rückmeldung braucht — ein blind neu generierter Block stagniert. Sätze als Haupt-Hebel, dann
Übungs-Schwierigkeit: erst mehr Volumen im erprobten Bewegungsmuster (sicher, messbar), erst bei
ausgeschöpftem Cap die schwerere Variante. RPE bewusst NICHT durch Logs gesteuert (nur Welle + Recovery),
um Hebel-Überlagerung zu vermeiden. „Kern bleibt, Rest rotiert": schwere Compounds konstant für
Technik-Aufbau und sauberes Overload-Tracking; Accessory/Isolation rotiert für Abwechslung und breitere
Bewegungserfahrung. Max. +1 Level/Block gegen zu große Sprünge. Bewertung erst im Session-Review (nicht
während des Trainings), um den Flow nicht zu brechen. V1-Schwellen bewusst offen — werden mit echten Daten
kalibriert statt geraten.

---

## 8. Sonderfälle — ✅ entschieden (2026-06-06)

### Verletzungs-Filterung (Generator-Seite) — 2-Stufen

Bei Verletzungs-Eingabe (z.B. „Knie") filtert der Generator in dieser Reihenfolge:
1. Übungen mit `joint_stress: knee` ausschließen (Ausschluss-Semantik, SCHEMA.md Abschn. 2).
2. Übungen mit `impact_level: high` ausschließen (bei Verletzung generell vorsichtiger).

> **Entschieden 2026-06-12 (ersetzt den früheren 3-Stufen-Ansatz):** Die pattern_tags-Blocker
> (Stufe 3) sind **gestrichen** — nach vollständigem Tagging waren sie zu 90 % redundant oder tot
> und blockten in 31 Fällen genau die bewusst nicht getaggten Reha-Keeper (z.B. Reverse Lunge bei
> Knie, Trap Bar Deadlift bei Rücken). Ihre einzige echte Lücke (Knöchel ↔ tiefe Dorsalflexion)
> ist durch den ankle-Tagging-Nachtrag geschlossen. `joint_stress` + `impact_level` sind die
> **einzige Wahrheit**; Qualitätssicherung über das verbindliche Validator-Gate (SCHEMA.md).

Ersatz immer aus gleichem Pattern. **Wichtige Klarstellung:** das System erkennt Gelenk-Belastung NICHT
aus dem Übungsnamen — **jede Übung muss explizit getaggt sein.**

> **Leerer-Pool-Fallback (MVP-5 Naht 4, `db80429`):** Bleibt ein Pattern-Pool nach dem Filter leer
> (z.B. Bodyweight-`push_vertical` bei Schulter), springt das **biomechanisch verwandte Pattern**
> ein (markiert, `_FALLBACK_PATTERN` in equipment_filter) — die Sicherheitsstufen werden dabei NIE
> gelockert. Greift auch der Ersatz nicht, entfällt der Slot ersatzlos. Reduziert sich über den
> Bibliotheks-Ausbau (BACKLOG MVP-2).

### Übungs-Bibliothek — Ziel-Schema (`exercises`)

Verbindliches Schema inkl. Tagging-Vokabel: siehe **`SCHEMA.md`**. Diese Spec definiert
nur die fachlichen Anforderungen: 3-Stufen-Verletzungsfilter (`joint_stress` →
`impact_level: high` → pattern-Blocker), Ersatz aus gleichem Pattern, explizites Tagging
jeder Übung als Produktiv-Voraussetzung.

**Tagging-Prozess:** bestehende Bibliothek manuell/KI-assistiert taggen · neue Übungen bei Anlage direkt
taggen · Coach kann Tags im Backoffice korrigieren.

**⚠️ Voraussetzung für Produktivgang:** Die Übungs-Bibliothek muss **vollständig getaggt** sein —
Bedingung für die Verletzungs-Logik UND den Self-Service-Tausch (Thema 7).

### Nebenziel

**Wird entfernt.** Nebenziel hat keinen Effekt auf den Plan → raus aus Formular, `models.py`, `parsers.py`.
Klare Ausrichtung auf ein Hauptziel.

### Akuter Schmerz — „Schmerz-Meldung" (Dashboard-Feature)

Das bisherige Formular-Feld `schmerzen_akut` (Ja/Nein in der Anamnese) **entfällt als Formular-Eingabe**
und wird zu einer **jederzeit verfügbaren Schmerz-Meldung im Klient-Dashboard.**

- **Trigger:** Button „Schmerz melden" im Dashboard, jederzeit (unabhängig von Anamnese-Zeitpunkten).
- **Flow:** Klient klickt → gibt **Körperbereich** (Knie, Schulter, Rücken, …) + kurze **Beschreibung** an
  → Meldung wird gespeichert → Coach bekommt **sofortige Notification** „Klient X hat Schmerzen gemeldet".
- **Plan:** läuft **normal weiter, kein automatischer Eingriff.** Klient kann einzelne Übungen weiterhin
  selbst tauschen (Self-Service, Thema 7). Coach entscheidet manuell, ob/wie er eingreift.
- **Neue Tabelle `pain_reports`:** client_id, report_date, body_part, description, status
  (`open` / `coach_acknowledged` / `resolved`).
- **Begründung:** jederzeit ein Melde-Kanal ohne auf die nächste Anamnese zu warten; Coach bleibt
  informiert; **kein** Auto-Eingriff, weil „akuter Schmerz" zu unspezifisch für automatische Logik ist —
  Coach-Urteil ist hier sicherer.
- **Abgrenzung zur Mini-Anamnese (Thema 7, K3):** Die Mini-Anamnese-Schmerzfrage erfasst beim
  **Block-Übergang** den aktuellen Zustand und steuert den **Übungs-Filter des nächsten Blocks**. Die
  Dashboard-Meldung ist der **akute Ad-hoc-Kanal mitten im Block** (Coach-Info, kein Auto-Eingriff).
  Beide schreiben in dieselbe Schmerz-/Verletzungshistorie; das System gleicht ab.
- → Code-Änderung: `schmerzen_akut` raus aus Anamnese/Typeform & `models.py`; neues Dashboard-Feature +
  `pain_reports`-Tabelle + Coach-Notification.

**Begründung:** Verletzungs-Filter kombiniert (joint_stress + impact_level als Hauptfilter, pattern_tags
als Sicherung), weil getaggte Gelenkbelastung präziser ist als Namens-/Tag-Heuristik — die Doppelung gibt
Sicherheitsmarge bei einem Gesundheitsthema. Explizites Tagging nötig, weil das System Belastung nicht aus
Übungsnamen ableiten kann; daher die vollständig getaggte Bibliothek als Produktiv-Voraussetzung. Nebenziel
gestrichen, weil es nie wirkte und ein klar fokussiertes Hauptziel bessere Pläne gibt als ein verwässerter
Mix. Akuter Schmerz als Dashboard-Meldung statt Formular-Flag mit Auto-Eingriff, weil „Schmerz" zu
unspezifisch für automatische Programm-Logik ist — Coach-Urteil ist sicherer; der Jederzeit-Kanal hält den
Coach informiert, ohne auf die nächste Anamnese zu warten.

---

## Konsistenz-Check — Protokoll (2026-06-06)

Vollständige Spec auf Widersprüche geprüft.

**✅ Sauber:** Volumen- und RPE-Hebel sind klar getrennt (Volumen: Modell A + Logs; RPE: Welle +
Recovery + Deload-Floor) — keine Überlagerung. PST-Re-Test nutzt dieselbe Test-Battery & Scoring wie die
Erst-Berechnung (Thema 2).

**Behobene Widersprüche:**
- **K1** — Self-Service-Tausch nutzt bei Schmerz jetzt denselben 3-Stufen-Verletzungsfilter wie der
  Generator (`joint_stress` + `impact_level` + pattern-Blocker).
- **K2** — Mini-Anamnese stellt eine generische Schmerzfrage; das System gleicht intern mit der Historie
  ab. Der Klient unterscheidet nicht neu/alt.
- **K3** — Schmerz-Kanäle abgegrenzt: Mini-Anamnese (Block-Übergang, steuert Filter) vs. Dashboard
  (akut, Coach-Info, kein Auto-Eingriff).
- **K4** — Trainingsjahre werden in der Mini-Anamnese neu erfasst → Level-Deckel wächst mit.
- **K5** — Level kann beim Re-Test symmetrisch um max. ±1/Block steigen oder sinken (Detraining).
