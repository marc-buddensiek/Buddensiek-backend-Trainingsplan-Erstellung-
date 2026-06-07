# Projektstatus — Buddensiek Performance KI-Trainingsplan

_Zuletzt aktualisiert: 2026-06-02_

---

## 1. Aktueller Stand

Das System ist vollständig implementiert von Typeform-Webhook bis PDF.  
Alle Tests grün: **26/26 Logik-Tests** + **7/7 Realism-Tests**.  
**16 Test-PDFs** generiert (alle Pipeline-Pfade ohne Claude API).

Die Pipeline läuft durch:
```
Typeform → parsers.py → level_calculator → split_selector → equipment_filter → claude_client → plan_assembler → PDF + Supabase
```

Claude API und Supabase sind noch nicht live geschaltet — der gesamte Logik-Stack läuft und ist testbar ohne API-Keys.

---

## 2. Was in der letzten Session gemacht wurde

**Fix 1 — `plan_assembler.py`**  
Variable `ist_mobility` war nie explizit gesetzt (nur implizit durch den if/else-Zweig).  
`metcon_blk` war im Mobility-Zweig nicht initialisiert — hätte zur Laufzeit `NameError` geworfen.  
Fix: `ist_mobility = session_typ == "mobility"` und `metcon_blk = None` vor dem if/else; `Session()`-Konstruktor vereinfacht zu `metcon_block=metcon_blk`.

**Fix 2 — `pdf_generator.py`**  
`MetconBlock` wurde im PDF nicht gerendert.  
Fix: Neuer **CONDITIONING FINISHER** Block nach den Hauptübungen — dunkelblauer Header, Format-Notiz, Übungsliste mit Volumen/RPE/Cues.

**CLAUDE.md erstellt**  
Tech-Stack, Ordnerstruktur, Befehle, Pipeline, Coaching-Konventionen, Enums.

---

## 3. Was die Test-Suite prüft

### Logik-Tests (26 Tests) — `scripts/run_tests.py`

Die Tests prüfen die Pipeline bis Schritt 5 (kein Claude, kein Supabase).  
Jeder Test: `parse → level → volumen (alle 4 Wochentypen) → split → equipment_filter`.

**Assertions pro Test:**
- `ziel_saetze >= 1` für alle 4 Wochentypen
- `4 <= ziel_rpe <= 10` für alle 4 Wochentypen
- Split hat mindestens eine Session
- Equipment-Filter liefert mindestens 4 Übungen gesamt

**Abgedeckte Pfade:**

| Kategorie | Was getestet wird |
|---|---|
| Equipment (6×) | gym / home_gym / kettlebell / bodyweight / travel / hybrid |
| Ziele (5×) | muskelaufbau / fettabbau / recomp / ausdauer / gesundheit |
| Tage (5×) | 2 / 3 / 4 / 5 / 6 Trainingstage |
| Level (2×) | Level 1 (Anfänger-PST) / Level 4 (Athleten-PST) |
| Verletzungen (4×) | Schulter / Knie / mehrere / akuter Schmerz |
| Recovery (2×) | Hoher Stress (9/10, 5h Schlaf) / Optimale Recovery |
| Nebenziel (2×) | Muskel+Fett / Fett+Ausdauer |
| Slot-Architektur (3×) | Anna L1 Recomp 4×45 (5 Slots) / Max L2 Muskel 4×60 (6 Slots) / Tim 2×20 (3 Slots Full Body) |

### Realism-Tests (7 Tests)

Prüft `pruefe_realismus(ziel, tage, dauer_min)` gegen Wochenzeit-Schwellen:

| Test | Wochenzeit | Erwartet |
|---|---|---|
| Muskelaufbau 2×20 | 40 min | warnung |
| Recomp 3×30 | 90 min | warnung |
| Muskelaufbau 3×45 | 135 min | hinweis |
| Muskelaufbau 4×45 | 180 min | OK |
| Recomp 4×60 | 240 min | OK |
| Gesundheit 2×60 | 120 min | OK (exakt an Schwelle) |
| Gesundheit 2×20 | 40 min | warnung |

---

## 4. Offene Frage: Bilden die Test-Regeln deine echten Coaching-Standards ab?

**Das muss mit dir abgeglichen werden.**

Die Tests prüfen aktuell nur dass das System _läuft und keine Fehler wirft_ — nicht ob die inhaltlichen Ergebnisse deinen Coaching-Standards entsprechen. Konkret unklar:

**Level-Berechnung:**
- Stimmen die PST-Punkte-Schwellen für Level 1/2/3/4 mit deiner Erfahrung überein?
- Sind die Trainingsjahre-Caps (keine→L1, unter_1→L2, ein_bis_zwei→L3, drei+→kein Cap) so richtig?

**Volumen:**
- Sind die Satz-Ranges pro Level und Wochentyp (z.B. L2 Akkumulation: X Sätze, RPE Y) realistisch für deine Klienten?
- Recovery-Modifier: Stress ≥ 8 oder Schlaf ≤ 5h → RPE −1 und −10% Volumen — zu aggressiv? Zu mild?

**Split-Logik:**
- Fettabbau = 100% Conditioning (kein Kraft) — ist das so gewollt für alle Fettabbau-Klienten?
- Recomp = Kraft + MetconBlock-Finisher — passt das Format?
- Ausdauer und Gesundheit sind noch nicht final definiert (aufgeschoben).

**Realism-Schwellen:**
- Muskelaufbau: warnung < 120 min/Woche, hinweis 120–180 min, OK ≥ 180 min — stimmt das?
- Gesundheit: warnung < 60 min, hinweis 60–120 min, OK ≥ 120 min — stimmt das?

**Was fehlt in der Test-Suite:**
- Kein Test prüft ob die _richtigen_ Übungs-Pattern für einen Split assigned werden
- Kein Test prüft ob Verletzungs-Substitutionen korrekt greifen (nur dass die Übungszahl kleiner wird)
- Kein Test prüft den tatsächlichen PDF-Inhalt

---

## 5. Nächste Schritte

1. **Coaching-Standards abgleichen** — die Fragen aus Abschnitt 4 mit Alen durchgehen, Schwellen und Regeln ggf. korrigieren

2. **Ausdauer + Gesundheit definieren** — Session-Format festlegen (analog zu Muskelaufbau/Recomp/Fettabbau), dann in `split_selector.py` implementieren

3. **Fettabbau dual-conditioning** — User hatte erwähnt: bei 45/60 min ggf. zwei Conditioning-Formate kombinieren statt nur eines. Logik definieren und umsetzen.

4. **Claude-Prompt finalisieren** — `claude/prompt_template.py` auf aktuellen Stand bringen und mit echten API-Calls testen (`python3 scripts/run_tests.py --claude`)

5. **Supabase-Schema anlegen** — Tabellen `klienten` und `plaene` in Supabase erstellen, `db.py` testen

6. **Railway Deployment** — App live schalten, Typeform-Webhook konfigurieren, End-to-End-Test mit echtem Formular

7. **Vercel Frontend** — Plan-JSON aus Supabase lesen und anzeigen (separates Repo)
