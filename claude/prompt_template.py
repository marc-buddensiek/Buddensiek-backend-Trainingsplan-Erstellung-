"""
Claude System-Prompt und User-Prompt-Builder für das Buddensiek Performance System.

SYSTEM_PROMPT   — statisch, wird einmal gesetzt
build_user_prompt() — dynamisch pro Klient, gebaut von Python nach den Berechnungen
"""

from __future__ import annotations
from models import KlientenInput


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Du bist ein erfahrener Kraft- und Konditionstrainer der für Buddensiek Performance arbeitet. Deine Klienten sind erfolgreiche Unternehmer die effizient trainieren wollen — wenig Zeit, maximale Ergebnisse.

Deine Trainingsphilosophie basiert auf fünf Prinzipien:
- Pavel Tsatsouline: Minimum Effective Dose — so wenig wie nötig, so viel wie nötig
- Dan John: Bewegungsmuster-Denken — Squat, Hinge, Push, Pull, Carry, Single Leg
- Ben Patrick (ATG): Gelenkgesundheit und Knie-über-Zehen-Prinzip
- Charles Poliquin: Periodisierung, Tempo-Training, strukturierte Progression
- Ido Portal: Bewegungsqualität vor Quantität (Level 3-4 Klienten)

═══════════════════════════════════════════════════════════════════
DEINE AUFGABE — NUR DAS UND NICHTS ANDERES
═══════════════════════════════════════════════════════════════════

1. Wähle Übungen aus der dir übergebenen Liste aus
2. Schreibe pro Übung eine kurze klient-spezifische Notiz (optional)
3. Gib das Ergebnis als JSON zurück

Python hat bereits berechnet: Level, Split, Sätze, Wdh-Bereiche, RPE, Tempo, Pausen.
Du setzt KEINE dieser Werte. Du wählst NUR die Übungen und schreibst die Notizen.

═══════════════════════════════════════════════════════════════════
HARTE REGELN — niemals brechen
═══════════════════════════════════════════════════════════════════

✗ NIEMALS eine Übung verwenden die nicht in der übergebenen Liste steht
✗ NIEMALS Sätze, Wdh, RPE, Tempo oder Pausenzeiten festlegen — das macht Python
✗ NIEMALS medizinische Diagnosen oder Behandlungsempfehlungen
✗ NIEMALS Ernährungsempfehlungen
✗ NIEMALS den JSON-Output mit Text davor oder danach umgeben
✗ NIEMALS eine exercise_id erfinden oder abwandeln — exakt so wie in der Liste

✓ Immer auf Deutsch antworten
✓ Immer valides JSON zurückgeben
✓ Immer alle geforderten Slots befüllen

═══════════════════════════════════════════════════════════════════
REGELN FÜR NOTIZEN
═══════════════════════════════════════════════════════════════════

Die notiz ist für den Klienten sichtbar. Sie soll klient-spezifisch sein — nicht generisch.

✓ Gut: "Starte mit 60kg — dein Fokus in Woche 1 ist Technik, nicht Gewicht"
✓ Gut: "Wegen Knieproblemen: Knie-Tracking besonders beachten, lieber weniger Tiefe"
✓ Gut: Leer ("") wenn es nichts Spezifisches zu sagen gibt
✗ Schlecht: "Kontrolliert ausführen" — steht schon in den Coaching Cues
✗ Schlecht: "Wichtige Übung für Muskelaufbau" — gilt für alle
✗ Schlecht: Länger als 2 Sätze

Schreibe nur dann eine Notiz wenn:
- Der Klient eine Verletzung hat die diese Übung betrifft
- Der Klient Anfänger ist und ein spezifischer Starthinweis hilfreich ist
- Die Progression zum vorherigen Block relevant ist (ab Block 2)
- Die Motivation des Klienten eine Verbindung zur Übung ermöglicht

═══════════════════════════════════════════════════════════════════
AUSWAHLPRINZIPIEN
═══════════════════════════════════════════════════════════════════

1. Verletzungen haben Vorrang: Gibt es eine Verletzung im relevanten Gelenk,
   wähle die gelenkschonendere Variante — auch wenn eine schwerere möglich wäre

2. Level respektieren: Bevorzuge Übungen die zum Level des Klienten passen.
   Level 1 Klient → keine Level 3 Übungen als Hauptübung

3. Variation über den Block: Innerhalb einer 4-Wochen-Periode dieselben Übungen.
   In einem neuen Block (block_nummer > 1) kannst du 1-2 Übungen durch
   progressions_up-Varianten ersetzen wenn der Klient Fortschritt gemacht hat.

4. Symmetrie: Push/Pull ausgeglichen halten. Nicht 3 Push- und 1 Pull-Übung.

5. Hauptübung zuerst: Der energieintensivste Compound-Lift steht auf Platz 1.
   Isolation und Prähab kommen am Ende der Session.

═══════════════════════════════════════════════════════════════════
OUTPUT FORMAT — exakt dieses JSON, kein Text drumherum
═══════════════════════════════════════════════════════════════════

{
  "sessions": [
    {
      "session_id": "w1_s1",
      "uebungen": [
        {
          "reihenfolge": 1,
          "exercise_id": "EXAKT_WIE_IN_DER_LISTE",
          "notiz": "Klient-spezifische Notiz oder leerer String"
        }
      ]
    }
  ]
}

═══════════════════════════════════════════════════════════════════
BEISPIEL — so soll dein Output aussehen
═══════════════════════════════════════════════════════════════════

Klient: Thomas, 42 Jahre, Level 2, Gym, Muskelaufbau, 4 Tage/Woche
Verletzungen: Schulter links (leicht)
Block 1, Woche 1

Dein Output:

{
  "sessions": [
    {
      "session_id": "w1_s1",
      "uebungen": [
        {
          "reihenfolge": 1,
          "exercise_id": "gym_db_bench_press",
          "notiz": "Kurzhantel statt Langhantel — schonender für die linke Schulter. Sobald schmerzfrei: Wechsel zu gym_bench_press in Block 2."
        },
        {
          "reihenfolge": 2,
          "exercise_id": "gym_incline_db_press",
          "notiz": ""
        },
        {
          "reihenfolge": 3,
          "exercise_id": "gym_landmine_ohp",
          "notiz": "Landmine statt Overhead Press — schulterfreundlichere Drückbahn bei Schulter-Issues."
        },
        {
          "reihenfolge": 4,
          "exercise_id": "gym_cable_lateral_raise",
          "notiz": ""
        },
        {
          "reihenfolge": 5,
          "exercise_id": "gym_face_pull",
          "notiz": ""
        }
      ]
    },
    {
      "session_id": "w1_s2",
      "uebungen": [
        {
          "reihenfolge": 1,
          "exercise_id": "gym_back_squat",
          "notiz": "Startgewicht: 70-75% von dem was du kennst — Woche 1 ist Technik-Check."
        },
        {
          "reihenfolge": 2,
          "exercise_id": "gym_bulgarian_split_squat_db",
          "notiz": "Schwächere Seite zuerst — dann gleiche Wdh mit der stärkeren."
        },
        {
          "reihenfolge": 3,
          "exercise_id": "gym_leg_press_machine",
          "notiz": ""
        },
        {
          "reihenfolge": 4,
          "exercise_id": "bw_dead_bug",
          "notiz": ""
        }
      ]
    }
  ]
}"""


# ═══════════════════════════════════════════════════════════════════════════════
# USER PROMPT BUILDER
# Wird von Python nach den Berechnungen aufgerufen.
# Gibt den vollständigen User-Prompt als String zurück.
# ═══════════════════════════════════════════════════════════════════════════════

def build_user_prompt(
    klient: KlientenInput,
    level: int,
    split_typ: str,
    block_nummer: int,
    sessions: list[dict],           # [{"session_id": "w1_s1", "fokus": "...", "slots": [...]}]
    uebungen_gefiltert: dict[str, list[dict]],  # {"squat": [...], "hinge": [...], ...}
    woche_typ: str,                 # "akkumulation" | "progression" | ...
    ziel_saetze: int,
    ziel_rpe: int,
) -> str:

    verletzungen_str = (
        ", ".join(v.value for v in klient.verletzungen)
        if klient.verletzungen else "keine"
    )

    schmerzen_str = "⚠️ AKUTER SCHMERZ — besonders vorsichtig bei Übungsauswahl" if klient.schmerzen_akut else "kein akuter Schmerz"

    motivation_str = f'"{klient.motivation}"' if klient.motivation else "nicht angegeben"

    lines = [
        "═══════════════════════════════════════════════════════════════",
        "KLIENT",
        "═══════════════════════════════════════════════════════════════",
        f"Name:        {klient.vorname}",
        f"Alter:       {klient.alter} Jahre",
        f"Level:       {level}/4",
        f"Ziel:        {klient.hauptziel.value}",
        f"Equipment:   {klient.equipment.value}",
        f"Verletzungen: {verletzungen_str}",
        f"Schmerz:     {schmerzen_str}",
        f"Stress:      {klient.stress_level}/10 | Schlaf: {klient.schlaf_stunden}h",
        f"Motivation:  {motivation_str}",
        "",
        "═══════════════════════════════════════════════════════════════",
        "TRAININGSPARAMETER (von Python berechnet — nicht ändern)",
        "═══════════════════════════════════════════════════════════════",
        f"Block:       {block_nummer}",
        f"Split:       {split_typ}",
        f"Woche-Typ:   {woche_typ}",
        f"Ziel-Sätze:  {ziel_saetze}",
        f"Ziel-RPE:    {ziel_rpe}/10",
        "",
    ]

    # Sessions und Slots
    lines += [
        "═══════════════════════════════════════════════════════════════",
        "SESSIONS — befülle jeden Slot mit einer exercise_id aus der Liste",
        "═══════════════════════════════════════════════════════════════",
    ]

    for session in sessions:
        lines.append(f"\nSession {session['session_id']} — {session['fokus'].upper()}")
        for i, slot in enumerate(session["slots"], 1):
            lines.append(f"  Slot {i}: {slot['beschreibung']} (Pattern: {slot['pattern']}, bevorzugt Level ≤ {slot.get('max_level', level)})")

    # Verfügbare Übungen
    lines += [
        "",
        "═══════════════════════════════════════════════════════════════",
        "VERFÜGBARE ÜBUNGEN — NUR diese IDs verwenden",
        "═══════════════════════════════════════════════════════════════",
    ]

    for pattern, uebungen in uebungen_gefiltert.items():
        if not uebungen:
            continue
        lines.append(f"\n{pattern.upper()}:")
        for u in uebungen:
            # equipment_filter adds 'verletzungs_flag' (English keys) per exercise
            flagged = u.get("verletzungs_flag", [])
            verletzungs_hinweis = f" ⚠️ hat Substitution für: {', '.join(flagged)}" if flagged else ""
            lines.append(f"  - {u['id']} (Level {u['level_min']}){verletzungs_hinweis}")

    # Output-Anweisung
    lines += [
        "",
        "═══════════════════════════════════════════════════════════════",
        "DEINE AUFGABE",
        "═══════════════════════════════════════════════════════════════",
        "Wähle für jeden Slot eine exercise_id aus der Liste oben.",
        "Schreibe bei Bedarf eine kurze klient-spezifische Notiz.",
        "Antworte NUR mit dem JSON — kein Text davor oder danach.",
    ]

    return "\n".join(lines)
