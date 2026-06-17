"""
End-to-End Test: fake_typeform.json → parse → logic → Claude API → validate output

Verwendung:
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/test_pipeline.py
"""

from __future__ import annotations
import json
import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from parsers import parse_typeform_payload
from logic.level_calculator import berechne_level
from logic.volume_calculator import berechne_volumen
from logic.split_selector import waehle_split
from logic.equipment_filter import filtere_uebungen
from logging_config import setup_logging


def main():
    setup_logging()   # damit das claude_client-Logging (ohne main) sichtbar ist
    payload_path = pathlib.Path(__file__).parent.parent / "data" / "fake_typeform.json"
    payload = json.loads(payload_path.read_text())

    print("=== 1. Typeform parsen ===")
    klient = parse_typeform_payload(payload)
    print(f"Klient:      {klient.vorname}, {klient.alter}J, {klient.equipment.value}")
    print(f"Ziel:        {klient.hauptziel.value}")
    print(f"Tage:        {klient.tage_pro_woche}/Woche, {klient.session_dauer_min}min")
    print(f"Verletzungen: {[v.value for v in klient.verletzungen] or 'keine'}")

    print("\n=== 2. Level ===")
    level, punkte = berechne_level(klient)
    print(f"PST:  {punkte}  →  Gesamt {sum(punkte.values())} → Level {level}")

    print("\n=== 3. Volumen ===")
    woche_typ = "akkumulation"
    volumen = berechne_volumen(klient, level, woche_typ)
    print(f"{woche_typ}: {volumen['ziel_saetze']} Sätze, RPE {volumen['ziel_rpe']} ({volumen['recovery_modifier']})")

    print("\n=== 4. Split ===")
    split = waehle_split(klient, level)
    print(f"Split: {split['split_typ']}")
    for s in split["sessions"]:
        print(f"  {s['session_id']} — {s['fokus']}")

    print("\n=== 5. Equipment-Filter ===")
    uebungen = filtere_uebungen(klient, level)
    total = sum(len(v) for v in uebungen.values())
    print(f"{total} Übungen verfügbar")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠️  ANTHROPIC_API_KEY nicht gesetzt — Claude-Aufruf übersprungen.")
        print("   export ANTHROPIC_API_KEY=sk-ant-...")
        return

    print("\n=== 6. Claude API ===")
    from claude.claude_client import generiere_uebungsauswahl

    output = generiere_uebungsauswahl(
        klient=klient,
        level=level,
        split_typ=split["split_typ"],
        block_nummer=1,
        sessions=split["sessions"],
        uebungen_gefiltert=uebungen,
        woche_typ=woche_typ,
        ziel_saetze=volumen["ziel_saetze"],
        ziel_rpe=volumen["ziel_rpe"],
    )

    print(f"✅ {len(output.sessions)} Sessions:")
    for s in output.sessions:
        print(f"\n  {s.session_id}:")
        for u in s.uebungen:
            notiz = f"\n    → {u.notiz}" if u.notiz else ""
            print(f"    {u.reihenfolge}. {u.exercise_id}{notiz}")


if __name__ == "__main__":
    main()
