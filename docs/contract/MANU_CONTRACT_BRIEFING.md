# JSON-Vertrag — Briefing fürs Frontend (Manu)

## Was das ist
Das Backend erzeugt pro Klient einen 4-Wochen-Trainingsplan als **JSON** — das ist das Produkt, das
die Web-App rendert. Das PDF ist nur Coach-/Dev-Vorschau, nicht der Auslieferungsweg. Dieses Briefing
+ die Beispiel-JSONs + SCHEMA_REFERENZ.md sind die Vertragsgrundlage. Die Beispiele sind die genaue
Wahrheit fürs Feld-Set; dieses Dokument trägt die Regeln & Absichten.

## Grobstruktur
plan → wochen[4] → jede Woche hat sessions[] → jede Session: warm_up, haupt_uebungen[],
metcon_block (Conditioning), cardio, cool_down. (Details: Beispiel-JSON.)

## Regeln (bitte so umsetzen)
1. **Einheitliches Übungs-Schema.** Jede Übung (Kraft, Conditioning, Warm-up, Cool-down) trägt
   `wert` (String) + `einheit` (wiederholungen | sekunden | meter | format). EINE Render-Logik für alle.
2. **`fokus_anzeige` ist das Kundenlabel.** Das anzeigen — NICHT das interne `fokus`-Feld.
3. **Reihenfolge folgt dem `tag`-Feld** (Wochentag), nicht der Array-Position. Sessions bitte nach
   Wochentag sortieren. (Ermöglicht späteren Tag-Tausch ohne Backend-Änderung.)
4. **Tolerant reader.** Felder, die du nicht kennst, ignorieren. Der Vertrag ist additiv-erweiterbar —
   neue optionale Felder kommen später dazu (z.B. Logging in V1.5); das darf die App nicht brechen.
5. **`seiten`.** Wenn gesetzt (int) → Übung ist „pro Seite", als „X je Seite" anzeigen. Wenn null →
   normal. (Aktuell überall null — das Feld ist da, die Befüllung kommt später; Anzeige-Logik bitte
   trotzdem schon einbauen.)
6. **Zirkel/Runden.** Conditioning-Blöcke mit `runden` (int) am BLOCK = „N Runden durch alle Übungen";
   die Übungen tragen dann KEIN `saetze`. `runden_pause_sek` = Pause nach jeder Runde. Zeit-basierte
   Formate (amrap/density) tragen `runden: null` (Zeit steckt in `wert`/`format_notiz`).

## Eine offene Frage an dich
Zwei interne Routing-Werte fahren im JSON mit, jeweils neben ihrem sauberen Label:
- `cardio.typ` ("liss"/"hiit") — Anzeige über `cardio.beschreibung` / `fokus_anzeige`, nicht "liss" roh.
- `fokus` (z.B. "Density — Volumen-Kondition") — interner Key; Anzeige über `fokus_anzeige`.
**Sollen die internen Werte im Vertrag bleiben** (du ignorierst sie dank tolerant reader) **oder raus?**
Beides geht — deine Präferenz entscheidet.

## Was sich noch ändert — aber NICHT das Schema
Die Trainings-INHALTE werden noch überarbeitet (Übungsauswahl, Dosierung, Reihenfolge, Volumen). Das
ändert WERTE in den Feldern, nicht die Felder. Du kannst gegen dieses Schema bauen — die Form ist stabil.

## Dateien
- examples/beispiel_recomp_gym_l3.json — Kraft + Zirkel-Finisher (runden block-level)
- examples/beispiel_fettabbau_kb_l2.json — Kraft + Density (Zeit-Format, runden:null)
- examples/beispiel_longevity_bw_l2.json — Kraft + Zone-2-Cardio + Athletik (cardio.beschreibung + dauer_min, ohne internen typ)
- SCHEMA_REFERENZ.md — Feld-Definitionen (aus models.py)
