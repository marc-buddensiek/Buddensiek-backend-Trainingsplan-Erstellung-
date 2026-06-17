# Mentor-Funde — Status & Abarbeitung

> Funde aus einem externen Mentor-Review (älterer Repo-Stand). Reine Doku.
> Status pro Fund wird beim Verifikations-Lauf (Grep/Lesen, kein Code) nachgezogen.

## A) Code-Funde — zu verifizieren (Grep/Lesen)

1. **Umlaut-Inkonsistenz:** interne Identifier mit Umlauten? (`ziel_sätze` vs
   `ziel_saetze` und allgemein ä/ö/ü/ß in `.py`-Identifiern) — Status: VERALTET
   (kein Umlaut-Identifier; durchgängig `ziel_saetze`, Umlaute nur in Enum-Werten/Strings)
2. **Woche-4 Deload vs. Peak:** Mismatch Testdaten „deload" vs. Code „peak",
   der crashen könnte? — Status: VERALTET (kein `peak`-Literal im Code; `block_typ`
   konsistent „deload" in Modell/Validator/Assembler/Fixture)
3. **API-Key-Name:** `.env.example`-Name == vom Code gelesener Env-Var-Name?
   — Status: BESTÄTIGT → gefixt in diesem Commit (.env.example + Skripte auf
   `ANTHROPIC_API_KEY`/`sk-ant-...` angeglichen; claude_client.py war schon korrekt)
4. **Pipeline-Test „0/23":** deckt Test-Suite den vollen Plan-Bau end-to-end
   (bis PDF) ab? — Status: VERALTET (run_tests baut via `assemble_plan`,
   generate_test_plans rendert PDFs; 26/26·7/7·5/5·3/3·2/2·18/18 grün)
5. **Sicherheit Kraft-Pfad:** kontraindizierte Übungen deterministisch VOR
   Claude-Auswahl gefiltert (nicht nur „vermeiden"-Notiz)? — Conditioning
   ist via Pool-Selektor (Naht 4) erledigt; Kraft-Pfad = MVP-9, prüfen.
   — Status: BESTÄTIGT (bereits sicher: `filtere_uebungen` entfernt kontraindizierte
   Übungen deterministisch VOR Claude; übergebene Liste ist verletzungssicher, keine
   bloße „vermeiden"-Notiz. Claude-Auswahl selbst = MVP-9, Filter sitzt upstream)

## B) Produkt-/Policy-Entscheidungen — Alen beantwortet (kein Code)

- **Doppel-Submit** des Intake-Formulars: ein Plan oder zwei?
  [AUFWAND: mittel — Entscheidung kurz, Umsetzung Standard-Muster (Duplikat
  erkennen + blocken)] [WANN: MVP-10/12, wenn Intake live geht]
- **KI-Antwort leer/ungültig:** Klient bekommt was? Wird Coach informiert?
  [AUFWAND: mittel — Entscheidung kurz, Umsetzung = Retry + Fehler abfangen +
  Coach-Benachrichtigung] [WANN: MVP-9]
- **pending_review:** automatisch raus oder Human-in-the-Loop Coach-Review?
  [AUFWAND: Entscheidung 1 Min; Umsetzung klein wenn simpel startet (Mail +
  manuelle Freigabe), wächst bei Bedarf] [WANN: MVP-10, vor Live-Gang]
- **schmerzen_akut:** was passiert konkret? (Eskalation/Restriktion/nur Prompt)
  [AUFWAND: Entscheidung kurz (Coach-Eskalation oder Restriktion); Umsetzung
  klein-mittel] [WANN: MVP-9, mit KI-Übungswahl]
- **Datenschutz/GDPR:** Speicherort, Zugriff, Aufbewahrung, KI-Weitergabe +
  Offenlegung an Klient
  [AUFWAND: GROSS — Recht + Produkt + Technik, kein Code-Prompt; ggf. fachliche
  Beratung, Datenschutzerklärung, Speicher-/Lösch-Konzept, Offenlegung
  KI-Weitergabe] [WANN: zwingend vor Live-Gang, Vorarbeit früh beginnen]
- **Externe Services down** (Typeform/KI/Supabase): Klient-Verhalten je Service
  [AUFWAND: mittel — pro Service eine Verhaltens-Entscheidung + Ausfall-
  Behandlung im Code] [WANN: verteilt MVP-9/10/12]
- **Plan-Generierungs-Geschwindigkeit:** Zielwert
  [AUFWAND: klein — fast nur Zielwert-Entscheidung, beeinflusst wie anderes
  gebaut wird] [WANN: MVP-8/9 als Zielvorgabe]
- **4-Wochen-Block-Ende:** wer triggert, was wenn kein Re-Test
  [AUFWAND: GROSS — eigener Funktionsbereich (Re-Test, Folge-Plan,
  Nicht-Antwort-Fall)] [WANN: V1.5, nach erstem Live-Gang]
- **Methodik-Versions-Stempel:** jeder Plan trägt Methoden-Version (billig jetzt)
  [AUFWAND: klein — ein Feld, bei Generierung setzen; JETZT billig, später teuer
  nachzurüsten] [WANN: früh, spätestens MVP-8/9]

## C) Top-Hebel & Größeres

- **API-Vertrag mit Manu schriftlich** (OpenAPI/FastAPI): rpe-float +
  `conditioning_block_2` betreffen ihn direkt — höchste Priorität
- **Korrektheits-Checker / Test-Matrix** = MVP-11 (geplant)

## D) Zeitlich eingeordnet — an MVP gebunden

### API-Vertrag mit Manu → MVP-10/12 (NICHT jetzt)
- Mentors „höchster Hebel", aber Timing ist später: setzt voraus, dass
  (a) ein Auslieferungs-Endpunkt existiert (`GET /api/plan/{id}` o.ä.) und
  (b) das Backend deployed läuft.
- Stand heute (verifiziert): 3 Endpunkte existieren — `GET /health`,
  `POST /api/new-plan` (fire-and-forget, liefert KEINEN Plan zurück),
  `POST /api/dev/test-plan` (dev-only, 403 in Prod). KEIN Klienten-
  Auslieferungs-Endpunkt. Auslieferung läuft downstream (Supabase/PDF).
- FastAPI erzeugt `/docs` (OpenAPI) automatisch — lokal erreichbar, deployed
  noch nicht (STATUS: Deployment offen). Sobald MVP-10 (Endpunkt) + MVP-12
  (deployed) durch sind: Manu bekommt die öffentliche `/docs`-URL als
  selbst-aktualisierenden Live-Vertrag. Kein handgeschriebener Vertrag nötig.
- Merkposten Deployment: `render.yaml` hat `sync:false` — etwaige `/docs`- oder
  Endpunkt-Änderungen müssten manuell nachgezogen werden.

### Intake: Typeform → Fillout → MVP-12
- Entscheidung steht: Fillout statt Typeform.
- Webhook-fähig (native Integration, POST an `/api/new-plan` möglich) —
  technisch kompatibel.
- ABER: Code liest aktuell Typeform-Format (`event_type=='form_response'`,
  `data/fake_typeform.json`). Fillout hat anderes Webhook-Format →
  Intake-Parser muss für Fillout (um)gebaut werden.
- WANN: bei MVP-12 (Intake-Pfad wird erst dann echt). NICHT vorziehen —
  sonst Parser doppelt gebaut. Intake-Parser von vornherein für Fillout
  bauen, nicht für Typeform.
- Merkposten: `data/fake_typeform.json` bei MVP-12 durch Fillout-
  Beispiel-Payload ersetzen/umbenennen.

### Korrektheits-Checker / Test-Matrix → IST MVP-11
- Mentors „test matrix" (4.3) = dein geplantes MVP-11. Keine neue Arbeit,
  nur Bestätigung. Prüft alle Kombinationen (Ziel × Tage × Dauer × Level ×
  Verletzungen), meldet nur Regel-Verstöße. Du definierst die Regeln aus
  Kategorie B + den Methodik-Invarianten.

### Approach (a) „Generate, don't duplicate" → Prinzip ab jetzt, praktisch bei MVP-8/10
- Single Source of Truth, Rest daraus erzeugen. Lebst du schon (COACHING_SPEC,
  SCHEMA). Wird konkret beim API-Vertrag: Plan-Form/Datentypen aus der
  OpenAPI-Spec erzeugen, nicht von Hand doppeln.

### Approach (b) „Automated checks as a gate" (CI) → MVP-11/12
- Korrektheits-Checker + API-Vertrag-Prüfung laufen automatisch bei jeder
  Änderung und blockieren, was sie bricht. Baut auf MVP-11 auf, scharf bei
  MVP-12 (Deployment). Verallgemeinerung deiner „kein Library-Commit ohne
  grünen Validator"-Regel.

### Level-Korridor-Deckel + Coach-Kapazitäts-Flag → VERWORFEN (nicht mehr MVP-8)
- **Bewusst & endgültig gestrichen (2026-06-17), nicht aufgeschoben.** Modell A dosiert das Volumen
  bereits (Tier-Sätze + Slot-Limit + Dauer-Deckel); ein Muskel-Korridor-Deckel + das darauf aufbauende
  `plan_metadata`-Flag wären eine **konkurrierende Steuerung auf anderer Achse** (Muskel-Sätze vs.
  Tier-Sätze), bräuchten eine nicht vorhandene Muskel-Aggregation und wurden schon einmal aus diesem
  Grund verworfen (Tagging-Wurzel glutes/quads). Coach reviewt manuell (human-in-the-loop). MVP-8 =
  nur noch Assembler/PDF; `plan_metadata` bleibt ungenutzter `=None`-Platzhalter.
- **OFFEN (→ MVP-11 Output-Review):** Dosiert Modell A das Volumen fachlich ausreichend OHNE
  Muskel-Korridor? Annahme **nicht verifiziert** — bei der Test-Output-Review (Ziel × Tage × Dauer ×
  Level) als Coach prüfen, ob das Volumen pro Muskel/Woche plausibel ist. Falls nicht: **gezielte**
  Lösung statt Generaldeckel. Ziel: Pläne ohne manuelles Drüberschauen fachlich korrekt.
- **Realism-/Kapazitäts-Warnung aus dem Klienten-PDF entfernt (2026-06-17):** „zu wenig Zeit fürs
  Ziel gewählt" gehört **beim Ausfüllen** ins Intake/Frontend (Fillout/Manu), nicht ins fertige
  Premium-PDF — konsistent mit der Kapazitäts-Streichung. `pruefe_realismus` bleibt als Funktion +
  Tests erhalten (kein Produktions-Konsument mehr) für die Intake-Wiederverwendung. Prüft nur das
  Zeitbudget (tage × dauer), **keine** strukturellen Plan-Defekte.

## E) GDPR-Aktionsplan — vor Live-Gang

WANN: Startpunkt sobald MVP-9 läuft und Richtung Supabase (MVP-10) geht.
Begründung: Ab echten Klientendaten in echter DB greift die Pflicht;
bei Fake-Daten/lokal noch nicht. Rechtlicher Teil kann Wochen dauern →
Vorarbeit (Denken) früh, Umsetzung an MVP-10/12.

HINWEIS: Gesundheitsdaten (Verletzungen, Diagnosen, Stress, Schlaf) =
besondere Kategorie (DSGVO Art. 9), strenger geschützt. Kein „Häkchen".

Schritte in Reihenfolge:

1. **Datenfluss-Landkarte** (selbst, kann jetzt): Welche Daten erhebe ich, wo
   fließen sie hin, wer/was sieht sie?
   Heutiger Fluss: Typeform (Erhebung) → Backend → Claude/Anthropic
   (KI-Übungswahl) → Supabase (Speicher) → PDF. Jede Station = Ort mit
   Gesundheitsdaten.

2. **KI-Weitergabe** (heikelster Punkt, Design-Entscheidung bei MVP-9):
   Daten gehen an Anthropic = Weitergabe an Auftragsverarbeiter. Prüfen:
   Muss ich identifizierende Daten überhaupt an die KI schicken, oder
   reicht PSEUDONYMISIERT („Klient, Knieproblem, Level 2" ohne Name)?
   Wenn KI nicht weiß WER, entschärft das viel. → beim Bau von MVP-9
   bewusst entscheiden.

3. **Auftragsverarbeitungsvertrag (AVV)** mit Anthropic UND Supabase klären
   (stellen Anbieter i.d.R. bereit). Server-Standort Supabase = EU prüfen.
   Intake-Tool: Wechsel von Typeform zu FILLOUT beschlossen. Fillout EU-Hosting
   nur auf Team/Enterprise-Plan + muss nach Upgrade per Support angefragt werden
   (Standard = USA). Für Gesundheitsdaten zwingend EU-Hosting aktivieren.

4. **Pflicht-Dokumente:** Datenschutzerklärung (was/wofür/wie lange/an wen)
   + Verzeichnis der Verarbeitungstätigkeiten + Klientenrechte (Auskunft,
   Löschung). → HIER einmal Datenschutz-Anwalt/Berater hinzuziehen
   (1 Stunde „prüf das"): Gesundheitsdaten + KI-Weitergabe ist die
   Risiko-Kombination, Laienfehler teuer.

5. **Technisch** (Code, NACH Policy-Entscheidung): Verschlüsselung, Lösch-
   Konzept (Aufbewahrungsdauer, wie löscht Klient seine Daten).

Offenlegung an Klient: dass Daten an KI-Anbieter gehen, muss transparent
gemacht werden (Teil von Schritt 4).

## Bestätigt richtig (kein Handlungsbedarf)

Eine Naht/Commit, Diff vor OK, kein Feature ohne Konsument, „grün≠richtig",
Tool-Wahl (FastAPI/Render/Supabase/Pydantic) reasonable.
