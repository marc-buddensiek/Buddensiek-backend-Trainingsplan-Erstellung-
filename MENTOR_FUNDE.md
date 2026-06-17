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
- **KI-Antwort leer/ungültig:** Klient bekommt was? Wird Coach informiert?
- **pending_review:** automatisch raus oder Human-in-the-Loop Coach-Review?
- **schmerzen_akut:** was passiert konkret? (Eskalation/Restriktion/nur Prompt)
- **Datenschutz/GDPR:** Speicherort, Zugriff, Aufbewahrung, KI-Weitergabe +
  Offenlegung an Klient
- **Externe Services down** (Typeform/KI/Supabase): Klient-Verhalten je Service
- **Plan-Generierungs-Geschwindigkeit:** Zielwert
- **4-Wochen-Block-Ende:** wer triggert, was wenn kein Re-Test
- **Methodik-Versions-Stempel:** jeder Plan trägt Methoden-Version (billig jetzt)

## C) Top-Hebel & Größeres

- **API-Vertrag mit Manu schriftlich** (OpenAPI/FastAPI): rpe-float +
  `conditioning_block_2` betreffen ihn direkt — höchste Priorität
- **Korrektheits-Checker / Test-Matrix** = MVP-11 (geplant)

## Bestätigt richtig (kein Handlungsbedarf)

Eine Naht/Commit, Diff vor OK, kein Feature ohne Konsument, „grün≠richtig",
Tool-Wahl (FastAPI/Render/Supabase/Pydantic) reasonable.
